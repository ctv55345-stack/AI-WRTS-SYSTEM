from . import db
from datetime import datetime

class ManualEvaluation(db.Model):
    __tablename__ = 'manual_evaluations'
    
    evaluation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.Integer, db.ForeignKey('training_videos.video_id', ondelete='CASCADE'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    overall_score = db.Column(db.Numeric(5, 2), nullable=False)
    technique_score = db.Column(db.Numeric(5, 2))
    posture_score = db.Column(db.Numeric(5, 2))
    spirit_score = db.Column(db.Numeric(5, 2))
    comments = db.Column(db.Text)
    strengths = db.Column(db.Text)
    improvements_needed = db.Column(db.Text)
    is_passed = db.Column(db.Boolean)
    evaluation_method = db.Column(db.String(20), nullable=False, default='manual')  # 'manual' or 'ai'
    ai_analysis_id = db.Column(db.Integer, db.ForeignKey('ai_analysis_results.analysis_id', ondelete='SET NULL'), nullable=True)
    ai_confidence = db.Column(db.Numeric(5, 2))  # AI confidence score if using AI
    evaluated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(overall_score >= 0, overall_score <= 100), name='chk_evaluations_overall'),
        db.CheckConstraint(db.or_(technique_score.is_(None), db.and_(technique_score >= 0, technique_score <= 100)), name='chk_evaluations_technique'),
        db.CheckConstraint(db.or_(posture_score.is_(None), db.and_(posture_score >= 0, posture_score <= 100)), name='chk_evaluations_posture'),
        db.CheckConstraint(db.or_(spirit_score.is_(None), db.and_(spirit_score >= 0, spirit_score <= 100)), name='chk_evaluations_spirit'),
        db.Index('idx_evaluations_video', 'video_id'),
        db.Index('idx_evaluations_instructor', 'instructor_id'),
        db.Index('idx_evaluations_date', 'evaluated_at'),
    )
