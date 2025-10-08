from app.models import db
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.class_enrollment import ClassEnrollment
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cv2
from flask import current_app


class ExamService:
    # THÊM MỚI: Constants
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    @staticmethod
    def _validate_video_file(file):
        """Validate uploaded video file"""
        if not file:
            return False, "Không có file"
        
        filename = secure_filename(file.filename)
        if not ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in ExamService.ALLOWED_EXTENSIONS):
            return False, "Định dạng không hợp lệ (chỉ chấp nhận MP4, AVI, MOV, MKV)"
        
        # Kiểm tra size (nếu có)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > ExamService.MAX_FILE_SIZE:
            return False, "File quá lớn (tối đa 500MB)"
        
        return True, filename
    
    @staticmethod
    def _get_video_duration(file_path):
        """Lấy độ dài video bằng OpenCV"""
        try:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = int(frame_count / fps) if fps > 0 else 0
            cap.release()
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0
    
    @staticmethod
    def _save_video_file(file, exam_id):
        """Lưu video file và trả về path + duration"""
        is_valid, result = ExamService._validate_video_file(file)
        if not is_valid:
            return None, result
        
        filename = result
        
        # Tạo thư mục nếu chưa có
        upload_folder = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
            'exam_videos'
        )
        os.makedirs(upload_folder, exist_ok=True)
        
        # Tạo tên file mới: exam_{id}_{timestamp}.ext
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"exam_{exam_id}_{int(datetime.utcnow().timestamp())}.{ext}"
        file_path = os.path.join(upload_folder, new_filename)
        
        # Lưu file
        file.save(file_path)
        
        # Lấy duration
        duration = ExamService._get_video_duration(file_path)
        
        return new_filename, duration

    @staticmethod
    def create_exam(data: dict, instructor_id: int, video_file=None):
        """
        Tạo exam mới - HỖ TRỢ CẢ ROUTINE VÀ UPLOAD
        
        Args:
            data: Dict chứa thông tin exam
            instructor_id: ID giảng viên
            video_file: FileStorage object (optional, nếu upload)
        """
        # Kiểm tra mã trùng
        if Exam.query.filter_by(exam_code=data['exam_code']).first():
            return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}
        
        # Tạo exam object
        exam = Exam(
            exam_code=data['exam_code'],
            exam_name=data['exam_name'],
            description=data.get('description'),
            class_id=data.get('class_id'),
            instructor_id=instructor_id,
            exam_type=data['exam_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=data['duration_minutes'],
            pass_score=data.get('pass_score', 70.00),
            max_attempts=data.get('max_attempts', 1),
            is_published=False,
            video_upload_method=data.get('video_source', 'routine')
        )
        
        # Xử lý video dựa trên method
        if data.get('video_source') == 'routine':
            # Dùng routine
            exam.routine_id = data.get('routine_id')
            if not exam.routine_id:
                return {'success': False, 'message': 'Vui lòng chọn bài võ'}
        
        elif data.get('video_source') == 'upload':
            # Upload video mới
            if not video_file:
                return {'success': False, 'message': 'Vui lòng upload video'}
            
            # Tạm thời set reference_video_path = 'temp' để pass constraint
            exam.reference_video_path = 'temp'
        
        else:
            return {'success': False, 'message': 'Phương thức video không hợp lệ'}
        
        try:
            # Add exam và flush để lấy exam_id
            db.session.add(exam)
            db.session.flush()
            
            # Nếu là upload, lưu video file và cập nhật path
            if data.get('video_source') == 'upload':
                filename, duration = ExamService._save_video_file(video_file, exam.exam_id)
                if filename is None:
                    db.session.rollback()
                    return {'success': False, 'message': duration}  # duration chứa error message
                
                exam.reference_video_path = filename
                exam.video_duration = duration
            
            db.session.commit()
            return {'success': True, 'exam': exam}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi: {str(e)}'}

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
        
        # Xóa video file nếu có
        if exam.video_upload_method == 'upload' and exam.reference_video_path:
            try:
                file_path = os.path.join(
                    current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
                    'exam_videos',
                    exam.reference_video_path
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting video file: {e}")
        
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
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        if not class_ids:
            return []
        
        return Exam.query.filter(
            Exam.class_id.in_(class_ids),
            Exam.is_published == True
        ).order_by(Exam.start_time.desc()).all()

    @staticmethod
    def get_student_exam_result(exam_id: int, student_id: int):
        return ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).order_by(ExamResult.attempt_number.desc()).all()


