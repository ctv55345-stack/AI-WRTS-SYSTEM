from app.models import db
from app.models.class_schedule import ClassSchedule


class ScheduleService:
    @staticmethod
    def get_schedules_by_class(class_id: int):
        return (
            ClassSchedule.query.filter_by(class_id=class_id)
            .order_by(
                db.case(
                    (ClassSchedule.day_of_week == 'monday', 1),
                    (ClassSchedule.day_of_week == 'tuesday', 2),
                    (ClassSchedule.day_of_week == 'wednesday', 3),
                    (ClassSchedule.day_of_week == 'thursday', 4),
                    (ClassSchedule.day_of_week == 'friday', 5),
                    (ClassSchedule.day_of_week == 'saturday', 6),
                    (ClassSchedule.day_of_week == 'sunday', 7),
                    else_=8,
                ),
                ClassSchedule.time_start,
            )
            .all()
        )

    @staticmethod
    def get_schedule_by_id(schedule_id: int):
        return ClassSchedule.query.get(schedule_id)

    @staticmethod
    def create_schedule(class_id: int, data: dict):
        existing = ClassSchedule.query.filter_by(
            class_id=class_id,
            day_of_week=data['day_of_week'],
            time_start=data['time_start'],
        ).first()
        if existing:
            return {'success': False, 'message': 'Lịch học này đã tồn tại'}

        schedule = ClassSchedule(
            class_id=class_id,
            day_of_week=data['day_of_week'],
            time_start=data['time_start'],
            time_end=data['time_end'],
            location=data.get('location'),
            notes=data.get('notes'),
            is_active=data.get('is_active', True),
        )

        db.session.add(schedule)
        db.session.commit()
        return {'success': True, 'schedule': schedule}

    @staticmethod
    def update_schedule(schedule_id: int, data: dict):
        schedule = ClassSchedule.query.get(schedule_id)
        if not schedule:
            return {'success': False, 'message': 'Không tìm thấy lịch học'}

        schedule.day_of_week = data['day_of_week']
        schedule.time_start = data['time_start']
        schedule.time_end = data['time_end']
        schedule.location = data.get('location')
        schedule.notes = data.get('notes')
        schedule.is_active = data.get('is_active', True)

        db.session.commit()
        return {'success': True, 'schedule': schedule}

    @staticmethod
    def delete_schedule(schedule_id: int):
        schedule = ClassSchedule.query.get(schedule_id)
        if not schedule:
            return {'success': False, 'message': 'Không tìm thấy lịch học'}

        db.session.delete(schedule)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def format_schedules(schedules: list[ClassSchedule]) -> str:
        if not schedules:
            return 'Chưa có lịch học'

        parts: list[str] = []
        for s in schedules:
            time_str = f"{s.time_start.strftime('%H:%M')}-{s.time_end.strftime('%H:%M')}"
            loc_str = f" @ {s.location}" if s.location else ''
            parts.append(f"{s.day_display}: {time_str}{loc_str}")
        return ' | '.join(parts)
