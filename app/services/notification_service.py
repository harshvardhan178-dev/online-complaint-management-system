import logging
from flask import current_app
from flask_mail import Mail, Message
from app.models import db, Notification, User

mail = Mail()
logger = logging.getLogger(__name__)

def create_notification(user_id: int, message: str, complaint_id: int = None, send_email: bool = True):
    """
    Creates an in-app notification and optionally attempts to send an email.
    """
    try:
        notification = Notification(
            user_id=user_id,
            complaint_id=complaint_id,
            message=message
        )
        db.session.add(notification)
        db.session.commit()

        # If email credentials are configured and send_email is requested:
        if send_email and current_app.config.get('MAIL_USERNAME'):
            recipient = db.session.get(User, user_id)
            if recipient and recipient.email:
                try:
                    msg = Message(
                        subject="SmartComplaint Update",
                        recipients=[recipient.email],
                        body=message
                    )
                    mail.send(msg)
                except Exception as mail_err:
                    logger.warning(f"Email could not be delivered to {recipient.email}: {mail_err}")

        return notification
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating notification: {e}")
        return None

def get_user_notifications(user_id: int, unread_only: bool = False, limit: int = 20):
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

def mark_notification_as_read(notification_id: int, user_id: int):
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_as_read(user_id: int):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return True
