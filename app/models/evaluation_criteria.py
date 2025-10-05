from . import db

class EvaluationCriteria(db.Model):
    __tablename__ = 'evaluation_criteria'
    
    criteria_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    routine_id = db.Column(db.Integer, db.ForeignKey('martial_routines.routine_id', ondelete='CASCADE'), nullable=False)
    criteria_name = db.Column(db.String(100), nullable=False)
    criteria_code = db.Column(db.String(50), nullable=False)
    weight_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    description = db.Column(db.Text)
    evaluation_method = db.Column(db.String(50))
    display_order = db.Column(db.Integer, nullable=False, default=0)
    
    # Constraints
    __table_args__ = (
        db.CheckConstraint(db.and_(weight_percentage > 0, weight_percentage <= 100), name='chk_criteria_weight'),
        db.UniqueConstraint('routine_id', 'criteria_code', name='uq_routine_code'),
        db.Index('idx_criteria_routine', 'routine_id'),
    )
