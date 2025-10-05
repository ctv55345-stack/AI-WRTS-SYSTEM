from . import db
from datetime import datetime

class Feedback(db.Model):
    __tablename__ = 'feedback'
    
    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    feedback_type = db.Column(db.Enum('bug_report', 'feature_request', 'complaint', 'suggestion', 'praise', name='feedback_type_enum'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', name='feedback_priority_enum'), nullable=False, default='normal')
    feedback_status = db.Column(db.Enum('pending', 'in_review', 'resolved', 'rejected', 'implemented', name='feedback_status_enum'), nullable=False, default='pending')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    resolution_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    # Constraints
    __table_args__ = (
        db.Index('idx_feedback_user', 'user_id'),
        db.Index('idx_feedback_status', 'feedback_status'),
        db.Index('idx_feedback_type', 'feedback_type'),
    )
