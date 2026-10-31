from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'admin', 'staff'
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    department = db.relationship('Department', back_populates='staff_members', foreign_keys=[department_id])
    complaints = db.relationship('Complaint', back_populates='submitter', foreign_keys='Complaint.user_id', lazy='dynamic')
    assigned_complaints = db.relationship('Complaint', back_populates='assignee', foreign_keys='Complaint.assigned_to', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    feedbacks = db.relationship('Feedback', back_populates='user', lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    @property
    def is_staff(self) -> bool:
        return self.role == 'staff'

    @property
    def is_regular_user(self) -> bool:
        return self.role == 'user'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'department': self.department.name if self.department else None,
            'department_id': self.department_id,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    staff_members = db.relationship('User', back_populates='department', foreign_keys='User.department_id')
    complaints = db.relationship('Complaint', back_populates='department', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'staff_count': len(self.staff_members),
            'complaints_count': self.complaints.count()
        }


class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, default='General')
    priority = db.Column(db.String(20), nullable=False, default='Medium')  # Low, Medium, High, Critical
    status = db.Column(db.String(30), nullable=False, default='Submitted')  # Submitted, Under Review, Assigned, In Progress, Resolved, Rejected
    
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    rejection_reason = db.Column(db.Text, nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)
    attachment = db.Column(db.String(255), nullable=True)
    video_attachment = db.Column(db.String(255), nullable=True)
    
    # Civic Location & Details
    subcategory = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True, index=True)
    area = db.Column(db.String(150), nullable=True, index=True)
    street_name = db.Column(db.String(200), nullable=True)
    landmark = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    submitter = db.relationship('User', back_populates='complaints', foreign_keys=[user_id])
    assignee = db.relationship('User', back_populates='assigned_complaints', foreign_keys=[assigned_to])
    department = db.relationship('Department', back_populates='complaints', foreign_keys=[department_id])
    timeline = db.relationship('StatusTimeline', back_populates='complaint', order_by='StatusTimeline.changed_at.asc()', cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', back_populates='complaint', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='complaint', cascade='all, delete-orphan')

    @property
    def status_badge_class(self):
        mapping = {
            'Submitted': 'badge-primary',
            'Under Review': 'badge-warning',
            'Assigned': 'badge-info',
            'In Progress': 'badge-secondary',
            'Resolved': 'badge-success',
            'Closed': 'badge-dark',
            'Rejected': 'badge-danger',
            'Reopened': 'badge-warning'
        }
        return mapping.get(self.status, 'badge-light')

    @property
    def priority_badge_class(self):
        mapping = {
            'Low': 'priority-low',
            'Medium': 'priority-medium',
            'High': 'priority-high',
            'Critical': 'priority-critical'
        }
        return mapping.get(self.priority, 'priority-medium')

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'subcategory': self.subcategory,
            'priority': self.priority,
            'status': self.status,
            'state': self.state,
            'city': self.city,
            'area': self.area,
            'street_name': self.street_name,
            'landmark': self.landmark,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_phone': self.contact_phone,
            'submitter_name': self.submitter.full_name if self.submitter else 'Unknown',
            'department_name': self.department.name if self.department else 'Unassigned',
            'assigned_staff': self.assignee.full_name if self.assignee else 'Unassigned',
            'attachment': self.attachment,
            'video_attachment': self.video_attachment,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M') if self.updated_at else None,
            'has_feedback': self.feedback is not None,
            'rating': self.feedback.rating if self.feedback else None
        }


class StatusTimeline(db.Model):
    __tablename__ = 'status_timeline'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    complaint = db.relationship('Complaint', back_populates='timeline')
    author = db.relationship('User', foreign_keys=[changed_by])


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship('User', back_populates='notifications')
    complaint = db.relationship('Complaint', back_populates='notifications')


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    complaint = db.relationship('Complaint', back_populates='feedback')
    user = db.relationship('User', back_populates='feedbacks')
