"""User Service Logic"""
from ..models.user import User
from ..core.extensions import db # Assuming db is your SQLAlchemy instance
from ..core.extensions import bcrypt # Only if User model doesn't handle hashing
from flask_jwt_extended import create_access_token
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException, AuthenticationException
import uuid # For generating UUIDs, if needed for new users
from datetime import datetime # For last_login_at, registered_at
from flask import current_app # For logging
import re # For phone number validation
import os
from werkzeug.utils import secure_filename

class UserService:

    def __init__(self):
        pass

    @staticmethod
    def register(phone_number, password, user_type, nickname=None):
        # This method seems to be an older or alternative stub,
        # We will focus on register_user called by the API.
        pass

    @staticmethod
    def login(phone_number, password):
        # This method seems to be an older or alternative stub,
        # We will focus on login_user called by the API.
        pass

    def register_user(self, phone_number, password, user_type='freelancer'):
        """
        注册新用户
        :param phone_number: 手机号
        :param password: 密码
        :param user_type: 用户类型，默认为零工
        :return: (user, token) 注册成功的用户对象和JWT token
        :raises: BusinessException
        """
        # 验证输入
        if not phone_number or not password:
            raise BusinessException("手机号和密码不能为空")
        
        if len(password) < 6:
            raise BusinessException("密码长度不能少于6个字符")
        
        # 检查手机号是否已存在
        if User.query.filter_by(phone_number=phone_number).first():
            raise BusinessException("该手机号已被注册")
        
        # 验证用户类型
        if user_type not in ['freelancer', 'employer']:
            user_type = 'freelancer'  # 默认为零工
        
        # 创建用户
        new_user = User(
            uuid=str(uuid.uuid4()),
            phone_number=phone_number,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
            current_role=user_type,
            available_roles=[user_type],
            status='active',
            registered_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # 创建访问令牌
            access_token = create_access_token(identity=str(new_user.uuid))
            
            return new_user, access_token
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"用户注册失败: {str(e)}")
            raise BusinessException("用户注册失败")

    def login_user(self, phone_number, password):
        """
        用户登录
        :param phone_number: 手机号
        :param password: 密码
        :return: (user, token) 登录成功的用户对象和JWT token
        :raises: AuthenticationException, BusinessException
        """
        # 验证输入
        if not phone_number or not password:
            raise BusinessException("手机号和密码不能为空")
        
        # 查找用户
        user = User.query.filter_by(phone_number=phone_number).first()
        if not user:
            raise AuthenticationException("用户不存在或密码错误")
        
        # 验证密码
        if not bcrypt.check_password_hash(user.password_hash, password):
            raise AuthenticationException("用户不存在或密码错误")
        
        # 检查账户状态
        if user.status != 'active':
            raise AuthenticationException("账户已被禁用")
        
        # 更新最后登录时间
        user.last_login_at = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        
        # 创建访问令牌，使用UUID作为身份标识
        access_token = create_access_token(identity=str(user.uuid))
        
        return user, access_token

    def get_user_by_id(self, user_id):
        """
        根据ID或UUID获取用户
        :param user_id: 用户ID或UUID
        :return: 用户对象
        :raises: NotFoundException
        """
        # 检查是否为UUID格式
        try:
            if isinstance(user_id, str) and len(user_id) > 10:
                # 可能是UUID，尝试验证格式
                uuid_obj = uuid.UUID(user_id)
                user = User.query.filter_by(uuid=str(uuid_obj)).first()
            else:
                # 尝试作为数字ID处理
                user = User.query.get(user_id)
        except ValueError:
            # 如果UUID格式验证失败，尝试作为普通ID
            user = User.query.get(user_id)
        
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found.")
        return user

    def get_user_by_uuid(self, user_uuid):
        """
        通过UUID获取用户
        :param user_uuid: 用户UUID字符串
        :return: 用户对象
        :raises: NotFoundException
        """
        try:
            user = User.query.filter_by(uuid=user_uuid).first()
            if not user:
                raise NotFoundException(f"User with UUID {user_uuid} not found.")
            return user
        except Exception as e:
            current_app.logger.error(f"获取用户失败: {str(e)}")
            raise NotFoundException(f"Failed to find user with UUID {user_uuid}")

    # Placeholder for update_profile, assuming it will be part of a more general UserProfileService later
    # For now, let's add a simple nickname update here if needed by a basic User API
    def update_user_details(self, user_id, data):
        """更新用户信息 (示例: 昵称, 邮箱等直接在User表上的字段)"""
        user = self.get_user_by_id(user_id) # Reuses the above method with NotFoundException

        if 'email' in data:
            # Add validation for email format if necessary
            existing_user_with_email = User.query.filter(User.id != user_id, User.email == data['email']).first()
            if existing_user_with_email:
                raise InvalidUsageException(message="该邮箱已被其他用户使用。", error_code=40901) # Similar to phone conflict
            user.email = data['email']
        
        # current_role and available_roles changes should be handled with more care,
        # potentially by an admin or through specific role change requests, not a generic update.

        # Update other simple fields directly on User model if any
        # e.g., if nickname was on User model directly (it's in profile tables)

        try:
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            # Log error e
            raise BusinessException(message=f"更新用户信息失败: {str(e)}", status_code=500, error_code=50001)

    # Methods like change_password, password_reset_request, password_reset_confirm
    # would also go here.

    def change_password(self, user_id, old_password, new_password):
        """
        修改用户密码
        :param user_id: 用户ID
        :param old_password: 旧密码
        :param new_password: 新密码
        :raises: NotFoundException, AuthenticationException, BusinessException
        """
        if not old_password or not new_password:
            raise BusinessException("旧密码和新密码不能为空")
        
        if len(new_password) < 6:
            raise BusinessException("新密码长度不能少于6个字符")
        
        # 获取用户
        user = self.get_user_by_id(user_id)
        
        # 验证旧密码
        if not bcrypt.check_password_hash(user.password_hash, old_password):
            raise AuthenticationException("旧密码不正确")
        
        # 更新密码
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        return True

    def update_user(self, user_id, data):
        """
        更新用户基本信息
        :param user_id: 用户ID
        :param data: 要更新的数据
        :return: 更新后的用户对象
        :raises: NotFoundException, BusinessException
        """
        if not data:
            raise BusinessException("请求数据不能为空")
        
        # 获取用户
        user = self.get_user_by_id(user_id)
        
        # 更新可修改的字段
        allowed_fields = ['email', 'nickname']
        
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return user

    def switch_role(self, user_id, role):
        """
        切换用户当前角色
        :param user_id: 用户ID
        :param role: 要切换的角色
        :return: 更新后的用户对象
        :raises: NotFoundException, BusinessException
        """
        if not role:
            raise BusinessException("角色不能为空")
        
        # 获取用户
        user = self.get_user_by_id(user_id)
        
        # 检查角色是否可用
        if role not in user.available_roles:
            raise BusinessException(f"用户没有 {role} 角色权限")
        
        # 更新当前角色
        user.current_role = role
        db.session.commit()
        
        return user

    def get_public_user_profile_by_uuid(self, user_uuid):
        """
        通过UUID获取用户的公开信息
        :param user_uuid: 用户的UUID
        :return: 用户对象 (将在API层通过UserPublicSchema序列化为公开信息)
        :raises: NotFoundException
        """
        try:
            # 确保user_uuid是一个有效的UUID格式
            valid_uuid = str(uuid.UUID(str(user_uuid)))
            
            # 通过UUID查找用户
            user = User.query.filter_by(uuid=valid_uuid).first()
            if not user:
                raise NotFoundException(message=f"未找到UUID为 {user_uuid} 的用户")
            
            # 返回用户对象，由API层使用UserPublicSchema处理为公开信息
            return user
        except ValueError:
            # 如果提供的UUID格式无效
            raise InvalidUsageException(message=f"无效的UUID格式: {user_uuid}")
        except Exception as e:
            current_app.logger.error(f"查找用户UUID失败: {str(e)}")
            raise BusinessException(message="获取用户公开信息失败", internal_message=str(e))

    def user_to_dict(self, user):
        """
        将User对象转换为字典，用于API响应
        :param user: User对象
        :return: 用户信息字典
        """
        if not user:
            return None
        
        return {
            'id': user.id,
            'uuid': user.uuid,
            'phone_number': user.phone_number,
            'email': user.email,
            'nickname': user.nickname if hasattr(user, 'nickname') else None,
            'current_role': user.current_role,
            'available_roles': user.available_roles,
            'status': user.status,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'registered_at': user.registered_at.isoformat() if user.registered_at else None
        }

# Instantiate the service for easy import
user_service = UserService()
