from datetime import datetime, timezone
import re
from difflib import SequenceMatcher
from app.models import db, Complaint, StatusTimeline, Feedback, User
from app.services.notification_service import create_notification

def utc_now():
    return datetime.now(timezone.utc)

def generate_complaint_id() -> str:
    """Generates unique formatted complaint ID, e.g. SC-2026-00001"""
    year = utc_now().year
    prefix = f"SC-{year}-"
    last_complaint = (
        Complaint.query.filter(
            (Complaint.complaint_id.like(f"{prefix}%")) |
            (Complaint.complaint_id.like(f"CMP-{year}-%"))
        )
        .order_by(Complaint.id.desc())
        .first()
    )
    if last_complaint:
        try:
            last_number = int(last_complaint.complaint_id.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    return f"{prefix}{new_number:05d}"

def detect_duplicates(title: str, description: str, category: str, exclude_id: int = None, threshold: float = 0.65):
    """
    Scans existing active complaints in the same category or overall to detect potential duplicates.
    Returns a list of matching complaints with similarity scores.
    """
    clean_target = f"{title.lower()} {description.lower()}"
    query = Complaint.query
    if category:
        query = query.filter(Complaint.category == category)
    if exclude_id:
        query = query.filter(Complaint.id != exclude_id)
    
    # Check complaints from the last 90 days
    recent_complaints = query.order_by(Complaint.created_at.desc()).limit(50).all()
    duplicates = []

    for c in recent_complaints:
        candidate_text = f"{c.title.lower()} {c.description.lower()}"
        ratio = SequenceMatcher(None, clean_target, candidate_text).ratio()
        if ratio >= threshold or (title.lower().strip() in c.title.lower().strip() and len(title.strip()) > 8):
            duplicates.append({
                'complaint': c,
                'similarity': round(ratio * 100, 1)
            })

    # Sort descending by similarity
    duplicates.sort(key=lambda x: x['similarity'], reverse=True)
    return duplicates[:5]

def create_complaint(user_id: int, title: str, description: str, category: str, priority: str, 
                     attachment: str = None, subcategory: str = None, state: str = None, 
                     city: str = None, area: str = None, street_name: str = None, 
                     landmark: str = None, latitude: float = None, longitude: float = None, 
                     video_attachment: str = None, contact_phone: str = None):
    new_id = generate_complaint_id()
    complaint = Complaint(
        complaint_id=new_id,
        user_id=user_id,
        title=title.strip(),
        description=description.strip(),
        category=category,
        subcategory=subcategory.strip() if subcategory else None,
        priority=priority,
        status='Submitted',
        attachment=attachment,
        video_attachment=video_attachment,
        state=state.strip() if state else None,
        city=city.strip() if city else None,
        area=area.strip() if area else None,
        street_name=street_name.strip() if street_name else None,
        landmark=landmark.strip() if landmark else None,
        latitude=latitude,
        longitude=longitude,
        contact_phone=contact_phone.strip() if contact_phone else None
    )
    db.session.add(complaint)
    db.session.flush()

    # Initial timeline entry
    timeline_entry = StatusTimeline(
        complaint_id=complaint.id,
        status='Submitted',
        note='Grievance registered in the system.',
        changed_by=user_id
    )
    db.session.add(timeline_entry)

    # In-app notification to the user
    create_notification(
        user_id=user_id,
        complaint_id=complaint.id,
        message=f"Grievance #{new_id} '{title[:35]}...' submitted successfully. We will track and update you."
    )

    db.session.commit()
    return complaint

def update_status(complaint: Complaint, new_status: str, changed_by_user_id: int, note: str = None, rejection_reason: str = None, resolution_note: str = None):
    old_status = complaint.status
    complaint.status = new_status
    if rejection_reason:
        complaint.rejection_reason = rejection_reason
    if resolution_note:
        complaint.resolution_note = resolution_note
    complaint.updated_at = utc_now()

    timeline_entry = StatusTimeline(
        complaint_id=complaint.id,
        status=new_status,
        note=note or (f"Status changed from {old_status} to {new_status}." if not rejection_reason else f"Rejected: {rejection_reason}"),
        changed_by=changed_by_user_id
    )
    db.session.add(timeline_entry)

    # Notify the user
    if new_status == 'Resolved':
        msg = f"Your grievance #{complaint.complaint_id} has been marked as Resolved."
        if resolution_note:
            msg += f" Note: {resolution_note}"
    elif new_status == 'Rejected':
        msg = f"Your grievance #{complaint.complaint_id} was rejected."
        if rejection_reason:
            msg += f" Reason: {rejection_reason}"
    elif new_status == 'Reopened':
        msg = f"Grievance #{complaint.complaint_id} has been reopened for further inspection."
    elif new_status == 'Closed':
        msg = f"Grievance #{complaint.complaint_id} has been officially closed."
    else:
        msg = f"Your grievance #{complaint.complaint_id} status changed to '{new_status}'."

    create_notification(
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        message=msg
    )

    db.session.commit()
    return complaint

def assign_complaint(complaint: Complaint, department_id: int, staff_id: int, assigned_by_user_id: int, note: str = None):
    complaint.department_id = department_id
    complaint.assigned_to = staff_id
    complaint.status = 'Assigned'
    complaint.updated_at = utc_now()

    assignee = db.session.get(User, staff_id) if staff_id else None
    assignee_name = assignee.full_name if assignee else "Department Staff"

    timeline_note = note or f"Complaint assigned to {assignee_name}."
    timeline_entry = StatusTimeline(
        complaint_id=complaint.id,
        status='Assigned',
        note=timeline_note,
        changed_by=assigned_by_user_id
    )
    db.session.add(timeline_entry)

    # Notify submitter
    create_notification(
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        message=f"Your complaint #{complaint.complaint_id} has been assigned to {assignee_name}."
    )

    # Notify staff member if assigned
    if staff_id:
        create_notification(
            user_id=staff_id,
            complaint_id=complaint.id,
            message=f"New complaint #{complaint.complaint_id} '{complaint.title[:30]}' has been assigned to you."
        )

    db.session.commit()
    return complaint

def submit_feedback(complaint_id: int, user_id: int, rating: int, comment: str):
    complaint = Complaint.query.filter_by(id=complaint_id, user_id=user_id).first_or_404()
    if complaint.feedback:
        complaint.feedback.rating = rating
        complaint.feedback.comment = comment
        complaint.feedback.submitted_at = utc_now()
        feedback = complaint.feedback
    else:
        feedback = Feedback(
            complaint_id=complaint_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)
    db.session.commit()
    return feedback
