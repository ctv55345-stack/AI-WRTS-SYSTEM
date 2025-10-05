from . import db
from datetime import datetime

class ExamResult(db.Model):
    __tablename__ = 'exam_results'
    
    result_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.exam_id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('training_videos.video_id', ondelete='SET NULL'))
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    score = db.Column(db.Numeric(5, 2))
    result_status = db.Column(db.Enum('submitted', 'grading', 'graded', 'passed', 'failed', name='result_status_enum'), nullable=False, default='submitted')
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    graded_at = db.Column(db.DateTime)
    instructor_comments = db.Column(db.Text)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.or_(score.is_(None), db.and_(score >= 0, score <= 100)), name='chk_results_score'),
        db.CheckConstraint(attempt_number > 0, name='chk_results_attempt'),
        db.Index('idx_results_exam', 'exam_id'),
        db.Index('idx_results_student', 'student_id'),
        db.Index('idx_results_status', 'result_status'),
    )
