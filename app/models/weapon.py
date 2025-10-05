from . import db
from datetime import datetime

class Weapon(db.Model):
    __tablename__ = 'weapons'
    
    weapon_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    weapon_name_vi = db.Column(db.String(50), unique=True, nullable=False)
    weapon_name_en = db.Column(db.String(50), unique=True, nullable=False)
    weapon_code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    routines = db.relationship('MartialRoutine', backref='weapon', lazy=True)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(weapon_code.in_(['SWORD', 'SPEAR', 'STAFF', 'HALBERD']), name='chk_weapons_code'),
        db.Index('idx_weapons_active', 'is_active'),
        db.Index('idx_weapons_order', 'display_order'),
    )
