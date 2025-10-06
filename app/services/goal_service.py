from app.models import db
from app.models.goal import Goal
from datetime import datetime

class GoalService:
    
    @staticmethod
    def create_goal(student_id, data):
        """Tạo mục tiêu mới"""
        goal = Goal(
            student_id=student_id,
            goal_type=data['goal_type'],
            goal_title=data['goal_title'],
            goal_description=data.get('goal_description'),
            target_value=data['target_value'],
            unit_of_measurement=data.get('unit_of_measurement'),
            start_date=data['start_date'],
            deadline=data['deadline'],
            goal_status='active'
        )
        
        db.session.add(goal)
        db.session.commit()
        return {'success': True, 'goal': goal}
    
    @staticmethod
    def get_student_goals(student_id, status=None):
        """Lấy mục tiêu của học viên"""
        query = Goal.query.filter_by(student_id=student_id)
        
        if status:
            query = query.filter_by(goal_status=status)
        
        return query.order_by(Goal.created_at.desc()).all()
    
    @staticmethod
    def update_goal_progress(goal_id, new_value):
        """Cập nhật tiến độ mục tiêu"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return {'success': False, 'message': 'Không tìm thấy mục tiêu'}
        
        goal.current_value = new_value
        
        # Tự động hoàn thành nếu đạt target
        if new_value >= goal.target_value:
            goal.goal_status = 'completed'
            goal.completed_at = datetime.utcnow()
        
        # Kiểm tra quá hạn
        if datetime.utcnow().date() > goal.deadline and goal.goal_status == 'active':
            goal.goal_status = 'failed'
        
        db.session.commit()
        return {'success': True, 'goal': goal}
    
    @staticmethod
    def delete_goal(goal_id):
        """Xóa mục tiêu"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return {'success': False, 'message': 'Không tìm thấy mục tiêu'}
        
        db.session.delete(goal)
        db.session.commit()
        return {'success': True}
