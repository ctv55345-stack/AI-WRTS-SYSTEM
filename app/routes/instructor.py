from flask import Blueprint, render_template, redirect, url_for, flash, session, current_app, request
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from app.services.class_service import ClassService
from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.services.evaluation_service import EvaluationService
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService
from app.utils.decorators import login_required, role_required
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.routine_forms import RoutineCreateForm, RoutineEditForm, CriteriaForm
from app.forms.assignment_forms import AssignmentCreateForm
from app.forms.exam_forms import ExamCreateForm
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.schedule_forms import ScheduleForm
from app.forms.evaluation_forms import ManualEvaluationForm
from app.services.schedule_service import ScheduleService
from app.models.class_enrollment import ClassEnrollment


instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')


@instructor_bp.route('/dashboard')
@login_required
@role_required('INSTRUCTOR')
def dashboard():
    approved_classes = ClassService.get_approved_classes_by_instructor(session['user_id'])
    my_proposals = ClassService.get_my_proposals(session['user_id'])
    return render_template('instructor/dashboard.html', approved_classes=approved_classes, my_proposals=my_proposals)


@instructor_bp.route('/classes')
@login_required
@role_required('INSTRUCTOR')
def classes():
    classes = ClassService.get_approved_classes_by_instructor(session['user_id'])
    return render_template('instructor/classes.html', classes=classes)


@instructor_bp.route('/classes/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_class():
    flash('Bạn không có quyền tạo lớp trực tiếp. Vui lòng gửi đề xuất lớp học.', 'error')
    return redirect(url_for('instructor.propose_class'))


@instructor_bp.route('/classes/<int:class_id>')
@login_required
@role_required('INSTRUCTOR')
def class_detail(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    if class_obj.instructor_id != session['user_id']:
        flash('Bạn không có quyền truy cập lớp này', 'error')
        return redirect(url_for('instructor.classes'))

    enrollments = ClassService.get_enrolled_students(class_id)
    
    # Lấy thống kê lớp học
    class_overview = AnalyticsService.get_class_overview(class_id)
    
    # Lấy điểm trung bình từng học viên
    student_scores = {}
    for enrollment in enrollments:
        student_overview = AnalyticsService.get_student_overview(enrollment.student_id)
        student_scores[enrollment.student_id] = student_overview['avg_manual_score']
    
    return render_template('instructor/class_detail.html', 
                         class_obj=class_obj, 
                         enrollments=enrollments, 
                         class_overview=class_overview,
                         student_scores=student_scores,
                         ClassService=ClassService)


@instructor_bp.route('/proposals')
@login_required
@role_required('INSTRUCTOR')
def my_proposals():
    proposals = ClassService.get_my_proposals(session['user_id'])
    return render_template('instructor/my_proposals.html', proposals=proposals)


@instructor_bp.route('/classes/propose', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def propose_class():
    form = ClassCreateForm()

    if form.is_submitted() and not form.validate():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')

    if form.validate_on_submit():
        data = {
            'class_code': form.class_code.data,
            'class_name': form.class_name.data,
            'description': form.description.data,
            'level': form.level.data,
            'max_students': form.max_students.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
        }
        result = ClassService.create_class_proposal(data, session['user_id'])
        if result['success']:
            flash('Đề xuất lớp học thành công! Vui lòng chờ Ban quản lý duyệt.', 'success')
            return redirect(url_for('instructor.my_proposals'))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_propose.html', form=form)
@instructor_bp.route('/classes/<int:class_id>/schedules')
@login_required
@role_required('INSTRUCTOR')
def class_schedules(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    schedules = ScheduleService.get_schedules_by_class(class_id)
    return render_template('instructor/class_schedules.html', class_obj=class_obj, schedules=schedules)


@instructor_bp.route('/classes/<int:class_id>/schedules/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_schedule(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ScheduleForm()
    if form.validate_on_submit():
        data = {
            'day_of_week': form.day_of_week.data,
            'time_start': form.time_start.data,
            'time_end': form.time_end.data,
            'location': form.location.data,
            'notes': form.notes.data,
            'is_active': form.is_active.data,
        }
        result = ScheduleService.create_schedule(class_id, data)
        if result['success']:
            flash('Thêm lịch học thành công!', 'success')
            return redirect(url_for('instructor.class_schedules', class_id=class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/schedule_add.html', form=form, class_obj=class_obj)


@instructor_bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_schedule(schedule_id: int):
    schedule = ScheduleService.get_schedule_by_id(schedule_id)
    if not schedule or schedule.class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lịch học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ScheduleForm(obj=schedule)
    if form.validate_on_submit():
        data = {
            'day_of_week': form.day_of_week.data,
            'time_start': form.time_start.data,
            'time_end': form.time_end.data,
            'location': form.location.data,
            'notes': form.notes.data,
            'is_active': form.is_active.data,
        }
        result = ScheduleService.update_schedule(schedule_id, data)
        if result['success']:
            flash('Cập nhật lịch học thành công!', 'success')
            return redirect(url_for('instructor.class_schedules', class_id=schedule.class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/schedule_edit.html', form=form, schedule=schedule)


@instructor_bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_schedule(schedule_id: int):
    schedule = ScheduleService.get_schedule_by_id(schedule_id)
    if not schedule or schedule.class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lịch học', 'error')
        return redirect(url_for('instructor.classes'))

    class_id = schedule.class_id
    result = ScheduleService.delete_schedule(schedule_id)
    if result['success']:
        flash('Xóa lịch học thành công!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.class_schedules', class_id=class_id))


@instructor_bp.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_class(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = ClassEditForm(obj=class_obj)

    if form.validate_on_submit():
        data = {
            'class_name': form.class_name.data,
            'description': form.description.data,
            'level': form.level.data,
            'max_students': form.max_students.data,
            'end_date': form.end_date.data,
            'is_active': form.is_active.data,
        }

        result = ClassService.update_class(class_id, data)
        if result['success']:
            flash('Cập nhật lớp học thành công!', 'success')
            return redirect(url_for('instructor.class_detail', class_id=class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_edit.html', form=form, class_obj=class_obj)


@instructor_bp.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_class(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    result = ClassService.delete_class(class_id)
    if result['success']:
        flash('Xóa lớp học thành công!', 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('instructor.classes'))


@instructor_bp.route('/classes/<int:class_id>/students/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_student(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))

    form = EnrollStudentForm()
    available_students = ClassService.get_available_students(class_id)
    form.student_id.choices = [(0, '-- Chọn học viên --')] + [
        (s.user_id, f'{s.full_name} ({s.username})') for s in available_students
    ]

    if form.validate_on_submit():
        result = ClassService.enroll_student(class_id, form.student_id.data, form.notes.data)
        if result['success']:
            flash('Thêm học viên thành công!', 'success')
            return redirect(url_for('instructor.class_detail', class_id=class_id))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_add_student.html', form=form, class_obj=class_obj)


@instructor_bp.route('/enrollments/<int:enrollment_id>/remove', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def remove_student(enrollment_id: int):
    enrollment = ClassEnrollment.query.get(enrollment_id)
    if not enrollment:
        flash('Không tìm thấy đăng ký', 'error')
        return redirect(url_for('instructor.classes'))

    if enrollment.class_obj.instructor_id != session['user_id']:
        flash('Bạn không có quyền thực hiện', 'error')
        return redirect(url_for('instructor.classes'))

    class_id = enrollment.class_id
    result = ClassService.remove_student(enrollment_id)

    if result['success']:
        flash('Xóa học viên khỏi lớp thành công!', 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('instructor.class_detail', class_id=class_id))


# ============ ROUTINE MANAGEMENT ============

@instructor_bp.route('/routines')
@login_required
@role_required('INSTRUCTOR')
def routines():
    level_filter = None
    weapon_filter = None
    status_filter = None
    filters = {}
    if level_filter:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter
    if status_filter == 'published':
        filters['is_published'] = True
    elif status_filter == 'draft':
        filters['is_published'] = False
    routines = RoutineService.get_routines_by_instructor(session['user_id'], filters)
    weapons = RoutineService.get_all_weapons()
    return render_template('instructor/routines.html', routines=routines, weapons=weapons)

@instructor_bp.route('/routines/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_routine():
    form = RoutineCreateForm()
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(0, '-- Chọn binh khí --')] + [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    # DEBUG REQUEST
    if request.method == 'POST':
        print("=" * 50)
        print("REQUEST FILES:")
        print(request.files)
        print(f"Keys: {list(request.files.keys())}")
        print("FORM DATA:")
        print(f"reference_video_url: {form.reference_video_url.data}")
        print(f"reference_video_file.data: {form.reference_video_file.data}")
        print(f"reference_video_file.raw_data: {form.reference_video_file.raw_data}")
        print("=" * 50)
    
    if form.validate_on_submit():
        video_url = None
        
        # ƯU TIÊN: Upload file nếu có
        if form.reference_video_file.data:
            video_file = form.reference_video_file.data
            filename = secure_filename(video_file.filename)
            
            # Tạo tên unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Lưu file
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'routines')
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            video_file.save(filepath)
            
            video_url = f"/static/uploads/routines/{filename}"
            
        # PHƯƠNG ÁN 2: Dùng URL nếu không upload file
        elif form.reference_video_url.data:
            video_url = form.reference_video_url.data
        
        data = {
            'routine_code': form.routine_code.data,
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'duration_seconds': form.duration_seconds.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': video_url
        }
        
        result = RoutineService.create_routine(data, session['user_id'])
        if result['success']:
            flash('Tạo bài võ thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=result['routine'].routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_create.html', form=form)


@instructor_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('INSTRUCTOR')
def routine_detail(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    criteria = RoutineService.get_criteria_by_routine(routine_id)
    total_weight = sum(c.weight_percentage for c in criteria)
    return render_template('instructor/routine_detail.html', routine=routine, criteria=criteria, total_weight=total_weight)


@instructor_bp.route('/routines/<int:routine_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_routine(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    form = RoutineEditForm(obj=routine)
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    if form.validate_on_submit():
        video_url = routine.reference_video_url  # Giữ URL cũ nếu không có thay đổi
        
        # ƯU TIÊN: Upload file nếu có
        if form.reference_video_file.data:
            video_file = form.reference_video_file.data
            filename = secure_filename(video_file.filename)
            
            # Tạo tên unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            # Lưu file
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'routines')
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            video_file.save(filepath)
            
            video_url = f"/static/uploads/routines/{filename}"
            
        # PHƯƠNG ÁN 2: Dùng URL nếu không upload file
        elif form.reference_video_url.data:
            video_url = form.reference_video_url.data
        
        data = {
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'duration_seconds': form.duration_seconds.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': video_url
        }
        
        result = RoutineService.update_routine(routine_id, data, session['user_id'])
        if result['success']:
            flash('Cập nhật bài võ thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_edit.html', form=form, routine=routine)


@instructor_bp.route('/routines/<int:routine_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_routine(routine_id: int):
    result = RoutineService.publish_routine(routine_id, session['user_id'])
    flash('Đã xuất bản bài võ!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/unpublish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def unpublish_routine(routine_id: int):
    result = RoutineService.unpublish_routine(routine_id, session['user_id'])
    flash('Đã gỡ xuất bản bài võ!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_routine(routine_id: int):
    result = RoutineService.delete_routine(routine_id, session['user_id'])
    if result['success']:
        flash('Xóa bài võ thành công!', 'success')
        return redirect(url_for('instructor.routines'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/criteria/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_criteria(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    form = CriteriaForm()
    if form.validate_on_submit():
        data = {
            'criteria_name': form.criteria_name.data,
            'criteria_code': form.criteria_code.data,
            'weight_percentage': form.weight_percentage.data,
            'description': form.description.data,
            'evaluation_method': form.evaluation_method.data,
        }
        result = RoutineService.add_criteria(routine_id, data)
        if result['success']:
            flash('Thêm tiêu chí đánh giá thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=routine_id))
        else:
            flash(result['message'], 'error')
    return render_template('instructor/criteria_add.html', form=form, routine=routine)


@instructor_bp.route('/criteria/<int:criteria_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_criteria(criteria_id: int):
    from app.models.evaluation_criteria import EvaluationCriteria
    criteria = EvaluationCriteria.query.get(criteria_id)
    if not criteria or criteria.routine.instructor_id != session['user_id']:
        flash('Không tìm thấy tiêu chí', 'error')
        return redirect(url_for('instructor.routines'))
    routine_id = criteria.routine_id
    result = RoutineService.delete_criteria(criteria_id)
    flash('Xóa tiêu chí thành công!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


# ============ ASSIGNMENT MANAGEMENT ============

@instructor_bp.route('/assignments')
@login_required
@role_required('INSTRUCTOR')
def assignments():
    assignments = AssignmentService.get_assignments_by_instructor(session['user_id'])
    return render_template('instructor/assignments.html', assignments=assignments)


@instructor_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_assignment():
    form = AssignmentCreateForm()
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    from app.models.class_enrollment import ClassEnrollment
    instructor_classes = ClassService.get_approved_classes_by_instructor(session['user_id'])
    student_ids = set()
    for cls in instructor_classes:
        enrollments = ClassEnrollment.query.filter_by(class_id=cls.class_id, enrollment_status='active').all()
        student_ids.update([e.student_id for e in enrollments])
    from app.models.user import User
    students = User.query.filter(User.user_id.in_(student_ids)).all() if student_ids else []
    form.assigned_to_student.choices = [(0, '-- Chọn học viên --')] + [(s.user_id, s.full_name) for s in students]
    form.assigned_to_class.choices = [(0, '-- Chọn lớp --')] + [(c.class_id, c.class_name) for c in instructor_classes]
    if form.validate_on_submit():
        data = {
            'routine_id': form.routine_id.data,
            'assignment_type': form.assignment_type.data,
            'assigned_to_student': form.assigned_to_student.data if form.assignment_type.data == 'individual' else None,
            'assigned_to_class': form.assigned_to_class.data if form.assignment_type.data == 'class' else None,
            'deadline': form.deadline.data,
            'instructions': form.instructions.data,
            'priority': form.priority.data,
            'is_mandatory': form.is_mandatory.data,
        }
        result = AssignmentService.create_assignment(data, session['user_id'])
        if result['success']:
            flash('Gán bài tập thành công!', 'success')
            return redirect(url_for('instructor.assignments'))
        else:
            flash(result['message'], 'error')
    return render_template('instructor/assignment_create.html', form=form)


@instructor_bp.route('/assignments/<int:assignment_id>')
@login_required
@role_required('INSTRUCTOR')
def assignment_detail(assignment_id: int):
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.assigned_by != session['user_id']:
        flash('Không tìm thấy bài tập', 'error')
        return redirect(url_for('instructor.assignments'))
    status_list = AssignmentService.get_submission_status(assignment_id)
    return render_template('instructor/assignment_detail.html', assignment=assignment, status_list=status_list)


@instructor_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_assignment(assignment_id: int):
    result = AssignmentService.delete_assignment(assignment_id, session['user_id'])
    flash('Xóa bài tập thành công!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.assignments'))


# ============ EXAM MANAGEMENT ============

@instructor_bp.route('/exams')
@login_required
@role_required('INSTRUCTOR')
def exams():
    exams = ExamService.get_exams_by_instructor(session['user_id'])
    return render_template('instructor/exams.html', exams=exams)


@instructor_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_exam():
    form = ExamCreateForm()
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    classes = ClassService.get_classes_by_instructor(session['user_id'])
    form.class_id.choices = [(0, '-- Không chọn (tất cả) --')] + [(c.class_id, c.class_name) for c in classes]
    if form.validate_on_submit():
        data = {
            'exam_code': form.exam_code.data,
            'exam_name': form.exam_name.data,
            'description': form.description.data,
            'class_id': form.class_id.data if form.class_id.data else None,
            'routine_id': form.routine_id.data,
            'exam_type': form.exam_type.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'duration_minutes': form.duration_minutes.data,
            'pass_score': form.pass_score.data,
            'max_attempts': form.max_attempts.data,
        }
        result = ExamService.create_exam(data, session['user_id'])
        if result['success']:
            flash('Tạo bài kiểm tra thành công! (Nháp)', 'success')
            return redirect(url_for('instructor.exam_detail', exam_id=result['exam'].exam_id))
        else:
            flash(result['message'], 'error')
    return render_template('instructor/exam_create.html', form=form)


@instructor_bp.route('/exams/<int:exam_id>')
@login_required
@role_required('INSTRUCTOR')
def exam_detail(exam_id: int):
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam or exam.instructor_id != session['user_id']:
        flash('Không tìm thấy bài kiểm tra', 'error')
        return redirect(url_for('instructor.exams'))
    results = ExamService.get_exam_results(exam_id)
    return render_template('instructor/exam_detail.html', exam=exam, results=results)


@instructor_bp.route('/exams/<int:exam_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_exam(exam_id: int):
    result = ExamService.publish_exam(exam_id, session['user_id'])
    flash('Đã xuất bản bài kiểm tra!' if result['success'] else result['message'], 'success' if result['success'] else 'error')
    return redirect(url_for('instructor.exam_detail', exam_id=exam_id))


@instructor_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_exam(exam_id: int):
    result = ExamService.delete_exam(exam_id, session['user_id'])
    if result['success']:
        flash('Xóa bài kiểm tra thành công!', 'success')
        return redirect(url_for('instructor.exams'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))


# ============ EVALUATION MANAGEMENT ============

@instructor_bp.route('/evaluations/pending')
@login_required
@role_required('INSTRUCTOR')
def pending_evaluations():
    """Danh sách video chờ chấm điểm"""
    from flask import request
    
    # Get filter parameter
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    if show_all:
        # Show all videos (both pending and completed)
        videos = EvaluationService.get_all_submissions(session['user_id'])
    else:
        # Show only pending videos
        videos = EvaluationService.get_pending_submissions(session['user_id'])
    
    return render_template('instructor/pending_evaluations.html', videos=videos, show_all=show_all)

@instructor_bp.route('/videos/<int:video_id>/evaluate', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def evaluate_video(video_id):
    """Chấm điểm video thủ công"""
    from app.services.video_service import VideoService
    
    video_data = VideoService.get_video_with_analysis(video_id)
    if not video_data:
        flash('Không tìm thấy video', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    video = video_data['video']
    ai_analysis = video_data['ai_analysis']
    
    # Kiểm tra quyền (giảng viên của lớp học sinh đang học)
    from app.models.class_enrollment import ClassEnrollment
    from app.models.class_model import Class
    
    enrollment = ClassEnrollment.query.filter_by(
        student_id=video.student_id,
        enrollment_status='active'
    ).first()
    
    if not enrollment or enrollment.class_obj.instructor_id != session['user_id']:
        flash('Bạn không có quyền chấm điểm video này', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    form = ManualEvaluationForm()
    
    if form.validate_on_submit():
        data = {
            'overall_score': form.overall_score.data,
            'technique_score': form.technique_score.data,
            'posture_score': form.posture_score.data,
            'spirit_score': form.spirit_score.data,
            'strengths': form.strengths.data,
            'improvements_needed': form.improvements_needed.data,
            'comments': form.comments.data,
            'is_passed': form.is_passed.data
        }
        
        result = EvaluationService.create_evaluation(
            video_id, 
            session['user_id'], 
            data
        )
        
        if result['success']:
            flash('Chấm điểm thành công! Đã gửi thông báo cho học viên.', 'success')
            return redirect(url_for('instructor.pending_evaluations'))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/evaluate_video.html',
                         video=video,
                         ai_analysis=ai_analysis,
                         form=form)


# ============ ANALYTICS ============

@instructor_bp.route('/analytics')
@login_required
@role_required('INSTRUCTOR')
def analytics():
    """Dashboard phân tích giảng viên"""
    instructor_id = session['user_id']
    
    # Lấy các lớp của giảng viên
    classes = ClassService.get_approved_classes_by_instructor(instructor_id)
    
    # Thống kê bài võ
    routine_stats = AnalyticsService.get_routine_usage_stats(instructor_id)
    
    return render_template('instructor/analytics.html',
                         classes=classes,
                         routine_stats=routine_stats)

@instructor_bp.route('/classes/<int:class_id>/analytics')
@login_required
@role_required('INSTRUCTOR')
def class_analytics(class_id):
    """Phân tích chi tiết lớp học"""
    class_obj = ClassService.get_class_by_id(class_id)
    
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))
    
    overview = AnalyticsService.get_class_overview(class_id)
    rankings = AnalyticsService.get_student_ranking(class_id)
    
    return render_template('instructor/class_analytics.html',
                         class_obj=class_obj,
                         overview=overview,
                         rankings=rankings)

@instructor_bp.route('/classes/<int:class_id>/report')
@login_required
@role_required('INSTRUCTOR')
def export_class_report(class_id):
    """Export báo cáo lớp học (JSON)"""
    from flask import jsonify
    
    class_obj = ClassService.get_class_by_id(class_id)
    
    if not class_obj or class_obj.instructor_id != session['user_id']:
        flash('Không tìm thấy lớp học', 'error')
        return redirect(url_for('instructor.classes'))
    
    report = ReportService.generate_class_report(class_id)
    
    # Trả về JSON (có thể mở rộng export PDF/Excel)
    return jsonify(report)
