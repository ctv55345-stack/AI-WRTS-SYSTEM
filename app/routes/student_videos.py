from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.forms.video_forms import VideoUploadForm, VideoFilterForm
from app.services.video_service import VideoService
from app.services.ai_service import AIService
from app.models.martial_routine import MartialRoutine
from app.models.assignment import Assignment
from functools import wraps

student_videos_bp = Blueprint('student_videos', __name__, url_prefix='/student/videos')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập', 'danger')
            return redirect(url_for('auth.login'))
        if session.get('role_code') != 'STUDENT':
            flash('Chỉ học viên mới có quyền truy cập', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_videos_bp.route('/upload', methods=['GET', 'POST'])
@student_required
def upload():
    """Upload video bài tập"""
    form = VideoUploadForm()
    
    # Load danh sách bài võ
    routines = MartialRoutine.query.filter_by(is_published=True).all()
    form.routine_id.choices = [(r.routine_id, f"{r.routine_name} ({r.routine_code})") for r in routines]
    
    # Nếu có assignment_id từ URL
    assignment_id = request.args.get('assignment_id')
    if assignment_id:
        form.assignment_id.data = assignment_id
        assignment = Assignment.query.get(assignment_id)
        if assignment:
            form.routine_id.data = assignment.routine_id
    
    if form.validate_on_submit():
        try:
            # Lưu video
            video = VideoService.save_video(
                file=form.video_file.data,
                student_id=session.get('user_id'),
                routine_id=form.routine_id.data,
                assignment_id=form.assignment_id.data if form.assignment_id.data else None,
                notes=form.notes.data
            )
            
            # Trigger AI processing (mock)
            AIService.process_video_mock(video.video_id)
            
            flash('Upload video thành công! Hệ thống đang phân tích...', 'success')
            return redirect(url_for('student_videos.history'))
            
        except Exception as e:
            flash(f'Lỗi khi upload: {str(e)}', 'danger')
    
    return render_template('student/video_upload.html', form=form)

@student_videos_bp.route('/history')
@student_required
def history():
    """Lịch sử nộp bài"""
    filter_form = VideoFilterForm()
    
    # Load danh sách bài võ cho filter (dùng 0 cho "Tất cả")
    routines = MartialRoutine.query.filter_by(is_published=True).all()
    filter_form.routine_id.choices = [(0, 'Tất cả')] + [(r.routine_id, r.routine_name) for r in routines]
    
    # Set choices cho status
    filter_form.status.choices = [
        ('', 'Tất cả'),
        ('pending', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại')
    ]
    
    # Lấy filter params
    routine_id = request.args.get('routine_id', type=int)
    status = request.args.get('status')
    
    # Nếu routine_id = 0 thì bỏ filter
    if routine_id == 0:
        routine_id = None
    
    # Nếu status = '' thì bỏ filter
    if status == '':
        status = None
    
    # Lấy danh sách video
    videos = VideoService.get_student_videos(
        student_id=session.get('user_id'),
        routine_id=routine_id,
        status=status
    )
    
    return render_template('student/video_history.html', 
                         videos=videos, 
                         filter_form=filter_form)

@student_videos_bp.route('/result/<int:video_id>')
@student_required
def view_result(video_id):
    """Xem kết quả phân tích"""
    result = VideoService.get_video_with_analysis(video_id)
    
    if not result:
        flash('Video không tồn tại', 'danger')
        return redirect(url_for('student_videos.history'))
    
    # Kiểm tra quyền truy cập
    if result['video'].student_id != session.get('user_id'):
        flash('Bạn không có quyền xem video này', 'danger')
        return redirect(url_for('student_videos.history'))
    
    return render_template('student/video_result.html', **result)

@student_videos_bp.route('/compare/<int:video_id>')
@student_required
def compare(video_id):
    """So sánh video với video mẫu"""
    video = VideoService.get_video_by_id(video_id)
    
    if not video:
        flash('Video không tồn tại', 'danger')
        return redirect(url_for('student_videos.history'))
    
    # Kiểm tra quyền truy cập
    if video.student_id != session.get('user_id'):
        flash('Bạn không có quyền xem video này', 'danger')
        return redirect(url_for('student_videos.history'))
    
    # Lấy video mẫu chuẩn
    reference_video = video.routine.reference_video_url if video.routine else None
    
    return render_template('student/video_compare.html', 
                         student_video=video, 
                         reference_video=reference_video)