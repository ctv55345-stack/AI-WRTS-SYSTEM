from flask_wtf import FlaskForm
from wtforms import SelectField, DateTimeField, TextAreaField, BooleanField, RadioField
from wtforms.validators import DataRequired, Optional


class AssignmentCreateForm(FlaskForm):
    routine_id = SelectField('Bài võ', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn bài võ'),
    ])
    assignment_type = RadioField('Loại gán', choices=[
        ('individual', 'Cá nhân'),
        ('class', 'Cả lớp'),
    ], default='individual', validators=[DataRequired()])
    assigned_to_student = SelectField('Học viên (nếu cá nhân)', coerce=int, validators=[Optional()])
    assigned_to_class = SelectField('Lớp học (nếu gán lớp)', coerce=int, validators=[Optional()])
    deadline = DateTimeField('Deadline', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    instructions = TextAreaField('Hướng dẫn', validators=[Optional()])
    priority = SelectField('Độ ưu tiên', choices=[
        ('low', 'Thấp'),
        ('normal', 'Bình thường'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ], default='normal')
    is_mandatory = BooleanField('Bắt buộc', default=True)

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
        if self.assignment_type.data == 'individual' and not self.assigned_to_student.data:
            self.assigned_to_student.errors.append('Vui lòng chọn học viên')
            return False
        if self.assignment_type.data == 'class' and not self.assigned_to_class.data:
            self.assigned_to_class.errors.append('Vui lòng chọn lớp học')
            return False
        return True


