from . import db
from datetime import datetime

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='CASCADE'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    assignment_type = db.Column(db.Enum('individual', 'class', name='assignment_type_enum'), nullable=False, default='individual')
    assigned_to_student = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    assigned_to_class = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'))
    deadline = db.Column(db.DateTime)
    instructions = db.Column(db.Text)
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', name='priority_enum'), nullable=False, default='normal')
    is_mandatory = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = db.relationship('TrainingVideo', backref='assignment', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            db.or_(
                db.and_(assignment_type == 'individual', assigned_to_student.isnot(None), assigned_to_class.is_(None)),
                db.and_(assignment_type == 'class', assigned_to_class.isnot(None), assigned_to_student.is_(None))
            ), name='chk_assignments_target'
        ),
        db.Index('idx_assignments_routine', 'routine_id'),
        db.Index('idx_assignments_student', 'assigned_to_student'),
        db.Index('idx_assignments_class', 'assigned_to_class'),
        db.Index('idx_assignments_deadline', 'deadline'),
    )
