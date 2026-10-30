import unittest
import os
import io
from app import create_app
from app.models import db, User, Complaint, Department, Feedback, Notification, StatusTimeline
from app.services.complaint_service import create_complaint, update_status, assign_complaint, detect_duplicates, submit_feedback
from app.services.report_service import generate_csv_report, generate_pdf_report, get_analytics_summary

class SmartComplaintTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

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

    def test_complaint_lifecycle(self):
        demo_user = User.query.filter_by(email='user@smartcomplaint.com').first()
        staff_user = User.query.filter_by(email='staff@smartcomplaint.com').first()
        it_dept = Department.query.filter_by(name='IT Support').first()

        # 1. Create Complaint
        c = create_complaint(
            user_id=demo_user.id,
            title='Projector broken in Lab 301',
            description='The HDMI port on the ceiling projector is damaged and not displaying.',
            category='IT & Software',
            priority='High'
        )
        self.assertTrue(c.complaint_id.startswith('CMP-'))
        self.assertEqual(c.status, 'Submitted')
        self.assertEqual(len(c.timeline), 1)

        # Notification created
        notif = Notification.query.filter_by(user_id=demo_user.id, complaint_id=c.id).first()
        self.assertIsNotNone(notif)
        self.assertIn(c.complaint_id, notif.message)

        # 2. Duplicate Detection
        duplicates = detect_duplicates('Projector broken in Lab 301', 'HDMI port broken', 'IT & Software')
        self.assertGreaterEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]['complaint'].id, c.id)

        # 3. Admin Assigns Complaint
        admin = User.query.filter_by(role='admin').first()
        assign_complaint(
            complaint=c,
            department_id=it_dept.id,
            staff_id=staff_user.id,
            assigned_by_user_id=admin.id,
            note='Please inspect within 24 hours.'
        )
        self.assertEqual(c.status, 'Assigned')
        self.assertEqual(c.assigned_to, staff_user.id)

        # 4. Staff Updates Progress
        update_status(
            complaint=c,
            new_status='In Progress',
            changed_by_user_id=staff_user.id,
            note='Ordered replacement HDMI adapter module.'
        )
        self.assertEqual(c.status, 'In Progress')

        # 5. Staff Resolves Complaint
        update_status(
            complaint=c,
            new_status='Resolved',
            changed_by_user_id=staff_user.id,
            note='Replaced HDMI module and tested display output.',
            resolution_note='Replaced HDMI module and verified 1080p output.'
        )
        self.assertEqual(c.status, 'Resolved')
        self.assertIsNotNone(c.resolution_note)

        # 6. User Submits Feedback
        fb = submit_feedback(
            complaint_id=c.id,
            user_id=demo_user.id,
            rating=5,
            comment='Super fast resolution! Thank you.'
        )
        self.assertEqual(fb.rating, 5)
        self.assertEqual(c.feedback.rating, 5)

        # 7. Analytics and Reports
        analytics = get_analytics_summary()
        self.assertGreaterEqual(analytics['total'], 1)
        self.assertEqual(analytics['resolved'], 1)

        csv_out = generate_csv_report([c])
        self.assertIn(c.complaint_id, csv_out.getvalue())

        pdf_out = generate_pdf_report([c])
        self.assertGreater(len(pdf_out.getvalue()), 1000)

if __name__ == '__main__':
    unittest.main()
