from datetime import datetime
from . import db


class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'

    schedule_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'), nullable=False)
    day_of_week = db.Column(
        db.Enum('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', name='day_enum'),
        nullable=False,
    )
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(100))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    class_obj = db.relationship('Class', backref=db.backref('schedules', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (
        db.CheckConstraint('time_end > time_start', name='chk_schedule_time'),
        db.Index('idx_class_schedule', 'class_id'),
        db.Index('idx_day', 'day_of_week'),
    )

    @property
    def day_display(self) -> str:
        days_map = {
            'monday': 'Thứ 2',
            'tuesday': 'Thứ 3',
            'wednesday': 'Thứ 4',
            'thursday': 'Thứ 5',
            'friday': 'Thứ 6',
            'saturday': 'Thứ 7',
            'sunday': 'Chủ nhật',
        }
        return days_map.get(self.day_of_week, self.day_of_week)
