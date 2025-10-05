from . import db
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'
    
    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    role_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    permissions = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(role_code.in_(['STUDENT', 'INSTRUCTOR', 'ADMIN', 'MANAGER']), name='chk_roles_code'),
        db.Index('idx_role_active', 'is_active'),
    )
