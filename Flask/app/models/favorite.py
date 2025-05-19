"""Favorite Model"""
from ..core.extensions import db
from datetime import datetime
import enum

# --- Enums for Favorite ---
class FavoriteTypeEnum(enum.Enum):
    job = 'job'
    freelancer = 'freelancer'
    employer = 'employer'

# --- Favorite Model ---
class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), db.ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True, comment='收藏者用户ID')
    favorite_type = db.Column(db.Enum(FavoriteTypeEnum), nullable=False, index=True, comment='收藏类型')
    target_id = db.Column(db.BigInteger().with_variant(db.Integer, "sqlite"), nullable=False, index=True, comment='被收藏对象的ID') # Indexing target_id can be useful
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # --- Relationships ---
    user = db.relationship('User', back_populates='favorites')
    # Polymorphic relationship for target is complex to set up with FK constraints.
    # Usually handled in service layer: query based on favorite_type and target_id.

    # --- Constraints ---
    __table_args__ = (db.UniqueConstraint('user_id', 'favorite_type', 'target_id', name='uk_user_type_target'),)

    def __repr__(self):
        return f'<Favorite {self.id} (User: {self.user_id}, Type: {self.favorite_type.name}, Target: {self.target_id})>'
