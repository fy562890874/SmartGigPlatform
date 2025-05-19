from ..models.job import Job, JobStatusEnum
from ..models.user import User
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime

class AdminJobService:
    def get_jobs_pending_review(self, page=1, per_page=10, sort_by=None):
        """
        获取待审核工作列表（管理员专用）
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式
        :return: 分页后的工作列表
        """
        from flask import current_app
        
        try:
            # 构建基础查询 - 获取待审核工作
            query = Job.query.filter_by(status=JobStatusEnum.pending_review)
            
            # 预加载雇主信息以优化性能
            query = query.options(
                joinedload(Job.employer).joinedload(User.employer_profile)
            )
            
            # 应用排序
            if sort_by == 'created_at_asc':
                query = query.order_by(Job.created_at.asc())  # 旧的先审核
            elif sort_by == 'created_at_desc':
                query = query.order_by(Job.created_at.desc())
            elif sort_by == 'salary_desc':
                query = query.order_by(Job.salary_amount.desc())
            else:
                # 默认按创建时间升序 (FIFO审核)
                query = query.order_by(Job.created_at.asc())
            
            # 执行分页
            paginated_jobs = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 记录日志
            current_app.logger.info(f"管理员查询待审核工作列表，页码: {page}, 每页: {per_page}, 总数: {paginated_jobs.total}")
            
            return paginated_jobs
            
        except Exception as e:
            current_app.logger.error(f"管理员获取待审核工作列表时出错: {str(e)}")
            raise BusinessException(message=f"获取待审核工作列表失败: {str(e)}", status_code=500, error_code=50001)
    
    def review_job_posting(self, admin_user_id, job_id, review_data):
        """
        审核工作发布（管理员专用）
        :param admin_user_id: 管理员ID
        :param job_id: 工作ID
        :param review_data: 审核数据，包含action (approve/reject)，rejection_reason (如果拒绝)
        :return: 更新后的工作对象
        """
        from flask import current_app
        
        # 验证审核动作
        if 'action' not in review_data or not review_data['action']:
            raise InvalidUsageException(message="审核动作不能为空", error_code=40001)
        
        if review_data['action'] not in ['approve', 'reject']:
            raise InvalidUsageException(message="无效的审核动作，必须是 approve 或 reject", error_code=40002)
        
        try:
            # 查询工作
            job = Job.query.get(job_id)
            if not job:
                raise NotFoundException(message="工作不存在", error_code=40401)
            
            # 验证工作状态必须是待审核
            if job.status != JobStatusEnum.pending_review:
                raise InvalidUsageException(message=f"该工作不在待审核状态，当前状态: {job.status.value}", error_code=40003)
            
            # 更新工作状态
            if review_data['action'] == 'approve':
                job.status = JobStatusEnum.active
                job.approved_at = datetime.utcnow()
                job.approver_id = admin_user_id  # 假设Job模型有这个字段
                
                current_app.logger.info(f"管理员 {admin_user_id} 批准了工作 {job_id}")
                
            elif review_data['action'] == 'reject':
                job.status = JobStatusEnum.rejected
                
                # 记录拒绝原因
                rejection_reason = review_data.get('rejection_reason', '管理员审核未通过')
                
                # 如果有专门的拒绝原因字段，使用该字段
                if hasattr(job, 'rejection_reason'):
                    job.rejection_reason = rejection_reason
                # 否则使用取消原因字段，但这语义上不太合适
                elif hasattr(job, 'cancellation_reason'):
                    job.cancellation_reason = rejection_reason
                
                job.updated_at = datetime.utcnow()
                
                current_app.logger.info(f"管理员 {admin_user_id} 拒绝了工作 {job_id}，原因: {rejection_reason}")
            
            # 提交更改
            db.session.commit()
            
            # 记录管理员操作日志
            # TODO: self._log_admin_action(admin_user_id, f"{review_data['action']}_job", job_id)
            
            # 通知雇主审核结果
            employer_user_id = job.employer_user_id
            self._notify_job_review_result(employer_user_id, job, review_data['action'], review_data.get('rejection_reason'))
            
            return job
            
        except Exception as e:
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException):
                db.session.rollback()
                current_app.logger.error(f"审核工作发布时出错: {str(e)}")
                raise BusinessException(message=f"审核工作失败: {str(e)}", status_code=500, error_code=50002)
            raise e
    
    def _notify_job_review_result(self, employer_user_id, job, action, rejection_reason=None):
        """
        通知雇主工作审核结果
        :param employer_user_id: 雇主用户ID
        :param job: 工作对象
        :param action: 审核动作 (approve/reject)
        :param rejection_reason: 拒绝原因（如果是拒绝）
        """
        from flask import current_app
        
        try:
            # 调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            notification_title = "工作发布审核结果通知"
            
            if action == 'approve':
                notification_content = f"您发布的工作 \"{job.title}\" 已通过审核，现在已在平台上线。"
            else:  # reject
                notification_content = f"您发布的工作 \"{job.title}\" 未通过审核。"
                if rejection_reason:
                    notification_content += f" 原因: {rejection_reason}"
            
            notification_data = {
                'notification_type': 'job_review_result',
                'title': notification_title,
                'content': notification_content,
                'related_resource_type': 'job',
                'related_resource_id': job.id
            }
            
            notification_service.create_notification(employer_user_id, notification_data)
            current_app.logger.info(f"已向雇主 {employer_user_id} 发送工作审核结果通知")
            
        except Exception as e:
            current_app.logger.error(f"发送工作审核结果通知失败: {str(e)}")
            # 通知失败不阻断主流程


# 服务实例
admin_job_service = AdminJobService() 