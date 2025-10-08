# Cải tiến Exams: Upload Video Giảng viên (Chỉ Sửa File Hiện Có)

## 1. Tổng quan Thay đổi

**Mục tiêu:** Cho phép giảng viên upload video mẫu khi tạo exam thay vì bắt buộc chọn từ routine.

**Files cần sửa:**
- ✅ `app/models/exam.py` - Thêm trường video
- ✅ `app/forms/exam_forms.py` - Thêm upload field
- ✅ `app/services/exam_service.py` - Logic upload
- ✅ `app/routes/instructor.py` - Xử lý upload
- ✅ `templates/instructor/exams.html` - UI cập nhật
- ✅ Migration script

**KHÔNG tạo file mới!**

---

## 2. DATABASE MIGRATION

### Migration Script
```python
# migrations/versions/xxxx_add_video_upload_to_exams.py
"""Add video upload support to exams

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Thêm các trường mới
    op.add_column('exams', 
        sa.Column('reference_video_path', sa.String(500), nullable=True))
    op.add_column('exams', 
        sa.Column('video_duration', sa.Integer(), nullable=True))
    op.add_column('exams', 
        sa.Column('video_upload_method', 
            sa.Enum('routine', 'upload', name='video_method_enum'),
            server_default='routine', nullable=False))
    
    # Cho phép routine_id NULL
    op.alter_column('exams', 'routine_id',
        existing_type=sa.Integer(),
        nullable=True)
    
    # Thêm constraint
    op.create_check_constraint(
        'chk_exams_video_source',
        'exams',
        """
        (video_upload_method = 'routine' AND routine_id IS NOT NULL) OR
        (video_upload_method = 'upload' AND reference_video_path IS NOT NULL)
        """
    )

def downgrade():
    op.drop_constraint('chk_exams_video_source', 'exams', type_='check')
    op.alter_column('exams', 'routine_id',
        existing_type=sa.Integer(),
        nullable=False)
    op.drop_column('exams', 'video_upload_method')
    op.drop_column('exams', 'video_duration')
    op.drop_column('exams', 'reference_video_path')
```

---

## 3. MODEL UPDATE

### File: `app/models/exam.py`

**Thay đổi:**
```python
from . import db
from datetime import datetime

class Exam(db.Model):
    __tablename__ = 'exams'
    
    exam_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    exam_code = db.Column(db.String(30), unique=True, nullable=False)
    exam_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.class_id', ondelete='SET NULL'))
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='RESTRICT'), nullable=False)
    
    # THAY ĐỔI: routine_id giờ có thể NULL
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='RESTRICT'), nullable=True)
    
    # THÊM MỚI: Video upload fields
    video_upload_method = db.Column(
        db.Enum('routine', 'upload', name='video_method_enum'), 
        nullable=False, 
        default='routine'
    )
    reference_video_path = db.Column(db.String(500))  # Path video upload
    video_duration = db.Column(db.Integer)  # Độ dài video (seconds)
    
    exam_type = db.Column(db.Enum('midterm', 'final', 'practice', 'certification', name='exam_type_enum'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    pass_score = db.Column(db.Numeric(5, 2), nullable=False, default=70.00)
    max_attempts = db.Column(db.Integer, nullable=False, default=1)
    is_published = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (giữ nguyên)
    exam_results = db.relationship('ExamResult', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    # THÊM MỚI: Helper methods
    def get_video_url(self):
        """Lấy URL video (từ routine hoặc upload)"""
        if self.video_upload_method == 'routine' and self.routine:
            return self.routine.reference_video_url
        elif self.video_upload_method == 'upload' and self.reference_video_path:
            return f'/static/uploads/exam_videos/{self.reference_video_path}'
        return None
    
    def has_video(self):
        """Kiểm tra có video hay không"""
        return (self.video_upload_method == 'routine' and self.routine_id) or \
               (self.video_upload_method == 'upload' and self.reference_video_path)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(end_time > start_time, name='chk_exams_time'),
        db.CheckConstraint(duration_minutes > 0, name='chk_exams_duration'),
        db.CheckConstraint(db.and_(pass_score >= 0, pass_score <= 100), name='chk_exams_pass_score'),
        db.CheckConstraint(max_attempts > 0, name='chk_exams_max_attempts'),
        # THÊM MỚI: Constraint đảm bảo có video
        db.CheckConstraint(
            db.or_(
                db.and_(video_upload_method == 'routine', routine_id.isnot(None)),
                db.and_(video_upload_method == 'upload', reference_video_path.isnot(None))
            ),
            name='chk_exams_video_source'
        ),
        db.Index('idx_exams_class', 'class_id'),
        db.Index('idx_exams_instructor', 'instructor_id'),
        db.Index('idx_exams_time', 'start_time', 'end_time'),
    )
```

---

## 4. FORM UPDATE

### File: `app/forms/exam_forms.py`

**Thay đổi:**
```python
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed  # THÊM import
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, DecimalField, RadioField  # THÊM RadioField
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
    
    # THÊM MỚI: Chọn nguồn video
    video_source = RadioField(
        'Nguồn video',
        choices=[
            ('routine', 'Chọn từ Routine có sẵn'),
            ('upload', 'Upload video mới')
        ],
        default='routine',
        validators=[DataRequired()]
    )
    
    # SỬA: routine_id giờ optional
    routine_id = SelectField('Bài võ', coerce=int, validators=[Optional()])
    
    # THÊM MỚI: Upload video
    reference_video = FileField(
        'Video mẫu',
        validators=[
            Optional(),
            FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Chỉ chấp nhận file video MP4, AVI, MOV, MKV!')
        ]
    )
    
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

    # THÊM MỚI: Custom validation
    def validate(self):
        if not super().validate():
            return False
        
        # Nếu chọn routine thì phải có routine_id
        if self.video_source.data == 'routine':
            if not self.routine_id.data or self.routine_id.data == 0:
                self.routine_id.errors.append('Vui lòng chọn bài võ')
                return False
        
        # Nếu chọn upload thì phải có file
        if self.video_source.data == 'upload':
            if not self.reference_video.data:
                self.reference_video.errors.append('Vui lòng upload video mẫu')
                return False
        
        return True

    def validate_end_time(self, field):
        if field.data and self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')
```

---

## 5. SERVICE UPDATE

### File: `app/services/exam_service.py`

**Thay đổi toàn bộ:**
```python
from app.models import db
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.class_enrollment import ClassEnrollment
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cv2
from flask import current_app


class ExamService:
    # THÊM MỚI: Constants
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    @staticmethod
    def _validate_video_file(file):
        """Validate uploaded video file"""
        if not file:
            return False, "Không có file"
        
        filename = secure_filename(file.filename)
        if not ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in ExamService.ALLOWED_EXTENSIONS):
            return False, "Định dạng không hợp lệ (chỉ chấp nhận MP4, AVI, MOV, MKV)"
        
        # Kiểm tra size (nếu có)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > ExamService.MAX_FILE_SIZE:
            return False, "File quá lớn (tối đa 500MB)"
        
        return True, filename
    
    @staticmethod
    def _get_video_duration(file_path):
        """Lấy độ dài video bằng OpenCV"""
        try:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = int(frame_count / fps) if fps > 0 else 0
            cap.release()
            return duration
        except Exception as e:
            print(f"Error getting video duration: {e}")
            return 0
    
    @staticmethod
    def _save_video_file(file, exam_id):
        """Lưu video file và trả về path + duration"""
        is_valid, result = ExamService._validate_video_file(file)
        if not is_valid:
            return None, result
        
        filename = result
        
        # Tạo thư mục nếu chưa có
        upload_folder = os.path.join(
            current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
            'exam_videos'
        )
        os.makedirs(upload_folder, exist_ok=True)
        
        # Tạo tên file mới: exam_{id}_{timestamp}.ext
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"exam_{exam_id}_{int(datetime.utcnow().timestamp())}.{ext}"
        file_path = os.path.join(upload_folder, new_filename)
        
        # Lưu file
        file.save(file_path)
        
        # Lấy duration
        duration = ExamService._get_video_duration(file_path)
        
        return new_filename, duration

    @staticmethod
    def create_exam(data: dict, instructor_id: int, video_file=None):
        """
        Tạo exam mới - HỖ TRỢ CẢ ROUTINE VÀ UPLOAD
        
        Args:
            data: Dict chứa thông tin exam
            instructor_id: ID giảng viên
            video_file: FileStorage object (optional, nếu upload)
        """
        # Kiểm tra mã trùng
        if Exam.query.filter_by(exam_code=data['exam_code']).first():
            return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}
        
        # Tạo exam object
        exam = Exam(
            exam_code=data['exam_code'],
            exam_name=data['exam_name'],
            description=data.get('description'),
            class_id=data.get('class_id'),
            instructor_id=instructor_id,
            exam_type=data['exam_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=data['duration_minutes'],
            pass_score=data.get('pass_score', 70.00),
            max_attempts=data.get('max_attempts', 1),
            is_published=False,
            video_upload_method=data.get('video_source', 'routine')
        )
        
        # Xử lý video dựa trên method
        if data.get('video_source') == 'routine':
            # Dùng routine
            exam.routine_id = data.get('routine_id')
            if not exam.routine_id:
                return {'success': False, 'message': 'Vui lòng chọn bài võ'}
        
        elif data.get('video_source') == 'upload':
            # Upload video mới
            if not video_file:
                return {'success': False, 'message': 'Vui lòng upload video'}
            
            # Flush để lấy exam_id
            db.session.add(exam)
            db.session.flush()
            
            # Lưu video file
            filename, duration = ExamService._save_video_file(video_file, exam.exam_id)
            if filename is None:
                db.session.rollback()
                return {'success': False, 'message': duration}  # duration chứa error message
            
            exam.reference_video_path = filename
            exam.video_duration = duration
        
        else:
            return {'success': False, 'message': 'Phương thức video không hợp lệ'}
        
        try:
            db.session.add(exam)
            db.session.commit()
            return {'success': True, 'exam': exam}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Lỗi: {str(e)}'}

    @staticmethod
    def get_exams_by_instructor(instructor_id: int):
        return Exam.query.filter_by(instructor_id=instructor_id).order_by(Exam.created_at.desc()).all()

    @staticmethod
    def get_exam_by_id(exam_id: int):
        return Exam.query.get(exam_id)

    @staticmethod
    def publish_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}
        exam.is_published = True
        db.session.commit()
        return {'success': True, 'exam': exam}

    @staticmethod
    def delete_exam(exam_id: int, instructor_id: int):
        exam = Exam.query.get(exam_id)
        if not exam:
            return {'success': False, 'message': 'Không tìm thấy bài kiểm tra'}
        if exam.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa'}
        
        result_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        if result_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {result_count} kết quả thi'}
        
        # Xóa video file nếu có
        if exam.video_upload_method == 'upload' and exam.reference_video_path:
            try:
                file_path = os.path.join(
                    current_app.config.get('UPLOAD_FOLDER', 'static/uploads'),
                    'exam_videos',
                    exam.reference_video_path
                )
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting video file: {e}")
        
        db.session.delete(exam)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_exam_results(exam_id: int):
        return ExamResult.query.filter_by(exam_id=exam_id).order_by(ExamResult.submitted_at.desc()).all()

    @staticmethod
    def get_exams_for_student(student_id: int):
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        if not class_ids:
            return []
        
        return Exam.query.filter(
            Exam.class_id.in_(class_ids),
            Exam.is_published == True
        ).order_by(Exam.start_time.desc()).all()

    @staticmethod
    def get_student_exam_result(exam_id: int, student_id: int):
        return ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).order_by(ExamResult.attempt_number.desc()).all()
```

---

## 6. ROUTE UPDATE

### File: `app/routes/instructor.py`

**Tìm và sửa route `create_exam`:**
```python
# ... existing imports ...
from werkzeug.utils import secure_filename  # THÊM import

# ... existing code ...

@instructor_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_exam():
    form = ExamCreateForm()
    
    # Load choices
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    classes = ClassService.get_classes_by_instructor(session['user_id'])
    form.class_id.choices = [(0, '-- Không chọn (tất cả) --')] + [(c.class_id, c.class_name) for c in classes]
    
    if form.validate_on_submit():
        # Chuẩn bị data
        data = {
            'exam_code': form.exam_code.data,
            'exam_name': form.exam_name.data,
            'description': form.description.data,
            'class_id': form.class_id.data if form.class_id.data else None,
            'routine_id': form.routine_id.data if form.routine_id.data else None,
            'exam_type': form.exam_type.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'duration_minutes': form.duration_minutes.data,
            'pass_score': form.pass_score.data,
            'max_attempts': form.max_attempts.data,
            'video_source': form.video_source.data,  # THÊM
        }
        
        # Lấy video file nếu có
        video_file = form.reference_video.data if form.video_source.data == 'upload' else None  # THÊM
        
        # Tạo exam với video file
        result = ExamService.create_exam(data, session['user_id'], video_file)  # SỬA: thêm video_file
        
        if result['success']:
            flash('Tạo bài kiểm tra thành công! (Trạng thái: Nháp)', 'success')
            return redirect(url_for('instructor.exam_detail', exam_id=result['exam'].exam_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/exam_create.html', form=form)

# ... giữ nguyên các route khác ...
```

---

## 7. TEMPLATE UPDATE

### File: `templates/instructor/exam_create.html` (TẠO MỚI)

```html
{% extends "base/instructor_base.html" %}

{% block title %}Tạo bài kiểm tra{% endblock %}

{% block instructor_content %}
<div class="page-header mb-4">
    <h1 class="page-title">
        <i class="fas fa-plus-circle me-2"></i>
        Tạo bài kiểm tra mới
    </h1>
</div>

<div class="card border-0 shadow-sm">
    <div class="card-body">
        <form method="POST" enctype="multipart/form-data">
            {{ form.hidden_tag() }}
            
            <!-- Thông tin cơ bản -->
            <div class="row mb-3">
                <div class="col-md-4">
                    {{ form.exam_code.label(class="form-label required") }}
                    {{ form.exam_code(class="form-control") }}
                    {% if form.exam_code.errors %}
                        <div class="text-danger small">{{ form.exam_code.errors[0] }}</div>
                    {% endif %}
                </div>
                <div class="col-md-8">
                    {{ form.exam_name.label(class="form-label required") }}
                    {{ form.exam_name(class="form-control") }}
                    {% if form.exam_name.errors %}
                        <div class="text-danger small">{{ form.exam_name.errors[0] }}</div>
                    {% endif %}
                </div>
            </div>
            
            <div class="mb-3">
                {{ form.description.label(class="form-label") }}
                {{ form.description(class="form-control", rows=3) }}
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    {{ form.exam_type.label(class="form-label required") }}
                    {{ form.exam_type(class="form-select") }}
                </div>
                <div class="col-md-6">
                    {{ form.class_id.label(class="form-label") }}
                    {{ form.class_id(class="form-select") }}
                </div>
            </div>
            
            <!-- VIDEO SOURCE SELECTION -->
            <div class="card bg-light mb-3">
                <div class="card-header">
                    <h5 class="mb-0">
                        <i class="fas fa-video me-2"></i>
                        Chọn Video Tham Chiếu
                    </h5>
                </div>
                <div class="card-body">
                    <!-- Radio buttons -->
                    <div class="btn-group mb-3" role="group">
                        {{ form.video_source(class="d-none") }}
                        <input type="radio" class="btn-check" name="video_source" id="source_routine" 
                               value="routine" {% if form.video_source.data == 'routine' %}checked{% endif %}>
                        <label class="btn btn-outline-primary" for="source_routine">
                            <i class="fas fa-list me-1"></i> Chọn từ Routine
                        </label>
                        
                        <input type="radio" class="btn-check" name="video_source" id="source_upload" 
                               value="upload" {% if form.video_source.data == 'upload' %}checked{% endif %}>
                        <label class="btn btn-outline-success" for="source_upload">
                            <i class="fas fa-cloud-upload-alt me-1"></i> Upload Video Mới
                        </label>
                    </div>
                    
                    <!-- Routine selection -->
                    <div id="routine-section" {% if form.video_source.data == 'upload' %}style="display:none"{% endif %}>
                        {{ form.routine_id.label(class="form-label") }}
                        {{ form.routine_id(class="form-select") }}
                        {% if form.routine_id.errors %}
                            <div class="text-danger small">{{ form.routine_id.errors[0] }}</div>
                        {% endif %}
                        <small class="text-muted">Chọn bài võ có sẵn với video mẫu</small>
                    </div>
                    
                    <!-- Video upload -->
                    <div id="upload-section" {% if form.video_source.data != 'upload' %}style="display:none"{% endif %}>
                        {{ form.reference_video.label(class="form-label") }}
                        {{ form.reference_video(class="form-control", id="videoFileInput") }}
                        {% if form.reference_video.errors %}
                            <div class="text-danger small">{{ form.reference_video.errors[0] }}</div>
                        {% endif %}
                        <small class="text-muted d-block mt-1">
                            <i class="fas fa-info-circle"></i>
                            Định dạng: MP4, AVI, MOV, MKV | Tối đa: 500MB
                        </small>
                        
                        <!-- Video preview -->
                        <div id="video-preview" class="mt-3" style="display:none">
                            <div class="alert alert-info">
                                <i class="fas fa-eye me-2"></i>
                                <strong>Xem trước:</strong>
                            </div>
                            <video id="preview-video" controls class="w-100" style="max-height:400px; border-radius:8px;">
                                <source id="preview-source" src="" type="video/mp4">
                            </video>
                            <div class="mt-2">
                                <span class="badge bg-primary" id="file-size"></span>
                                <span class="badge bg-info" id="video-duration"></span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Thời gian -->
            <div class="row mb-3">
                <div class="col-md-4">
                    {{ form.start_time.label(class="form-label required") }}
                    {{ form.start_time(class="form-control") }}
                    {% if form.start_time.errors %}
                        <div class="text-danger small">{{ form.start_time.errors[0] }}</div>
                    {% endif %}
                </div>
                <div class="col-md-4">
                    {{ form.end_time.label(class="form-label required") }}
                    {{ form.end_time(class="form-control") }}
                    {% if form.end_time.errors %}
                        <div class="text-danger small">{{ form.end_time.errors[0] }}</div>
                    {% endif %}
                </div>
                <div class="col-md-4">
                    {{ form.duration_minutes.label(class="form-label required") }}
                    {{ form.duration_minutes(class="form-control") }}
                    {% if form.duration_minutes.errors %}
                        <div class="text-danger small">{{ form.duration_minutes.errors[0] }}</div>
                    {% endif %}
                </div>
            </div>
            
            <!-- Cài đặt -->
            <div class="row mb-4">
                <div class="col-md-6">
                    {{ form.pass_score.label(class="form-label") }}
                    {{ form.pass_score(class="form-control") }}
                </div>
                <div class="col-md-6">
                    {{ form.max_attempts.label(class="form-label") }}
                    {{ form.max_attempts(class="form-control") }}
                </div>
            </div>
            
            <!-- Buttons -->
            <div class="d-flex gap-2">
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save me-2"></i>Tạo bài kiểm tra
                </button>
                <a href="{{ url_for('instructor.exams') }}" class="btn btn-secondary">
                    <i class="fas fa-times me-2"></i>Hủy
                </a>
            </div>
        </form>
    </div>
</div>

<script>
// Toggle giữa routine và upload
document.querySelectorAll('input[name="video_source"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const routineSection = document.getElementById('routine-section');
        const uploadSection = document.getElementById('upload-section');
        
        if (this.value === 'routine') {
            routineSection.style.display = 'block';
            uploadSection.style.display = 'none';
            document.getElementById('video-preview').style.display = 'none';
        } else {
            routineSection.style.display = 'none';
            uploadSection.style.display = 'block';
        }
    });
});

// Video preview
document.getElementById('videoFileInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // Show preview
        const url = URL.createObjectURL(file);
        document.getElementById('preview-source').src = url;
        document.getElementById('preview-video').load();
        document.getElementById('video-preview').style.display = 'block';
        
        // Show file info
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        document.getElementById('file-size').textContent = `Kích thước: ${sizeMB} MB`;
        
        // Get duration
        const video = document.getElementById('preview-video');
        video.addEventListener('loadedmetadata', function() {
            const duration = Math.floor(video.duration);
            const minutes = Math.floor(duration / 60);
            const seconds = duration % 60;
            document.getElementById('video-duration').textContent = 
                `Độ dài: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        });
    }
});
</script>
{% endblock %}
```

---

## 8. CẬP NHẬT TEMPLATE DANH SÁCH

### File: `templates/instructor/exams.html`

**Tìm và sửa phần hiển thị routine:**
```html
<!-- TÌM dòng này: -->
<td>{{ exam.routine.routine_name if exam.routine else '--' }}</td>

<!-- ĐỔI THÀNH: -->
<td>
    {% if exam.video_upload_method == 'routine' and exam.routine %}
        <i class="fas fa-list text-primary me-1"></i>
        {{ exam.routine.routine_name }}
    {% elif exam.video_upload_method == 'upload' %}
        <i class="fas fa-cloud-upload-alt text-success me-1"></i>
        Video upload
    {% else %}
        --
    {% endif %}
</td>
```

---

## 9. TESTING CHECKLIST

- [ ] Migration chạy thành công
- [ ] Tạo exam với routine (backward compatible)
- [ ] Tạo exam với video upload
- [ ] Validate file format (chỉ mp4, avi, mov, mkv)
- [ ] Validate file size (max 500MB)
- [ ] Preview video trước khi upload
- [ ] Lưu video vào đúng thư mục
- [ ] Hiển thị đúng video trong exam detail
- [ ] Xóa exam cũng xóa file video
- [ ] Học viên xem được video mẫu
- [ ] Chấm điểm với video upload
- [ ] UI responsive trên mobile

---

## 10. LƯU Ý QUAN TRỌNG

**Config cần thiết trong `config.py`:**
```python
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
```

**Tạo thư mục:**
```bash
mkdir -p static/uploads/exam_videos
chmod 755 static/uploads/exam_videos
```

**Dependencies cần có:**
```
opencv-python>=4.5.0
Flask-WTF>=1.0.0
```

**Chạy migration:**
```bash
flask db migrate -m "Add video upload to exams"
flask db upgrade
```