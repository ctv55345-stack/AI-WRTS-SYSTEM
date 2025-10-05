from . import db
from datetime import datetime

class TrainingVideo(db.Model):
    __tablename__ = 'training_videos'
    
    video_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='RESTRICT'), nullable=False)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.assignment_id', ondelete='SET NULL'))
    video_url = db.Column(db.String(500), nullable=False)
    thumbnail_url = db.Column(db.String(500))
    file_size_mb = db.Column(db.Numeric(10, 2))
    duration_seconds = db.Column(db.Integer, nullable=False)
    resolution = db.Column(db.String(20))
    upload_status = db.Column(db.Enum('uploading', 'completed', 'failed', name='upload_status_enum'), nullable=False, default='uploading')
    processing_status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='processing_status_enum'), nullable=False, default='pending')
    uploaded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    ai_analysis = db.relationship('AIAnalysisResult', backref='video', uselist=False, lazy=True, cascade='all, delete-orphan')
    manual_evaluations = db.relationship('ManualEvaluation', backref='video', lazy=True, cascade='all, delete-orphan')
    training_histories = db.relationship('TrainingHistory', backref='video', lazy=True)
    exam_results = db.relationship('ExamResult', backref='video', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.or_(file_size_mb.is_(None), file_size_mb > 0), name='chk_videos_file_size'),
        db.CheckConstraint(duration_seconds > 0, name='chk_videos_duration'),
        db.Index('idx_videos_student', 'student_id'),
        db.Index('idx_videos_routine', 'routine_id'),
        db.Index('idx_videos_assignment', 'assignment_id'),
        db.Index('idx_videos_status', 'processing_status'),
        db.Index('idx_videos_uploaded', 'uploaded_at'),
    )
