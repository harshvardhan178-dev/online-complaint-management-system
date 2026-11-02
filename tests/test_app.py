
import unittest

from app import create_app
from app.config import Config
from app.models import (
    db, User, Complaint, Department,
    Feedback, Notification, StatusTimeline
)
from app.services.complaint_service import (
    create_complaint,
    update_status,
    assign_complaint,
    detect_duplicates,
    submit_feedback
)
from app.services.report_service import (
    generate_csv_report,
    generate_pdf_report,
    get_analytics_summary
)


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    DEFAULT_ADMIN_EMAIL = 'admin@smartcomplaint.com'
    DEFAULT_ADMIN_PASSWORD = 'Admin@123'
    DEFAULT_ADMIN_NAME = 'System Administrator'


class SmartComplaintTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.client = self.app.test_client()

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
        res = self.client.post(
            '/login',
            data={
                'email': 'admin@smartcomplaint.com',
                'password': 'Admin@123'
            },
            follow_redirects=False
        )

        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/dashboard', res.headers['Location'])

        # Logout
        self.client.get('/logout')

        # Failed login
        res_fail = self.client.post(
            '/login',
            data={
                'email': 'admin@smartcomplaint.com',
                'password': 'WrongPassword'
            },
            follow_redirects=True
        )

        self.assertIn(
            b'Invalid email or password',
            res_fail.data
        )

    def test_registration_enforces_citizen_role(self):
        # Attempt to escalate role via POST parameter tampering
        res = self.client.post(
            '/register',
            data={
                'full_name': 'Test Citizen',
                'email': 'citizen_test@smartcomplaint.com',
                'password': 'SecurePassword@123',
                'confirm_password': 'SecurePassword@123',
                'phone': '9876543210',
                'role': 'admin',  # Attacker attempts role escalation
                'department_id': '1'
            },
            follow_redirects=True
        )
        self.assertEqual(res.status_code, 200)

        created_user = User.query.filter_by(email='citizen_test@smartcomplaint.com').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.role, 'user', "Public registration must strictly force 'user' role")
        self.assertIsNone(created_user.department_id, "Public registration must not assign department")

    def test_staff_login_sets_department_id_in_session(self):
        res = self.client.post(
            '/login',
            data={
                'email': 'staff@smartcomplaint.com',
                'password': 'Staff@123'
            },
            follow_redirects=False
        )
        self.assertEqual(res.status_code, 302)
        self.assertIn('/staff/dashboard', res.headers['Location'])

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_role'), 'staff')
            staff_user = User.query.filter_by(email='staff@smartcomplaint.com').first()
            self.assertEqual(sess.get('department_id'), staff_user.department_id)

    def test_csrf_protection_active(self):
        # Test CSRF protection when explicitly enabled
        class CSRFConfig(TestConfig):
            WTF_CSRF_ENABLED = True

        csrf_app = create_app(CSRFConfig)
        with csrf_app.test_client() as csrf_client:
            # POST without CSRF token
            res = csrf_client.post(
                '/login',
                data={'email': 'admin@smartcomplaint.com', 'password': 'Admin@123'},
                follow_redirects=False
            )
            # Should be redirected with error or return 400
            self.assertIn(res.status_code, [302, 400])

    def test_civic_complaint_lifecycle(self):

        demo_user = User.query.filter_by(
            email='user@smartcomplaint.com'
        ).first()

        staff_user = User.query.filter_by(
            email='staff@smartcomplaint.com'
        ).first()

        pwd_dept = Department.query.filter(
            Department.name.like('%Public Works%')
        ).first()

        self.assertIsNotNone(demo_user)
        self.assertIsNotNone(staff_user)
        self.assertIsNotNone(pwd_dept)

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

        # 2. Notification
        notif = Notification.query.filter_by(
            user_id=demo_user.id,
            complaint_id=c.id
        ).first()

        self.assertIsNotNone(notif)
        self.assertIn(c.complaint_id, notif.message)

        # 3. Duplicate Detection
        duplicates = detect_duplicates(
            'Large dangerous pothole on Ring Road',
            'Pothole issue on outer ring road',
            'Roads & Transportation'
        )

        self.assertGreaterEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]['complaint'].id, c.id)

        # 4. Assign Complaint
        admin = User.query.filter_by(role='admin').first()

        assign_complaint(
            complaint=c,
            department_id=pwd_dept.id,
            staff_id=staff_user.id,
            assigned_by_user_id=admin.id,
            note='Dispatched to PWD South Zone Field Unit.'
        )

        self.assertEqual(c.status, 'Assigned')
        self.assertEqual(c.assigned_to, staff_user.id)

        # 5. Staff Updates Progress
        update_status(
            complaint=c,
            new_status='In Progress',
            changed_by_user_id=staff_user.id,
            note='Asphalt patch crew dispatched on site.'
        )

        self.assertEqual(c.status, 'In Progress')

        # 6. Resolve Complaint
        update_status(
            complaint=c,
            new_status='Resolved',
            changed_by_user_id=staff_user.id,
            note='Pothole filled with bitumen mix and leveled with road roller.',
            resolution_note='Pothole filled with cold asphalt mix, compacted, and leveled.'
        )

        self.assertEqual(c.status, 'Resolved')
        self.assertIsNotNone(c.resolution_note)

        # 7. Submit Feedback
        fb = submit_feedback(
            complaint_id=c.id,
            user_id=demo_user.id,
            rating=5,
            comment='Rapid response! Road is completely smooth now.'
        )

        self.assertEqual(fb.rating, 5)
        self.assertEqual(c.feedback.rating, 5)

        # 8. Reopen Complaint
        update_status(
            complaint=c,
            new_status='Reopened',
            changed_by_user_id=demo_user.id,
            note='Edge of the patch started crumbling.'
        )

        self.assertEqual(c.status, 'Reopened')

        # 9. Analytics and Reports
        analytics = get_analytics_summary()

        self.assertGreaterEqual(analytics['total'], 1)

        csv_out = generate_csv_report([c])

        self.assertIn(c.complaint_id, csv_out.getvalue())
        self.assertIn('New Delhi', csv_out.getvalue())

        pdf_out = generate_pdf_report([c])

        self.assertGreater(len(pdf_out.getvalue()), 1000)


if __name__ == '__main__':
    unittest.main()
