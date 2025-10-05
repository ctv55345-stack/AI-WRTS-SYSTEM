from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Import tất cả models để migrate nhận diện
from .role import Role
from .user import User
from .weapon import Weapon
from .class_model import Class
from .class_enrollment import ClassEnrollment
from .class_schedule import ClassSchedule
from .martial_routine import MartialRoutine
from .evaluation_criteria import EvaluationCriteria
from .assignment import Assignment
from .training_video import TrainingVideo
from .ai_analysis import AIAnalysisResult
from .manual_evaluation import ManualEvaluation
from .training_history import TrainingHistory
from .goal import Goal
from .notification import Notification
from .exam import Exam
from .exam_result import ExamResult
from .feedback import Feedback
from .auth_token import AuthToken
