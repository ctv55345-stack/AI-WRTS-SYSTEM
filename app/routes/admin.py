from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.user_service import UserService
from app.utils.decorators import login_required, role_required
from app.forms.admin_forms import CreateUserForm, EditUserForm

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@role_required('ADMIN')
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
@role_required('ADMIN')
def users():
    users = UserService.get_all_users()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def create_user():
    form = CreateUserForm()
    
    # Load roles vào SelectField
    roles = UserService.get_all_roles()
    form.role_id.choices = [(0, '-- Chọn vai trò --')] + [(r.role_id, r.role_name) for r in roles]
    
    if form.validate_on_submit():
        data = {
            'username': form.username.data,
            'password': form.password.data,
            'email': form.email.data,
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data,
            'role_id': form.role_id.data
        }
        
        result = UserService.create_user(data)
        if result['success']:
            flash('Tạo tài khoản thành công!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result['message'], 'error')
    
    return render_template('admin/user_create.html', form=form)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN')
def edit_user(user_id):
    user = UserService.get_user_by_id(user_id)
    form = EditUserForm(obj=user)
    
    # Load roles vào SelectField
    roles = UserService.get_all_roles()
    form.role_id.choices = [(r.role_id, r.role_name) for r in roles]
    
    if form.validate_on_submit():
        data = {
            'email': form.email.data,
            'full_name': form.full_name.data,
            'phone': form.phone.data,
            'date_of_birth': form.date_of_birth.data,
            'gender': form.gender.data if form.gender.data else None,
            'address': form.address.data,
            'role_id': form.role_id.data,
            'is_active': form.is_active.data
        }
        
        result = UserService.update_user(user_id, data)
        if result['success']:
            flash('Cập nhật thành công!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result['message'], 'error')
    
    return render_template('admin/user_edit.html', form=form, user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('ADMIN')
def delete_user(user_id):
    result = UserService.delete_user(user_id)
    if result['success']:
        flash('Xóa tài khoản thành công!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin.users'))
