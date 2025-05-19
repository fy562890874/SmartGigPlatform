from ..models.system_config import SystemConfig
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException
from datetime import datetime

class SystemConfigService:
    def get_all_configs(self):
        """
        获取所有系统配置
        :return: 系统配置列表
        """
        from flask import current_app
        
        try:
            configs = SystemConfig.query.order_by(SystemConfig.config_key.asc()).all()
            return configs
        except Exception as e:
            current_app.logger.error(f"获取所有系统配置时出错: {str(e)}")
            raise BusinessException(message=f"获取系统配置失败: {str(e)}", status_code=500, error_code=50001)
    
    def get_config_by_key(self, config_key):
        """
        根据键名获取特定系统配置
        :param config_key: 配置键名
        :return: 系统配置对象
        """
        from flask import current_app
        
        config = SystemConfig.query.get(config_key)
        if not config:
            raise NotFoundException(message="配置项未找到", error_code=40401)
        
        return config
    
    def create_or_update_config(self, admin_user_id, config_key, data):
        """
        创建或更新系统配置
        :param admin_user_id: 管理员用户ID
        :param config_key: 配置键名
        :param data: 配置数据，包含config_value, description(可选)
        :return: 创建或更新后的系统配置对象
        """
        from flask import current_app
        
        if not data.get('config_value'):
            raise BusinessException(message="配置值不能为空", status_code=400, error_code=40001)
        
        try:
            # 查找是否存在
            config = SystemConfig.query.get(config_key)
            is_new = False
            
            if config:
                # 更新
                config.config_value = data['config_value']
                if 'description' in data and data['description']:
                    config.description = data['description']
                config.updated_at = datetime.utcnow()
            else:
                # 创建
                is_new = True
                config = SystemConfig(
                    config_key=config_key,
                    config_value=data['config_value'],
                    description=data.get('description', '')
                )
                db.session.add(config)
            
            # 记录审计日志（如果系统中有审计日志模块）
            # TODO: self._log_admin_action(admin_user_id, "update_system_config" if not is_new else "create_system_config", config_key)
            
            db.session.commit()
            
            current_app.logger.info(f"管理员 {admin_user_id} {'创建' if is_new else '更新'}了系统配置 {config_key}")
            
            return config, is_new
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新系统配置时出错: {str(e)}")
            raise BusinessException(message=f"更新系统配置失败: {str(e)}", status_code=500, error_code=50002)
    
    def _log_admin_action(self, admin_user_id, action, target):
        """
        记录管理员操作到审计日志
        :param admin_user_id: 管理员ID
        :param action: 操作类型
        :param target: 操作目标
        """
        # 这里可以实现审计日志记录
        # 如果有AuditLog模型，可以在这里创建日志记录
        pass


# 服务实例
system_config_service = SystemConfigService() 