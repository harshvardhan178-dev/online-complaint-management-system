import os
from flask import Flask, session, g
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_session import Session
from app.config import Config
from app.models import db, User, Department, Notification
from app.services.notification_service import mail

bcrypt = Bcrypt()
migrate = Migrate()
sess = Session()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure uploads and session directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    sess.init_app(app)
    mail.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.staff import staff_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)

    # Health check probe for Render, Kubernetes, and load balancers
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            return {
                'status': 'unhealthy',
                'database': f'error: {str(e)}',
                'service': 'SmartComplaint'
            }, 500

        return {
            'status': 'healthy',
            'service': 'SmartComplaint',
            'version': '2.0.0',
            'database': db_status,
            'environment': app.config.get('FLASK_ENV', 'production')
        }, 200

    # Production Security Response Headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Custom Branded Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Global context processor for notifications & layout helpers
    @app.context_processor
    def inject_global_vars():
        unread_count = 0
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
            if current_user:
                unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return dict(
            current_user=current_user,
            unread_notifications_count=unread_count
        )

    # Auto-seed database tables and initial accounts on first startup
    with app.app_context():
        db.create_all()
        seed_initial_data(app)

    return app

def seed_initial_data(app):
    """Seeds initial departments and default administrator / staff / demo user accounts."""
    try:
        # Default Departments
        initial_depts = [
            ("IT Support", "Technical issues, network, portals, and computer hardware."),
            ("Facilities & Maintenance", "Hostel rooms, plumbing, electrical repairs, sanitation."),
            ("Finance & Accounts", "Fee payments, refunds, scholarships, billing."),
            ("Administration", "General campus policies, security, certificates, scheduling."),
            ("Academic Affairs", "Courses, grades, exam schedules, faculty concerns.")
        ]
        created_depts = {}
        for name, desc in initial_depts:
            dept = Department.query.filter_by(name=name).first()
            if not dept:
                dept = Department(name=name, description=desc)
                db.session.add(dept)
                db.session.flush()
            created_depts[name] = dept

        # Default Admin Account
        admin_email = app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@smartcomplaint.com')
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin = User(
                full_name=app.config.get('DEFAULT_ADMIN_NAME', 'System Administrator'),
                email=admin_email,
                phone='9876543210',
                role='admin',
                is_active=True
            )
            admin.set_password(app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin@123'))
            db.session.add(admin)

        # Default Staff Member for IT Support
        staff_email = 'staff@smartcomplaint.com'
        staff = User.query.filter_by(email=staff_email).first()
        if not staff:
            it_dept = created_depts.get("IT Support")
            staff = User(
                full_name='Alex Rivera (Staff)',
                email=staff_email,
                phone='9876543211',
                role='staff',
                department_id=it_dept.id if it_dept else None,
                is_active=True
            )
            staff.set_password('Staff@123')
            db.session.add(staff)

        # Default Demo User
        demo_user_email = 'user@smartcomplaint.com'
        demo_user = User.query.filter_by(email=demo_user_email).first()
        if not demo_user:
            demo_user = User(
                full_name='John Doe',
                email=demo_user_email,
                phone='9876543212',
                role='user',
                is_active=True
            )
            demo_user.set_password('User@123')
            db.session.add(demo_user)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"Database seed skipped or already initialized: {e}")
