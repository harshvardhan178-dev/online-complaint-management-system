"""
Demo Data Seeder for SmartComplaint System
Populates realistic sample complaints, timeline entries, notifications, and feedback.
"""
from datetime import datetime, timedelta, timezone
from app import create_app
from app.models import db, User, Department, Complaint, StatusTimeline, Notification, Feedback

def run_seed():
    app = create_app()
    with app.app_context():
        print("Seeding realistic sample complaints and demo accounts...")

        # Get or create additional staff / demo users
        it_dept = Department.query.filter_by(name="IT Support").first()
        facilities_dept = Department.query.filter_by(name="Facilities & Maintenance").first()
        finance_dept = Department.query.filter_by(name="Finance & Accounts").first()
        admin_dept = Department.query.filter_by(name="Administration").first()
        academic_dept = Department.query.filter_by(name="Academic Affairs").first()

        admin_user = User.query.filter_by(role='admin').first()
        default_user = User.query.filter_by(email='user@smartcomplaint.com').first()
        staff_it = User.query.filter_by(email='staff@smartcomplaint.com').first()

        # Add Facilities Staff if not present
        staff_facilities = User.query.filter_by(email='facilities_staff@smartcomplaint.com').first()
        if not staff_facilities:
            staff_facilities = User(
                full_name='Marcus Vance',
                email='facilities_staff@smartcomplaint.com',
                phone='9876543220',
                role='staff',
                department_id=facilities_dept.id if facilities_dept else None,
                is_active=True
            )
            staff_facilities.set_password('Staff@123')
            db.session.add(staff_facilities)

        # Add second student/user
        student_sarah = User.query.filter_by(email='sarah@smartcomplaint.com').first()
        if not student_sarah:
            student_sarah = User(
                full_name='Sarah Jenkins',
                email='sarah@smartcomplaint.com',
                phone='9876543221',
                role='user',
                is_active=True
            )
            student_sarah.set_password('User@123')
            db.session.add(student_sarah)

        db.session.commit()

        # Check if sample complaints already seeded
        if Complaint.query.count() > 0:
            print(f"Database already contains {Complaint.query.count()} complaints. Skipping seed.")
            return

        now = datetime.now(timezone.utc)

        sample_tickets = [
            {
                'id_code': 'CMP-2026-00001',
                'user': default_user,
                'title': 'High-speed Wi-Fi dropping frequently in Science Block B',
                'desc': 'Wi-Fi access points on floors 2 and 3 keep disconnecting during lectures. Signal strength drops to 0 bars randomly.',
                'cat': 'IT & Software',
                'priority': 'High',
                'status': 'Resolved',
                'dept': it_dept,
                'staff': staff_it,
                'created_offset': 15,
                'resolution_note': 'Rebooted Cisco core switch, updated AP firmware to version 12.4.2, and replaced frayed patch cable in rack 2.',
                'timeline': [
                    (15, 'Submitted', 'Complaint submitted via web portal.', default_user),
                    (14, 'Under Review', 'Acknowledged by IT Helpdesk.', admin_user),
                    (13, 'Assigned', 'Assigned to Alex Rivera (Network Support).', admin_user),
                    (12, 'In Progress', 'Inspected switch room B-204; diagnostics showed high packet loss on trunk port.', staff_it),
                    (10, 'Resolved', 'Replaced faulty Ethernet patch cable and restarted AP cluster. Connection stability verified.', staff_it)
                ],
                'feedback': (5, 'Wi-Fi has been rock solid ever since. Great turnaround time!')
            },
            {
                'id_code': 'CMP-2026-00002',
                'user': student_sarah,
                'title': 'Water leakage under sink in Hostel Block 4, Room 204',
                'desc': 'Severe continuous pipe dripping under the shared bathroom sink causing standing water on the tiled floor.',
                'cat': 'Hostel & Facilities',
                'priority': 'Critical',
                'status': 'In Progress',
                'dept': facilities_dept,
                'staff': staff_facilities,
                'created_offset': 6,
                'resolution_note': None,
                'timeline': [
                    (6, 'Submitted', 'Reported urgent water leakage in hostel washroom.', student_sarah),
                    (5, 'Assigned', 'Urgent maintenance request routed to plumbing dispatch.', admin_user),
                    (4, 'In Progress', 'Plumber inspected pipe; shutoff valve replaced. Sourcing replacement U-bend pipe from warehouse.', staff_facilities)
                ],
                'feedback': None
            },
            {
                'id_code': 'CMP-2026-00003',
                'user': default_user,
                'title': 'Double charge on semester examination fee invoice',
                'desc': 'My credit card transaction was deducted twice ($150 x 2) for receipt reference #EXAM-9921 on October 20th.',
                'cat': 'Finance & Billing',
                'priority': 'Medium',
                'status': 'Under Review',
                'dept': finance_dept,
                'staff': None,
                'created_offset': 4,
                'resolution_note': None,
                'timeline': [
                    (4, 'Submitted', 'Transaction duplicate dispute lodged by student.', default_user),
                    (2, 'Under Review', 'Forwarded to Accounts Payable bank reconciliation team.', admin_user)
                ],
                'feedback': None
            },
            {
                'id_code': 'CMP-2026-00004',
                'user': student_sarah,
                'title': 'Projector bulb burned out in Audi 2',
                'desc': 'Ceiling digital projector blinks orange and fails to project display signals during afternoon seminars.',
                'cat': 'IT & Software',
                'priority': 'High',
                'status': 'Assigned',
                'dept': it_dept,
                'staff': staff_it,
                'created_offset': 3,
                'resolution_note': None,
                'timeline': [
                    (3, 'Submitted', 'Complaint filed by Faculty Representative.', student_sarah),
                    (2, 'Assigned', 'Assigned to IT media operations for bulb replacement.', admin_user)
                ],
                'feedback': None
            },
            {
                'id_code': 'CMP-2026-00005',
                'user': default_user,
                'title': 'Air conditioning unit leaking refrigerant odor in Seminar Hall',
                'desc': 'Strong chemical smell and rattling compressor noise coming from ceiling duct in Seminar Room C.',
                'cat': 'Hostel & Facilities',
                'priority': 'Medium',
                'status': 'Resolved',
                'dept': facilities_dept,
                'staff': staff_facilities,
                'created_offset': 25,
                'resolution_note': 'HVAC technician serviced compressor unit, cleaned internal condenser coils and refilled coolant safely.',
                'timeline': [
                    (25, 'Submitted', 'Initial complaint logged.', default_user),
                    (24, 'Assigned', 'Assigned to HVAC maintenance crew.', admin_user),
                    (22, 'In Progress', 'Filters cleaned, technicians sealed minor joint leak.', staff_facilities),
                    (20, 'Resolved', 'Cooling restored to 21°C and odor cleared completely.', staff_facilities)
                ],
                'feedback': (4, 'Issue resolved satisfactorily and air is clean again.')
            },
            {
                'id_code': 'CMP-2026-00006',
                'user': student_sarah,
                'title': 'Request to change exam date for personal family vacation',
                'desc': 'Requesting faculty administration to shift final physics exam by 3 days due to non-refundable flight bookings.',
                'cat': 'Academics',
                'priority': 'Low',
                'status': 'Rejected',
                'dept': academic_dept,
                'staff': None,
                'created_offset': 18,
                'rejection_reason': 'According to Section 4.2 of the Academic Policy, universal examinations cannot be rescheduled for personal vacations without certified medical grounds.',
                'timeline': [
                    (18, 'Submitted', 'Student submitted exam date change request.', student_sarah),
                    (17, 'Under Review', 'Reviewed against academic board calendar guidelines.', admin_user),
                    (16, 'Rejected', 'Rejected: University exam board regulations strictly prohibit vacation rescheduling.', admin_user)
                ],
                'feedback': None
            },
            {
                'id_code': 'CMP-2026-00007',
                'user': default_user,
                'title': 'Library off-campus proxy returning 502 Bad Gateway',
                'desc': 'When trying to access IEEE and ScienceDirect databases from home, the authentication proxy throws 502 error.',
                'cat': 'IT & Software',
                'priority': 'Medium',
                'status': 'Submitted',
                'dept': it_dept,
                'staff': None,
                'created_offset': 1,
                'resolution_note': None,
                'timeline': [
                    (1, 'Submitted', 'Ticket filed by student via portal.', default_user)
                ],
                'feedback': None
            }
        ]

        for item in sample_tickets:
            created_time = now - timedelta(days=item['created_offset'])
            c = Complaint(
                complaint_id=item['id_code'],
                user_id=item['user'].id,
                title=item['title'],
                description=item['desc'],
                category=item['cat'],
                priority=item['priority'],
                status=item['status'],
                department_id=item['dept'].id if item['dept'] else None,
                assigned_to=item['staff'].id if item['staff'] else None,
                rejection_reason=item.get('rejection_reason'),
                resolution_note=item.get('resolution_note'),
                created_at=created_time,
                updated_at=now - timedelta(days=item['timeline'][-1][0])
            )
            db.session.add(c)
            db.session.flush()

            # Add status timeline
            for offset_days, status_val, note_text, author_obj in item['timeline']:
                tl = StatusTimeline(
                    complaint_id=c.id,
                    status=status_val,
                    note=note_text,
                    changed_by=author_obj.id if author_obj else None,
                    changed_at=now - timedelta(days=offset_days)
                )
                db.session.add(tl)

            # Add Feedback if specified
            if item.get('feedback'):
                rating_val, comment_text = item['feedback']
                fb = Feedback(
                    complaint_id=c.id,
                    user_id=item['user'].id,
                    rating=rating_val,
                    comment=comment_text,
                    submitted_at=now - timedelta(days=item['timeline'][-1][0])
                )
                db.session.add(fb)

            # In-app notification for the user
            notif = Notification(
                user_id=item['user'].id,
                complaint_id=c.id,
                message=f"Complaint #{c.complaint_id} status updated to '{c.status}'.",
                is_read=(c.status in ('Resolved', 'Rejected')),
                created_at=now - timedelta(days=item['timeline'][-1][0])
            )
            db.session.add(notif)

        db.session.commit()
        print("Demo complaints, timelines, and feedback successfully seeded!")

if __name__ == '__main__':
    run_seed()
