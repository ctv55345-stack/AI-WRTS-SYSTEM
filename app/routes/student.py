from flask import Blueprint, render_template
from app.utils.decorators import login_required, role_required

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
@role_required('STUDENT')
def dashboard():
    return render_template('student/dashboard.html')
