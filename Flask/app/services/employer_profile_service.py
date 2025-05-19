import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

from ..models.user import User
from ..models.profile import EmployerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, BusinessException, AuthorizationException
from ..services.user_service import user_service

class EmployerProfileService:
    def __init__(self):
        self.user_service = user_service

    def get_profile_by_user_id(self, user_id):
        """
        通过用户ID获取雇主档案
        :param user_id: 用户ID
        :return: 雇主档案对象
        :raises: NotFoundException
        """
        # 确保用户存在
        user = self.user_service.get_user_by_id(user_id)
        
        # 查找雇主档案
        profile = EmployerProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            raise NotFoundException(f"用户ID {user_id} 没有雇主档案")
        
        return profile

    def create_profile(self, user_id, data):
        """
        创建雇主档案
        :param user_id: 用户ID
        :param data: 档案数据
        :return: 新创建的雇主档案
        """
        # 确保用户存在
        user = self.user_service.get_user_by_id(user_id)
        
        # 检查是否已有档案
        existing_profile = EmployerProfile.query.filter_by(user_id=user.id).first()
        if existing_profile:
            raise BusinessException("雇主档案已存在，请使用更新接口")
        
        # 创建新档案
        profile = EmployerProfile(
            user_id=user.id,
            profile_type=data.get('profile_type', 'individual'),
            real_name=data.get('real_name', ''),
            nickname=data.get('nickname', ''),
            contact_email=data.get('contact_email', ''),
            contact_phone=data.get('contact_phone', ''),
            location_province=data.get('location_province', ''),
            location_city=data.get('location_city', ''),
            location_district=data.get('location_district', ''),
            location_address=data.get('location_address', ''),
            bio=data.get('bio', ''),
            hiring_preference=data.get('hiring_preference', ''),
            website_url=data.get('website_url', ''),
            linkedin_url=data.get('linkedin_url', '')
        )
        
        # 如果是企业类型，添加企业信息
        if data.get('profile_type') == 'company':
            profile.company_name = data.get('company_name', '')
            profile.business_license_number = data.get('business_license_number', '')
            profile.company_address = data.get('company_address', '')
            profile.company_description = data.get('company_description', '')
        
        db.session.add(profile)
        db.session.commit()
        
        return profile

    def update_profile(self, user_id, data):
        """
        更新雇主档案
        :param user_id: 用户ID
        :param data: 更新数据
        :return: 更新后的雇主档案
        """
        # 获取现有档案
        profile = self.get_profile_by_user_id(user_id)
        
        # 更新基本字段
        profile.real_name = data.get('real_name', profile.real_name)
        profile.nickname = data.get('nickname', profile.nickname)
        profile.contact_email = data.get('contact_email', profile.contact_email)
        profile.contact_phone = data.get('contact_phone', profile.contact_phone)
        profile.location_province = data.get('location_province', profile.location_province)
        profile.location_city = data.get('location_city', profile.location_city)
        profile.location_district = data.get('location_district', profile.location_district)
        profile.location_address = data.get('location_address', profile.location_address)
        profile.bio = data.get('bio', profile.bio)
        profile.hiring_preference = data.get('hiring_preference', profile.hiring_preference)
        profile.website_url = data.get('website_url', profile.website_url)
        profile.linkedin_url = data.get('linkedin_url', profile.linkedin_url)
        
        # 如果是企业类型，更新企业信息
        if profile.profile_type == 'company':
            profile.company_name = data.get('company_name', profile.company_name)
            profile.business_license_number = data.get('business_license_number', profile.business_license_number)
            profile.company_address = data.get('company_address', profile.company_address)
            profile.company_description = data.get('company_description', profile.company_description)
        
        db.session.commit()
        
        return profile

    def upload_avatar(self, user_id, avatar_file):
        """
        上传雇主头像
        :param user_id: 用户ID
        :param avatar_file: 上传的头像文件
        :return: 头像URL
        """
        # 确保用户存在
        user = self.user_service.get_user_by_id(user_id)
        
        # 检查文件类型
        if not self._allowed_image_file(avatar_file.filename):
            raise BusinessException("只允许上传JPG、JPEG、PNG格式的图片")
        
        # 保存文件
        filename = secure_filename(f"avatar_{user.uuid}_{uuid.uuid4()}.{avatar_file.filename.rsplit('.', 1)[1].lower()}")
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        avatar_file.save(file_path)
        
        # 获取URL
        avatar_url = f"/uploads/avatars/{filename}"
        
        # 更新用户档案
        try:
            employer_profile = self.get_profile_by_user_id(user_id)
            employer_profile.avatar_url = avatar_url
            db.session.commit()
        except NotFoundException:
            # 如果用户没有档案，创建一个基本档案
            self.create_profile(user_id, {
                'profile_type': 'individual',
                'avatar_url': avatar_url
            })
        
        return avatar_url

    def upload_license(self, user_id, license_file):
        """
        上传营业执照
        :param user_id: 用户ID
        :param license_file: 上传的执照文件
        :return: 执照URL
        """
        # 确保用户存在
        user = self.user_service.get_user_by_id(user_id)
        
        # 检查文件类型
        if not self._allowed_image_file(license_file.filename):
            raise BusinessException("只允许上传JPG、JPEG、PNG格式的图片")
        
        # 保存文件
        filename = secure_filename(f"license_{user.uuid}_{uuid.uuid4()}.{license_file.filename.rsplit('.', 1)[1].lower()}")
        upload_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'licenses')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        license_file.save(file_path)
        
        # 获取URL
        license_url = f"/uploads/licenses/{filename}"
        
        # 更新用户档案
        try:
            employer_profile = self.get_profile_by_user_id(user_id)
            # 确保是企业类型
            if employer_profile.profile_type != 'company':
                employer_profile.profile_type = 'company'
            employer_profile.business_license_photo_url = license_url
            db.session.commit()
        except NotFoundException:
            # 如果用户没有档案，创建一个基本档案
            self.create_profile(user_id, {
                'profile_type': 'company',
                'business_license_photo_url': license_url
            })
        
        return license_url

    def _allowed_image_file(self, filename):
        """检查是否为允许的图片文件类型"""
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# 创建服务实例
employer_profile_service = EmployerProfileService() 