# Complete Code - CHỈ Chấm theo Video Assignment

## THAY ĐỔI CHÍNH:
- ❌ Bỏ fallback về video routine
- ✅ BẮT BUỘC giảng viên upload video khi tạo assignment
- ✅ Chỉ hiển thị video assignment khi chấm điểm

---

## BƯỚC 1: Database Migration (GIỮ NGUYÊN)

```sql
ALTER TABLE assignments 
ADD COLUMN instructor_video_url VARCHAR(500) 
COMMENT 'Video demo của giảng viên - BẮT BUỘC';
```

---

## BƯỚC 2: Assignment Model (GIỮ NGUYÊN)

### File: `app/models/assignment.py`

```python
from . import db
from datetime import datetime

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    assignment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='CASCADE'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    assignment_type = db.Column(db.Enum('individual', 'class', name='assignment_type_enum'), nullable=False, default='individual')
    assigned_to_student = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'))
    assigned_to_class = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='CASCADE'))
    deadline = db.Column(db.DateTime)
    instructions = db.Column(db.Text)
    priority = db.Column(db.Enum('low', 'normal', 'high', 'urgent', name='priority_enum'), nullable=False, default='normal')
    is_mandatory = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Video demo của giảng viên - BẮT BUỘC
    instructor_video_url = db.Column(db.String(500), nullable=False, comment='Video demo của giảng viên')
    
    # Relationships
    videos = db.relationship('TrainingVideo', backref='assignment', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            db.or_(
                db.and_(assignment_type == 'individual', assigned_to_student.isnot(None), assigned_to_class.is_(None)),
                db.and_(assignment_type == 'class', assigned_to_class.isnot(None), assigned_to_student.is_(None))
            ),
            name='chk_assignments_target'
        ),
        db.Index('idx_assignments_routine', 'routine_id'),
        db.Index('idx_assignments_student', 'assigned_to_student'),
        db.Index('idx_assignments_class', 'assigned_to_class'),
        db.Index('idx_assignments_deadline', 'deadline'),
    )
```

---

## BƯỚC 3: Assignment Form - BẮT BUỘC UPLOAD VIDEO

### File: `app/forms/assignment_forms.py`

```python
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, DateTimeField, TextAreaField, BooleanField, SubmitField, StringField
from wtforms.validators import DataRequired, Optional

class AssignmentCreateForm(FlaskForm):
    routine_id = SelectField('Bài võ (*)', coerce=int, validators=[DataRequired()])
    
    assignment_type = SelectField('Loại bài tập (*)', 
        choices=[('individual', 'Cá nhân'), ('class', 'Lớp học')],
        validators=[DataRequired()]
    )
    
    assigned_to_student = SelectField('Học viên', coerce=int, validators=[Optional()])
    assigned_to_class = SelectField('Lớp học', coerce=int, validators=[Optional()])
    
    deadline = DateTimeField('Hạn nộp', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    
    instructions = TextAreaField('Hướng dẫn')
    
    priority = SelectField('Độ ưu tiên (*)',
        choices=[
            ('low', 'Thấp'),
            ('normal', 'Bình thường'),
            ('high', 'Cao'),
            ('urgent', 'Khẩn cấp')
        ],
        default='normal',
        validators=[DataRequired()]
    )
    
    is_mandatory = BooleanField('Bắt buộc', default=True)
    
    # BẮT BUỘC: Phải upload video hoặc nhập URL
    instructor_video_url = StringField('Link Video Demo')
    
    instructor_video_file = FileField('Upload Video Demo (*)', 
        validators=[
            FileAllowed(['mp4', 'mov', 'avi', 'mkv'], 'Chỉ chấp nhận video!')
        ]
    )
    
    submit = SubmitField('Gán bài tập')
    
    def validate(self, extra_validators=None):
        """Custom validation: Phải có video URL hoặc file"""
        if not super().validate(extra_validators):
            return False
        
        # Kiểm tra phải có ít nhất 1 trong 2: URL hoặc file
        if not self.instructor_video_url.data and not self.instructor_video_file.data:
            self.instructor_video_file.errors.append('Vui lòng upload video demo hoặc nhập link video')
            return False
        
        return True
```

---

## BƯỚC 4: Assignment Service

### File: `app/services/assignment_service.py`

```python
from app.models import db
from app.models.assignment import Assignment
from app.models.notification import Notification
from datetime import datetime

class AssignmentService:
    
    @staticmethod
    def create_assignment(data: dict, assigned_by: int):
        """Tạo assignment mới - BẮT BUỘC có video"""
        try:
            # VALIDATE: Bắt buộc phải có video
            if not data.get('instructor_video_url'):
                return {'success': False, 'message': 'Vui lòng upload video demo cho bài tập này'}
            
            assignment = Assignment(
                routine_id=data['routine_id'],
                assigned_by=assigned_by,
                assignment_type=data['assignment_type'],
                assigned_to_student=data.get('assigned_to_student'),
                assigned_to_class=data.get('assigned_to_class'),
                deadline=data.get('deadline'),
                instructions=data.get('instructions'),
                priority=data.get('priority', 'normal'),
                is_mandatory=data.get('is_mandatory', True),
                instructor_video_url=data['instructor_video_url']  # BẮT BUỘC
            )
            
            db.session.add(assignment)
            db.session.flush()
            
            # Gửi thông báo
            if data['assignment_type'] == 'individual':
                notification = Notification(
                    recipient_id=data['assigned_to_student'],
                    sender_id=assigned_by,
                    notification_type='assignment',
                    title='Bài tập mới',
                    content=f'Bạn có bài tập mới với video hướng dẫn',
                    related_entity_id=assignment.assignment_id,
                    related_entity_type='assignment'
                )
                db.session.add(notification)
            
            elif data['assignment_type'] == 'class':
                from app.models.class_enrollment import ClassEnrollment
                enrollments = ClassEnrollment.query.filter_by(
                    class_id=data['assigned_to_class'],
                    enrollment_status='active'
                ).all()
                
                for enrollment in enrollments:
                    notification = Notification(
                        recipient_id=enrollment.student_id,
                        sender_id=assigned_by,
                        notification_type='assignment',
                        title='Bài tập mới cho lớp',
                        content=f'Lớp có bài tập mới với video hướng dẫn',
                        related_entity_id=assignment.assignment_id,
                        related_entity_type='assignment'
                    )
                    db.session.add(notification)
            
            db.session.commit()
            return {'success': True, 'assignment': assignment}
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def get_assignment_by_id(assignment_id: int):
        return Assignment.query.get(assignment_id)
    
    @staticmethod
    def get_assignments_by_instructor(instructor_id: int):
        return Assignment.query.filter_by(
            assigned_by=instructor_id
        ).order_by(Assignment.created_at.desc()).all()
```

---

## BƯỚC 5: Routes - BẮT BUỘC VIDEO

### File: `app/routes/instructor.py` - Function `create_assignment`

```python
@instructor_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_assignment():
    form = AssignmentCreateForm()
    
    # Load routines
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    # Load students
    from app.models.class_enrollment import ClassEnrollment
    instructor_classes = ClassService.get_classes_by_instructor(session['user_id'])
    student_ids = set()
    for cls in instructor_classes:
        enrollments = ClassEnrollment.query.filter_by(class_id=cls.class_id, enrollment_status='active').all()
        student_ids.update([e.student_id for e in enrollments])
    
    from app.models.user import User
    students = User.query.filter(User.user_id.in_(student_ids)).all() if student_ids else []
    form.assigned_to_student.choices = [(0, '-- Chọn học viên --')] + [(s.user_id, s.full_name) for s in students]
    
    # Load classes
    form.assigned_to_class.choices = [(0, '-- Chọn lớp --')] + [(c.class_id, c.class_name) for c in instructor_classes]
    
    if form.validate_on_submit():
        # XỬ LÝ VIDEO - BẮT BUỘC
        instructor_video_url = None
        
        # Ưu tiên 1: Upload file
        if form.instructor_video_file.data:
            from werkzeug.utils import secure_filename
            import os
            from datetime import datetime
            from flask import current_app
            
            video_file = form.instructor_video_file.data
            filename = secure_filename(video_file.filename)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"assignment_{session['user_id']}_{timestamp}_{filename}"
            
            upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'static/uploads'), 'assignments')
            os.makedirs(upload_path, exist_ok=True)
            
            filepath = os.path.join(upload_path, filename)
            video_file.save(filepath)
            
            instructor_video_url = f"/static/uploads/assignments/{filename}"
            
        # Ưu tiên 2: Dùng URL
        elif form.instructor_video_url.data:
            instructor_video_url = form.instructor_video_url.data
        
        # KIỂM TRA BẮT BUỘC
        if not instructor_video_url:
            flash('Vui lòng upload video demo hoặc nhập link video!', 'error')
            return render_template('instructor/assignment_create.html', form=form)
        
        # Tạo assignment
        data = {
            'routine_id': form.routine_id.data,
            'assignment_type': form.assignment_type.data,
            'assigned_to_student': form.assigned_to_student.data if form.assignment_type.data == 'individual' else None,
            'assigned_to_class': form.assigned_to_class.data if form.assignment_type.data == 'class' else None,
            'deadline': form.deadline.data,
            'instructions': form.instructions.data,
            'priority': form.priority.data,
            'is_mandatory': form.is_mandatory.data,
            'instructor_video_url': instructor_video_url  # BẮT BUỘC
        }
        
        result = AssignmentService.create_assignment(data, session['user_id'])
        if result['success']:
            flash('Gán bài tập thành công!', 'success')
            return redirect(url_for('instructor.assignments'))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/assignment_create.html', form=form)
```

### File: `app/routes/instructor.py` - Function `evaluate_video`

```python
@instructor_bp.route('/videos/<int:video_id>/evaluate', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def evaluate_video(video_id):
    """Chấm điểm video - CHỈ theo video assignment"""
    from app.services.video_service import VideoService
    
    video_data = VideoService.get_video_with_analysis(video_id)
    if not video_data:
        flash('Không tìm thấy video', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    video = video_data['video']
    ai_analysis = video_data['ai_analysis']
    
    # Kiểm tra quyền
    from app.models.class_enrollment import ClassEnrollment
    
    enrollment = ClassEnrollment.query.filter_by(
        student_id=video.student_id,
        enrollment_status='active'
    ).first()
    
    if not enrollment or enrollment.class_obj.instructor_id != session['user_id']:
        flash('Bạn không có quyền chấm điểm video này', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    # CHỈ LẤY VIDEO TỪ ASSIGNMENT - BẮT BUỘC
    if not video.assignment_id or not video.assignment:
        flash('Video này không thuộc assignment nào!', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    if not video.assignment.instructor_video_url:
        flash('Assignment này chưa có video demo!', 'error')
        return redirect(url_for('instructor.pending_evaluations'))
    
    reference_video_url = video.assignment.instructor_video_url
    video_source = f"Video demo Assignment #{video.assignment.assignment_id}"
    
    form = ManualEvaluationForm()
    
    if form.validate_on_submit():
        data = {
            'overall_score': form.overall_score.data,
            'technique_score': form.technique_score.data,
            'posture_score': form.posture_score.data,
            'spirit_score': form.spirit_score.data,
            'strengths': form.strengths.data,
            'improvements_needed': form.improvements_needed.data,
            'comments': form.comments.data,
            'is_passed': form.is_passed.data
        }
        
        result = EvaluationService.create_evaluation(video_id, session['user_id'], data)
        
        if result['success']:
            flash('Chấm điểm thành công!', 'success')
            return redirect(url_for('instructor.pending_evaluations'))
        else:
            flash(result['message'], 'error')
    
    return render_template(
        'instructor/evaluate_video.html', 
        form=form, 
        video=video, 
        ai_analysis=ai_analysis,
        reference_video_url=reference_video_url,
        video_source=video_source
    )
```

---

## BƯỚC 6: Templates

### File: `templates/instructor/assignment_create.html`

```html
{% extends "base.html" %}

{% block title %}Tạo bài tập mới{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0">
                        <i class="fas fa-tasks me-2"></i>Gán bài tập mới
                    </h4>
                </div>
                
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        {{ form.csrf_token }}
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.routine_id.label }}</label>
                            {{ form.routine_id(class="form-select") }}
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.assignment_type.label }}</label>
                            {{ form.assignment_type(class="form-select", id="assignmentType") }}
                        </div>
                        
                        <div class="mb-3" id="studentSelect">
                            <label class="form-label">{{ form.assigned_to_student.label }}</label>
                            {{ form.assigned_to_student(class="form-select") }}
                        </div>
                        
                        <div class="mb-3" id="classSelect" style="display:none;">
                            <label class="form-label">{{ form.assigned_to_class.label }}</label>
                            {{ form.assigned_to_class(class="form-select") }}
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.deadline.label }}</label>
                            {{ form.deadline(class="form-control", type="datetime-local") }}
                            <small class="text-muted">Để trống nếu không có deadline</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.priority.label }}</label>
                            {{ form.priority(class="form-select") }}
                        </div>
                        
                        <div class="mb-3 form-check">
                            {{ form.is_mandatory(class="form-check-input") }}
                            <label class="form-check-label">Bài tập bắt buộc</label>
                        </div>
                        
                        <!-- VIDEO DEMO - BẮT BUỘC -->
                        <div class="card mb-3 border-danger">
                            <div class="card-header bg-danger bg-opacity-10">
                                <h6 class="mb-0 text-danger">
                                    <i class="fas fa-video me-2"></i>
                                    Video Demo - BẮT BUỘC (*)
                                </h6>
                            </div>
                            <div class="card-body">
                                <div class="alert alert-warning mb-3">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    <strong>BẮT BUỘC:</strong> Bạn phải upload video demo để học viên so sánh khi làm bài tập.
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">{{ form.instructor_video_url.label }}</label>
                                    {{ form.instructor_video_url(class="form-control", placeholder="https://example.com/video.mp4") }}
                                </div>
                                
                                <div class="mb-0">
                                    <label class="form-label text-danger">
                                        <i class="fas fa-asterisk fa-xs me-1"></i>
                                        {{ form.instructor_video_file.label }}
                                    </label>
                                    {{ form.instructor_video_file(class="form-control") }}
                                    {% if form.instructor_video_file.errors %}
                                    <div class="text-danger mt-2">
                                        {{ form.instructor_video_file.errors[0] }}
                                    </div>
                                    {% endif %}
                                    <small class="text-muted">MP4, MOV, AVI, MKV - Tối đa 500MB</small>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">{{ form.instructions.label }}</label>
                            {{ form.instructions(class="form-control", rows="4", placeholder="Hướng dẫn thêm...") }}
                        </div>
                        
                        <div class="d-flex justify-content-between">
                            <a href="{{ url_for('instructor.assignments') }}" class="btn btn-secondary">
                                <i class="fas fa-arrow-left me-2"></i>Hủy
                            </a>
                            {{ form.submit(class="btn btn-primary") }}
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('assignmentType').addEventListener('change', function() {
    const studentSelect = document.getElementById('studentSelect');
    const classSelect = document.getElementById('classSelect');
    
    if (this.value === 'individual') {
        studentSelect.style.display = 'block';
        classSelect.style.display = 'none';
    } else {
        studentSelect.style.display = 'none';
        classSelect.style.display = 'block';
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const type = document.getElementById('assignmentType').value;
    if (type === 'class') {
        document.getElementById('studentSelect').style.display = 'none';
        document.getElementById('classSelect').style.display = 'block';
    }
});
</script>
{% endblock %}
```

### File: `templates/instructor/evaluate_video.html` (GIỮ NGUYÊN)

Template này không thay đổi, vì đã chỉ hiển thị video assignment rồi.

---

## BƯỚC 7: Tạo thư mục uploads

```bash
mkdir -p static/uploads/assignments
chmod 755 static/uploads/assignments
```

---

## BƯỚC 8: Cấu hình

### File: `app/__init__.py` hoặc `app/config.py`

```python
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

---

## TÓM TẮT LOGIC MỚI

### ❌ BỎ:
- Không còn dùng `routine.reference_video_url`
- Không còn fallback về video routine
- Video routine chỉ để tham khảo, không dùng để chấm

### ✅ MỚI:
- **BẮT BUỘC** upload video khi tạo assignment
- Chỉ chấm theo video assignment
- Nếu không có video assignment → Báo lỗi, không cho chấm
- Form validation: Phải có URL hoặc file

### Luồng hoạt động:
1. **Tạo assignment**: Giảng viên PHẢI upload video demo
2. **Học viên nộp bài**: Upload video làm bài
3. **Chấm điểm**: So sánh video học viên vs video assignment (duy nhất)

---

## MigrationNếu cần đổi cột thành NOT NULL:

```sql
-- Cập nhật NULL thành empty string trước
UPDATE assignments SET instructor_video_url = '' WHERE instructor_video_url IS NULL;

-- Đổi thành NOT NULL
ALTER TABLE assignments 
MODIFY COLUMN instructor_video_url VARCHAR(500) NOT NULL 
COMMENT 'Video demo của giảng viên - BẮT BUỘC';
```