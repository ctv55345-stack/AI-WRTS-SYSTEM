from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from app.utils.decorators import login_required, role_required
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
    from datetime import datetime
    today = datetime.now()
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
    from datetime import datetime
    now = datetime.utcnow()
    upcoming = []
    past = []
    for exam in exams:
        results = ExamService.get_student_exam_result(exam.exam_id, session['user_id'])
        exam_info = {
            'exam': exam,
            'results': results,
            'attempts_used': len(results),
            'can_attempt': len(results) < exam.max_attempts and now < exam.end_time,
        }
        if now < exam.start_time:
            upcoming.append(exam_info)
        else:
            past.append(exam_info)
    return render_template('student/my_exams.html', upcoming=upcoming, past=past)
