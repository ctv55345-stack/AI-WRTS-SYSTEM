from app.models import db
from app.models.assignment import Assignment
from app.models.martial_routine import MartialRoutine
from app.models.user import User
from app.models.class_enrollment import ClassEnrollment
from app.models.training_video import TrainingVideo
from app.models.class_model import Class


class AssignmentService:
    @staticmethod
    def create_assignment(data: dict, assigned_by: int):
        # Validate that the class is approved if assignment is for a class
        if data.get('assigned_to_class'):
            class_obj = Class.query.get(data['assigned_to_class'])
            if not class_obj:
                return {'success': False, 'message': 'Không tìm thấy lớp học'}
            if class_obj.approval_status != 'approved':
                return {'success': False, 'message': 'Chỉ có thể tạo bài tập cho lớp đã được duyệt'}
            if class_obj.instructor_id != assigned_by:
                return {'success': False, 'message': 'Bạn không có quyền tạo bài tập cho lớp này'}

        assignment = Assignment(
            routine_id=data['routine_id'],
            assigned_by=assigned_by,
            assignment_type=data['assignment_type'],
            assigned_to_student=data.get('assigned_to_student'),
            assigned_to_class=data.get('assigned_to_class'),
            deadline=data.get('deadline'),
            instructions=data.get('instructions'),
            priority=data.get('priority', 'normal'),
            is_mandatory=data.get('is_mandatory', True),
        )

        db.session.add(assignment)
        db.session.commit()
        return {'success': True, 'assignment': assignment}

    @staticmethod
    def get_assignments_by_instructor(instructor_id: int):
        return Assignment.query.filter_by(assigned_by=instructor_id).order_by(Assignment.created_at.desc()).all()

    @staticmethod
    def get_assignment_by_id(assignment_id: int):
        return Assignment.query.get(assignment_id)

    @staticmethod
    def get_assigned_students(assignment_id: int):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return []

        if assignment.assignment_type == 'individual':
            return [assignment.student] if assignment.student else []

        enrollments = ClassEnrollment.query.filter_by(
            class_id=assignment.assigned_to_class,
            enrollment_status='active',
        ).all()
        return [e.student for e in enrollments]

    @staticmethod
    def get_submission_status(assignment_id: int):
        students = AssignmentService.get_assigned_students(assignment_id)
        status_list = []
        for student in students:
            videos = TrainingVideo.query.filter_by(
                student_id=student.user_id,
                assignment_id=assignment_id,
            ).order_by(TrainingVideo.uploaded_at.desc()).all()
            status_list.append({
                'student': student,
                'submitted': len(videos) > 0,
                'video_count': len(videos),
                'latest_video': videos[0] if videos else None,
            })
        return status_list

    @staticmethod
    def delete_assignment(assignment_id: int, instructor_id: int):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return {'success': False, 'message': 'Không tìm thấy bài tập'}
        if assignment.assigned_by != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa bài tập này'}
        db.session.delete(assignment)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_assignments_for_student(student_id: int):
        individual = Assignment.query.filter_by(
            assignment_type='individual',
            assigned_to_student=student_id,
        ).all()

        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active',
        ).all()
        class_ids = [e.class_id for e in enrollments]
        class_assignments = Assignment.query.filter(
            Assignment.assignment_type == 'class',
            Assignment.assigned_to_class.in_(class_ids),
        ).all() if class_ids else []
        return individual + class_assignments

    @staticmethod
    def can_submit(assignment_id: int, student_id: int):
        """Check if student can submit assignment"""
        assignment = Assignment.query.get(assignment_id)
        
        if not assignment:
            return {'can_submit': False, 'message': 'Bài tập không tồn tại'}
        
        # Check deadline
        if assignment.is_expired:
            return {'can_submit': False, 'message': 'Bài tập đã quá hạn nộp'}
        
        return {'can_submit': True}
    
    @staticmethod
    def get_active_assignments_for_student(student_id: int):
        """Get active assignments that haven't expired"""
        from datetime import datetime
        
        # Get individual assignments
        individual = Assignment.query.filter_by(
            assigned_to_student=student_id,
            assignment_type='individual'
        ).all()
        
        # Get class assignments
        from app.models.class_enrollment import ClassEnrollment
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        class_assignments = Assignment.query.filter(
            Assignment.assigned_to_class.in_(class_ids),
            Assignment.assignment_type == 'class'
        ).all() if class_ids else []
        
        all_assignments = individual + class_assignments
        
        # Filter out expired assignments
        active = [a for a in all_assignments if not a.is_expired]
        
        return active


