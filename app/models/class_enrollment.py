from . import db
from datetime import datetime

class ClassEnrollment(db.Model):
    __tablename__ = 'class_enrollments'
    
    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    enrollment_status = db.Column(db.Enum('active', 'suspended', 'completed', 'dropped', name='enrollment_status_enum'), nullable=False, default='active')
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', name='uq_class_student'),
        db.Index('idx_enrollments_class', 'class_id'),
        db.Index('idx_enrollments_student', 'student_id'),
        db.Index('idx_enrollments_status', 'enrollment_status'),
    )
