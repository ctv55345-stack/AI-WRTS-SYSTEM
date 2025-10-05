from . import db
from datetime import datetime

class AuthToken(db.Model):
    __tablename__ = 'auth_tokens'
    
    token_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    token_hash = db.Column(db.String(255), unique=True, nullable=False)
    token_type = db.Column(db.Enum('access', 'refresh', 'reset_password', 'email_verification', name='token_type_enum'), nullable=False)
    device_info = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    is_revoked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(expires_at > created_at, name='chk_tokens_expiry'),
        db.Index('idx_tokens_user', 'user_id'),
        db.Index('idx_tokens_type', 'token_type'),
        db.Index('idx_tokens_expires', 'expires_at'),
        db.Index('idx_tokens_hash', 'token_hash'),
    )
