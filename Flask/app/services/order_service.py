from ..core.extensions import db
from ..models.order import Order, OrderStatusEnum, CancellationPartyEnum, ConfirmationStatusEnum
from ..models.user import User
from ..models.job import Job, JobApplication # Corrected import for JobApplication
from ..utils.exceptions import NotFoundException, AuthorizationException, InvalidUsageException, BusinessException
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone # Ensure timezone is imported
from decimal import Decimal, InvalidOperation
from flask import current_app

class OrderService:

    def get_order_by_id(self, order_id, user_id):
        """
        Get an order by its ID.
        Ensures the requesting user is part of the order (either freelancer or employer).
        """
        order = Order.query.options(
            joinedload(Order.job),
            joinedload(Order.application),
            joinedload(Order.freelancer),
            joinedload(Order.employer)
        ).get(order_id)

        if not order:
            raise NotFoundException("订单不存在。")

        if order.freelancer_user_id != user_id and order.employer_user_id != user_id:
            # Potentially allow admin access later
            raise AuthorizationException("您无权查看此订单。")
        
        return order

    def get_orders_for_user(self, user_id, user_role, filters=None, page=1, per_page=20, sort_by=None):
        """
        Get orders for a specific user (either as freelancer or employer).
        Supports filtering, pagination, and sorting.
        """
        query = Order.query.options(
            joinedload(Order.job),
            joinedload(Order.freelancer),
            joinedload(Order.employer)
        )

        if user_role == 'freelancer':
            query = query.filter(Order.freelancer_user_id == user_id)
        elif user_role == 'employer':
            query = query.filter(Order.employer_user_id == user_id)
        else:
            # This case should ideally not happen if role is determined correctly
            raise AuthorizationException("无效的用户角色，无法查询订单。")

        if filters:
            if filters.get('status'):
                query = query.filter(Order.status == filters['status'])
            # Add more filters as needed: job_id, date ranges, etc.

        # TODO: Implement sorting based on sort_by parameter
        # Example: if sort_by == 'created_at_desc': query = query.order_by(Order.created_at.desc())
        # Default sort or handle based on input
        query = query.order_by(Order.created_at.desc())

        paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        return paginated_orders

    def create_order_from_application(self, application: JobApplication, employer_user_id: int):
        """
        Creates an order when a job application is accepted.
        This method would typically be called by JobApplicationService.
        """
        if not application:
            raise InvalidUsageException("无效的申请信息。")
        
        job = Job.query.get(application.job_id)
        if not job:
            raise NotFoundException("关联的工作不存在。")

        if job.employer_user_id != employer_user_id:
            raise AuthorizationException("操作的雇主与工作发布者不符。")

        # Ensure an order doesn't already exist for this application
        existing_order = Order.query.filter_by(application_id=application.id).first()
        if existing_order:
            raise InvalidUsageException(f"申请ID {application.id} 已创建订单 {existing_order.id}。")

        # Calculate order amount, platform fee, freelancer income
        # This logic might be complex based on job salary_type, duration, platform fee rules
        # For simplicity, let's assume job.salary_amount is the total order_amount for now.
        # Actual calculation should be robust.
        
        current_salary_amount = job.salary_amount
        if current_salary_amount is None:
            raise InvalidUsageException("工作薪资金额 (job.salary_amount) 为空，无法创建订单。")

        try:
            # Ensure order_amount is Decimal
            order_amount_decimal = Decimal(str(current_salary_amount))
        except InvalidOperation:
            raise InvalidUsageException(
                f"工作薪资金额 '{current_salary_amount}' 格式无效，无法转换为Decimal。"
            )

        # Define platform_fee_rate as Decimal directly
        platform_fee_rate_decimal = Decimal('0.10')

        # Perform calculation with two Decimal objects
        platform_fee = order_amount_decimal * platform_fee_rate_decimal
        freelancer_income = order_amount_decimal - platform_fee

        if order_amount_decimal <= Decimal('0'): # Comparison with Decimal
            raise InvalidUsageException("订单金额必须为正数。")


        new_order = Order(
            job_id=application.job_id,
            application_id=application.id,
            freelancer_user_id=application.freelancer_user_id,
            employer_user_id=employer_user_id, # or job.employer_user_id
            order_amount=order_amount_decimal,
            platform_fee=platform_fee,
            freelancer_income=freelancer_income,
            start_time_scheduled=job.start_time, # Or from application if it specifies negotiated times
            end_time_scheduled=job.end_time,   # Or from application
            status=OrderStatusEnum.pending_start.value,
            freelancer_confirmation_status=ConfirmationStatusEnum.pending.value, # Or 'confirmed' if auto-confirmed by freelancer apply
            employer_confirmation_status=ConfirmationStatusEnum.confirmed.value, # Employer accepts, so confirmed by them
            # confirmation_deadline: Could be set based on start_time_scheduled
        )
        
        db.session.add(new_order)
        try:
            # Update job status or accepted_people count if necessary (handled in JobApplicationService or here)
            # job.accepted_people = (job.accepted_people or 0) + 1
            # if job.accepted_people >= job.required_people:
            #     job.status = JobStatusEnum.filled.value # Assuming JobStatusEnum exists
            
            db.session.commit()
            return new_order
        except Exception as e:
            db.session.rollback()
            # Log error e
            raise BusinessException(message=f"从申请创建订单失败: {str(e)}", status_code=500)

    def process_order_action(self, order_id: int, user_id: int, user_role: str, action_data: dict):
        """
        Processes various actions on an order based on user role and current order status.
        """
        order = self.get_order_by_id(order_id, user_id) # Ensures user has basic access
        action = action_data.get('action')

        if not action:
            raise InvalidUsageException("操作类型 (action) 不能为空。")

        if action == 'start_work':
            return self._freelancer_start_work(order, user_id)
        elif action == 'complete_work':
            # Actual times might be passed in action_data
            actual_times_data = {
                'start_time_actual': action_data.get('start_time_actual'),
                'end_time_actual': action_data.get('end_time_actual')
            }
            return self._freelancer_complete_work(order, user_id, actual_times_data)
        elif action == 'confirm_completion':
            return self._employer_confirm_completion(order, user_id)
        elif action == 'cancel_order':
            cancellation_reason = action_data.get('cancellation_reason')
            return self._cancel_order(order, user_id, user_role, cancellation_reason)
        # Add 'dispute_completion' later
        else:
            raise InvalidUsageException(f"不支持的操作类型: {action}")

    def _freelancer_start_work(self, order: Order, freelancer_id: int):
        if order.freelancer_user_id != freelancer_id:
            raise AuthorizationException("只有零工本人才能开始工作。")
        
        # 获取当前状态的字符串值以进行比较
        current_status = order.status
        if hasattr(order.status, 'value'):
            current_status = order.status.value
        
        if current_status != OrderStatusEnum.pending_start.value:
            raise InvalidUsageException(f"订单状态为 {current_status}，无法开始工作。")

        # 直接使用枚举对象设置状态
        order.status = OrderStatusEnum.in_progress
        order.start_time_actual = datetime.now(timezone.utc) # Explicitly UTC aware
        order.freelancer_confirmation_status = ConfirmationStatusEnum.confirmed
        
        try:
            db.session.commit()
            return order
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"开始工作失败: {str(e)}", status_code=500)

    def _freelancer_complete_work(self, order: Order, freelancer_id: int, actual_times_data: dict = None):
        if order.freelancer_user_id != freelancer_id:
            raise AuthorizationException("只有零工本人才能完成工作。")
        
        # 获取当前状态的字符串值以进行比较
        current_status = order.status
        if hasattr(order.status, 'value'):
            current_status = order.status.value
        
        if current_status != OrderStatusEnum.in_progress.value:
            raise InvalidUsageException(f"订单状态为 {current_status}，无法完成工作。")

        # 直接使用枚举对象设置状态
        order.status = OrderStatusEnum.pending_confirmation
        
        # Ensure order.start_time_actual (from DB or previous step) is UTC aware
        if not order.start_time_actual:
            raise InvalidUsageException("实际开始时间未记录。请先开始工作或在完成工作时提供。")
        
        start_actual_to_use = order.start_time_actual
        if start_actual_to_use.tzinfo is None:
            start_actual_to_use = start_actual_to_use.replace(tzinfo=timezone.utc)

        # Default end time to now (UTC)
        end_actual_to_use = datetime.now(timezone.utc)

        if actual_times_data:
            start_actual_str = actual_times_data.get('start_time_actual')
            end_actual_str = actual_times_data.get('end_time_actual')

            if start_actual_str:
                try:
                    dt_obj = datetime.fromisoformat(start_actual_str.replace('Z', '+00:00'))
                    # Convert to UTC if it has timezone info, otherwise assume UTC
                    start_actual_to_use = dt_obj.astimezone(timezone.utc) if dt_obj.tzinfo else dt_obj.replace(tzinfo=timezone.utc)
                except ValueError:
                    raise InvalidUsageException(f"提供的实际开始时间格式无效: {start_actual_str}")
            
            if end_actual_str:
                try:
                    dt_obj = datetime.fromisoformat(end_actual_str.replace('Z', '+00:00'))
                    # Convert to UTC if it has timezone info, otherwise assume UTC
                    end_actual_to_use = dt_obj.astimezone(timezone.utc) if dt_obj.tzinfo else dt_obj.replace(tzinfo=timezone.utc)
                except ValueError:
                    raise InvalidUsageException(f"提供的实际结束时间格式无效: {end_actual_str}")
        
        # Now, both start_actual_to_use and end_actual_to_use are UTC aware
        if start_actual_to_use >= end_actual_to_use:
            raise InvalidUsageException("实际结束时间必须晚于实际开始时间。")

        order.start_time_actual = start_actual_to_use
        order.end_time_actual = end_actual_to_use
        duration = order.end_time_actual - order.start_time_actual
        order.work_duration_actual = round(duration.total_seconds() / 3600, 2) # Duration in hours

        order.confirmation_deadline = datetime.now(timezone.utc) + timedelta(days=7)
        
        try:
            db.session.commit()
            return order
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"完成工作操作失败: {str(e)}", status_code=500)

    def _employer_confirm_completion(self, order: Order, employer_id: int):
        if order.employer_user_id != employer_id:
            raise AuthorizationException("只有雇主本人才能确认完成。")
        
        # 获取当前状态的字符串值以进行比较
        current_status = order.status
        if hasattr(order.status, 'value'):
            current_status = order.status.value
        
        if current_status != OrderStatusEnum.pending_confirmation.value:
            raise InvalidUsageException(f"订单状态为 {current_status}，无法确认完成。")

        # 直接使用枚举对象设置状态
        order.status = OrderStatusEnum.completed
        order.employer_confirmation_status = ConfirmationStatusEnum.confirmed
        order.confirmation_deadline = None # Clear deadline
        
        try:
            db.session.commit()
            # TODO: Trigger payment processing / fund release to freelancer
            # TODO: Send notifications (e.g., to freelancer, for evaluation)
            return order
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"确认工作完成失败: {str(e)}", status_code=500)

    def _cancel_order(self, order: Order, user_id: int, user_role: str, reason: str = None):
        can_cancel = False
        
        # 获取当前状态的字符串值以进行比较
        current_status = order.status
        if hasattr(order.status, 'value'):
            current_status = order.status.value
        
        if user_role == 'freelancer' and order.freelancer_user_id == user_id:
            cancelling_party = CancellationPartyEnum.freelancer
            # Freelancer can cancel if order is pending_start
            if current_status == OrderStatusEnum.pending_start.value:
                can_cancel = True
        elif user_role == 'employer' and order.employer_user_id == user_id:
            cancelling_party = CancellationPartyEnum.employer
            # Employer can cancel if order is pending_start
            if current_status == OrderStatusEnum.pending_start.value:
                can_cancel = True
        # Add admin/platform cancellation logic later

        if not can_cancel:
            raise InvalidUsageException(f"订单状态为 {current_status} 或您无权取消此订单。")
        
        if not reason:
            raise InvalidUsageException("取消订单必须提供原因。")

        # 直接使用枚举对象设置状态
        order.status = OrderStatusEnum.cancelled
        order.cancellation_reason = reason
        order.cancelled_by = cancelling_party
        order.confirmation_deadline = None

        try:
            db.session.commit()
            # TODO: Handle potential refunds if payment was made
            # TODO: Update job status (e.g., reopen if it was 'filled' by this order)
            # TODO: Send notifications
            return order
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"取消订单失败: {str(e)}", status_code=500)

    def update_order_actual_times(self, order_id: int, user_id: int, data: dict):
        """
        Allows a freelancer to update the actual start and end times of an order.
        Typically used if not provided during the 'complete_work' action or needs correction.
        """
        order = self.get_order_by_id(order_id, user_id)

        if order.freelancer_user_id != user_id:
            raise AuthorizationException("只有零工本人才能更新实际工作时间。")

        # 获取当前状态的字符串值以进行比较
        current_status = order.status
        if hasattr(order.status, 'value'):
            current_status = order.status.value
        
        # Allow updates for in_progress or pending_confirmation orders
        if current_status not in [OrderStatusEnum.in_progress.value, OrderStatusEnum.pending_confirmation.value]:
            raise InvalidUsageException(f"订单状态为 {current_status}，无法更新实际工作时间。")

        start_actual_str = data.get('start_time_actual')
        end_actual_str = data.get('end_time_actual')

        if not start_actual_str or not end_actual_str:
            raise InvalidUsageException("实际开始和结束时间都必须提供。")

        try:
            # 将ISO 8601格式字符串转换为datetime对象，确保时区处理正确
            dt_start_str = str(start_actual_str).replace('Z', '+00:00')
            dt_end_str = str(end_actual_str).replace('Z', '+00:00')
            
            try:
                dt_start_obj = datetime.fromisoformat(dt_start_str)
            except ValueError:
                raise InvalidUsageException(f"无效的开始时间格式: {start_actual_str}。请使用ISO 8601格式 (例如: 2023-01-01T12:00:00Z)")
            
            try:
                dt_end_obj = datetime.fromisoformat(dt_end_str)
            except ValueError:
                raise InvalidUsageException(f"无效的结束时间格式: {end_actual_str}。请使用ISO 8601格式 (例如: 2023-01-01T18:00:00Z)")
            
            # 转换为UTC时区
            dt_start = dt_start_obj.astimezone(timezone.utc) if dt_start_obj.tzinfo else dt_start_obj.replace(tzinfo=timezone.utc)
            dt_end = dt_end_obj.astimezone(timezone.utc) if dt_end_obj.tzinfo else dt_end_obj.replace(tzinfo=timezone.utc)
        except Exception as e:
            current_app.logger.error(f"处理订单时间时发生错误: {str(e)}")
            raise InvalidUsageException(f"时间格式处理失败。请确保使用有效的ISO 8601格式。")

        if dt_start >= dt_end:
            raise InvalidUsageException("实际结束时间必须晚于实际开始时间。")

        # 检查开始时间是否早于计划开始时间太多（例如，超过24小时）
        if order.start_time_scheduled and dt_start < order.start_time_scheduled - timedelta(hours=24):
            raise InvalidUsageException("实际开始时间不能早于计划开始时间24小时以上。")

        order.start_time_actual = dt_start
        order.end_time_actual = dt_end
        duration = dt_end - dt_start
        order.work_duration_actual = round(duration.total_seconds() / 3600, 2)

        try:
            db.session.commit()
            return order
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新订单实际时间失败: {str(e)}")
            raise BusinessException(message=f"更新订单实际时间失败: {str(e)}", status_code=500)


order_service = OrderService()