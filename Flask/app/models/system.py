"""System Configuration Model"""
from ..core.extensions import db
from datetime import datetime

# --- SystemConfig Model ---
class SystemConfig(db.Model):
    __tablename__ = 'system_configs'

    config_key = db.Column(db.String(100), primary_key=True, comment='配置项键名')
    config_value = db.Column(db.Text, nullable=False, comment='配置项值')
    description = db.Column(db.String(255), nullable=True, comment='配置项描述')
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'
