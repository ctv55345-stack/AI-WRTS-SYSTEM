from app.models import db
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.class_enrollment import ClassEnrollment


class ExamService:
    @staticmethod
    def create_exam(data: dict, instructor_id: int):
        if Exam.query.filter_by(exam_code=data['exam_code']).first():
            return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}

        exam = Exam(
            exam_code=data['exam_code'],
            exam_name=data['exam_name'],
            description=data.get('description'),
            class_id=data.get('class_id'),
            instructor_id=instructor_id,
            routine_id=data['routine_id'],
            exam_type=data['exam_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=data['duration_minutes'],
            pass_score=data.get('pass_score', 70.00),
            max_attempts=data.get('max_attempts', 1),
            is_published=False,
        )

        db.session.add(exam)
        db.session.commit()
        return {'success': True, 'exam': exam}

    @staticmethod
    def get_exams_by_instructor(instructor_id: int):
        return Exam.query.filter_by(instructor_id=instructor_id).order_by(Exam.created_at.desc()).all()

    @staticmethod
    def get_exam_by_id(exam_id: int):
        return Exam.query.get(exam_id)

    @staticmethod
    def publish_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}
        exam.is_published = True
        db.session.commit()
        return {'success': True, 'exam': exam}

    @staticmethod
    def delete_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa'}
        result_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        if result_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {result_count} kết quả thi'}
        db.session.delete(exam)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_exam_results(exam_id: int):
        return ExamResult.query.filter_by(exam_id=exam_id).order_by(ExamResult.submitted_at.desc()).all()

    @staticmethod
    def get_exams_for_student(student_id: int):
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active',
        ).all()
        class_ids = [e.class_id for e in enrollments]
        if not class_ids:
            return []
        return Exam.query.filter(
            Exam.class_id.in_(class_ids),
            Exam.is_published == True,
        ).order_by(Exam.start_time.desc()).all()

    @staticmethod
    def get_student_exam_result(exam_id: int, student_id: int):
        return ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id,
        ).order_by(ExamResult.attempt_number.desc()).all()


