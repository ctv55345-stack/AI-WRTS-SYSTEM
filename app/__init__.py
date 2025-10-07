from flask import Flask
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from app.models import db
from app.config import Config
from datetime import datetime


migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)
    
    # CSRF Configuration (uncomment để tắt CSRF tạm thời nếu cần debug)
    # app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Jinja global: now()
    @app.context_processor
    def inject_now():
        return {
            'now': lambda: datetime.utcnow()
        }
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.student_videos import student_videos_bp
    from app.routes.instructor import instructor_bp
    from app.routes.admin import admin_bp
    from app.routes.manager import manager_bp
    from app.routes.shared import shared_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(student_videos_bp)
    app.register_blueprint(instructor_bp, url_prefix='/instructor')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(shared_bp)
    
    return app