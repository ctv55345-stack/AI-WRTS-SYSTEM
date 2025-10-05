from . import db
from datetime import datetime

class MartialRoutine(db.Model):
    __tablename__ = 'martial_routines'
    
    routine_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    routine_code = db.Column(db.String(30), unique=True, nullable=False)
    routine_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    weapon_id = db.Column(db.Integer, db.ForeignKey('weapons.weapon_id', ondelete='RESTRICT'), nullable=False)
    level = db.Column(db.Enum('beginner', 'intermediate', 'advanced', name='routine_level_enum'), nullable=False, default='beginner')
    difficulty_score = db.Column(db.Numeric(3, 1), nullable=False, default=1.0)
    reference_video_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    duration_seconds = db.Column(db.Integer, nullable=False)
    total_moves = db.Column(db.Integer, nullable=False, default=1)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    pass_threshold = db.Column(db.Numeric(5, 2), nullable=False, default=70.00)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluation_criteria = db.relationship('EvaluationCriteria', backref='routine', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='routine', lazy=True, cascade='all, delete-orphan')
    videos = db.relationship('TrainingVideo', backref='routine', lazy=True)
    training_histories = db.relationship('TrainingHistory', backref='routine', lazy=True)
    exams = db.relationship('Exam', backref='routine', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(duration_seconds > 0, duration_seconds <= 3600), name='chk_routines_duration'),
        db.CheckConstraint(db.and_(difficulty_score >= 1.0, difficulty_score <= 10.0), name='chk_routines_difficulty'),
        db.CheckConstraint(db.and_(pass_threshold >= 0, pass_threshold <= 100), name='chk_routines_threshold'),
        db.CheckConstraint(total_moves > 0, name='chk_routines_total_moves'),
        db.Index('idx_routines_weapon', 'weapon_id'),
        db.Index('idx_routines_level', 'level'),
        db.Index('idx_routines_instructor', 'instructor_id'),
        db.Index('idx_routines_published', 'is_published', 'is_active'),
    )
