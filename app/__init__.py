
import os

from flask import Flask, session
from sqlalchemy import text
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError

from app.config import Config
from app.models import db, User, Department, Notification
from app.services.notification_service import mail


# Initialize extensions
bcrypt = Bcrypt()
migrate = Migrate()
sess = Session()
csrf = CSRFProtect()


def create_app(config_class=Config):

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create upload and session directories
    os.makedirs(
        app.config['UPLOAD_FOLDER'],
        exist_ok=True
    )

    os.makedirs(
        app.config['SESSION_FILE_DIR'],
        exist_ok=True
    )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    sess.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.admin import admin_bp
    from app.routes.staff import staff_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(staff_bp)

    # Health check
    @app.route('/health')
    def health_check():

        try:
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'

        except Exception as e:
            db.session.rollback()

            app.logger.error(
                "Database health check failed: %s",
                e
            )

            return {
                'status': 'unhealthy',
                'database': 'connection failed',
                'service': 'SmartComplaint'
            }, 500

        return {
            'status': 'healthy',
            'service': 'SmartComplaint',
            'version': '2.0.0',
            'database': db_status,
            'environment': app.config.get(
                'FLASK_ENV',
                'production'
            )
        }, 200

    # Security response headers
    @app.after_request
    def set_security_headers(response):

        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'

        return response

    # 404 Error handler
    @app.errorhandler(404)
    def not_found_error(error):

        from flask import render_template

        return render_template('errors/404.html'), 404

    # 403 Error handler
    @app.errorhandler(403)
    def forbidden_error(error):

        from flask import render_template

        return render_template('errors/403.html'), 403

    # CSRF Error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import flash, redirect, request
        flash(f'Security session validation failed: {e.description}. Please refresh and try again.', 'danger')
        return redirect(request.referrer or '/')

    # 500 Error handler
    @app.errorhandler(500)
    def internal_error(error):

        from flask import render_template

        db.session.rollback()

        return render_template('errors/500.html'), 500

    # Global context processor
    @app.context_processor
    def inject_global_vars():

        unread_count = 0
        current_user = None

        if 'user_id' in session:

            current_user = db.session.get(
                User,
                session['user_id']
            )

            if current_user:

                unread_count = Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()

        return dict(
            current_user=current_user,
            unread_notifications_count=unread_count
        )

    # Database initialization
    is_production = (
        str(app.config.get('FLASK_ENV', '')).lower()
        == 'production'
    )
    skip_init = (
        is_production
        or os.getenv('SKIP_AUTO_DB_INIT') == '1'
    )

    if not skip_init:

        with app.app_context():

            db.create_all()
            seed_initial_data(app)

    # Production database seeding command
    @app.cli.command("seed-data")
    def seed_data_command():

        """Create initial departments and administrator."""

        seed_initial_data(app)

        print(
            "SmartComplaint initial data setup completed."
        )

    return app


def seed_initial_data(app):

    """Create departments, administrator, and test accounts."""

    try:

        # 1. Initial departments
        initial_depts = [

            (
                "Public Works Department (PWD)",
                "Roads, potholes, footpaths, bridges, and public transit infrastructure."
            ),

            (
                "Electricity Board & Streetlights",
                "Power outages, street lighting, electric poles, transformers, and exposed wiring."
            ),

            (
                "Water Supply & Sewerage Board",
                "Drinking water supply, pipeline leaks, low pressure, and clean water delivery."
            ),

            (
                "Municipal Sanitation & Drainage",
                "Blocked drains, sewage overflow, open manholes, and flood mitigation."
            ),

            (
                "Solid Waste & Garbage Management",
                "Garbage collection, overflowing dumpsters, roadside dumping, and public cleanliness."
            ),

            (
                "Parks & Public Recreation",
                "Public parks, children's playgrounds, benches, and green space maintenance."
            ),

            (
                "Public Health & Environment",
                "Air/water/noise pollution control, mosquito fogging, and environmental sanitation."
            ),

            (
                "General Municipal Administration",
                "Encroachments, stray animal welfare, civic permissions, and public grievance escalation."
            )
        ]

        # 2. Create departments
        for name, description in initial_depts:

            department = Department.query.filter_by(
                name=name
            ).first()

            if department is None:

                department = Department(
                    name=name,
                    description=description
                )

                db.session.add(department)

        db.session.flush()

        # 3. Create administrator
        admin_email = app.config.get(
            'DEFAULT_ADMIN_EMAIL',
            'admin@smartcomplaint.com'
        )

        admin_password = app.config.get(
            'DEFAULT_ADMIN_PASSWORD'
        )

        admin = User.query.filter_by(
            email=admin_email
        ).first()

        if admin is None:

            if not admin_password:
                print(
                    "WARNING: DEFAULT_ADMIN_PASSWORD is not set. "
                    "Default administrator creation skipped. "
                    "Set DEFAULT_ADMIN_PASSWORD in environment variables."
                )
            else:
                admin = User(
                    full_name=app.config.get(
                        'DEFAULT_ADMIN_NAME',
                        'System Administrator'
                    ),
                    email=admin_email,
                    phone='9876543210',
                    role='admin',
                    is_active=True
                )

                admin.set_password(admin_password)

                db.session.add(admin)

        # 4. Create demo accounts only during testing
        if app.config.get('TESTING'):

            pwd_dept = Department.query.filter(
                Department.name.like('%Public Works%')
            ).first()

            # Demo staff
            staff = User.query.filter_by(
                email='staff@smartcomplaint.com'
            ).first()

            if staff is None:

                staff = User(
                    full_name='Demo Staff',
                    email='staff@smartcomplaint.com',
                    phone='9876543211',
                    role='staff',
                    is_active=True,
                    department_id=(
                        pwd_dept.id if pwd_dept else None
                    )
                )

                staff.set_password('Staff@123')

                db.session.add(staff)

            # Demo citizen
            demo_user = User.query.filter_by(
                email='user@smartcomplaint.com'
            ).first()

            if demo_user is None:

                demo_user = User(
                    full_name='Demo Citizen',
                    email='user@smartcomplaint.com',
                    phone='9876543212',
                    role='user',
                    is_active=True
                )

                demo_user.set_password('User@123')

                db.session.add(demo_user)

        # 5. Save database changes
        db.session.commit()

    except Exception as e:

        db.session.rollback()

        app.logger.error(
            "Database initialization failed: %s",
            e
        )

        raise
