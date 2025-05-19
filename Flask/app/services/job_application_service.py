from ..models.user import User
from ..models.job import Job, JobStatusEnum, JobApplication, JobApplicationStatusEnum
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, InvalidUsageException, AuthorizationException, BusinessException
from datetime import datetime
from .order_service import order_service # Import OrderService

class JobApplicationService:
    def create_job_application(self, freelancer_user_id, job_id, data):
        freelancer = User.query.get(freelancer_user_id)
        if not freelancer or 'freelancer' not in freelancer.available_roles:
            raise AuthorizationException(message="仅零工用户可以申请工作。", error_code=40302)

        job = Job.query.get(job_id)
        if not job:
            raise NotFoundException(message="工作不存在或已被删除。", error_code=40401)

        if job.status.value != JobStatusEnum.active.value:
            raise InvalidUsageException(message=f"该工作当前状态为 {job.status}，无法申请。", error_code=40902)
        
        if job.application_deadline and job.application_deadline < datetime.utcnow():
            raise InvalidUsageException(message="已过该工作的申请截止日期。", error_code=40903)
            
        if job.employer_user_id == freelancer_user_id:
            raise InvalidUsageException(message="您不能申请自己发布的工作。", error_code=40001)

        existing_application = JobApplication.query.filter_by(
            job_id=job_id,
            freelancer_user_id=freelancer_user_id
        ).first()

        if existing_application:
            # Allow re-application if previously cancelled by freelancer? Business rule.
            if existing_application.status == JobApplicationStatusEnum.cancelled_by_freelancer.value:
                # Potentially reactivate or create new. For now, let's treat as conflict.
                 raise InvalidUsageException(message="您曾取消过对此工作的申请，如需重新申请请联系客服或后续开放此功能。", error_code=40901) 
            raise InvalidUsageException(message="您已申请过该工作。", error_code=40901)

        application_message = data.get('application_message')

        new_application = JobApplication(
            job_id=job.id, # Use job.id
            freelancer_user_id=freelancer_user_id,
            employer_user_id=job.employer_user_id, # Store employer_user_id from job
            apply_message=application_message, # Changed from application_message
            status=JobApplicationStatusEnum.pending.value
        )
        db.session.add(new_application)
        try:
            db.session.commit()
            return new_application
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"申请工作失败: {str(e)}", status_code=500, error_code=50001)

    def get_applications_for_job(self, job_id, employer_user_id, page=1, per_page=10, filters=None):
        job = Job.query.get(job_id)
        if not job:
            raise NotFoundException(message="工作不存在。", error_code=40401)
        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权查看此工作的申请列表。", error_code=40301)
        
        query = JobApplication.query.filter_by(job_id=job_id)
        if filters and filters.get('status'):
            query = query.filter(JobApplication.status == filters['status'])
        
        query = query.order_by(JobApplication.created_at.desc())
        applications = query.paginate(page=page, per_page=per_page, error_out=False)
        return applications

    def get_applications_by_freelancer(self, freelancer_user_id, page=1, per_page=10, filters=None):
        user = User.query.get(freelancer_user_id)
        if not user:
            raise NotFoundException(message="用户不存在。")
            
        query = JobApplication.query.filter_by(freelancer_user_id=freelancer_user_id)
        if filters and filters.get('status'):
            query = query.filter(JobApplication.status == filters['status'])
            
        query = query.order_by(JobApplication.created_at.desc())
        applications = query.paginate(page=page, per_page=per_page, error_out=False)
        return applications

    def get_application_by_id(self, application_id, current_user_id):
        application = JobApplication.query.get(application_id)
        if not application:
            raise NotFoundException(message="申请记录不存在。", error_code=40401)
        
        # Security check: user must be freelancer or employer related to this application
        if not (application.freelancer_user_id == current_user_id or application.job.employer_user_id == current_user_id):
            raise AuthorizationException(message="您无权查看此申请详情。", error_code=40301)
        return application

    def _can_employer_modify_application(self, application, employer_user_id):
        if application.job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权修改此申请的状态。", error_code=40301)
        return True

    def _can_freelancer_modify_application(self, application, freelancer_user_id):
        if application.freelancer_user_id != freelancer_user_id:
            raise AuthorizationException(message="您无权修改此申请的状态。", error_code=40301)
        return True

    def process_application(self, application_id, employer_user_id, new_status_str, reason=None):
        application = self.get_application_by_id(application_id, employer_user_id) # verify auth through here
        self._can_employer_modify_application(application, employer_user_id)

        job = application.job
        valid_employer_statuses = [JobApplicationStatusEnum.accepted.value, JobApplicationStatusEnum.rejected.value]
        # JobApplicationStatusEnum.interview_scheduled.value, etc. can be added

        created_order = None # Initialize created_order

        if new_status_str not in valid_employer_statuses:
            raise InvalidUsageException(message=f"雇主不能将申请状态更改为 '{new_status_str}'。")

        # 获取当前状态的字符串值以进行比较
        current_status = application.status
        if hasattr(application.status, 'value'):
            current_status = application.status.value
        else:
            current_status = str(application.status)

        if current_status not in [JobApplicationStatusEnum.pending.value, JobApplicationStatusEnum.viewed.value]:
            # Add more states if employer can re-process, e.g. from 'interview_scheduled'
            raise InvalidUsageException(message=f"申请当前状态为 '{current_status}'，无法直接更改为 '{new_status_str}'。", error_code=40902)

        if new_status_str == JobApplicationStatusEnum.accepted.value:
            if job.accepted_people >= job.required_people:
                raise InvalidUsageException(message="该工作已招满，无法接受更多申请。", error_code=40904)
            try:
                created_order = order_service.create_order_from_application(application, employer_user_id)
            except BusinessException as be:
                db.session.rollback()
                raise InvalidUsageException(message=f"接受申请时创建订单失败: {be.message}", error_code=be.error_code or 400)
            except Exception as e:
                db.session.rollback()
                raise BusinessException(message=f"接受申请时创建订单遇到意外错误: {str(e)}", status_code=500)
            
            job.accepted_people += 1
            # 检查是否需要更新工作状态
            # if job.accepted_people >= job.required_people:
            #     job.status = JobStatusEnum.filled
        
        # 尝试转换为枚举对象，如果model需要枚举对象
        try:
            # 这里假设application.status需要枚举对象
            application.status = JobApplicationStatusEnum(new_status_str)
        except (ValueError, TypeError):
            # 如果转换失败，直接使用字符串
            application.status = new_status_str
        
        if new_status_str == JobApplicationStatusEnum.rejected.value and reason:
            application.rejection_reason = reason
        else:
            application.rejection_reason = None # Clear if not rejected or no reason
        
        application.processed_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return_data = {'application': application, 'order': None}
            if new_status_str == JobApplicationStatusEnum.accepted.value and created_order is not None:
                return_data['order'] = created_order
            return return_data
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"处理申请状态失败: {str(e)}", status_code=500, error_code=50001)

    def cancel_application_by_freelancer(self, application_id, freelancer_user_id, reason=None):
        application = self.get_application_by_id(application_id, freelancer_user_id) # verify auth
        self._can_freelancer_modify_application(application, freelancer_user_id)

        job = application.job
        allowed_to_cancel_statuses_values = [ # Changed variable name for clarity
            JobApplicationStatusEnum.pending.value,
            JobApplicationStatusEnum.viewed.value,
            JobApplicationStatusEnum.accepted.value # Freelancer can cancel an accepted offer
        ]

        # 获取当前状态的字符串值以进行比较
        current_status = application.status
        if hasattr(application.status, 'value'):
            current_status = application.status.value
        else:
            current_status = str(application.status)

        if current_status not in allowed_to_cancel_statuses_values:
            raise InvalidUsageException(message=f"申请当前状态为 '{current_status}'，无法取消。", error_code=40902)

        if current_status == JobApplicationStatusEnum.accepted.value:
             if job.accepted_people > 0:
                job.accepted_people -=1
             # If an order was created, it might need to be voided/cancelled. 
             # This is complex and depends on order_service capabilities and business rules.
             # For now, we only adjust accepted_people.
             # if application.order_id:
             #    order_service.cancel_order(application.order_id, freelancer_user_id, actor_role='freelancer', reason="申请人取消已接受的申请")

        # 尝试转换为枚举对象，如果model需要枚举对象
        try:
            # 这里假设application.status需要枚举对象
            application.status = JobApplicationStatusEnum.cancelled_by_freelancer
        except (ValueError, TypeError):
            # 如果转换失败，直接使用字符串
            application.status = JobApplicationStatusEnum.cancelled_by_freelancer.value
        
        # application.cancellation_reason = reason # If model has cancellation_reason
        if reason: # Use rejection_reason temporarily if no dedicated field
            application.rejection_reason = reason 

        application.processed_at = datetime.utcnow()
        try:
            db.session.commit()
            return application
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"取消申请失败: {str(e)}", status_code=500, error_code=50001)

job_application_service = JobApplicationService()