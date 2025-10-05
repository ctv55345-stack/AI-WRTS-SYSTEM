from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class ExamCreateForm(FlaskForm):
    exam_code = StringField('Mã bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập mã bài kiểm tra'),
        Length(max=30, message='Mã tối đa 30 ký tự'),
    ])
    exam_name = StringField('Tên bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập tên bài kiểm tra'),
        Length(max=100, message='Tên tối đa 100 ký tự'),
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    class_id = SelectField('Lớp học', coerce=int, validators=[Optional()])
    routine_id = SelectField('Bài võ', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn bài võ'),
    ])
    exam_type = SelectField('Loại kiểm tra', choices=[
        ('practice', 'Thi thử'),
        ('midterm', 'Giữa kỳ'),
        ('final', 'Cuối kỳ'),
        ('certification', 'Chứng chỉ'),
    ], validators=[DataRequired()])
    start_time = DateTimeField('Thời gian bắt đầu', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian bắt đầu'),
    ])
    end_time = DateTimeField('Thời gian kết thúc', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian kết thúc'),
    ])
    duration_minutes = IntegerField('Thời gian làm bài (phút)', validators=[
        DataRequired(message='Vui lòng nhập thời gian làm bài'),
        NumberRange(min=1, message='Thời gian tối thiểu 1 phút'),
    ])
    pass_score = DecimalField('Điểm đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Điểm từ 0-100%'),
    ], default=70.00)
    max_attempts = IntegerField('Số lần thi tối đa', validators=[
        Optional(),
        NumberRange(min=1, message='Tối thiểu 1 lần'),
    ], default=1)

    def validate_end_time(self, field):
        if field.data and self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')


