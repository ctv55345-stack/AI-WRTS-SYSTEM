from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class GoalCreateForm(FlaskForm):
    goal_type = SelectField('Loại mục tiêu (*)', choices=[
        ('score_improvement', 'Cải thiện điểm số'),
        ('practice_frequency', 'Tần suất luyện tập'),
        ('routine_completion', 'Hoàn thành bài võ'),
        ('custom', 'Tùy chỉnh')
    ], validators=[DataRequired()])
    
    goal_title = StringField('Tiêu đề mục tiêu (*)', validators=[
        DataRequired(message='Vui lòng nhập tiêu đề'),
        Length(max=200, message='Tối đa 200 ký tự')
    ])
    
    goal_description = TextAreaField('Mô tả')
    
    target_value = DecimalField('Giá trị mục tiêu (*)', validators=[
        DataRequired(message='Vui lòng nhập giá trị'),
        NumberRange(min=0.01, message='Giá trị phải lớn hơn 0')
    ])
    
    unit_of_measurement = StringField('Đơn vị đo', validators=[
        Length(max=50, message='Tối đa 50 ký tự')
    ])
    
    start_date = DateField('Ngày bắt đầu (*)', validators=[DataRequired()], format='%Y-%m-%d')
    deadline = DateField('Hạn chót (*)', validators=[DataRequired()], format='%Y-%m-%d')
    
    submit = SubmitField('Tạo mục tiêu')
