# ===================================================================
# FILE: app/services/routine_service.py
# ===================================================================
from app.models import db
from app.models.martial_routine import MartialRoutine
from app.models.evaluation_criteria import EvaluationCriteria
from app.models.weapon import Weapon
from datetime import datetime


class RoutineService:
    @staticmethod
    def get_all_weapons():
        return Weapon.query.filter_by(is_active=True).order_by(Weapon.display_order).all()

    @staticmethod
    def get_routines_by_instructor(instructor_id: int, filters=None):
        query = MartialRoutine.query.filter_by(instructor_id=instructor_id)
        
        if filters:
            if filters.get('level'):
                query = query.filter_by(level=filters['level'])
            if filters.get('weapon_id'):
                query = query.filter_by(weapon_id=filters['weapon_id'])
            if filters.get('is_published') is not None:
                query = query.filter_by(is_published=filters['is_published'])
        
        return query.order_by(MartialRoutine.created_at.desc()).all()

    @staticmethod
    def get_routine_by_id(routine_id: int):
        return MartialRoutine.query.get(routine_id)

    @staticmethod
    def create_routine(data: dict, instructor_id: int):
        # Check duplicate code
        if MartialRoutine.query.filter_by(routine_code=data['routine_code']).first():
            return {'success': False, 'message': 'Mã bài võ đã tồn tại'}

        routine = MartialRoutine(
            routine_code=data['routine_code'],
            routine_name=data['routine_name'],
            description=data.get('description'),
            weapon_id=data['weapon_id'],
            level=data['level'],
            difficulty_score=data.get('difficulty_score', 1.0),
            reference_video_url=data.get('reference_video_url'),
            thumbnail_url=data.get('thumbnail_url'),
            duration_seconds=data['duration_seconds'],
            total_moves=data.get('total_moves', 1),
            instructor_id=instructor_id,
            pass_threshold=data.get('pass_threshold', 70.00),
            is_published=False,  # Draft by default
            is_active=True
        )

        db.session.add(routine)
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def update_routine(routine_id: int, data: dict, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        # Check ownership
        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền sửa bài võ này'}

        routine.routine_name = data['routine_name']
        routine.description = data.get('description')
        routine.weapon_id = data['weapon_id']
        routine.level = data['level']
        routine.difficulty_score = data.get('difficulty_score', routine.difficulty_score)
        routine.reference_video_url = data.get('reference_video_url', routine.reference_video_url)
        routine.thumbnail_url = data.get('thumbnail_url', routine.thumbnail_url)
        routine.duration_seconds = data['duration_seconds']
        routine.total_moves = data.get('total_moves', routine.total_moves)
        routine.pass_threshold = data.get('pass_threshold', routine.pass_threshold)

        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def publish_routine(routine_id: int, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}

        routine.is_published = True
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def unpublish_routine(routine_id: int, instructor_id: int):
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền'}

        routine.is_published = False
        db.session.commit()
        return {'success': True, 'routine': routine}

    @staticmethod
    def delete_routine(routine_id: int, instructor_id: int):
        from app.models.training_video import TrainingVideo
        
        routine = MartialRoutine.query.get(routine_id)
        if not routine:
            return {'success': False, 'message': 'Không tìm thấy bài võ'}

        if routine.instructor_id != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa bài võ này'}

        # Check if used
        video_count = TrainingVideo.query.filter_by(routine_id=routine_id).count()
        if video_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {video_count} video bài tập'}

        db.session.delete(routine)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_criteria_by_routine(routine_id: int):
        return EvaluationCriteria.query.filter_by(routine_id=routine_id).order_by(EvaluationCriteria.display_order).all()

    @staticmethod
    def add_criteria(routine_id: int, data: dict):
        # Check total weight
        existing_total = db.session.query(db.func.sum(EvaluationCriteria.weight_percentage)).filter_by(routine_id=routine_id).scalar() or 0
        
        if existing_total + data['weight_percentage'] > 100:
            return {'success': False, 'message': f'Tổng trọng số vượt quá 100% (hiện tại: {existing_total}%)'}

        criteria = EvaluationCriteria(
            routine_id=routine_id,
            criteria_name=data['criteria_name'],
            criteria_code=data['criteria_code'],
            weight_percentage=data['weight_percentage'],
            description=data.get('description'),
            evaluation_method=data.get('evaluation_method'),
            display_order=data.get('display_order', 0)
        )

        db.session.add(criteria)
        db.session.commit()
        return {'success': True, 'criteria': criteria}

    @staticmethod
    def delete_criteria(criteria_id: int):
        criteria = EvaluationCriteria.query.get(criteria_id)
        if not criteria:
            return {'success': False, 'message': 'Không tìm thấy tiêu chí'}

        db.session.delete(criteria)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_published_routines(filters=None):
        # ===================================================================
# FILE: templates/instructor/criteria_add.html
# ===================================================================
# ===================================================================
# FILE: templates/instructor/assignment_create.html  
# ===================================================================
# ===================================================================
# FILE: templates/instructor/exam_create.html & exam_detail.html
# ===================================================================
"""
[Similar structure to assignment templates - shortened for space]
[Include all form fields: exam_code, exam_name, routine_id, exam_type, times, duration, pass_score, max_attempts]
[exam_detail shows exam info + list of exam_results with student names and scores]
"""


# ===================================================================
# FILE: app/routes/student.py (THÊM VÀO)
# ===================================================================

from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService

# ============ ROUTINE VIEW (STUDENT) ============

@student_bp.route('/routines')
@login_required
@role_required('STUDENT')
def routines():
    """View published routines"""
    level_filter = request.args.get('level')
    weapon_filter = request.args.get('weapon_id', type=int)
    
    filters = {}
    if level_filter:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter
    
    routines = RoutineService.get_published_routines(filters)
    weapons = RoutineService.get_all_weapons()
    
    return render_template('student/routines.html', routines=routines, weapons=weapons)


@student_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('STUDENT')
def routine_detail(routine_id: int):
    """View routine details"""
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or not routine.is_published:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('student.routines'))
    
    criteria = RoutineService.get_criteria_by_routine(routine_id)
    
    return render_template('student/routine_detail.html', routine=routine, criteria=criteria)


# ============ ASSIGNMENT VIEW (STUDENT) ============

@student_bp.route('/my-assignments')
@login_required
@role_required('STUDENT')
def my_assignments():
    """View my assignments"""
    assignments = AssignmentService.get_assignments_for_student(session['user_id'])
    
    # Separate pending and completed
    from datetime import datetime
    pending = []
    completed = []
    
    for assignment in assignments:
        from app.models.training_video import TrainingVideo
        submitted = TrainingVideo.query.filter_by(
            student_id=session['user_id'],
            assignment_id=assignment.assignment_id
        ).first()
        
        if submitted:
            completed.append({'assignment': assignment, 'video': submitted})
        else:
            pending.append(assignment)
    
    return render_template('student/my_assignments.html', pending=pending, completed=completed)


# ============ EXAM VIEW (STUDENT) ============

@student_bp.route('/my-exams')
@login_required
@role_required('STUDENT')
def my_exams():
    """View my exams"""
    exams = ExamService.get_exams_for_student(session['user_id'])
    
    from datetime import datetime
    now = datetime.utcnow()
    
    upcoming = []
    past = []
    
    for exam in exams:
        results = ExamService.get_student_exam_result(exam.exam_id, session['user_id'])
        
        exam_info = {
            'exam': exam,
            'results': results,
            'attempts_used': len(results),
            'can_attempt': len(results) < exam.max_attempts and now < exam.end_time
        }
        
        if now < exam.start_time:
            upcoming.append(exam_info)
        else:
            past.append(exam_info)
    
    return render_template('student/my_exams.html', upcoming=upcoming, past=past)


# ===================================================================
# FILE: templates/student/routines.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Danh sách bài võ</title>
    <style>
        .filter-bar { padding: 15px; background: #f8f9fa; margin: 15px 0; border-radius: 5px; }
        .routine-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>DANH SÁCH BÀI VÕ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <div class="filter-bar">
        <form method="GET">
            <label>Cấp độ:</label>
            <select name="level" onchange="this.form.submit()">
                <option value="">Tất cả</option>
                <option value="beginner" {{ 'selected' if request.args.get('level') == 'beginner' }}>Sơ cấp</option>
                <option value="intermediate" {{ 'selected' if request.args.get('level') == 'intermediate' }}>Trung cấp</option>
                <option value="advanced" {{ 'selected' if request.args.get('level') == 'advanced' }}>Nâng cao</option>
            </select>
            
            <label style="margin-left:15px;">Binh khí:</label>
            <select name="weapon_id" onchange="this.form.submit()">
                <option value="">Tất cả</option>
                {% for w in weapons %}
                <option value="{{ w.weapon_id }}" {{ 'selected' if request.args.get('weapon_id')|int == w.weapon_id }}>{{ w.weapon_name_vi }}</option>
                {% endfor %}
            </select>
        </form>
    </div>
    
    {% if routines %}
        {% for r in routines %}
        <div class="routine-card">
            <h3>{{ r.routine_name }}</h3>
            <p>
                <strong>Binh khí:</strong> {{ r.weapon.weapon_name_vi }} |
                <strong>Cấp độ:</strong> 
                {% if r.level == 'beginner' %}🟢 Sơ cấp
                {% elif r.level == 'intermediate' %}🟡 Trung cấp
                {% elif r.level == 'advanced' %}🔴 Nâng cao
                {% endif %} |
                <strong>Độ khó:</strong> {{ r.difficulty_score }}/10<br>
                <strong>Thời lượng:</strong> {{ (r.duration_seconds / 60)|round(1) }} phút |
                <strong>Số động tác:</strong> {{ r.total_moves }} |
                <strong>Ngưỡng đạt:</strong> {{ r.pass_threshold }}%
            </p>
            {% if r.description %}
            <p><em>{{ r.description }}</em></p>
            {% endif %}
            <p>
                <a href="{{ url_for('student.routine_detail', routine_id=r.routine_id) }}" style="padding:6px 12px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">📖 Xem chi tiết</a>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa có bài võ nào được xuất bản</p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('student.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/student/routine_detail.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Chi tiết bài võ</title>
    <style>
        .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .info-table td { padding: 10px; border: 1px solid #ddd; }
        .info-table td:first-child { background: #f8f9fa; font-weight: bold; width: 200px; }
        .video-container { margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .criteria-item { padding: 10px; margin: 5px 0; background: #e7f3ff; border-left: 3px solid #007bff; }
    </style>
</head>
<body>
    <h1>CHI TIẾT BÀI VÕ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <table class="info-table">
        <tr>
            <td>Tên bài võ</td>
            <td><strong>{{ routine.routine_name }}</strong></td>
        </tr>
        <tr>
            <td>Mã bài võ</td>
            <td>{{ routine.routine_code }}</td>
        </tr>
        <tr>
            <td>Mô tả</td>
            <td>{{ routine.description or 'Không có' }}</td>
        </tr>
        <tr>
            <td>Binh khí</td>
            <td>{{ routine.weapon.weapon_name_vi }} ({{ routine.weapon.weapon_name_en }})</td>
        </tr>
        <tr>
            <td>Cấp độ</td>
            <td>
                {% if routine.level == 'beginner' %}🟢 Sơ cấp
                {% elif routine.level == 'intermediate' %}🟡 Trung cấp
                {% elif routine.level == 'advanced' %}🔴 Nâng cao
                {% endif %}
            </td>
        </tr>
        <tr>
            <td>Độ khó</td>
            <td>{{ routine.difficulty_score }}/10</td>
        </tr>
        <tr>
            <td>Thời lượng</td>
            <td>{{ (routine.duration_seconds / 60)|round(1) }} phút ({{ routine.duration_seconds }} giây)</td>
        </tr>
        <tr>
            <td>Số động tác</td>
            <td>{{ routine.total_moves }}</td>
        </tr>
        <tr>
            <td>Ngưỡng đạt</td>
            <td><strong style="color:#28a745;">{{ routine.pass_threshold }}%</strong></td>
        </tr>
        <tr>
            <td>Giảng viên</td>
            <td>{{ routine.creator.full_name }}</td>
        </tr>
    </table>
    
    {% if routine.reference_video_url %}
    <div class="video-container">
        <h3>🎥 VIDEO MẪU CHUẨN</h3>
        <p><a href="{{ routine.reference_video_url }}" target="_blank" style="padding:10px 20px; background:#dc3545; color:white; text-decoration:none; border-radius:4px;">▶️ Xem video mẫu</a></p>
        <p><small>Lưu ý: Xem kỹ video mẫu trước khi tập luyện và quay video của bạn</small></p>
    </div>
    {% else %}
    <p style="color:#ffc107;">⚠️ Bài võ này chưa có video mẫu chuẩn</p>
    {% endif %}
    
    {% if criteria %}
    <h2>TIÊU CHÍ ĐÁNH GIÁ</h2>
    <p>Bài của bạn sẽ được đánh giá theo các tiêu chí sau:</p>
    {% for c in criteria %}
    <div class="criteria-item">
        <strong>{{ c.criteria_name }}</strong> - <strong style="color:#007bff;">{{ c.weight_percentage }}%</strong>
        {% if c.description %}<br><small>{{ c.description }}</small>{% endif %}
    </div>
    {% endfor %}
    {% endif %}
    
    <hr>
    <p>
        <a href="{{ url_for('student.routines') }}" style="padding:8px 15px; background:#6c757d; color:white; text-decoration:none; border-radius:4px;">← Quay lại</a>
        <a href="{{ url_for('student.dashboard') }}" style="padding:8px 15px; background:#007bff; color:white; text-decoration:none; border-radius:4px; margin-left:10px;">🏠 Dashboard</a>
    </p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/student/my_assignments.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Bài tập của tôi</title>
    <style>
        .assignment-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .assignment-card.pending { border-left: 4px solid #ffc107; }
        .assignment-card.completed { border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <h1>BÀI TẬP CỦA TÔI</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <h2>BÀI TẬP ĐANG CHỜ ({{ pending|length }})</h2>
    {% if pending %}
        {% for a in pending %}
        <div class="assignment-card pending">
            <h3>{{ a.routine.routine_name }}</h3>
            <p>
                <strong>Độ ưu tiên:</strong> 
                <span style="color:{% if a.priority == 'urgent' %}#dc3545{% elif a.priority == 'high' %}#ffc107{% else %}#6c757d{% endif %};">
                    {{ a.priority|upper }}
                </span> |
                <strong>Bắt buộc:</strong> {{ 'Có' if a.is_mandatory else 'Không' }}<br>
                
                {% if a.deadline %}
                <strong>Deadline:</strong> {{ a.deadline.strftime('%d/%m/%Y %H:%M') }}<br>
                {% endif %}
                
                <strong>Ngày gán:</strong> {{ a.created_at.strftime('%d/%m/%Y') }}
            </p>
            {% if a.instructions %}
            <p><em>Hướng dẫn: {{ a.instructions }}</em></p>
            {% endif %}
            <p>
                <a href="{{ url_for('student.routine_detail', routine_id=a.routine_id) }}" style="padding:6px 12px; background:#007bff; color:white; text-decoration:none; border-radius:3px;">📖 Xem bài võ</a>
                <span style="margin-left:10px; color:#dc3545; font-weight:bold;">❌ Chưa nộp</span>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Không có bài tập nào đang chờ</p>
    {% endif %}
    
    <hr>
    
    <h2>BÀI TẬP ĐÃ NỘP ({{ completed|length }})</h2>
    {% if completed %}
        {% for item in completed %}
        <div class="assignment-card completed">
            <h3>{{ item.assignment.routine.routine_name }}</h3>
            <p>
                <strong>Đã nộp:</strong> {{ item.video.uploaded_at.strftime('%d/%m/%Y %H:%M') }} 
                <span style="color:#28a745; font-weight:bold;">✅</span>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa nộp bài tập nào</p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('student.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/student/my_exams.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Bài kiểm tra của tôi</title>
    <style>
        .exam-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>BÀI KIỂM TRA CỦA TÔI</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <h2>BÀI KIỂM TRA SẮP TỚI ({{ upcoming|length }})</h2>
    {% if upcoming %}
        {% for item in upcoming %}
        <div class="exam-card">
            <h3>{{ item.exam.exam_name }}</h3>
            <p>
                <strong>Loại:</strong> {{ item.exam.exam_type }} |
                <strong>Bài võ:</strong> {{ item.exam.routine.routine_name }}<br>
                <strong>Thời gian thi:</strong> {{ item.exam.start_time.strftime('%d/%m/%Y %H:%M') }} - {{ item.exam.end_time.strftime('%d/%m/%Y %H:%M') }}<br>
                <strong>Thời lượng:</strong> {{ item.exam.duration_minutes }} phút |
                <strong>Điểm đạt:</strong> {{ item.exam.pass_score }}% |
                <strong>Số lần thi:</strong> {{ item.attempts_used }}/{{ item.exam.max_attempts }}
            </p>
            {% if item.can_attempt %}
            <p style="color:#28a745; font-weight:bold;">✅ Có thể thi</p>
            {% else %}
            <p style="color:#6c757d;">⏳ Chưa đến giờ hoặc đã hết lượt thi</p>
            {% endif %}
        </div>
        {% endfor %}
    {% else %}
        <p>Không có bài kiểm tra sắp tới</p>
    {% endif %}
    
    <hr>
    
    <h2>BÀI KIỂM TRA ĐÃ QUA ({{ past|length }})</h2>
    {% if past %}
        {% for item in past %}
        <div class="exam-card">
            <h3>{{ item.exam.exam_name }}</h3>
            <p>
                <strong>Thời gian:</strong> {{ item.exam.start_time.strftime('%d/%m/%Y') }}<br>
                <strong>Số lần đã thi:</strong> {{ item.attempts_used }}/{{ item.exam.max_attempts }}
            </p>
            {% if item.results %}
                <p><strong>Kết quả:</strong></p>
                {% for result in item.results %}
                <p>
                    Lần {{ result.attempt_number }}: 
                    {% if result.score %}
                        <strong style="color:{% if result.score >= item.exam.pass_score %}#28a745{% else %}#dc3545{% endif %};">
                            {{ result.score }}% 
                            ({{ 'ĐẠT' if result.score >= item.exam.pass_score else 'KHÔNG ĐẠT' }})
                        </strong>
                    {% else %}
                        <span style="color:#ffc107;">Chờ chấm điểm</span>
                    {% endif %}
                </p>
                {% endfor %}
            {% endif %}
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa có bài kiểm tra nào</p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('student.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""
<!DOCTYPE html>
<html>
<head>
    <title>Gán bài tập mới</title>
    <script>
        function toggleFields() {
            var type = document.querySelector('input[name="assignment_type"]:checked').value;
            document.getElementById('student_field').style.display = (type === 'individual') ? 'block' : 'none';
            document.getElementById('class_field').style.display = (type === 'class') ? 'block' : 'none';
        }
    </script>
</head>
<body>
    <h1>GÁN BÀI TẬP MỚI</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="POST">
        {{ form.hidden_tag() }}
        
        <p>
            {{ form.routine_id.label }}<br>
            {{ form.routine_id() }}
            {% if form.routine_id.errors %}
                {% for error in form.routine_id.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.assignment_type.label }}<br>
            {% for choice in form.assignment_type %}
                <label>
                    {{ choice(onclick="toggleFields()") }} {{ choice.label.text }}
                </label><br>
            {% endfor %}
        </p>
        
        <div id="student_field" style="display:block;">
            <p>
                {{ form.assigned_to_student.label }}<br>
                {{ form.assigned_to_student() }}
                {% if form.assigned_to_student.errors %}
                    {% for error in form.assigned_to_student.errors %}
                        <br><span style="color:red;">{{ error }}</span>
                    {% endfor %}
                {% endif %}
            </p>
        </div>
        
        <div id="class_field" style="display:none;">
            <p>
                {{ form.assigned_to_class.label }}<br>
                {{ form.assigned_to_class() }}
                {% if form.assigned_to_class.errors %}
                    {% for error in form.assigned_to_class.errors %}
                        <br><span style="color:red;">{{ error }}</span>
                    {% endfor %}
                {% endif %}
            </p>
        </div>
        
        <p>
            {{ form.deadline.label }}<br>
            {{ form.deadline() }}
            <br><small>Để trống nếu không có deadline</small>
        </p>
        
        <p>
            {{ form.priority.label }}<br>
            {{ form.priority() }}
        </p>
        
        <p>
            <label>
                {{ form.is_mandatory() }}
                {{ form.is_mandatory.label }}
            </label>
        </p>
        
        <p>
            {{ form.instructions.label }}<br>
            {{ form.instructions(rows=4, cols=60) }}
        </p>
        
        <p>
            <button type="submit" style="padding:10px 20px; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">Gán bài tập</button>
        </p>
    </form>
    
    <hr>
    <p><a href="{{ url_for('instructor.assignments') }}">← Quay lại</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/assignment_detail.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Chi tiết bài tập</title>
    <style>
        .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .info-table td { padding: 10px; border: 1px solid #ddd; }
        .info-table td:first-child { background: #f8f9fa; font-weight: bold; width: 200px; }
        .student-item { padding: 10px; margin: 5px 0; background: #f8f9fa; border-left: 3px solid #007bff; }
        .student-item.submitted { border-left-color: #28a745; }
    </style>
</head>
<body>
    <h1>CHI TIẾT BÀI TẬP</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <table class="info-table">
        <tr>
            <td>Bài võ</td>
            <td><strong>{{ assignment.routine.routine_name }}</strong></td>
        </tr>
        <tr>
            <td>Loại gán</td>
            <td>{{ 'Cá nhân' if assignment.assignment_type == 'individual' else 'Lớp học' }}</td>
        </tr>
        <tr>
            <td>Gán cho</td>
            <td>
                {% if assignment.assignment_type == 'individual' %}
                    {{ assignment.student.full_name }} ({{ assignment.student.username }})
                {% else %}
                    Lớp {{ assignment.class_obj.class_name }}
                {% endif %}
            </td>
        </tr>
        <tr>
            <td>Độ ưu tiên</td>
            <td>{{ assignment.priority }}</td>
        </tr>
        <tr>
            <td>Bắt buộc</td>
            <td>{{ 'Có' if assignment.is_mandatory else 'Không' }}</td>
        </tr>
        {% if assignment.deadline %}
        <tr>
            <td>Deadline</td>
            <td>{{ assignment.deadline.strftime('%d/%m/%Y %H:%M') }}</td>
        </tr>
        {% endif %}
        <tr>
            <td>Hướng dẫn</td>
            <td>{{ assignment.instructions or 'Không có' }}</td>
        </tr>
        <tr>
            <td>Ngày gán</td>
            <td>{{ assignment.created_at.strftime('%d/%m/%Y %H:%M') }}</td>
        </tr>
    </table>
    
    <h2>TRẠNG THÁI NỘP BÀI ({{ status_list|selectattr('submitted')|list|length }}/{{ status_list|length }})</h2>
    
    {% for status in status_list %}
    <div class="student-item {{ 'submitted' if status.submitted }}">
        <strong>{{ status.student.full_name }}</strong> ({{ status.student.username }})
        {% if status.submitted %}
            <span style="color:#28a745; font-weight:bold;">✅ Đã nộp ({{ status.video_count }} video)</span>
            {% if status.latest_video %}
            <br><small>Lần cuối: {{ status.latest_video.uploaded_at.strftime('%d/%m/%Y %H:%M') }}</small>
            {% endif %}
        {% else %}
            <span style="color:#dc3545; font-weight:bold;">❌ Chưa nộp</span>
        {% endif %}
    </div>
    {% endfor %}
    
    <hr>
    <p>
        <form method="POST" action="{{ url_for('instructor.delete_assignment', assignment_id=assignment.assignment_id) }}" style="display:inline;">
            {{ csrf_token() }}
            <button type="submit" onclick="return confirm('Xác nhận xóa bài tập?')" style="padding:8px 15px; background:#dc3545; color:white; border:none; border-radius:4px; cursor:pointer;">🗑️ Xóa bài tập</button>
        </form>
    </p>
    
    <hr>
    <p><a href="{{ url_for('instructor.assignments') }}">← Về danh sách</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/exams.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Quản lý kiểm tra</title>
    <style>
        .exam-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .exam-card.draft { border-left: 4px solid #ffc107; }
        .exam-card.published { border-left: 4px solid #28a745; }
    </style>
</head>
<body>
    <h1>QUẢN LÝ BÀI KIỂM TRA</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <p><a href="{{ url_for('instructor.create_exam') }}" style="padding:8px 15px; background:#007bff; color:white; text-decoration:none; border-radius:4px;">+ Tạo bài kiểm tra mới</a></p>
    
    {% if exams %}
        {% for e in exams %}
        <div class="exam-card {{ 'published' if e.is_published else 'draft' }}">
            <h3>
                {{ e.exam_name }}
                <span style="padding:2px 6px; background:{{ '#28a745' if e.is_published else '#ffc107' }}; color:white; border-radius:3px; font-size:12px;">
                    {{ 'Đã xuất bản' if e.is_published else 'Nháp' }}
                </span>
            </h3>
            <p>
                <strong>Mã:</strong> {{ e.exam_code }} |
                <strong>Loại:</strong> {{ e.exam_type }} |
                <strong>Bài võ:</strong> {{ e.routine.routine_name }}<br>
                {% if e.class_id %}
                <strong>Lớp:</strong> {{ e.class_obj.class_name }} |
                {% endif %}
                <strong>Thời gian:</strong> {{ e.start_time.strftime('%d/%m/%Y %H:%M') }} - {{ e.end_time.strftime('%d/%m/%Y %H:%M') }}<br>
                <strong>Thời lượng làm bài:</strong> {{ e.duration_minutes }} phút |
                <strong>Điểm đạt:</strong> {{ e.pass_score }}% |
                <strong>Số lần thi:</strong> {{ e.max_attempts }}
            </p>
            <p>
                <a href="{{ url_for('instructor.exam_detail', exam_id=e.exam_id) }}">📊 Chi tiết & kết quả</a>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa có bài kiểm tra nào. <a href="{{ url_for('instructor.create_exam') }}">Tạo bài kiểm tra đầu tiên</a></p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('instructor.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""
<!DOCTYPE html>
<html>
<head>
    <title>Thêm tiêu chí đánh giá</title>
</head>
<body>
    <h1>THÊM TIÊU CHÍ ĐÁNH GIÁ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <p><strong>Bài võ:</strong> {{ routine.routine_name }}</p>
    
    <form method="POST">
        {{ form.hidden_tag() }}
        
        <p>
            {{ form.criteria_name.label }}<br>
            {{ form.criteria_name(size=40) }}
            {% if form.criteria_name.errors %}
                {% for error in form.criteria_name.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.criteria_code.label }}<br>
            {{ form.criteria_code(size=30) }}
            <br><small>VD: TECHNIQUE, POSTURE, TIMING</small>
            {% if form.criteria_code.errors %}
                {% for error in form.criteria_code.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.weight_percentage.label }}<br>
            {{ form.weight_percentage() }}
            <small>(%)</small>
            {% if form.weight_percentage.errors %}
                {% for error in form.weight_percentage.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.description.label }}<br>
            {{ form.description(rows=3, cols=50) }}
        </p>
        
        <p>
            {{ form.evaluation_method.label }}<br>
            {{ form.evaluation_method(size=40) }}
            <br><small>VD: AI_ANALYSIS, MANUAL_SCORING</small>
        </p>
        
        <p>
            <button type="submit" style="padding:10px 20px; background:#007bff; color:white; border:none; border-radius:4px; cursor:pointer;">Thêm tiêu chí</button>
        </p>
    </form>
    
    <hr>
    <p><a href="{{ url_for('instructor.routine_detail', routine_id=routine.routine_id) }}">← Quay lại</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/routine_edit.html
# ===================================================================
"""
<!DOCTYPE html>routine_edit
<html>
<head>
    <title>Sửa bài võ</title>
</head>
<body>
    <h1>SỬA BÀI VÕ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <p><strong>Mã:</strong> {{ routine.routine_code }} (không thể đổi)</p>
    
    <form method="POST">
        {{ form.hidden_tag() }}
        
        <p>
            {{ form.routine_name.label }}<br>
            {{ form.routine_name(size=50) }}
            {% if form.routine_name.errors %}
                {% for error in form.routine_name.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.description.label }}<br>
            {{ form.description(rows=4, cols=50) }}
        </p>
        
        <p>
            {{ form.weapon_id.label }}<br>
            {{ form.weapon_id() }}
        </p>
        
        <p>
            {{ form.level.label }}<br>
            {{ form.level() }}
        </p>
        
        <p>
            {{ form.difficulty_score.label }}<br>
            {{ form.difficulty_score() }}
        </p>
        
        <p>
            {{ form.duration_seconds.label }}<br>
            {{ form.duration_seconds() }}
        </p>
        
        <p>
            {{ form.total_moves.label }}<br>
            {{ form.total_moves() }}
        </p>
        
        <p>
            {{ form.pass_threshold.label }}<br>
            {{ form.pass_threshold() }}
        </p>
        
        <p>
            {{ form.reference_video_url.label }}<br>
            {{ form.reference_video_url(size=60) }}
        </p>
        
        <p>
            <button type="submit" style="padding:10px 20px; background:#007bff; color:white; border:none; border-radius:4px; cursor:pointer;">Lưu thay đổi</button>
        </p>
    </form>
    
    <hr>
    <p><a href="{{ url_for('instructor.routine_detail', routine_id=routine.routine_id) }}">← Quay lại</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/assignments.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Quản lý bài tập</title>
    <style>
        .assignment-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .assignment-card.individual { border-left: 4px solid #007bff; }
        .assignment-card.class { border-left: 4px solid #28a745; }
        .priority-low { color: #6c757d; }
        .priority-normal { color: #007bff; }
        .priority-high { color: #ffc107; }
        .priority-urgent { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <h1>QUẢN LÝ BÀI TẬP</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <p><a href="{{ url_for('instructor.create_assignment') }}" style="padding:8px 15px; background:#007bff; color:white; text-decoration:none; border-radius:4px;">+ Gán bài tập mới</a></p>
    
    {% if assignments %}
        {% for a in assignments %}
        <div class="assignment-card {{ a.assignment_type }}">
            <h3>
                {{ a.routine.routine_name }}
                <span style="padding:2px 6px; background:#007bff; color:white; border-radius:3px; font-size:12px;">
                    {{ 'Cá nhân' if a.assignment_type == 'individual' else 'Lớp học' }}
                </span>
            </h3>
            <p>
                <strong>Gán cho:</strong>
                {% if a.assignment_type == 'individual' %}
                    {{ a.student.full_name }} ({{ a.student.username }})
                {% else %}
                    Lớp {{ a.class_obj.class_name }}
                {% endif %}<br>
                
                <strong>Độ ưu tiên:</strong> 
                <span class="priority-{{ a.priority }}">
                    {% if a.priority == 'low' %}Thấp
                    {% elif a.priority == 'normal' %}Bình thường
                    {% elif a.priority == 'high' %}Cao
                    {% elif a.priority == 'urgent' %}🚨 KHẨN CẤP
                    {% endif %}
                </span> |
                
                <strong>Bắt buộc:</strong> {{ 'Có' if a.is_mandatory else 'Không' }}<br>
                
                {% if a.deadline %}
                <strong>Deadline:</strong> {{ a.deadline.strftime('%d/%m/%Y %H:%M') }}<br>
                {% endif %}
                
                <strong>Ngày gán:</strong> {{ a.created_at.strftime('%d/%m/%Y %H:%M') }}
            </p>
            
            {% if a.instructions %}
            <p><em>{{ a.instructions }}</em></p>
            {% endif %}
            
            <p>
                <a href="{{ url_for('instructor.assignment_detail', assignment_id=a.assignment_id) }}">📊 Xem chi tiết & trạng thái nộp bài</a>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa có bài tập nào. <a href="{{ url_for('instructor.create_assignment') }}">Gán bài tập đầu tiên</a></p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('instructor.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""Get published routines for students"""
        query = MartialRoutine.query.filter_by(is_published=True, is_active=True)
        
        if filters:
            if filters.get('level'):
                query = query.filter_by(level=filters['level'])
            if filters.get('weapon_id'):
                query = query.filter_by(weapon_id=filters['weapon_id'])
        
        return query.order_by(MartialRoutine.created_at.desc()).all()


# ===================================================================
# FILE: app/services/assignment_service.py
# ===================================================================
from app.models import db
from app.models.assignment import Assignment
from app.models.martial_routine import MartialRoutine
from app.models.user import User
from app.models.class_enrollment import ClassEnrollment
from app.models.training_video import TrainingVideo
from datetime import datetime


class AssignmentService:
    @staticmethod
    def create_assignment(data: dict, assigned_by: int):
        assignment = Assignment(
            routine_id=data['routine_id'],
            assigned_by=assigned_by,
            assignment_type=data['assignment_type'],
            assigned_to_student=data.get('assigned_to_student'),
            assigned_to_class=data.get('assigned_to_class'),
            deadline=data.get('deadline'),
            instructions=data.get('instructions'),
            priority=data.get('priority', 'normal'),
            is_mandatory=data.get('is_mandatory', True)
        )

        db.session.add(assignment)
        db.session.commit()
        return {'success': True, 'assignment': assignment}

    @staticmethod
    def get_assignments_by_instructor(instructor_id: int):
        return Assignment.query.filter_by(assigned_by=instructor_id).order_by(Assignment.created_at.desc()).all()

    @staticmethod
    def get_assignment_by_id(assignment_id: int):
        return Assignment.query.get(assignment_id)

    @staticmethod
    def get_assigned_students(assignment_id: int):
        """Get list of students assigned to this assignment"""
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return []

        if assignment.assignment_type == 'individual':
            return [assignment.student] if assignment.student else []
        else:  # class
            enrollments = ClassEnrollment.query.filter_by(
                class_id=assignment.assigned_to_class,
                enrollment_status='active'
            ).all()
            return [e.student for e in enrollments]

    @staticmethod
    def get_submission_status(assignment_id: int):
        """Get submission status for each student"""
        students = AssignmentService.get_assigned_students(assignment_id)
        
        status_list = []
        for student in students:
            videos = TrainingVideo.query.filter_by(
                student_id=student.user_id,
                assignment_id=assignment_id
            ).order_by(TrainingVideo.uploaded_at.desc()).all()

            status_list.append({
                'student': student,
                'submitted': len(videos) > 0,
                'video_count': len(videos),
                'latest_video': videos[0] if videos else None
            })
        
        return status_list

    @staticmethod
    def delete_assignment(assignment_id: int, instructor_id: int):
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return {'success': False, 'message': 'Không tìm thấy bài tập'}

        if assignment.assigned_by != instructor_id:
            return {'success': False, 'message': 'Bạn không có quyền xóa bài tập này'}

        db.session.delete(assignment)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_assignments_for_student(student_id: int):
        """Get all assignments for a student"""
        from app.models.class_enrollment import ClassEnrollment
        
        # Individual assignments
        individual = Assignment.query.filter_by(
            assignment_type='individual',
            assigned_to_student=student_id
        ).all()

        # Class assignments
        enrollments = ClassEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='active'
        ).all()
        class_ids = [e.class_id for e in enrollments]
        
        class_assignments = Assignment.query.filter(
            Assignment.assignment_type == 'class',
            Assignment.assigned_to_class.in_(class_ids)
        ).all() if class_ids else []

        return individual + class_assignments


# ===================================================================
# FILE: app/services/exam_service.py
# ===================================================================
from app.models import db
from app.models.exam import Exam
from app.models.exam_result import ExamResult
from app.models.class_enrollment import ClassEnrollment
from datetime import datetime


class ExamService:
    @staticmethod
    def create_exam(data: dict, instructor_id: int):
        # Check duplicate code
        if Exam.query.filter_by(exam_code=data['exam_code']).first():
            return {'success': False, 'message': 'Mã bài kiểm tra đã tồn tại'}

        exam = Exam(
            exam_code=data['exam_code'],
            exam_name=data['exam_name'],
            description=data.get('description'),
            class_id=data.get('class_id'),
            instructor_id=instructor_id,
            routine_id=data['routine_id'],
            exam_type=data['exam_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_minutes=data['duration_minutes'],
            pass_score=data.get('pass_score', 70.00),
            max_attempts=data.get('max_attempts', 1),
            is_published=False
        )

        db.session.add(exam)
        db.session.commit()
        return {'success': True, 'exam': exam}

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

        # Check if has results
        result_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        if result_count > 0:
            return {'success': False, 'message': f'Không thể xóa - đã có {result_count} kết quả thi'}

        db.session.delete(exam)
        db.session.commit()
        return {'success': True}

    @staticmethod
    def get_exam_results(exam_id: int):
        return ExamResult.query.filter_by(exam_id=exam_id).order_by(ExamResult.submitted_at.desc()).all()

    @staticmethod
    def get_exams_for_student(student_id: int):
        """Get all exams for a student (from their classes)"""
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
        """Get student's results for an exam"""
        return ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).order_by(ExamResult.attempt_number.desc()).all()


# ===================================================================
# FILE: app/forms/routine_forms.py
# ===================================================================
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, DecimalField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError


class RoutineCreateForm(FlaskForm):
    routine_code = StringField('Mã bài võ', validators=[
        DataRequired(message='Vui lòng nhập mã bài võ'),
        Length(max=30, message='Mã bài võ tối đa 30 ký tự')
    ])
    routine_name = StringField('Tên bài võ', validators=[
        DataRequired(message='Vui lòng nhập tên bài võ'),
        Length(max=100, message='Tên bài võ tối đa 100 ký tự')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    weapon_id = SelectField('Binh khí', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn binh khí')
    ])
    level = SelectField('Cấp độ', choices=[
        ('beginner', 'Sơ cấp'),
        ('intermediate', 'Trung cấp'),
        ('advanced', 'Nâng cao')
    ], validators=[DataRequired(message='Vui lòng chọn cấp độ')])
    difficulty_score = DecimalField('Độ khó (1-10)', validators=[
        Optional(),
        NumberRange(min=1.0, max=10.0, message='Độ khó từ 1.0 đến 10.0')
    ], default=1.0)
    duration_seconds = IntegerField('Thời lượng (giây)', validators=[
        DataRequired(message='Vui lòng nhập thời lượng'),
        NumberRange(min=1, max=3600, message='Thời lượng từ 1-3600 giây')
    ])
    total_moves = IntegerField('Số động tác', validators=[
        Optional(),
        NumberRange(min=1, message='Số động tác tối thiểu 1')
    ], default=1)
    pass_threshold = DecimalField('Ngưỡng đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Ngưỡng từ 0-100%')
    ], default=70.00)
    reference_video_url = StringField('URL video mẫu', validators=[
        Optional(),
        Length(max=500, message='URL tối đa 500 ký tự')
    ])


class CriteriaForm(FlaskForm):
    criteria_name = StringField('Tên tiêu chí', validators=[
        DataRequired(message='Vui lòng nhập tên tiêu chí'),
        Length(max=100, message='Tên tiêu chí tối đa 100 ký tự')
    ])
    criteria_code = StringField('Mã tiêu chí', validators=[
        DataRequired(message='Vui lòng nhập mã tiêu chí'),
        Length(max=50, message='Mã tiêu chí tối đa 50 ký tự')
    ])
    weight_percentage = DecimalField('Trọng số (%)', validators=[
        DataRequired(message='Vui lòng nhập trọng số'),
        NumberRange(min=0.01, max=100, message='Trọng số từ 0.01-100%')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    evaluation_method = StringField('Phương pháp đánh giá', validators=[
        Optional(),
        Length(max=50, message='Phương pháp tối đa 50 ký tự')
    ])


# ===================================================================
# FILE: app/forms/assignment_forms.py
# ===================================================================
from flask_wtf import FlaskForm
from wtforms import SelectField, DateTimeField, TextAreaField, BooleanField, RadioField
from wtforms.validators import DataRequired, Optional, ValidationError
from datetime import datetime


class AssignmentCreateForm(FlaskForm):
    routine_id = SelectField('Bài võ', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn bài võ')
    ])
    assignment_type = RadioField('Loại gán', choices=[
        ('individual', 'Cá nhân'),
        ('class', 'Cả lớp')
    ], default='individual', validators=[DataRequired()])
    assigned_to_student = SelectField('Học viên (nếu cá nhân)', coerce=int, validators=[Optional()])
    assigned_to_class = SelectField('Lớp học (nếu gán lớp)', coerce=int, validators=[Optional()])
    deadline = DateTimeField('Deadline', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    instructions = TextAreaField('Hướng dẫn', validators=[Optional()])
    priority = SelectField('Độ ưu tiên', choices=[
        ('low', 'Thấp'),
        ('normal', 'Bình thường'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp')
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


# ===================================================================
# FILE: app/forms/exam_forms.py
# ===================================================================
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, IntegerField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from datetime import datetime


class ExamCreateForm(FlaskForm):
    exam_code = StringField('Mã bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập mã bài kiểm tra'),
        Length(max=30, message='Mã tối đa 30 ký tự')
    ])
    exam_name = StringField('Tên bài kiểm tra', validators=[
        DataRequired(message='Vui lòng nhập tên bài kiểm tra'),
        Length(max=100, message='Tên tối đa 100 ký tự')
    ])
    description = TextAreaField('Mô tả', validators=[Optional()])
    class_id = SelectField('Lớp học', coerce=int, validators=[Optional()])
    routine_id = SelectField('Bài võ', coerce=int, validators=[
        DataRequired(message='Vui lòng chọn bài võ')
    ])
    exam_type = SelectField('Loại kiểm tra', choices=[
        ('practice', 'Thi thử'),
        ('midterm', 'Giữa kỳ'),
        ('final', 'Cuối kỳ'),
        ('certification', 'Chứng chỉ')
    ], validators=[DataRequired()])
    start_time = DateTimeField('Thời gian bắt đầu', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian bắt đầu')
    ])
    end_time = DateTimeField('Thời gian kết thúc', format='%Y-%m-%dT%H:%M', validators=[
        DataRequired(message='Vui lòng chọn thời gian kết thúc')
    ])
    duration_minutes = IntegerField('Thời gian làm bài (phút)', validators=[
        DataRequired(message='Vui lòng nhập thời gian làm bài'),
        NumberRange(min=1, message='Thời gian tối thiểu 1 phút')
    ])
    pass_score = DecimalField('Điểm đạt (%)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Điểm từ 0-100%')
    ], default=70.00)
    max_attempts = IntegerField('Số lần thi tối đa', validators=[
        Optional(),
        NumberRange(min=1, message='Tối thiểu 1 lần')
    ], default=1)

    def validate_end_time(self, field):
        if field.data and self.start_time.data and field.data <= self.start_time.data:
            raise ValidationError('Thời gian kết thúc phải sau thời gian bắt đầu')


# ===================================================================
# FILE: app/routes/instructor.py (THÊM VÀO)
# ===================================================================
# ... (existing code) ...

from app.services.routine_service import RoutineService
from app.services.assignment_service import AssignmentService
from app.services.exam_service import ExamService
from app.forms.routine_forms import RoutineCreateForm, CriteriaForm
from app.forms.assignment_forms import AssignmentCreateForm
from app.forms.exam_forms import ExamCreateForm

# ============ ROUTINE MANAGEMENT ============

@instructor_bp.route('/routines')
@login_required
@role_required('INSTRUCTOR')
def routines():
    """List all routines created by instructor"""
    level_filter = request.args.get('level')
    weapon_filter = request.args.get('weapon_id', type=int)
    status_filter = request.args.get('status')
    
    filters = {}
    if level_filter:
        filters['level'] = level_filter
    if weapon_filter:
        filters['weapon_id'] = weapon_filter
    if status_filter == 'published':
        filters['is_published'] = True
    elif status_filter == 'draft':
        filters['is_published'] = False
    
    routines = RoutineService.get_routines_by_instructor(session['user_id'], filters)
    weapons = RoutineService.get_all_weapons()
    
    return render_template('instructor/routines.html', routines=routines, weapons=weapons)


@instructor_bp.route('/routines/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_routine():
    form = RoutineCreateForm()
    
    # Load weapons
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(0, '-- Chọn binh khí --')] + [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    if form.validate_on_submit():
        data = {
            'routine_code': form.routine_code.data,
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'duration_seconds': form.duration_seconds.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': form.reference_video_url.data
        }
        
        result = RoutineService.create_routine(data, session['user_id'])
        if result['success']:
            flash('Tạo bài võ thành công! (Trạng thái: Nháp)', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=result['routine'].routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_create.html', form=form)


@instructor_bp.route('/routines/<int:routine_id>')
@login_required
@role_required('INSTRUCTOR')
def routine_detail(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    
    criteria = RoutineService.get_criteria_by_routine(routine_id)
    total_weight = sum(c.weight_percentage for c in criteria)
    
    return render_template('instructor/routine_detail.html', 
                         routine=routine, 
                         criteria=criteria,
                         total_weight=total_weight)


@instructor_bp.route('/routines/<int:routine_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def edit_routine(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    
    form = RoutineCreateForm(obj=routine)
    weapons = RoutineService.get_all_weapons()
    form.weapon_id.choices = [(w.weapon_id, w.weapon_name_vi) for w in weapons]
    
    if form.validate_on_submit():
        data = {
            'routine_name': form.routine_name.data,
            'description': form.description.data,
            'weapon_id': form.weapon_id.data,
            'level': form.level.data,
            'difficulty_score': form.difficulty_score.data,
            'duration_seconds': form.duration_seconds.data,
            'total_moves': form.total_moves.data,
            'pass_threshold': form.pass_threshold.data,
            'reference_video_url': form.reference_video_url.data
        }
        
        result = RoutineService.update_routine(routine_id, data, session['user_id'])
        if result['success']:
            flash('Cập nhật bài võ thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/routine_edit.html', form=form, routine=routine)


@instructor_bp.route('/routines/<int:routine_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_routine(routine_id: int):
    result = RoutineService.publish_routine(routine_id, session['user_id'])
    if result['success']:
        flash('Đã xuất bản bài võ!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/unpublish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def unpublish_routine(routine_id: int):
    result = RoutineService.unpublish_routine(routine_id, session['user_id'])
    if result['success']:
        flash('Đã gỡ xuất bản bài võ!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_routine(routine_id: int):
    result = RoutineService.delete_routine(routine_id, session['user_id'])
    if result['success']:
        flash('Xóa bài võ thành công!', 'success')
        return redirect(url_for('instructor.routines'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


@instructor_bp.route('/routines/<int:routine_id>/criteria/add', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def add_criteria(routine_id: int):
    routine = RoutineService.get_routine_by_id(routine_id)
    if not routine or routine.instructor_id != session['user_id']:
        flash('Không tìm thấy bài võ', 'error')
        return redirect(url_for('instructor.routines'))
    
    form = CriteriaForm()
    
    if form.validate_on_submit():
        data = {
            'criteria_name': form.criteria_name.data,
            'criteria_code': form.criteria_code.data,
            'weight_percentage': form.weight_percentage.data,
            'description': form.description.data,
            'evaluation_method': form.evaluation_method.data
        }
        
        result = RoutineService.add_criteria(routine_id, data)
        if result['success']:
            flash('Thêm tiêu chí đánh giá thành công!', 'success')
            return redirect(url_for('instructor.routine_detail', routine_id=routine_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/criteria_add.html', form=form, routine=routine)


@instructor_bp.route('/criteria/<int:criteria_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_criteria(criteria_id: int):
    from app.models.evaluation_criteria import EvaluationCriteria
    criteria = EvaluationCriteria.query.get(criteria_id)
    
    if not criteria or criteria.routine.instructor_id != session['user_id']:
        flash('Không tìm thấy tiêu chí', 'error')
        return redirect(url_for('instructor.routines'))
    
    routine_id = criteria.routine_id
    result = RoutineService.delete_criteria(criteria_id)
    
    if result['success']:
        flash('Xóa tiêu chí thành công!', 'success')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('instructor.routine_detail', routine_id=routine_id))


# ============ ASSIGNMENT MANAGEMENT ============

@instructor_bp.route('/assignments')
@login_required
@role_required('INSTRUCTOR')
def assignments():
    """List all assignments"""
    assignments = AssignmentService.get_assignments_by_instructor(session['user_id'])
    return render_template('instructor/assignments.html', assignments=assignments)


@instructor_bp.route('/assignments/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_assignment():
    form = AssignmentCreateForm()
    
    # Load routines
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    # Load students (from instructor's classes)
    from app.models.role import Role
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
        data = {
            'routine_id': form.routine_id.data,
            'assignment_type': form.assignment_type.data,
            'assigned_to_student': form.assigned_to_student.data if form.assignment_type.data == 'individual' else None,
            'assigned_to_class': form.assigned_to_class.data if form.assignment_type.data == 'class' else None,
            'deadline': form.deadline.data,
            'instructions': form.instructions.data,
            'priority': form.priority.data,
            'is_mandatory': form.is_mandatory.data
        }
        
        result = AssignmentService.create_assignment(data, session['user_id'])
        if result['success']:
            flash('Gán bài tập thành công!', 'success')
            return redirect(url_for('instructor.assignments'))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/assignment_create.html', form=form)


@instructor_bp.route('/assignments/<int:assignment_id>')
@login_required
@role_required('INSTRUCTOR')
def assignment_detail(assignment_id: int):
    assignment = AssignmentService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.assigned_by != session['user_id']:
        flash('Không tìm thấy bài tập', 'error')
        return redirect(url_for('instructor.assignments'))
    
    status_list = AssignmentService.get_submission_status(assignment_id)
    
    return render_template('instructor/assignment_detail.html', 
                         assignment=assignment, 
                         status_list=status_list)


@instructor_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_assignment(assignment_id: int):
    result = AssignmentService.delete_assignment(assignment_id, session['user_id'])
    if result['success']:
        flash('Xóa bài tập thành công!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.assignments'))


# ============ EXAM MANAGEMENT ============

@instructor_bp.route('/exams')
@login_required
@role_required('INSTRUCTOR')
def exams():
    """List all exams"""
    exams = ExamService.get_exams_by_instructor(session['user_id'])
    return render_template('instructor/exams.html', exams=exams)


@instructor_bp.route('/exams/create', methods=['GET', 'POST'])
@login_required
@role_required('INSTRUCTOR')
def create_exam():
    form = ExamCreateForm()
    
    # Load routines
    routines = RoutineService.get_routines_by_instructor(session['user_id'], {'is_published': True})
    form.routine_id.choices = [(0, '-- Chọn bài võ --')] + [(r.routine_id, r.routine_name) for r in routines]
    
    # Load classes
    classes = ClassService.get_classes_by_instructor(session['user_id'])
    form.class_id.choices = [(0, '-- Không chọn (tất cả) --')] + [(c.class_id, c.class_name) for c in classes]
    
    if form.validate_on_submit():
        data = {
            'exam_code': form.exam_code.data,
            'exam_name': form.exam_name.data,
            'description': form.description.data,
            'class_id': form.class_id.data if form.class_id.data else None,
            'routine_id': form.routine_id.data,
            'exam_type': form.exam_type.data,
            'start_time': form.start_time.data,
            'end_time': form.end_time.data,
            'duration_minutes': form.duration_minutes.data,
            'pass_score': form.pass_score.data,
            'max_attempts': form.max_attempts.data
        }
        
        result = ExamService.create_exam(data, session['user_id'])
        if result['success']:
            flash('Tạo bài kiểm tra thành công! (Trạng thái: Nháp)', 'success')
            return redirect(url_for('instructor.exam_detail', exam_id=result['exam'].exam_id))
        else:
            flash(result['message'], 'error')
    
    return render_template('instructor/exam_create.html', form=form)


@instructor_bp.route('/exams/<int:exam_id>')
@login_required
@role_required('INSTRUCTOR')
def exam_detail(exam_id: int):
    exam = ExamService.get_exam_by_id(exam_id)
    if not exam or exam.instructor_id != session['user_id']:
        flash('Không tìm thấy bài kiểm tra', 'error')
        return redirect(url_for('instructor.exams'))
    
    results = ExamService.get_exam_results(exam_id)
    
    return render_template('instructor/exam_detail.html', exam=exam, results=results)


@instructor_bp.route('/exams/<int:exam_id>/publish', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def publish_exam(exam_id: int):
    result = ExamService.publish_exam(exam_id, session['user_id'])
    if result['success']:
        flash('Đã xuất bản bài kiểm tra!', 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('instructor.exam_detail', exam_id=exam_id))


@instructor_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
@login_required
@role_required('INSTRUCTOR')
def delete_exam(exam_id: int):
    result = ExamService.delete_exam(exam_id, session['user_id'])
    if result['success']:
        flash('Xóa bài kiểm tra thành công!', 'success')
        return redirect(url_for('instructor.exams'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('instructor.exam_detail', exam_id=exam_id))


# ===================================================================
# FILE: templates/instructor/routines.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Quản lý bài võ</title>
    <style>
        .filter-bar { padding: 15px; background: #f8f9fa; margin: 15px 0; border-radius: 5px; }
        .routine-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .routine-card.draft { border-left: 4px solid #ffc107; }
        .routine-card.published { border-left: 4px solid #28a745; }
        .badge { padding: 3px 8px; border-radius: 3px; font-size: 12px; font-weight: bold; }
        .badge-draft { background: #ffc107; color: black; }
        .badge-published { background: #28a745; color: white; }
    </style>
</head>
<body>
    <h1>QUẢN LÝ BÀI VÕ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }}; 
                     border-color:{{ '#c3e6cb' if category == 'success' else '#f5c6cb' }}; 
                     color:{{ '#155724' if category == 'success' else '#721c24' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <p><a href="{{ url_for('instructor.create_routine') }}" style="padding:8px 15px; background:#007bff; color:white; text-decoration:none; border-radius:4px;">+ Tạo bài võ mới</a></p>
    
    <div class="filter-bar">
        <form method="GET">
            <label>Cấp độ:</label>
            <select name="level" onchange="this.form.submit()">
                <option value="">Tất cả</option>
                <option value="beginner" {{ 'selected' if request.args.get('level') == 'beginner' }}>Sơ cấp</option>
                <option value="intermediate" {{ 'selected' if request.args.get('level') == 'intermediate' }}>Trung cấp</option>
                <option value="advanced" {{ 'selected' if request.args.get('level') == 'advanced' }}>Nâng cao</option>
            </select>
            
            <label style="margin-left:15px;">Binh khí:</label>
            <select name="weapon_id" onchange="this.form.submit()">
                <option value="">Tất cả</option>
                {% for w in weapons %}
                <option value="{{ w.weapon_id }}" {{ 'selected' if request.args.get('weapon_id')|int == w.weapon_id }}>{{ w.weapon_name_vi }}</option>
                {% endfor %}
            </select>
            
            <label style="margin-left:15px;">Trạng thái:</label>
            <select name="status" onchange="this.form.submit()">
                <option value="">Tất cả</option>
                <option value="draft" {{ 'selected' if request.args.get('status') == 'draft' }}>Nháp</option>
                <option value="published" {{ 'selected' if request.args.get('status') == 'published' }}>Đã xuất bản</option>
            </select>
        </form>
    </div>
    
    {% if routines %}
        {% for r in routines %}
        <div class="routine-card {{ 'published' if r.is_published else 'draft' }}">
            <h3>
                {{ r.routine_name }}
                <span class="badge badge-{{ 'published' if r.is_published else 'draft' }}">
                    {{ 'Đã xuất bản' if r.is_published else 'Nháp' }}
                </span>
            </h3>
            <p>
                <strong>Mã:</strong> {{ r.routine_code }} |
                <strong>Binh khí:</strong> {{ r.weapon.weapon_name_vi }} |
                <strong>Cấp độ:</strong> {{ r.level }} |
                <strong>Thời lượng:</strong> {{ r.duration_seconds }}s |
                <strong>Độ khó:</strong> {{ r.difficulty_score }}/10<br>
                <strong>Ngưỡng đạt:</strong> {{ r.pass_threshold }}% |
                <strong>Số động tác:</strong> {{ r.total_moves }}
            </p>
            <p>
                <a href="{{ url_for('instructor.routine_detail', routine_id=r.routine_id) }}">📖 Chi tiết</a> |
                <a href="{{ url_for('instructor.edit_routine', routine_id=r.routine_id) }}">✏️ Sửa</a>
            </p>
        </div>
        {% endfor %}
    {% else %}
        <p>Chưa có bài võ nào. <a href="{{ url_for('instructor.create_routine') }}">Tạo bài võ đầu tiên</a></p>
    {% endif %}
    
    <hr>
    <p><a href="{{ url_for('instructor.dashboard') }}">← Về Dashboard</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/routine_create.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Tạo bài võ mới</title>
</head>
<body>
    <h1>TẠO BÀI VÕ MỚI</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }}; 
                     border-color:{{ '#c3e6cb' if category == 'success' else '#f5c6cb' }}; 
                     color:{{ '#155724' if category == 'success' else '#721c24' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <form method="POST">
        {{ form.hidden_tag() }}
        
        <p>
            {{ form.routine_code.label }}<br>
            {{ form.routine_code(size=30) }}
            {% if form.routine_code.errors %}
                {% for error in form.routine_code.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.routine_name.label }}<br>
            {{ form.routine_name(size=50) }}
            {% if form.routine_name.errors %}
                {% for error in form.routine_name.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.description.label }}<br>
            {{ form.description(rows=4, cols=50) }}
        </p>
        
        <p>
            {{ form.weapon_id.label }}<br>
            {{ form.weapon_id() }}
            {% if form.weapon_id.errors %}
                {% for error in form.weapon_id.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.level.label }}<br>
            {{ form.level() }}
        </p>
        
        <p>
            {{ form.difficulty_score.label }}<br>
            {{ form.difficulty_score() }}
            <small>(1.0 = dễ, 10.0 = khó)</small>
            {% if form.difficulty_score.errors %}
                {% for error in form.difficulty_score.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.duration_seconds.label }}<br>
            {{ form.duration_seconds() }}
            <small>(giây)</small>
            {% if form.duration_seconds.errors %}
                {% for error in form.duration_seconds.errors %}
                    <br><span style="color:red;">{{ error }}</span>
                {% endfor %}
            {% endif %}
        </p>
        
        <p>
            {{ form.total_moves.label }}<br>
            {{ form.total_moves() }}
        </p>
        
        <p>
            {{ form.pass_threshold.label }}<br>
            {{ form.pass_threshold() }}
            <small>(%)</small>
        </p>
        
        <p>
            {{ form.reference_video_url.label }}<br>
            {{ form.reference_video_url(size=60) }}
            <br><small>Nhập URL video mẫu chuẩn (YouTube, Vimeo, hoặc link trực tiếp)</small>
        </p>
        
        <p>
            <button type="submit" style="padding:10px 20px; background:#28a745; color:white; border:none; border-radius:4px; cursor:pointer;">Tạo bài võ (Nháp)</button>
        </p>
    </form>
    
    <hr>
    <p><a href="{{ url_for('instructor.routines') }}">← Quay lại</a></p>
</body>
</html>
"""


# ===================================================================
# FILE: templates/instructor/routine_detail.html
# ===================================================================
"""
<!DOCTYPE html>
<html>
<head>
    <title>Chi tiết bài võ</title>
    <style>
        .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .info-table td { padding: 10px; border: 1px solid #ddd; }
        .info-table td:first-child { background: #f8f9fa; font-weight: bold; width: 200px; }
        .criteria-list { margin: 15px 0; }
        .criteria-item { padding: 10px; margin: 5px 0; background: #f8f9fa; border-left: 3px solid #007bff; }
        .action-btn { padding: 8px 15px; margin: 5px; text-decoration: none; border-radius: 4px; display: inline-block; }
        .btn-success { background: #28a745; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-primary { background: #007bff; color: white; }
    </style>
</head>
<body>
    <h1>CHI TIẾT BÀI VÕ</h1>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div style="padding:10px; margin:10px 0; border:1px solid; 
                     background-color:{{ '#d4edda' if category == 'success' else '#f8d7da' }}; 
                     border-color:{{ '#c3e6cb' if category == 'success' else '#f5c6cb' }}; 
                     color:{{ '#155724' if category == 'success' else '#721c24' }};">
                    <strong>[{{ category|upper }}]</strong> {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    <table class="info-table">
        <tr>
            <td>Trạng thái</td>
            <td>
                <strong style="color:{{ '#28a745' if routine.is_published else '#ffc107' }};">
                    {{ '✅ Đã xuất bản' if routine.is_published else '📝 Nháp' }}
                </strong>
            </td>
        </tr>
        <tr>
            <td>Mã bài võ</td>
            <td><strong>{{ routine.routine_code }}</strong></td>
        </tr>
        <tr>
            <td>Tên bài võ</td>
            <td><strong>{{ routine.routine_name }}</strong></td>
        </tr>
        <tr>
            <td>Mô tả</td>
            <td>{{ routine.description or 'Không có' }}</td>
        </tr>
        <tr>
            <td>Binh khí</td>
            <td>{{ routine.weapon.weapon_name_vi }} ({{ routine.weapon.weapon_name_en }})</td>
        </tr>
        <tr>
            <td>Cấp độ</td>
            <td>{{ routine.level }}</td>
        </tr>
        <tr>
            <td>Độ khó</td>
            <td>{{ routine.difficulty_score }}/10</td>
        </tr>
        <tr>
            <td>Thời lượng</td>
            <td>{{ routine.duration_seconds }} giây ({{ (routine.duration_seconds / 60)|round(1) }} phút)</td>
        </tr>
        <tr>
            <td>Số động tác</td>
            <td>{{ routine.total_moves }}</td>
        </tr>
        <tr>
            <td>Ngưỡng đạt</td>
            <td>{{ routine.pass_threshold }}%</td>
        </tr>
        <tr>
            <td>Video mẫu</td>
            <td>
                {% if routine.reference_video_url %}
                    <a href="{{ routine.reference_video_url }}" target="_blank">🎥 Xem video</a>
                {% else %}
                    Chưa có
                {% endif %}
            </td>
        </tr>
        <tr>
            <td>Ngày tạo</td>
            <td>{{ routine.created_at.strftime('%d/%m/%Y %H:%M') }}</td>
        </tr>
        <tr>
            <td>Cập nhật lần cuối</td>
            <td>{{ routine.updated_at.strftime('%d/%m/%Y %H:%M') }}</td>
        </tr>
    </table>
    
    <h2>TIÊU CHÍ ĐÁNH GIÁ (Tổng: {{ total_weight }}%)</h2>
    <p><a href="{{ url_for('instructor.add_criteria', routine_id=routine.routine_id) }}" class="action-btn btn-primary">+ Thêm tiêu chí</a></p>
    
    {% if criteria %}
        <div class="criteria-list">
            {% for c in criteria %}
            <div class="criteria-item">
                <strong>{{ c.criteria_name }}</strong> ({{ c.criteria_code }}) - <strong>{{ c.weight_percentage }}%</strong>
                {% if c.description %}<br><small>{{ c.description }}</small>{% endif %}
                {% if c.evaluation_method %}<br><small>Phương pháp: {{ c.evaluation_method }}</small>{% endif %}
                <form method="POST" action="{{ url_for('instructor.delete_criteria', criteria_id=c.criteria_id) }}" style="display:inline; float:right;">
                    {{ csrf_token() }}
                    <button type="submit" onclick="return confirm('Xác nhận xóa?')" style="padding:3px 8px; background:#dc3545; color:white; border:none; border-radius:3px; cursor:pointer;">Xóa</button>
                </form>
            </div>
            {% endfor %}
        </div>
        {% if total_weight < 100 %}
        <p style="color:#ffc107;">⚠️ Tổng trọng số chưa đủ 100% (còn {{ 100 - total_weight }}%)</p>
        {% elif total_weight > 100 %}
        <p style="color:#dc3545;">❌ Tổng trọng số vượt quá 100%!</p>
        {% else %}
        <p style="color:#28a745;">✅ Tổng trọng số hợp lệ (100%)</p>
        {% endif %}
    {% else %}
        <p>Chưa có tiêu chí đánh giá nào</p>
    {% endif %}
    
    <hr>
    <h2>THAO TÁC</h2>
    <p>
        <a href="{{ url_for('instructor.edit_routine', routine_id=routine.routine_id) }}" class="action-btn btn-primary">✏️ Sửa bài võ</a>
        
        {% if routine.is_published %}
            <form method="POST" action="{{ url_for('instructor.unpublish_routine', routine_id=routine.routine_id) }}" style="display:inline;">
                {{ csrf_token() }}
                <button type="submit" class="action-btn btn-warning">📝 Gỡ xuất bản</button>
            </form>
        {% else %}
            <form method="POST" action="{{ url_for('instructor.publish_routine', routine_id=routine.routine_id) }}" style="display:inline;">
                {{ csrf_token() }}
                <button type="submit" class="action-btn btn-success">✅ Xuất bản</button>
            </form>
        {% endif %}
        
        <form method="POST" action="{{ url_for('instructor.delete_routine', routine_id=routine.routine_id) }}" style="display:inline;">
            {{ csrf_token() }}
            <button type="submit" onclick="return confirm('Xác nhận xóa bài võ?')" class="action-btn btn-danger">🗑️ Xóa</button>
        </form>
    </p>
    
    <hr>
    <p><a href="{{ url_for('instructor.routines') }}">← Về danh sách</a></p>
</body>
</html>
"""