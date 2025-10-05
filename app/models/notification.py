from . import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    notification_type = db.Column(db.Enum('assignment', 'evaluation', 'system', 'announcement', 'reminder', name='notif_type_enum'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    related_entity_type = db.Column(db.String(50))
    related_entity_id = db.Column(db.Integer)
    priority = db.Column(db.Enum('low', 'normal', 'high', name='notif_priority_enum'), nullable=False, default='normal')
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_notifications_recipient', 'recipient_id', 'is_read'),
        db.Index('idx_notifications_type', 'notification_type'),
        db.Index('idx_notifications_created', 'created_at'),
    )
