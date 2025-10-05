from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.services.class_service import ClassService
from app.utils.decorators import login_required, role_required
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.class_forms import ClassCreateForm, ClassEditForm, EnrollStudentForm
from app.forms.schedule_forms import ScheduleForm
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
    form = ClassCreateForm()

    if form.validate_on_submit():
        data = {
            'class_code': form.class_code.data,
            'class_name': form.class_name.data,
            'description': form.description.data,
            'level': form.level.data,
            'max_students': form.max_students.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'schedule': form.schedule.data,
        }

        result = ClassService.create_class(data, session['user_id'])
        if result['success']:
            flash('Tạo lớp học thành công!', 'success')
            return redirect(url_for('instructor.classes'))
        else:
            flash(result['message'], 'error')

    return render_template('instructor/class_create.html', form=form)


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
    return render_template('instructor/class_detail.html', class_obj=class_obj, enrollments=enrollments, ClassService=ClassService)


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
            'schedule': form.schedule.data,
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
