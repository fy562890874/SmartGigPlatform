"""User Service Logic"""
from ..models.user import User
from ..core.extensions import db # Assuming db is your SQLAlchemy instance
from ..core.extensions import bcrypt # Only if User model doesn't handle hashing
from flask_jwt_extended import create_access_token
from ..utils.exceptions import AuthenticationException, InvalidUsageException, NotFoundException, BusinessException
import uuid # For generating UUIDs, if needed for new users
from datetime import datetime # For last_login_at, registered_at
from flask import current_app # For logging
import re # For phone number validation

class UserService:

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

    def register_user(self, data):
        """
        用户注册服务
        :param data: 包含 phone_number, password, 和可选的 user_type 的字典
        :return: 创建的 User 对象
        :raises: InvalidUsageException, BusinessException
        """
        phone_number = data.get('phone_number')
        password = data.get('password')
        user_type = data.get('user_type', 'freelancer')

        if not phone_number or not password:
            raise InvalidUsageException("手机号和密码不能为空")

        if not re.match(r"^1\d{10}$", phone_number): # Changed from ^1\\\\d{10}$
            raise InvalidUsageException("无效的手机号码格式")

        if len(password) < 6:
            raise InvalidUsageException("密码长度至少为6位")

        if User.query.filter_by(phone_number=phone_number).first():
            raise BusinessException("该手机号已被注册", status_code=409)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(
            # Assuming User model has a uuid field, uncomment if so
            # uuid=str(uuid.uuid4()),
            phone_number=phone_number,
            password_hash=hashed_password, # Ensure User model has 'password_hash' field
            current_role=user_type,
            available_roles=[user_type], # Initialize available_roles with the current role
            status='active', # Default status
            registered_at=datetime.utcnow()
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            # db.session.refresh(new_user) # Optional: to get ID if auto-generated and needed immediately
            return new_user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during user registration: {str(e)}")
            raise BusinessException("注册过程中发生错误，请重试")

    def login_user(self, phone_number, password):
        """
        用户登录服务
        :param phone_number: User's phone number
        :param password: User's password
        :return: Tuple (User object, access_token)
        :raises: AuthenticationException, InvalidUsageException
        """
        if not phone_number or not password:
            raise InvalidUsageException("手机号和密码不能为空")

        user = User.query.filter_by(phone_number=phone_number).first()

        # Ensure User model has 'password_hash' field and 'status' field
        if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):
            if getattr(user, 'status', 'active') == 'inactive': # Or 'banned', etc.
                raise AuthenticationException("账号已被禁用")

            user.last_login_at = datetime.utcnow()
            try:
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error updating last_login_at for user {user.id if hasattr(user, 'id') else phone_number}: {str(e)}")
                # Continue with login even if last_login_at update fails

            # 统一使用uuid作为身份标识
            if not hasattr(user, 'uuid') or not user.uuid:
                # 如果用户没有uuid，生成一个并保存
                user.uuid = str(uuid.uuid4())
                try:
                    db.session.commit()
                    current_app.logger.info(f"Generated and saved new UUID for user {user.id}: {user.uuid}")
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Failed to save generated UUID: {str(e)}")
                    # 继续使用临时生成的UUID
            
            # 创建令牌时统一使用uuid
            access_token = create_access_token(identity=str(user.uuid))
            return user, access_token
        else:
            raise AuthenticationException("手机号或密码错误")

    def get_user_by_id(self, user_id):
        user = User.query.get(user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found.")
        return user

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
        user = self.get_user_by_id(user_id)
        if not bcrypt.check_password_hash(user.password_hash, old_password):
            raise InvalidUsageException(message="旧密码不正确。", error_code=40002)
        if len(new_password) < 6:
            raise InvalidUsageException(message="新密码长度不能少于6位。", error_code=40003)
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"修改密码失败: {str(e)}")
            raise BusinessException(message="修改密码时发生错误", internal_message=str(e))
        return user # Or None/True depending on desired return

    def switch_role(self, user_id, new_role):
        """
        切换用户当前角色
        :param user_id: 从JWT中获取的用户ID
        :param new_role: 要切换到的新角色
        :return: 更新后的用户对象
        :raises: InvalidUsageException, NotFoundException, BusinessException
        """
        user = self.get_user_by_id(user_id)  # 这会在用户不存在时抛出NotFoundException
        
        # 验证新角色是否是用户可用角色之一
        if new_role not in user.available_roles:
            raise InvalidUsageException(
                message=f"无效的角色切换请求: '{new_role}' 不是用户的可用角色之一", 
                error_code=40004
            )
        
        # 验证新角色是否是有效的主要角色
        if new_role not in ['freelancer', 'employer']:
            raise InvalidUsageException(
                message=f"目标角色 '{new_role}' 无效。只允许切换到 'freelancer' 或 'employer'", 
                error_code=40005
            )
        
        # 如果角色相同，则无需切换
        if user.current_role == new_role:
            return user
        
        # 执行角色切换
        user.current_role = new_role
        try:
            db.session.commit()
            current_app.logger.info(f"用户 {user_id} 成功切换到角色: {new_role}")
            return user
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"切换用户 {user_id} 角色失败: {str(e)}")
            raise BusinessException(message="切换用户角色时发生错误", internal_message=str(e))

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

# Instantiate the service for easy import
user_service = UserService()
