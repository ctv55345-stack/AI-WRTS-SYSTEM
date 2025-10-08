from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.utils.decorators import login_required, role_required
from app.utils.helpers import get_vietnam_time, get_vietnam_time_naive
from app.models.class_enrollment import ClassEnrollment
from app.models.class_model import Class
from app.models.class_schedule import ClassSchedule
from app.models.user import User
from sqlalchemy import and_
from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.services.video_service import VideoService
from app.services.ai_service import AIService
from app.services.analytics_service import AnalyticsService
from app.services.goal_service import GoalService
from app.forms.goal_forms import GoalCreateForm


student_bp = Blueprint('student', __name__, url_prefix='/student')


@student_bp.route('/dashboard')
@login_required
@role_required('STUDENT')
def dashboard():
    # Thống kê nhanh
    student_id = session['user_id']

    # Đếm lớp đang học
    active_classes = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).count()

    # Đếm lớp đã hoàn thành
    completed_classes = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='completed'
    ).count()

    # Lấy lịch học hôm nay (lấy 5 lịch gần nhất)
    today = get_vietnam_time_naive()
    day_map = {
        0: 'monday', 1: 'tuesday', 2: 'wednesday', 3: 'thursday',
        4: 'friday', 5: 'saturday', 6: 'sunday'
    }
    today_day = day_map[today.weekday()]

    # Lấy lịch hôm nay
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()

    class_ids = [e.class_id for e in enrollments]

    today_schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id.in_(class_ids),
        ClassSchedule.day_of_week == today_day,
        ClassSchedule.is_active == True
    ).order_by(ClassSchedule.time_start).limit(5).all()

    return render_template('student/dashboard.html',
                         active_classes=active_classes,
                         completed_classes=completed_classes,
                         today_schedules=today_schedules)


@student_bp.route('/classes')
@login_required
@role_required('STUDENT')
def classes():
    """Danh sách tất cả lớp học của học viên"""
    student_id = session['user_id']

    # Lấy tất cả enrollments
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id
    ).order_by(ClassEnrollment.enrolled_at.desc()).all()

    return render_template('student/classes.html', enrollments=enrollments)


@student_bp.route('/classes/<int:class_id>')
@login_required
@role_required('STUDENT')
def class_detail(class_id: int):
    """Chi tiết lớp học"""
    student_id = session['user_id']

    # Kiểm tra học viên có trong lớp không
    enrollment = ClassEnrollment.query.filter_by(
        student_id=student_id,
        class_id=class_id
    ).first()

    if not enrollment:
        flash('Bạn không có quyền truy cập lớp này', 'error')
        return redirect(url_for('student.classes'))

    class_obj = Class.query.get(class_id)
    if not class_obj:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('student.classes'))

    # Lấy lịch học
    schedules = ClassSchedule.query.filter_by(
        class_id=class_id,
        is_active=True
    ).order_by(ClassSchedule.day_of_week, ClassSchedule.time_start).all()

    # Lấy danh sách học viên cùng lớp
    classmates = ClassEnrollment.query.filter_by(
        class_id=class_id,
        enrollment_status='active'
    ).filter(ClassEnrollment.student_id != student_id).all()

    return render_template('student/class_detail.html',
                         class_obj=class_obj,
                         enrollment=enrollment,
                         schedules=schedules,
                         classmates=classmates)


@student_bp.route('/schedules')
@login_required
@role_required('STUDENT')
def all_schedules():
    """Xem tất cả lịch học (theo tuần)"""
    student_id = session['user_id']

    # Lấy tất cả lớp đang học
    enrollments = ClassEnrollment.query.filter_by(
        student_id=student_id,
        enrollment_status='active'
    ).all()

    class_ids = [e.class_id for e in enrollments]

    # Lấy tất cả lịch học
    schedules = ClassSchedule.query.filter(
        ClassSchedule.class_id.in_(class_ids),
        ClassSchedule.is_active == True
    ).order_by(ClassSchedule.day_of_week, ClassSchedule.time_start).all()

    # Nhóm theo ngày
    schedule_by_day = {
        'monday': [],
        'tuesday': [],
        'wednesday': [],
        'thursday': [],
        'friday': [],
        'saturday': [],
        'sunday': []
    }

    for schedule in schedules:
        schedule_by_day[schedule.day_of_week].append(schedule)

    return render_template('student/schedules.html',
                         schedule_by_day=schedule_by_day)


# ============ ROUTINE VIEW (STUDENT) ============

@student_bp.route('/routines')
@login_required
@role_required('STUDENT')
def routines():
    level_filter = None
    weapon_filter = None
    filters = {}
    if level_filter:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter
    routines = RoutineService.get_published_routines(filters)
    weapons = RoutineService.get_all_weapons()
    return render_template('student/routines.html', routines=routines, weapons=weapons)


@student_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('STUDENT')
def routine_detail(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or not routine.is_published:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('student.routines'))
    criteria = RoutineService.get_criteria_by_routine(routine_id)
    return render_template('student/routine_detail.html', routine=routine, criteria=criteria)


@student_bp.route('/my-assignments')
@login_required
@role_required('STUDENT')
def my_assignments():
    # Use the new method that filters out expired assignments
    assignments = AssignmentService.get_active_assignments_for_student(session['user_id'])
    from datetime import datetime
    pending = []
    completed = []
    for assignment in assignments:
        from app.models.training_video import TrainingVideo
        submitted = TrainingVideo.query.filter_by(
            student_id=session['user_id'],
            assignment_id=assignment.assignment_id,
        ).first()
        if submitted:
            completed.append({'assignment': assignment, 'video': submitted})
        else:
            pending.append(assignment)
    return render_template('student/my_assignments.html', pending=pending, completed=completed)


@student_bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@role_required('STUDENT')
def submit_assignment(assignment_id):
    """Nộp bài tập - Upload video"""
    
    # GET: Hiển thị form upload
    if request.method == 'GET':
        assignment = AssignmentService.get_assignment_by_id(assignment_id)
        
        if not assignment:
            flash('Không tìm thấy bài tập', 'error')
            return redirect(url_for('student.my_assignments'))
        
        # Kiểm tra quyền submit
        check = AssignmentService.can_submit(assignment_id, session['user_id'])
        if not check['can_submit']:
            flash(check['message'], 'error')
            return redirect(url_for('student.my_assignments'))
        
        return render_template('student/assignment_submit.html', assignment=assignment)
    
    # POST: Xử lý upload video
    if request.method == 'POST':
        # Kiểm tra quyền submit
        check = AssignmentService.can_submit(assignment_id, session['user_id'])
        
        if not check['can_submit']:
            flash(check['message'], 'error')
            return redirect(url_for('student.my_assignments'))
        
        # Validate file upload
        if 'video_file' not in request.files:
            flash('Không tìm thấy file video', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        video_file = request.files['video_file']
        
        if video_file.filename == '':
            flash('Chưa chọn file', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        # Kiểm tra định dạng file
        allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}
        file_ext = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
        
        if file_ext not in allowed_extensions:
            flash(f'Định dạng không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))
        
        try:
            # Lấy thông tin assignment
            assignment = AssignmentService.get_assignment_by_id(assignment_id)
            
            # Lưu video với assignment_id
            video = VideoService.save_video(
                file=video_file,
                student_id=session['user_id'],
                routine_id=assignment.routine_id,
                assignment_id=assignment_id,
                notes=request.form.get('notes', '')
            )
            
            # Trigger AI phân tích (nếu có)
            AIService.process_video_mock(video.video_id)
            
            flash('Nộp bài thành công! Hệ thống đang phân tích video...', 'success')
            return redirect(url_for('student.my_assignments'))
            
        except Exception as e:
            flash(f'Lỗi khi nộp bài: {str(e)}', 'error')
            return redirect(url_for('student.submit_assignment', assignment_id=assignment_id))


@student_bp.route('/my-exams')
@login_required
@role_required('STUDENT')
def my_exams():
    exams = ExamService.get_exams_for_student(session['user_id'])
    now = get_vietnam_time_naive()
    upcoming = []
    active = []  # Đang trong thời gian thi
    past = []
    
    for exam in exams:
        results = ExamService.get_student_exam_result(exam.exam_id, session['user_id'])
        exam_info = {
            'exam': exam,
            'results': results,
            'attempts_used': len(results),
            'can_attempt': len(results) < exam.max_attempts and now < exam.end_time,
        }
        
        # Phân loại exam theo thời gian
        if now < exam.start_time:
            # Chưa đến giờ thi
            upcoming.append(exam_info)
        elif now <= exam.end_time:
            # Đang trong thời gian thi
            active.append(exam_info)
        else:
            # Đã hết hạn thi
            past.append(exam_info)
    
    return render_template('student/my_exams.html', 
                         upcoming=upcoming, 
                         active=active,
                         past=past, 
                         now=now)


# ============ ANALYTICS & GOALS ============

@student_bp.route('/analytics')
@login_required
@role_required('STUDENT')
def analytics():
    """Dashboard phân tích học viên"""
    student_id = session['user_id']
    
    overview = AnalyticsService.get_student_overview(student_id)
    score_data = AnalyticsService.get_score_progression(student_id, days=30)
    completion = AnalyticsService.get_routine_completion(student_id)
    strengths = AnalyticsService.get_strengths_weaknesses(student_id)
    
    return render_template('student/analytics.html',
                         overview=overview,
                         score_data=score_data,
                         completion=completion,
                         strengths=strengths)

@student_bp.route('/goals')
@login_required
@role_required('STUDENT')
def goals():
    """Quản lý mục tiêu"""
    student_id = session['user_id']
    active_goals = GoalService.get_student_goals(student_id, status='active')
    completed_goals = GoalService.get_student_goals(student_id, status='completed')
    
    return render_template('student/goals.html',
                         active_goals=active_goals,
                         completed_goals=completed_goals)

@student_bp.route('/goals/create', methods=['GET', 'POST'])
@login_required
@role_required('STUDENT')
def create_goal():
    """Tạo mục tiêu mới"""
    form = GoalCreateForm()
    
    if form.validate_on_submit():
        data = {
            'goal_type': form.goal_type.data,
            'goal_title': form.goal_title.data,
            'goal_description': form.goal_description.data,
            'target_value': form.target_value.data,
            'unit_of_measurement': form.unit_of_measurement.data,
            'start_date': form.start_date.data,
            'deadline': form.deadline.data
        }
        
        result = GoalService.create_goal(session['user_id'], data)
        
        if result['success']:
            flash('Tạo mục tiêu thành công!', 'success')
            return redirect(url_for('student.goals'))
        else:
            flash('Có lỗi xảy ra', 'error')
    
    return render_template('student/goal_create.html', form=form)

@student_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
@role_required('STUDENT')
def delete_goal(goal_id):
    """Xóa mục tiêu"""
    result = GoalService.delete_goal(goal_id)
    
    if result['success']:
        flash('Xóa mục tiêu thành công!', 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('student.goals'))


# ============ EXAM TAKING (THÊM MỚI) ============

@student_bp.route('/exams/<int:exam_id>/take', methods=['GET'])
@login_required
@role_required('STUDENT')
def take_exam(exam_id: int):
    """Trang làm bài thi"""
    # Lấy thông tin exam
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam or not exam.is_published:
        flash('Không tìm thấy bài kiểm tra hoặc chưa được xuất bản', 'error')
        return redirect(url_for('student.my_exams'))
    
    # Kiểm tra điều kiện vào thi
    can_take, message = ExamService.can_take_exam(exam_id, session['user_id'])
    if not can_take:
        flash(message, 'error')
        return redirect(url_for('student.my_exams'))
    
    # Lấy số lần đã thi
    results = ExamService.get_student_exam_result(exam_id, session['user_id'])
    attempt_number = len(results) + 1
    
    # Lấy video URL
    video_url = exam.get_video_url()
    
    return render_template(
        'student/take_exam.html',
        exam=exam,
        attempt_number=attempt_number,
        video_url=video_url
    )


@student_bp.route('/exams/<int:exam_id>/submit', methods=['POST'])
@login_required
@role_required('STUDENT')
def submit_exam(exam_id: int):
    """Nộp bài thi"""
    # Kiểm tra điều kiện
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam:
        flash('Không tìm thấy bài kiểm tra', 'error')
        return redirect(url_for('student.my_exams'))
    
    can_take, message = ExamService.can_take_exam(exam_id, session['user_id'])
    if not can_take:
        flash(message, 'error')
        return redirect(url_for('student.my_exams'))
    
    # Lấy video file
    if 'student_video' not in request.files:
        flash('Vui lòng ghi video làm bài', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    video_file = request.files['student_video']
    if not video_file or video_file.filename == '':
        flash('Vui lòng chọn video', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    # Validate video format
    allowed_extensions = {'mp4', 'avi', 'mov', 'webm'}
    file_ext = video_file.filename.rsplit('.', 1)[1].lower() if '.' in video_file.filename else ''
    
    if file_ext not in allowed_extensions:
        flash(f'Định dạng không hợp lệ. Chỉ chấp nhận: {", ".join(allowed_extensions)}', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))
    
    try:
        # Nộp bài và lưu kết quả
        result = ExamService.submit_exam_result(
            exam_id=exam_id,
            student_id=session['user_id'],
            video_file=video_file,
            notes=request.form.get('notes', '')
        )
        
        if result['success']:
            flash('Nộp bài thành công! Hệ thống đang chấm điểm...', 'success')
            return redirect(url_for('student.my_exams'))
        else:
            flash(result['message'], 'error')
            return redirect(url_for('student.take_exam', exam_id=exam_id))
            
    except Exception as e:
        flash(f'Lỗi khi nộp bài: {str(e)}', 'error')
        return redirect(url_for('student.take_exam', exam_id=exam_id))