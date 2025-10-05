from . import db
from datetime import datetime

class TrainingHistory(db.Model):
    __tablename__ = 'training_history'
    
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='RESTRICT'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('training_videos.video_id', ondelete='SET NULL'))
    final_score = db.Column(db.Numeric(5, 2))
    evaluation_source = db.Column(db.Enum('ai', 'instructor', 'combined', name='eval_source_enum'), nullable=False)
    is_passed = db.Column(db.Boolean)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    practice_duration_minutes = db.Column(db.Integer)
    practiced_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.or_(final_score.is_(None), db.and_(final_score >= 0, final_score <= 100)), name='chk_history_final_score'),
        db.CheckConstraint(attempt_number > 0, name='chk_history_attempt'),
        db.Index('idx_history_student', 'student_id'),
        db.Index('idx_history_routine', 'routine_id'),
        db.Index('idx_history_date', 'practiced_at'),
        db.Index('idx_history_passed', 'is_passed'),
    )
