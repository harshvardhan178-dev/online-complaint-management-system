from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import db, Complaint, StatusTimeline
from app.routes.auth import staff_required
from app.services.complaint_service import update_status

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.before_request
@staff_required
def staff_guard():
    pass

@staff_bp.route('/dashboard')
def dashboard():
    staff_id = session['user_id']
    status_filter = request.args.get('status', '').strip()
    priority_filter = request.args.get('priority', '').strip()

    query = Complaint.query.filter(
        (Complaint.assigned_to == staff_id) |
        ((Complaint.assigned_to == None) & (Complaint.department_id == session.get('department_id')))
    )

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority_filter:
        query = query.filter(Complaint.priority == priority_filter)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    # KPI counts
    total = Complaint.query.filter_by(assigned_to=staff_id).count()
    assigned_count = Complaint.query.filter_by(assigned_to=staff_id, status='Assigned').count()
    in_progress_count = Complaint.query.filter_by(assigned_to=staff_id, status='In Progress').count()
    resolved_count = Complaint.query.filter_by(assigned_to=staff_id, status='Resolved').count()

    stats = {
        'total': total,
        'assigned': assigned_count,
        'in_progress': in_progress_count,
        'resolved': resolved_count
    }

    return render_template(
        'staff/dashboard.html',
        complaints=complaints,
        stats=stats,
        status_filter=status_filter,
        priority_filter=priority_filter
    )

@staff_bp.route('/complaint/<int:complaint_id>')
def complaint_detail(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    return render_template('staff/complaint_detail.html', complaint=complaint)

@staff_bp.route('/complaint/<int:complaint_id>/progress', methods=['POST'])
def update_progress(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    note = request.form.get('note', '').strip()

    if not note:
        flash('Progress note cannot be empty.', 'warning')
        return redirect(url_for('staff.complaint_detail', complaint_id=complaint_id))

    update_status(
        complaint=complaint,
        new_status='In Progress',
        changed_by_user_id=session['user_id'],
        note=note
    )
    flash('Progress updated successfully.', 'success')
    return redirect(url_for('staff.complaint_detail', complaint_id=complaint_id))

@staff_bp.route('/complaint/<int:complaint_id>/resolve', methods=['POST'])
def resolve(complaint_id):
    complaint = db.get_or_404(Complaint, complaint_id)
    resolution_note = request.form.get('resolution_note', '').strip()

    if not resolution_note:
        flash('Please describe how the complaint was resolved.', 'warning')
        return redirect(url_for('staff.complaint_detail', complaint_id=complaint_id))

    update_status(
        complaint=complaint,
        new_status='Resolved',
        changed_by_user_id=session['user_id'],
        note=f"Resolved: {resolution_note}",
        resolution_note=resolution_note
    )
    flash(f'Complaint #{complaint.complaint_id} marked as Resolved.', 'success')
    return redirect(url_for('staff.dashboard'))
