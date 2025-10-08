from flask_wtf import FlaskForm
from wtforms import DecimalField, TextAreaField, BooleanField, SubmitField, RadioField
from wtforms.validators import DataRequired, NumberRange, Optional

class ManualEvaluationForm(FlaskForm):
    evaluation_method = RadioField('Phương thức chấm điểm', 
        choices=[('manual', 'Chấm thủ công'), ('ai', 'Sử dụng kết quả AI')],
        default='manual',
        validators=[DataRequired()]
    )
    overall_score = DecimalField('Điểm tổng (*)', validators=[
        DataRequired(message='Vui lòng nhập điểm tổng'),
        NumberRange(min=0, max=100, message='Điểm phải từ 0-100')
    ])
    technique_score = DecimalField('Điểm kỹ thuật', validators=[
        Optional(), NumberRange(min=0, max=100, message='Điểm phải từ 0-100')
    ])
    posture_score = DecimalField('Điểm tư thế', validators=[
        Optional(), NumberRange(min=0, max=100, message='Điểm phải từ 0-100')
    ])
    spirit_score = DecimalField('Điểm tinh thần', validators=[
        Optional(), NumberRange(min=0, max=100, message='Điểm phải từ 0-100')
    ])
    strengths = TextAreaField('Điểm mạnh', validators=[Optional()])
    improvements_needed = TextAreaField('Điểm cần cải thiện', validators=[Optional()])
    comments = TextAreaField('Nhận xét chung', validators=[Optional()])
    is_passed = BooleanField('Đạt yêu cầu')
    submit = SubmitField('Lưu đánh giá')
