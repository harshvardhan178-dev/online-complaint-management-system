from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file, jsonify, Response
from app.models import db, Complaint, User, Department, StatusTimeline, Feedback
from app.routes.auth import admin_required
from app.services.complaint_service import update_status, assign_complaint
from app.services.report_service import generate_csv_report, generate_pdf_report, get_analytics_summary

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@admin_required
def admin_guard():
    pass

@admin_bp.route('/dashboard')
def dashboard():
    analytics = get_analytics_summary()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(8).all()
    departments = Department.query.order_by(Department.name).all()
    staff_members = User.query.filter_by(role='staff', is_active=True).all()

    return render_template(
        'admin/dashboard.html',
        analytics=analytics,
        total_users=total_users,
        total_staff=total_staff,
        recent_complaints=recent_complaints,
        departments=departments,
        staff_members=staff_members
    )

@admin_bp.route('/complaints')
def complaints():
    status = request.args.get('status', '').strip()
    category = request.args.get('category', '').strip()
    priority = request.args.get('priority', '').strip()
    dept_id = request.args.get('department_id', type=int)
    search = request.args.get('search', '').strip()

    query = Complaint.query

    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if dept_id:
        query = query.filter(Complaint.department_id == dept_id)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(pattern)) |
            (Complaint.title.ilike(pattern)) |
            (Complaint.description.ilike(pattern))
        )

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    complaints_list = pagination.items
    departments = Department.query.order_by(Department.name).all()
    staff_members = User.query.filter_by(role='staff', is_active=True).all()

    return render_template(
        'admin/complaints.html',
        complaints=complaints_list,
        pagination=pagination,
        departments=departments,
        staff_members=staff_members,
        selected_status=status,
        selected_category=category,
        selected_priority=priority,
        selected_dept=dept_id,
        search=search
    )

@admin_bp.route('/complaint/<int:complaint_id>/assign', methods=['POST'])
def assign(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    dept_id = request.form.get('department_id', type=int)
    staff_id = request.form.get('staff_id', type=int)
    note = request.form.get('note', '').strip()

    assign_complaint(
        complaint=complaint,
        department_id=dept_id,
        staff_id=staff_id,
        assigned_by_user_id=session['user_id'],
        note=note or "Assigned by Administrator."
    )
    flash(f'Complaint #{complaint.complaint_id} assigned successfully.', 'success')
    return redirect(request.referrer or url_for('admin.complaints'))

@admin_bp.route('/complaint/<int:complaint_id>/status', methods=['POST'])
def change_status(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    new_status = request.form.get('status')
    note = request.form.get('note', '').strip()
    rejection_reason = request.form.get('rejection_reason', '').strip() if new_status == 'Rejected' else None

    update_status(
        complaint=complaint,
        new_status=new_status,
        changed_by_user_id=session['user_id'],
        note=note,
        rejection_reason=rejection_reason
    )
    flash(f'Complaint #{complaint.complaint_id} status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('admin.complaints'))

@admin_bp.route('/users')
def users():
    role_filter = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip()

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        pattern = f"%{search}%"
        query = query.filter((User.full_name.ilike(pattern)) | (User.email.ilike(pattern)))

    users_list = query.order_by(User.created_at.desc()).all()
    departments = Department.query.order_by(Department.name).all()

    return render_template('admin/users.html', users=users_list, departments=departments, role_filter=role_filter, search=search)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    if user_id == session['user_id']:
        flash('You cannot deactivate your own admin account.', 'danger')
        return redirect(url_for('admin.users'))

    user = db.get_or_404(User, user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User {user.full_name} has been {status_str}.", 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
def update_user(user_id):
    user = db.get_or_404(User, user_id)
    role = request.form.get('role', user.role)
    dept_id = request.form.get('department_id', type=int)

    # Protect self-demotion from admin
    if user.id == session['user_id'] and role != 'admin':
        flash('You cannot change your own admin role.', 'warning')
        return redirect(url_for('admin.users'))

    user.role = role
    user.department_id = dept_id if role == 'staff' else None
    db.session.commit()
    flash(f"User {user.full_name} updated successfully.", 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/departments/add', methods=['POST'])
def add_department():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Department name is required.', 'danger')
        return redirect(url_for('admin.users'))

    existing = Department.query.filter(Department.name.ilike(name)).first()
    if existing:
        flash('Department already exists.', 'warning')
        return redirect(url_for('admin.users'))

    dept = Department(name=name, description=description)
    db.session.add(dept)
    db.session.commit()
    flash(f"Department '{name}' added successfully.", 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/reports')
def reports():
    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/reports.html', departments=departments)

@admin_bp.route('/reports/export/csv')
def export_csv():
    status = request.args.get('status')
    category = request.args.get('category')
    dept_id = request.args.get('department_id', type=int)

    query = Complaint.query
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if dept_id:
        query = query.filter_by(department_id=dept_id)

    complaints_list = query.order_by(Complaint.created_at.desc()).all()
    csv_stream = generate_csv_report(complaints_list)

    filename = f"complaints_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_stream.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@admin_bp.route('/reports/export/pdf')
def export_pdf():
    status = request.args.get('status')
    category = request.args.get('category')
    dept_id = request.args.get('department_id', type=int)

    query = Complaint.query
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if dept_id:
        query = query.filter_by(department_id=dept_id)

    complaints_list = query.order_by(Complaint.created_at.desc()).all()
    pdf_buffer = generate_pdf_report(complaints_list)

    filename = f"complaints_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route('/analytics')
def analytics():
    summary = get_analytics_summary()
    return render_template('admin/analytics.html', analytics=summary)
