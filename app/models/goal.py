from . import db
from datetime import datetime

class Goal(db.Model):
    __tablename__ = 'goals'
    
    goal_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    goal_type = db.Column(db.Enum('score_improvement', 'practice_frequency', 'routine_completion', 'custom', name='goal_type_enum'), nullable=False)
    goal_title = db.Column(db.String(200), nullable=False)
    goal_description = db.Column(db.Text)
    target_value = db.Column(db.Numeric(10, 2), nullable=False)
    current_value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unit_of_measurement = db.Column(db.String(50))
    start_date = db.Column(db.Date, nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    goal_status = db.Column(db.Enum('active', 'completed', 'failed', 'cancelled', name='goal_status_enum'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(target_value > 0, current_value >= 0, current_value <= target_value), name='chk_goals_values'),
        db.CheckConstraint(deadline >= start_date, name='chk_goals_dates'),
        db.Index('idx_goals_student', 'student_id'),
        db.Index('idx_goals_status', 'goal_status'),
        db.Index('idx_goals_deadline', 'deadline'),
    )
