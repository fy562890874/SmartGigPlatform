from ..models.verification import VerificationRecord, VerificationRecordStatusEnum, VerificationProfileTypeEnum
from ..models.profile import FreelancerProfile, EmployerProfile, VerificationStatusEnum
from ..models.user import User, UserStatusEnum
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime

class AdminVerificationService:
    def get_pending_verifications(self, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取待审核的认证记录列表（管理员专用）
        :param filters: 过滤条件，例如profile_type
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式
        :return: 分页后的认证记录列表
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        try:
            # 构建基础查询 - 获取待审核认证记录
            query = VerificationRecord.query.filter_by(status=VerificationRecordStatusEnum.pending)
            
            # 预加载用户信息以优化性能
            query = query.options(
                joinedload(VerificationRecord.user)
            )
            
            # 应用过滤条件
            if 'profile_type' in filters and filters['profile_type']:
                try:
                    profile_type_enum = VerificationProfileTypeEnum(filters['profile_type'])
                    query = query.filter(VerificationRecord.profile_type == profile_type_enum)
                except ValueError:
                    # 无效的档案类型，忽略此过滤条件
                    current_app.logger.warning(f"管理员认证查询：无效的档案类型 {filters['profile_type']}")
                    pass
            
            # 应用排序
            if sort_by == 'created_at_asc':
                query = query.order_by(VerificationRecord.created_at.asc())  # 旧的先审核
            elif sort_by == 'created_at_desc':
                query = query.order_by(VerificationRecord.created_at.desc())
            else:
                # 默认按创建时间升序 (FIFO审核)
                query = query.order_by(VerificationRecord.created_at.asc())
            
            # 执行分页
            paginated_verifications = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 记录日志
            current_app.logger.info(f"管理员查询待审核认证列表，过滤条件: {filters}, 页码: {page}, 每页: {per_page}, 总数: {paginated_verifications.total}")
            
            return paginated_verifications
            
        except Exception as e:
            current_app.logger.error(f"管理员获取待审核认证列表时出错: {str(e)}")
            raise BusinessException(message=f"获取待审核认证列表失败: {str(e)}", status_code=500, error_code=50001)
    
    def review_verification_request(self, admin_user_id, verification_id, review_data):
        """
        审核认证申请（管理员专用）
        :param admin_user_id: 管理员ID
        :param verification_id: 认证记录ID
        :param review_data: 审核数据，包含action (approve/reject)，rejection_reason (如果拒绝)
        :return: 更新后的认证记录对象
        """
        from flask import current_app
        
        # 验证审核动作
        if 'action' not in review_data or not review_data['action']:
            raise InvalidUsageException(message="审核动作不能为空", error_code=40001)
        
        if review_data['action'] not in ['approve', 'reject']:
            raise InvalidUsageException(message="无效的审核动作，必须是 approve 或 reject", error_code=40002)
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 查询认证记录
                record = VerificationRecord.query.options(joinedload(VerificationRecord.user)).get(verification_id)
                if not record:
                    raise NotFoundException(message="认证记录不存在", error_code=40401)
                
                # 验证认证记录状态必须是待审核
                if record.status != VerificationRecordStatusEnum.pending:
                    raise InvalidUsageException(
                        message=f"该认证申请不在待审核状态，当前状态: {record.status.value}", 
                        error_code=40003
                    )
                
                # 更新认证记录
                record.reviewer_id = admin_user_id
                record.reviewed_at = datetime.utcnow()
                
                if review_data['action'] == 'approve':
                    record.status = VerificationRecordStatusEnum.approved
                    
                    # 更新用户档案的认证状态
                    self._update_profile_verification_status(record, VerificationStatusEnum.verified)
                    
                    # 如果是首次认证通过且用户状态是待认证，则更新用户状态为活跃
                    if record.user.status == UserStatusEnum.pending_verification:
                        record.user.status = UserStatusEnum.active
                        record.user.updated_at = datetime.utcnow()
                    
                    current_app.logger.info(f"管理员 {admin_user_id} 批准了用户 {record.user_id} 的认证申请 {verification_id}")
                    
                elif review_data['action'] == 'reject':
                    record.status = VerificationRecordStatusEnum.rejected
                    
                    # 记录拒绝原因
                    rejection_reason = review_data.get('rejection_reason', '管理员审核未通过')
                    record.rejection_reason = rejection_reason
                    
                    # 更新用户档案的认证状态
                    self._update_profile_verification_status(record, VerificationStatusEnum.rejected)
                    
                    current_app.logger.info(f"管理员 {admin_user_id} 拒绝了用户 {record.user_id} 的认证申请 {verification_id}，原因: {rejection_reason}")
            
            # 记录管理员操作日志
            # TODO: self._log_admin_action(admin_user_id, f"{review_data['action']}_verification", verification_id)
            
            # 通知用户审核结果
            self._notify_verification_review_result(record, review_data['action'], review_data.get('rejection_reason'))
            
            return record
            
        except Exception as e:
            # 异常时事务已经回滚
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException):
                current_app.logger.error(f"审核认证申请时出错: {str(e)}")
                raise BusinessException(message=f"审核认证失败: {str(e)}", status_code=500, error_code=50002)
            raise e
    
    def _update_profile_verification_status(self, verification_record, new_status):
        """
        更新用户档案的认证状态
        :param verification_record: 认证记录对象
        :param new_status: 新的认证状态
        """
        from flask import current_app
        
        user = verification_record.user
        if not user:
            current_app.logger.error(f"认证记录 {verification_record.id} 关联的用户不存在")
            return
        
        # 根据档案类型更新相应档案
        if verification_record.profile_type == VerificationProfileTypeEnum.freelancer:
            profile = user.freelancer_profile
            if profile:
                profile.verification_status = new_status
                profile.verification_record_id = verification_record.id
            else:
                current_app.logger.warning(f"用户 {user.id} 没有零工档案")
                
        elif verification_record.profile_type in [
            VerificationProfileTypeEnum.employer_individual, 
            VerificationProfileTypeEnum.employer_company
        ]:
            profile = user.employer_profile
            if profile:
                profile.verification_status = new_status
                profile.verification_record_id = verification_record.id
            else:
                current_app.logger.warning(f"用户 {user.id} 没有雇主档案")
                
        else:
            current_app.logger.warning(f"未识别的档案类型: {verification_record.profile_type}")
    
    def _notify_verification_review_result(self, verification_record, action, rejection_reason=None):
        """
        通知用户认证审核结果
        :param verification_record: 认证记录对象
        :param action: 审核动作 (approve/reject)
        :param rejection_reason: 拒绝原因（如果是拒绝）
        """
        from flask import current_app
        
        try:
            # 调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            notification_title = "认证审核结果通知"
            
            profile_type_name = verification_record.profile_type.value
            if profile_type_name == 'freelancer':
                profile_type_display = "零工"
            elif profile_type_name == 'employer_individual':
                profile_type_display = "个人雇主"
            elif profile_type_name == 'employer_company':
                profile_type_display = "企业雇主"
            else:
                profile_type_display = profile_type_name
            
            if action == 'approve':
                notification_content = f"您的{profile_type_display}认证已通过审核。"
            else:  # reject
                notification_content = f"您的{profile_type_display}认证未通过审核。"
                if rejection_reason:
                    notification_content += f" 原因: {rejection_reason}"
            
            notification_data = {
                'notification_type': 'verification_review_result',
                'title': notification_title,
                'content': notification_content,
                'related_resource_type': 'verification',
                'related_resource_id': verification_record.id
            }
            
            notification_service.create_notification(verification_record.user_id, notification_data)
            current_app.logger.info(f"已向用户 {verification_record.user_id} 发送认证审核结果通知")
            
        except Exception as e:
            current_app.logger.error(f"发送认证审核结果通知失败: {str(e)}")
            # 通知失败不阻断主流程


# 服务实例
admin_verification_service = AdminVerificationService() 