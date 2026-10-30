import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify, send_from_directory, g
from app.models import db, Complaint, Department, Feedback, Notification
from app.routes.auth import login_required
from app.services.complaint_service import create_complaint, detect_duplicates, submit_feedback
from app.services.notification_service import get_user_notifications, mark_notification_as_read, mark_all_notifications_as_read

user_bp = Blueprint('user', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@user_bp.route('/')
def index():
    if 'user_id' in session:
        role = session.get('user_role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'staff':
            return redirect(url_for('staff.dashboard'))
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    total_complaints = Complaint.query.filter_by(user_id=user_id).count()
    pending = Complaint.query.filter(Complaint.user_id == user_id, Complaint.status.in_(['Submitted', 'Under Review'])).count()
    in_progress = Complaint.query.filter(Complaint.user_id == user_id, Complaint.status.in_(['Assigned', 'In Progress'])).count()
    resolved = Complaint.query.filter_by(user_id=user_id, status='Resolved').count()
    rejected = Complaint.query.filter_by(user_id=user_id, status='Rejected').count()

    recent_complaints = (
        Complaint.query.filter_by(user_id=user_id)
        .order_by(Complaint.created_at.desc())
        .limit(6)
        .all()
    )

    notifications = get_user_notifications(user_id=user_id, limit=5)
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    stats = {
        'total': total_complaints,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
        'unread_count': unread_count
    }

    return render_template(
        'user/dashboard.html',
        stats=stats,
        recent_complaints=recent_complaints,
        notifications=notifications
    )

@user_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    departments = Department.query.order_by(Department.name).all()
    categories = ['IT & Software', 'Hostel & Facilities', 'Finance & Billing', 'Administration', 'Academics', 'Infrastructure', 'General']

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General')
        priority = request.form.get('priority', 'Medium')
        force_submit = request.form.get('force_submit') == 'true'

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('user/submit_complaint.html', departments=departments, categories=categories)

        # Check for duplicates unless user explicitly bypassed
        if not force_submit:
            duplicates = detect_duplicates(title, description, category)
            if duplicates:
                return render_template(
                    'user/submit_complaint.html',
                    departments=departments,
                    categories=categories,
                    potential_duplicates=duplicates,
                    form_data=request.form
                )

        # Handle attachment
        attachment_filename = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                    safe_name = secure_filename(f"{session['user_id']}_{int(os.times()[4])}_{file.filename}")
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)
                    file.save(file_path)
                    attachment_filename = safe_name
                else:
                    flash('File type not allowed. Allowed types: PNG, JPG, PDF, DOC, DOCX, TXT', 'warning')
                    return render_template('user/submit_complaint.html', departments=departments, categories=categories)

        complaint = create_complaint(
            user_id=session['user_id'],
            title=title,
            description=description,
            category=category,
            priority=priority,
            attachment=attachment_filename
        )

        flash(f'Complaint #{complaint.complaint_id} submitted successfully!', 'success')
        return redirect(url_for('user.track_complaint', complaint_id=complaint.complaint_id))

    return render_template('user/submit_complaint.html', departments=departments, categories=categories)

@user_bp.route('/track')
@user_bp.route('/track/<complaint_id>')
@login_required
def track_complaint(complaint_id=None):
    user_id = session['user_id']
    query_id = complaint_id or request.args.get('complaint_id', '').strip()

    complaint = None
    if query_id:
        if session.get('user_role') in ('admin', 'staff'):
            complaint = Complaint.query.filter(Complaint.complaint_id.ilike(query_id)).first()
        else:
            complaint = Complaint.query.filter(Complaint.complaint_id.ilike(query_id), Complaint.user_id == user_id).first()

        if not complaint:
            flash(f'Complaint "{query_id}" not found or you do not have permission to view it.', 'warning')

    return render_template('user/track_complaint.html', complaint=complaint, query_id=query_id)

@user_bp.route('/history')
@login_required
def complaint_history():
    user_id = session['user_id']
    status_filter = request.args.get('status', '').strip()
    category_filter = request.args.get('category', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    search = request.args.get('search', '').strip()

    query = Complaint.query.filter_by(user_id=user_id)

    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(search_pattern)) |
            (Complaint.title.ilike(search_pattern)) |
            (Complaint.description.ilike(search_pattern))
        )

    page = request.args.get('page', 1, type=int)
    per_page = 8
    pagination = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    complaints = pagination.items
    categories = ['IT & Software', 'Hostel & Facilities', 'Finance & Billing', 'Administration', 'Academics', 'Infrastructure', 'General']

    return render_template(
        'user/complaint_history.html',
        complaints=complaints,
        pagination=pagination,
        status_filter=status_filter,
        category_filter=category_filter,
        priority_filter=priority_filter,
        search=search,
        categories=categories
    )

@user_bp.route('/feedback/<int:complaint_id>', methods=['POST'])
@login_required
def give_feedback(complaint_id):
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '').strip()

    try:
        submit_feedback(complaint_id=complaint_id, user_id=session['user_id'], rating=rating, comment=comment)
        flash('Thank you! Your feedback has been recorded.', 'success')
    except Exception as e:
        flash(f'Could not submit feedback: {str(e)}', 'danger')

    complaint = db.session.get(Complaint, complaint_id)
    return redirect(url_for('user.track_complaint', complaint_id=complaint.complaint_id if complaint else None))

@user_bp.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    all_notifs = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    return render_template('user/notifications.html', notifications=all_notifs)

@user_bp.route('/notifications/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    mark_notification_as_read(notif_id, session['user_id'])
    return jsonify({'success': True})

@user_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_read():
    mark_all_notifications_as_read(session['user_id'])
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('user.notifications'))

@user_bp.route('/uploads/<filename>')
@login_required
def view_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@user_bp.route('/api/check-duplicates', methods=['POST'])
@login_required
def api_check_duplicates():
    data = request.get_json() or {}
    title = data.get('title', '')
    desc = data.get('description', '')
    category = data.get('category', '')

    if len(title.strip()) < 5:
        return jsonify({'duplicates': []})

    results = detect_duplicates(title, desc, category)
    formatted = []
    for r in results:
        formatted.append({
            'complaint_id': r['complaint'].complaint_id,
            'title': r['complaint'].title,
            'status': r['complaint'].status,
            'category': r['complaint'].category,
            'similarity': r['similarity']
        })
    return jsonify({'duplicates': formatted})

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = db.session.get(Complaint.submitter.property.mapper.class_, session['user_id'])
    if not user:
        from app.models import User
        user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if full_name:
            user.full_name = full_name
            session['user_name'] = full_name

        user.phone = phone

        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'warning')
                return redirect(url_for('user.profile'))
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('user.profile'))
            user.set_password(new_password)
            flash('Profile and password updated successfully.', 'success')
        else:
            flash('Profile updated successfully.', 'success')

        db.session.commit()
        return redirect(url_for('user.profile'))

    user_stats = {
        'total': Complaint.query.filter_by(user_id=user.id).count(),
        'resolved': Complaint.query.filter_by(user_id=user.id, status='Resolved').count(),
        'pending': Complaint.query.filter(Complaint.user_id == user.id, Complaint.status.in_(['Submitted', 'Under Review'])).count(),
    }
    return render_template('user/profile.html', user=user, user_stats=user_stats)
