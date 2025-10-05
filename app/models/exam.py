from . import db
from datetime import datetime

class Exam(db.Model):
    __tablename__ = 'exams'
    
    exam_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exam_code = db.Column(db.String(30), unique=True, nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='SET NULL'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='RESTRICT'), nullable=False)
    exam_type = db.Column(db.Enum('midterm', 'final', 'practice', 'certification', name='exam_type_enum'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    pass_score = db.Column(db.Numeric(5, 2), nullable=False, default=70.00)
    max_attempts = db.Column(db.Integer, nullable=False, default=1)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exam_results = db.relationship('ExamResult', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(end_time > start_time, name='chk_exams_time'),
        db.CheckConstraint(duration_minutes > 0, name='chk_exams_duration'),
        db.CheckConstraint(db.and_(pass_score >= 0, pass_score <= 100), name='chk_exams_pass_score'),
        db.CheckConstraint(max_attempts > 0, name='chk_exams_max_attempts'),
        db.Index('idx_exams_class', 'class_id'),
        db.Index('idx_exams_instructor', 'instructor_id'),
        db.Index('idx_exams_time', 'start_time', 'end_time'),
    )
