from . import db
from datetime import datetime
from .class_enrollment import ClassEnrollment

class Class(db.Model):
    __tablename__ = 'classes'
    
    class_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_code = db.Column(db.String(20), unique=True, nullable=False)
    class_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='level_enum'), nullable=False, default='beginner')
    max_students = db.Column(db.Integer, nullable=False, default=30)
    current_students = db.Column(db.Integer, nullable=False, default=0)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    # Approval workflow
    approval_status = db.Column(db.Enum('pending', 'approved', 'rejected', name='approval_status_enum'), nullable=False, default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    # Structured schedule fields
    schedule_days = db.Column(db.String(50))  # e.g., "2,4,6"
    schedule_time_start = db.Column(db.Time)  # e.g., 18:00
    schedule_time_end = db.Column(db.Time)    # e.g., 20:00
    schedule_note = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor = db.relationship('User', foreign_keys=[instructor_id], back_populates='classes_as_instructor')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_classes')
    enrollments = db.relationship('ClassEnrollment', backref='class_obj', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', foreign_keys='Assignment.assigned_to_class', backref='class_obj', lazy=True, cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='class_obj', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(max_students > 0, max_students <= 100), name='chk_classes_max_students'),
        db.CheckConstraint(db.and_(current_students >= 0, current_students <= max_students), name='chk_classes_current_students'),
        db.CheckConstraint(db.or_(end_date.is_(None), end_date >= start_date), name='chk_classes_date_range'),
        db.Index('idx_classes_instructor', 'instructor_id'),
        db.Index('idx_classes_active', 'is_active'),
        db.Index('idx_classes_level', 'level'),
        db.Index('idx_approval_status', 'approval_status'),
    )

    @property
    def actual_students_count(self):
        return ClassEnrollment.query.filter_by(
            class_id=self.class_id,
            enrollment_status='active'
        ).count()
    @property
    def approval_status_display(self):
        status_map = {
            'pending': 'Chờ duyệt',
            'approved': 'Đã duyệt',
            'rejected': 'Từ chối'
        }
        return status_map.get(self.approval_status, self.approval_status)