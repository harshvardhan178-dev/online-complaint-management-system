import unittest
import os
import io
import json
from app import create_app
from app.config import Config
from app.models import db, User, Complaint, Department, Feedback, Notification, StatusTimeline
from app.services.complaint_service import create_complaint, update_status, assign_complaint, detect_duplicates, submit_feedback
from app.services.report_service import generate_csv_report, generate_pdf_report, get_analytics_summary

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class SmartComplaintTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_seed_data_loaded(self):
        admin = User.query.filter_by(role='admin').first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.email, 'admin@smartcomplaint.com')

        staff = User.query.filter_by(role='staff').first()
        self.assertIsNotNone(staff)

        demo_user = User.query.filter_by(role='user').first()
        self.assertIsNotNone(demo_user)

        depts = Department.query.all()
        self.assertGreaterEqual(len(depts), 5)

    def test_health_check_endpoint(self):
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['database'], 'connected')

    def test_login_flow(self):
        # Successful login
        res = self.client.post('/login', data={
            'email': 'admin@smartcomplaint.com',
            'password': 'Admin@123'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/dashboard', res.headers['Location'])

        # Log out
        self.client.get('/logout')

        # Failed login
        res_fail = self.client.post('/login', data={
            'email': 'admin@smartcomplaint.com',
            'password': 'WrongPassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', res_fail.data)

    def test_civic_complaint_lifecycle(self):
        demo_user = User.query.filter_by(email='user@smartcomplaint.com').first()
        staff_user = User.query.filter_by(email='staff@smartcomplaint.com').first()
        pwd_dept = Department.query.filter(Department.name.like('%Public Works%')).first()

        # 1. Create Civic Complaint
        c = create_complaint(
            user_id=demo_user.id,
            title='Large dangerous pothole on Ring Road near Metro station',
            description='A 2-foot pothole has developed after recent rains causing traffic disruption.',
            category='Roads & Transportation',
            subcategory='Potholes',
            priority='Critical',
            city='New Delhi',
            state='Delhi NCT',
            area='Nehru Place',
            street_name='Outer Ring Road',
            landmark='Opposite Metro Pillar 142',
            latitude=28.5494,
            longitude=77.2528,
            contact_phone='9876543210'
        )
        self.assertTrue(c.complaint_id.startswith('SC-'))
        self.assertEqual(c.status, 'Submitted')
        self.assertEqual(c.city, 'New Delhi')
        self.assertEqual(c.subcategory, 'Potholes')
        self.assertEqual(len(c.timeline), 1)

        # Notification created
        notif = Notification.query.filter_by(user_id=demo_user.id, complaint_id=c.id).first()
        self.assertIsNotNone(notif)
        self.assertIn(c.complaint_id, notif.message)

        # 2. Duplicate Detection
        duplicates = detect_duplicates('Large dangerous pothole on Ring Road', 'Pothole issue on outer ring road', 'Roads & Transportation')
        self.assertGreaterEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]['complaint'].id, c.id)

        # 3. Admin Assigns Complaint to Department & Field Officer
        admin = User.query.filter_by(role='admin').first()
        assign_complaint(
            complaint=c,
            department_id=pwd_dept.id if pwd_dept else None,
            staff_id=staff_user.id,
            assigned_by_user_id=admin.id,
            note='Dispatched to PWD South Zone Field Unit.'
        )
        self.assertEqual(c.status, 'Assigned')
        self.assertEqual(c.assigned_to, staff_user.id)

        # 4. Staff Updates Progress
        update_status(
            complaint=c,
            new_status='In Progress',
            changed_by_user_id=staff_user.id,
            note='Asphalt patch crew dispatched on site.'
        )
        self.assertEqual(c.status, 'In Progress')

        # 5. Staff Resolves Complaint
        update_status(
            complaint=c,
            new_status='Resolved',
            changed_by_user_id=staff_user.id,
            note='Pothole filled with bitumen mix and leveled with road roller.',
            resolution_note='Pothole filled with cold asphalt mix, compacted, and leveled.'
        )
        self.assertEqual(c.status, 'Resolved')
        self.assertIsNotNone(c.resolution_note)

        # 6. Citizen Submits Feedback
        fb = submit_feedback(
            complaint_id=c.id,
            user_id=demo_user.id,
            rating=5,
            comment='Rapid response! Road is completely smooth now.'
        )
        self.assertEqual(fb.rating, 5)
        self.assertEqual(c.feedback.rating, 5)

        # 7. Workflow Reopen Test
        update_status(
            complaint=c,
            new_status='Reopened',
            changed_by_user_id=demo_user.id,
            note='Edge of the patch started crumbling.'
        )
        self.assertEqual(c.status, 'Reopened')

        # 8. Analytics and Reports
        analytics = get_analytics_summary()
        self.assertGreaterEqual(analytics['total'], 1)

        csv_out = generate_csv_report([c])
        self.assertIn(c.complaint_id, csv_out.getvalue())
        self.assertIn('New Delhi', csv_out.getvalue())

        pdf_out = generate_pdf_report([c])
        self.assertGreater(len(pdf_out.getvalue()), 1000)

if __name__ == '__main__':
    unittest.main()
