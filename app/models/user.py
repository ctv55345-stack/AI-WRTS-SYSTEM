from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('male', 'female', 'other', name='gender_enum'))
    address = db.Column(db.Text)
    avatar_url = db.Column(db.String(500))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id', ondelete='RESTRICT'), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_email_verified = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Relationships
    classes_as_instructor = db.relationship('Class', foreign_keys='Class.instructor_id', backref='instructor', lazy=True)
    enrollments = db.relationship('ClassEnrollment', foreign_keys='ClassEnrollment.student_id', backref='student', lazy=True)
    routines_created = db.relationship('MartialRoutine', foreign_keys='MartialRoutine.instructor_id', backref='creator', lazy=True)
    assignments_created = db.relationship('Assignment', foreign_keys='Assignment.assigned_by', backref='assigner', lazy=True)
    assignments_received = db.relationship('Assignment', foreign_keys='Assignment.assigned_to_student', backref='student', lazy=True)
    videos = db.relationship('TrainingVideo', backref='student', lazy=True)
    manual_evaluations = db.relationship('ManualEvaluation', foreign_keys='ManualEvaluation.instructor_id', backref='evaluator', lazy=True)
    training_histories = db.relationship('TrainingHistory', backref='student', lazy=True)
    goals = db.relationship('Goal', backref='student', lazy=True)
    notifications_received = db.relationship('Notification', foreign_keys='Notification.recipient_id', backref='recipient', lazy=True)
    notifications_sent = db.relationship('Notification', foreign_keys='Notification.sender_id', backref='sender', lazy=True)
    exams_created = db.relationship('Exam', backref='instructor', lazy=True)
    exam_results = db.relationship('ExamResult', backref='student', lazy=True)
    feedback_submitted = db.relationship('Feedback', foreign_keys='Feedback.user_id', backref='user', lazy=True)
    feedback_assigned = db.relationship('Feedback', foreign_keys='Feedback.assigned_to', backref='assignee', lazy=True)
    auth_tokens = db.relationship('AuthToken', backref='user', lazy=True)
    
    # Password methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.func.char_length(username) >= 3, name='chk_users_username_length'),
        db.CheckConstraint(db.func.char_length(password_hash) >= 60, name='chk_users_password_length'),
        db.Index('idx_users_role', 'role_id'),
        db.Index('idx_users_active', 'is_active'),
        db.Index('idx_users_email', 'email'),
    )