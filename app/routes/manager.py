from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.services.class_service import ClassService
from app.utils.decorators import login_required, role_required
from app.forms.class_forms import ClassApprovalForm


manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


@manager_bp.route('/dashboard')
@login_required
@role_required('MANAGER')
def dashboard():
    stats = ClassService.get_statistics()
    # pending count
    pending_count = len(ClassService.get_pending_proposals())
    return render_template('manager/dashboard.html', stats=stats, pending_count=pending_count)


@manager_bp.route('/statistics')
@login_required
@role_required('MANAGER')
def statistics():
    stats = ClassService.get_statistics()
    all_classes = ClassService.get_all_classes()
    return render_template('manager/statistics.html', stats=stats, classes=all_classes)


@manager_bp.route('/pending-classes')
@login_required
@role_required('MANAGER')
def pending_classes():
    pending = ClassService.get_pending_proposals()
    return render_template('manager/pending_classes.html', pending=pending)


@manager_bp.route('/classes/<int:class_id>/review', methods=['GET', 'POST'])
@login_required
@role_required('MANAGER')
def review_class(class_id: int):
    class_obj = ClassService.get_class_by_id(class_id)
    if not class_obj or class_obj.approval_status != 'pending':
        flash('Không tìm thấy lớp chờ duyệt', 'error')
        return redirect(url_for('manager.pending_classes'))

    form = ClassApprovalForm()
    if form.validate_on_submit():
        if form.decision.data == 'approve':
            result = ClassService.approve_class(class_id, session['user_id'])
            if result['success']:
                flash('Đã duyệt lớp học thành công!', 'success')
            else:
                flash(result['message'], 'error')
        else:
            result = ClassService.reject_class(class_id, session['user_id'], form.rejection_reason.data)
            if result['success']:
                flash('Đã từ chối đề xuất lớp học!', 'success')
            else:
                flash(result['message'], 'error')
        return redirect(url_for('manager.pending_classes'))

    return render_template('manager/review_class.html', class_obj=class_obj, form=form)


@manager_bp.route('/all-classes')
@login_required
@role_required('MANAGER')
def all_classes():
    classes = ClassService.get_all_classes()
    return render_template('manager/all_classes.html', classes=classes)
