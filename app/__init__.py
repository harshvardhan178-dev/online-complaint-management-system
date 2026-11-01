
import os
from flask import Flask, session
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

    # Ensure upload and session directories exist
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

    # Health check
    @app.route('/health')
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            app.logger.error("Database health check failed: %s", e)
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
            'environment': app.config.get('FLASK_ENV', 'production')
        }, 200

    # Security response headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    # Error handlers
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

    # Global context processor
    @app.context_processor
    def inject_global_vars():
        unread_count = 0
        current_user = None

        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])

            if current_user:
                unread_count = Notification.query.filter_by(
                    user_id=current_user.id,
                    is_read=False
                ).count()

        return dict(
            current_user=current_user,
            unread_notifications_count=unread_count
        )

    # Initialize database and seed initial departments/admin
    with app.app_context():
        db.create_all()
        seed_initial_data(app)

    return app


def seed_initial_data(app):
    """Create initial departments and administrator account."""

    try:
        # Initial civic departments
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

        created_depts = {}

        for name, desc in initial_depts:
            dept = Department.query.filter_by(name=name).first()

            if not dept:
                dept = Department(
                    name=name,
                    description=desc
                )
                db.session.add(dept)
                db.session.flush()

            created_depts[name] = dept

        # Create default administrator only if one does not exist
        admin_email = app.config.get('DEFAULT_ADMIN_EMAIL')
        admin = User.query.filter_by(email=admin_email).first()

        if not admin:
            admin_password = app.config.get('DEFAULT_ADMIN_PASSWORD')

            if not admin_password:
                raise RuntimeError(
                    "DEFAULT_ADMIN_PASSWORD is not configured. "
                    "Set it in your environment variables."
                )

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

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        app.logger.error("Database initialization failed: %s", e)
        raise
