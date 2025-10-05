from . import db
from datetime import datetime

class AIAnalysisResult(db.Model):
    __tablename__ = 'ai_analysis_results'
    
    analysis_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_id = db.Column(db.Integer, db.ForeignKey('training_videos.video_id', ondelete='CASCADE'), nullable=False, unique=True)
    weapon_detected = db.Column(db.String(50), nullable=False)
    weapon_confidence = db.Column(db.Numeric(5, 2), nullable=False)
    overall_score = db.Column(db.Numeric(5, 2), nullable=False)
    technique_score = db.Column(db.Numeric(5, 2))
    posture_score = db.Column(db.Numeric(5, 2))
    timing_score = db.Column(db.Numeric(5, 2))
    detailed_feedback = db.Column(db.JSON, nullable=False)
    key_frames = db.Column(db.JSON)
    errors_detected = db.Column(db.JSON)
    ai_model_version = db.Column(db.String(20), nullable=False)
    processing_time_seconds = db.Column(db.Numeric(8, 2), nullable=False)
    analyzed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(weapon_confidence >= 0, weapon_confidence <= 100), name='chk_analysis_weapon_confidence'),
        db.CheckConstraint(db.and_(overall_score >= 0, overall_score <= 100), name='chk_analysis_overall_score'),
        db.CheckConstraint(db.or_(technique_score.is_(None), db.and_(technique_score >= 0, technique_score <= 100)), name='chk_analysis_technique_score'),
        db.CheckConstraint(db.or_(posture_score.is_(None), db.and_(posture_score >= 0, posture_score <= 100)), name='chk_analysis_posture_score'),
        db.CheckConstraint(db.or_(timing_score.is_(None), db.and_(timing_score >= 0, timing_score <= 100)), name='chk_analysis_timing_score'),
        db.CheckConstraint(processing_time_seconds > 0, name='chk_analysis_processing_time'),
        db.Index('idx_analysis_video', 'video_id'),
        db.Index('idx_analysis_score', 'overall_score'),
        db.Index('idx_analysis_date', 'analyzed_at'),
    )
