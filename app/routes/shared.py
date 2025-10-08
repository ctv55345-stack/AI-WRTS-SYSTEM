from flask import Blueprint, render_template, redirect, url_for, flash, session
from app.utils.decorators import login_required
from app.forms.feedback_forms import FeedbackSubmitForm
from app.services.feedback_service import FeedbackService

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/')
def home():
    """Trang chủ (landing page)"""
    return render_template('home.html')

@shared_bp.route('/feedback/submit', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    """Submit feedback (all roles)"""
    form = FeedbackSubmitForm()
    
    if form.validate_on_submit():
        data = {
            'feedback_type': form.feedback_type.data,
            'subject': form.subject.data,
            'content': form.content.data
        }
        
        result = FeedbackService.create_feedback(session['user_id'], data)
        
        if result['success']:
            flash('Gửi phản hồi thành công! Cảm ơn bạn đã đóng góp.', 'success')
            return redirect(url_for('shared.my_feedback'))
        else:
            flash('Có lỗi xảy ra', 'error')
    
    return render_template('shared/feedback_submit.html', form=form)

@shared_bp.route('/feedback/my')
@login_required
def my_feedback():
    """Xem feedback của mình"""
    feedbacks = FeedbackService.get_user_feedback(session['user_id'])
    return render_template('shared/my_feedback.html', feedbacks=feedbacks)