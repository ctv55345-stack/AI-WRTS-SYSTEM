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
    
    # THAY ĐỔI: routine_id giờ có thể NULL
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='RESTRICT'), nullable=True)
    
    # THÊM MỚI: Video upload fields
    video_upload_method = db.Column(
        db.Enum('routine', 'upload', name='video_method_enum'), 
        nullable=False, 
        default='routine'
    )
    reference_video_path = db.Column(db.String(500))  # Path video upload
    video_duration = db.Column(db.Integer)  # Độ dài video (seconds)
    
    exam_type = db.Column(db.Enum('midterm', 'final', 'practice', 'certification', name='exam_type_enum'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    pass_score = db.Column(db.Numeric(5, 2), nullable=False, default=70.00)
    max_attempts = db.Column(db.Integer, nullable=False, default=1)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (giữ nguyên)
    exam_results = db.relationship('ExamResult', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    # THÊM MỚI: Helper methods
    def get_video_url(self):
        """Lấy URL video (từ routine hoặc upload)"""
        if self.video_upload_method == 'routine' and self.routine:
            return self.routine.reference_video_url
        elif self.video_upload_method == 'upload' and self.reference_video_path:
            return f'/static/uploads/exam_videos/{self.reference_video_path}'
        return None
    
    def has_video(self):
        """Kiểm tra có video hay không"""
        return (self.video_upload_method == 'routine' and self.routine_id) or \
               (self.video_upload_method == 'upload' and self.reference_video_path)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(end_time > start_time, name='chk_exams_time'),
        db.CheckConstraint(duration_minutes > 0, name='chk_exams_duration'),
        db.CheckConstraint(db.and_(pass_score >= 0, pass_score <= 100), name='chk_exams_pass_score'),
        db.CheckConstraint(max_attempts > 0, name='chk_exams_max_attempts'),
        # THÊM MỚI: Constraint đảm bảo có video
        db.CheckConstraint(
            db.or_(
                db.and_(video_upload_method == 'routine', routine_id.isnot(None)),
                db.and_(video_upload_method == 'upload', reference_video_path.isnot(None))
            ),
            name='chk_exams_video_source'
        ),
        db.Index('idx_exams_class', 'class_id'),
        db.Index('idx_exams_instructor', 'instructor_id'),
        db.Index('idx_exams_time', 'start_time', 'end_time'),
    )
