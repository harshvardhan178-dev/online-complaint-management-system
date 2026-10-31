"""
Demo Data Seeder for SmartComplaint - Online Public Grievance and Civic Issue Management System
Populates realistic municipal complaints, timeline entries, notifications, and citizen feedback.
"""
from datetime import datetime, timedelta, timezone
from app import create_app
from app.models import db, User, Department, Complaint, StatusTimeline, Notification, Feedback

def run_seed():
    app = create_app()
    with app.app_context():
        print("Clearing and re-seeding civic complaints and municipal departments...")

        # Re-fetch departments
        pwd_dept = Department.query.filter(Department.name.like("%Public Works%")).first()
        elec_dept = Department.query.filter(Department.name.like("%Electricity%")).first()
        water_dept = Department.query.filter(Department.name.like("%Water%")).first()
        drainage_dept = Department.query.filter(Department.name.like("%Sanitation & Drainage%")).first()
        garbage_dept = Department.query.filter(Department.name.like("%Solid Waste%")).first()
        parks_dept = Department.query.filter(Department.name.like("%Parks%")).first()
        health_dept = Department.query.filter(Department.name.like("%Health%")).first()

        admin_user = User.query.filter_by(role='admin').first()
        default_user = User.query.filter_by(email='user@smartcomplaint.com').first()
        staff_pwd = User.query.filter_by(email='staff@smartcomplaint.com').first()

        # Additional municipal field staff
        staff_water = User.query.filter_by(email='water_officer@smartcomplaint.com').first()
        if not staff_water:
            staff_water = User(
                full_name='Priya Sundaram (Water Inspector)',
                email='water_officer@smartcomplaint.com',
                phone='9876543220',
                role='staff',
                department_id=water_dept.id if water_dept else None,
                is_active=True
            )
            staff_water.set_password('Staff@123')
            db.session.add(staff_water)

        # Second citizen user
        citizen_priya = User.query.filter_by(email='sarah@smartcomplaint.com').first()
        if not citizen_priya:
            citizen_priya = User(
                full_name='Pooja Mehta (Resident)',
                email='sarah@smartcomplaint.com',
                phone='9876543221',
                role='user',
                is_active=True
            )
            citizen_priya.set_password('User@123')
            db.session.add(citizen_priya)

        db.session.commit()

        # Delete existing complaints to refresh with civic data
        Feedback.query.delete()
        StatusTimeline.query.delete()
        Notification.query.delete()
        Complaint.query.delete()
        db.session.commit()

        now = datetime.now(timezone.utc)

        civic_tickets = [
            {
                'id_code': 'SC-2026-00001',
                'user': default_user,
                'title': 'Dangerous deep pothole near Metro Pillar 142 on Outer Ring Road',
                'desc': 'A deep 2-foot pothole has formed following heavy rains, causing two-wheelers to skid and triggering heavy traffic jams during peak evening hours.',
                'cat': 'Roads & Transportation',
                'subcat': 'Potholes',
                'priority': 'Critical',
                'status': 'In Progress',
                'state': 'Delhi NCT',
                'city': 'New Delhi',
                'area': 'Nehru Place / Kalkaji',
                'street_name': 'Outer Ring Road',
                'landmark': 'Opposite Metro Pillar 142 & Paras Cinema',
                'lat': 28.5494,
                'lng': 77.2528,
                'phone': '9876543212',
                'dept': pwd_dept,
                'staff': staff_pwd,
                'created_offset': 4,
                'resolution_note': None,
                'timeline': [
                    (4, 'Submitted', 'Grievance registered with geo-tag and photo evidence.', default_user),
                    (3, 'Under Review', 'Verified by Municipal Control Room; classified high priority.', admin_user),
                    (2, 'Assigned', 'Dispatched to PWD South Zone Field Unit (Rajesh Kumar).', admin_user),
                    (1, 'In Progress', 'Asphalt cold mix and road roller mobilized. Work scheduled for night closure.', staff_pwd)
                ],
                'feedback': None
            },
            {
                'id_code': 'SC-2026-00002',
                'user': citizen_priya,
                'title': 'High-pressure drinking water pipeline burst flooding residential lane',
                'desc': 'Main 6-inch potable water pipeline has ruptured underground. Clean water is bubbling onto the street for 3 hours and water pressure in adjacent houses has fallen to zero.',
                'cat': 'Water Supply',
                'subcat': 'Water leakage',
                'priority': 'Critical',
                'status': 'Resolved',
                'state': 'Karnataka',
                'city': 'Bengaluru',
                'area': 'Indiranagar 2nd Stage',
                'street_name': '100 Feet Road, 12th Cross',
                'landmark': 'Near BDA Complex & Corner House Ice Cream',
                'lat': 12.9719,
                'lng': 77.6412,
                'phone': '9876543221',
                'dept': water_dept,
                'staff': staff_water,
                'created_offset': 10,
                'resolution_note': 'Excavated section, isolated the burst segment, installed heavy-duty stainless steel clamp, and restored pipeline pressure.',
                'timeline': [
                    (10, 'Submitted', 'Urgent pipeline burst reported by neighborhood residents.', citizen_priya),
                    (9, 'Under Review', 'Prioritized as Critical drinking water asset loss.', admin_user),
                    (8, 'Assigned', 'Assigned to Water Supply Fast Response Team (Priya Sundaram).', admin_user),
                    (6, 'In Progress', 'Water valves isolated; excavation crew on site.', staff_water),
                    (3, 'Resolved', 'Replacement sleeve welded, pressure tested to 4.5 bar, and road patch restored.', staff_water),
                    (1, 'Closed', 'Resident confirmed 24/7 supply restored.', admin_user)
                ],
                'feedback': (5, 'Extremely impressed! The field crew arrived in under 4 hours and fixed the ruptured pipe before evening.')
            },
            {
                'id_code': 'SC-2026-00003',
                'user': default_user,
                'title': 'Series of 6 streetlights completely dark along Sector 18 Community Park',
                'desc': 'All streetlights from Pole E-41 to E-46 have been non-functional for 5 consecutive nights, making the corridor unsafe for women, children, and evening joggers.',
                'cat': 'Electricity & Streetlights',
                'subcat': 'Streetlights not working',
                'priority': 'High',
                'status': 'Under Review',
                'state': 'Uttar Pradesh',
                'city': 'Noida',
                'area': 'Sector 18 Commercial & Residential Hub',
                'street_name': 'Park Avenue Link Road',
                'landmark': 'Adjoining Central Park Gate #3',
                'lat': 28.5708,
                'lng': 77.3260,
                'phone': '9876543212',
                'dept': elec_dept,
                'staff': None,
                'created_offset': 2,
                'resolution_note': None,
                'timeline': [
                    (2, 'Submitted', 'Grievance submitted by Ward representative.', default_user),
                    (1, 'Under Review', 'Sent to Electrical Maintenance Division for line test inspection.', admin_user)
                ],
                'feedback': None
            },
            {
                'id_code': 'SC-2026-00004',
                'user': citizen_priya,
                'title': 'Open overflowing stormwater drain causing severe sewage waterlogging',
                'desc': 'Drainage canal clogged with plastic debris and silt. Waste water is backing up onto pedestrian walkways and entering apartment basement parking.',
                'cat': 'Drainage & Sewage',
                'subcat': 'Blocked drains',
                'priority': 'High',
                'status': 'Assigned',
                'state': 'Maharashtra',
                'city': 'Mumbai',
                'area': 'Andheri West',
                'street_name': 'Veera Desai Road',
                'landmark': 'Near Country Club Entrance',
                'lat': 19.1363,
                'lng': 72.8277,
                'phone': '9876543221',
                'dept': drainage_dept,
                'staff': staff_pwd,
                'created_offset': 5,
                'resolution_note': None,
                'timeline': [
                    (5, 'Submitted', 'Citizen reported blocked drainage culvert.', citizen_priya),
                    (3, 'Under Review', 'Reviewed and scheduled for high-pressure suction clearing.', admin_user),
                    (2, 'Assigned', 'Assigned to Municipal Drainage Field Unit.', admin_user)
                ],
                'feedback': None
            },
            {
                'id_code': 'SC-2026-00005',
                'user': default_user,
                'title': 'Community garbage bins overflowing for 4 days creating health hazard',
                'desc': 'Large community green bins have not been emptied since Monday. Stray animals are scattering waste across the road and foul odor is penetrating nearby homes.',
                'cat': 'Garbage & Sanitation',
                'subcat': 'Garbage not collected',
                'priority': 'Medium',
                'status': 'Resolved',
                'state': 'Delhi NCT',
                'city': 'New Delhi',
                'area': 'Lajpat Nagar IV',
                'street_name': 'Block C Inner Ring',
                'landmark': 'Behind Post Office',
                'lat': 28.5672,
                'lng': 77.2433,
                'phone': '9876543212',
                'dept': garbage_dept,
                'staff': staff_pwd,
                'created_offset': 8,
                'resolution_note': 'Dispatched compactor truck DL-1GB-3342. Cleared 2.4 tonnes of solid waste, disinfected bin area with lime powder.',
                'timeline': [
                    (8, 'Submitted', 'Complaint filed with photo of overflowing dumpster.', default_user),
                    (7, 'Assigned', 'Sanitation supervisor alerted.', admin_user),
                    (6, 'In Progress', 'Garbage compactor vehicle on site.', staff_pwd),
                    (5, 'Resolved', 'Area cleared and disinfected.', staff_pwd)
                ],
                'feedback': (4, 'Thank you for clearing the trash quickly and cleaning the ground.')
            },
            {
                'id_code': 'SC-2026-00006',
                'user': citizen_priya,
                'title': 'Broken children slide and swing set in Children Community Park',
                'desc': 'Metal chains on two swings are broken with rusted sharp edges exposed. Plastic spiral slide is cracked. Poses immediate danger of injury to neighborhood kids.',
                'cat': 'Public Facilities',
                'subcat': 'Public playground problems',
                'priority': 'Low',
                'status': 'Submitted',
                'state': 'Telangana',
                'city': 'Hyderabad',
                'area': 'Jubilee Hills',
                'street_name': 'Road No. 36',
                'landmark': 'Children Fun Park near Check Post',
                'lat': 17.4319,
                'lng': 78.4073,
                'phone': '9876543221',
                'dept': parks_dept,
                'staff': None,
                'created_offset': 1,
                'resolution_note': None,
                'timeline': [
                    (1, 'Submitted', 'Complaint lodged by Residents Welfare Association.', citizen_priya)
                ],
                'feedback': None
            },
            {
                'id_code': 'SC-2026-00007',
                'user': default_user,
                'title': 'Stagnant water ponding in abandoned construction plot breeding mosquitoes',
                'desc': 'Large puddle of water has remained stagnant for 3 weeks in vacant plot #48. Swarms of mosquitoes are spreading into neighboring houses; risk of dengue/malaria outbreak.',
                'cat': 'Environment & Public Health',
                'subcat': 'Mosquito breeding areas',
                'priority': 'High',
                'status': 'In Progress',
                'state': 'Delhi NCT',
                'city': 'New Delhi',
                'area': 'Dwarka Sector 12',
                'street_name': 'Dwarka Expressway Link',
                'landmark': 'Adjacent to Plot #48 & DDA Community Centre',
                'lat': 28.5921,
                'lng': 77.0460,
                'phone': '9876543212',
                'dept': health_dept,
                'staff': staff_pwd,
                'created_offset': 7,
                'resolution_note': None,
                'timeline': [
                    (7, 'Submitted', 'Health hazard complaint submitted with video and photo.', default_user),
                    (6, 'Under Review', 'Forwarded to Vector Borne Disease Control unit.', admin_user),
                    (5, 'Assigned', 'Fogging and anti-larval spray team deployed.', admin_user),
                    (2, 'In Progress', 'Treated stagnant water with abate anti-larval chemical; owner issued municipal notice.', staff_pwd)
                ],
                'feedback': None
            }
        ]

        for t in civic_tickets:
            created_dt = now - timedelta(days=t['created_offset'])
            complaint = Complaint(
                complaint_id=t['id_code'],
                user_id=t['user'].id,
                title=t['title'],
                description=t['desc'],
                category=t['cat'],
                subcategory=t['subcat'],
                priority=t['priority'],
                status=t['status'],
                department_id=t['dept'].id if t['dept'] else None,
                assigned_to=t['staff'].id if t['staff'] else None,
                state=t['state'],
                city=t['city'],
                area=t['area'],
                street_name=t['street_name'],
                landmark=t['landmark'],
                latitude=t['lat'],
                longitude=t['lng'],
                contact_phone=t['phone'],
                resolution_note=t['resolution_note'],
                created_at=created_dt,
                updated_at=created_dt + timedelta(hours=12)
            )
            db.session.add(complaint)
            db.session.flush()

            # Timeline
            for day_offset, st_name, note, author in t['timeline']:
                tl = StatusTimeline(
                    complaint_id=complaint.id,
                    status=st_name,
                    note=note,
                    changed_by=author.id if author else None,
                    changed_at=now - timedelta(days=day_offset)
                )
                db.session.add(tl)

            # Notifications
            notif = Notification(
                user_id=complaint.user_id,
                complaint_id=complaint.id,
                message=f"Grievance #{complaint.complaint_id} status updated to '{complaint.status}'.",
                is_read=t['status'] in ('Resolved', 'Closed'),
                created_at=complaint.updated_at
            )
            db.session.add(notif)

            # Feedback
            if t['feedback']:
                rating_val, comment_str = t['feedback']
                fb = Feedback(
                    complaint_id=complaint.id,
                    user_id=complaint.user_id,
                    rating=rating_val,
                    comment=comment_str,
                    submitted_at=complaint.updated_at + timedelta(hours=2)
                )
                db.session.add(fb)

        db.session.commit()
        print(f"Successfully seeded {len(civic_tickets)} realistic civic complaints across all departments.")

if __name__ == '__main__':
    run_seed()
