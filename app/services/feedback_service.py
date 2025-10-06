from app.models import db
from app.models.feedback import Feedback
from datetime import datetime

class FeedbackService:
    
    @staticmethod
    def create_feedback(user_id, data):
        """Tạo feedback mới"""
        feedback = Feedback(
            user_id=user_id,
            feedback_type=data['feedback_type'],
            subject=data['subject'],
            content=data['content'],
            priority='normal',
            feedback_status='pending'
        )
        
        db.session.add(feedback)
        db.session.commit()
        return {'success': True, 'feedback': feedback}
    
    @staticmethod
    def get_all_feedback(filters=None):
        """Lấy tất cả feedback với filter"""
        query = Feedback.query
        
        if filters:
            if filters.get('status'):
                query = query.filter_by(feedback_status=filters['status'])
            if filters.get('type'):
                query = query.filter_by(feedback_type=filters['type'])
            if filters.get('priority'):
                query = query.filter_by(priority=filters['priority'])
        
        return query.order_by(Feedback.created_at.desc()).all()
    
    @staticmethod
    def get_feedback_by_id(feedback_id):
        """Lấy feedback theo ID"""
        return Feedback.query.get(feedback_id)
    
    @staticmethod
    def update_feedback(feedback_id, data):
        """Cập nhật feedback"""
        feedback = Feedback.query.get(feedback_id)
        if not feedback:
            return {'success': False, 'message': 'Không tìm thấy phản hồi'}
        
        feedback.priority = data.get('priority', feedback.priority)
        feedback.feedback_status = data.get('feedback_status', feedback.feedback_status)
        feedback.resolution_notes = data.get('resolution_notes', feedback.resolution_notes)
        feedback.updated_at = datetime.utcnow()
        
        if data.get('feedback_status') in ['resolved', 'rejected', 'implemented']:
            feedback.resolved_at = datetime.utcnow()
        
        db.session.commit()
        return {'success': True, 'feedback': feedback}
    
    @staticmethod
    def get_user_feedback(user_id):
        """Lấy feedback của user"""
        return Feedback.query.filter_by(user_id=user_id).order_by(
            Feedback.created_at.desc()
        ).all()
