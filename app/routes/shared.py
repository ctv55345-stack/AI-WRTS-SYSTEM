from flask import Blueprint, render_template, redirect, url_for
from flask import session

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/')
def index():
    # Redirect to login page
    return redirect(url_for('auth.login'))

@shared_bp.route('/home')
def home():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Redirect based on role
    role_code = session.get('role_code')
    if role_code == 'STUDENT':
        return redirect(url_for('student.dashboard'))
    elif role_code == 'INSTRUCTOR':
        return redirect(url_for('instructor.dashboard'))
    elif role_code == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    elif role_code == 'MANAGER':
        return redirect(url_for('manager.dashboard'))
    else:
        return redirect(url_for('auth.login'))
