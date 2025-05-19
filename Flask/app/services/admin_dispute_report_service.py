from ..models.dispute import Dispute, DisputeStatusEnum
from ..models.report import Report, ReportTypeEnum, ReportStatusEnum
from ..models.order import Order, OrderStatusEnum
from ..models.job import Job
from ..models.user import User
from ..models.evaluation import Evaluation
from ..models.message import Message
from ..models.payment import Payment, PaymentStatusEnum
from ..models.wallet import UserWallet, WalletTransaction, TransactionTypeEnum
from ..services.dispute_report_service import dispute_service, report_service
from ..services.admin_user_service import admin_user_service
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime
from decimal import Decimal

class AdminDisputeService:
    def get_pending_disputes(self, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取待处理的争议列表（管理员专用）
        :param filters: 过滤条件，例如status
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式
        :return: 分页后的争议列表
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        try:
            # 构建基础查询 - 获取需要管理员处理的争议
            # 包括pending, negotiating, 和platform_intervening状态的争议
            query = Dispute.query.filter(Dispute.status.in_([
                DisputeStatusEnum.pending,
                DisputeStatusEnum.negotiating,
                DisputeStatusEnum.platform_intervening
            ]))
            
            # 预加载关联信息以优化性能
            query = query.options(
                joinedload(Dispute.order).joinedload(Order.job),
                joinedload(Dispute.initiator)
            )
            
            # 应用过滤条件
            if 'status' in filters and filters['status']:
                try:
                    status_enum = DisputeStatusEnum(filters['status'])
                    # 只有需要管理员处理的状态可以被过滤
                    if status_enum in [DisputeStatusEnum.pending, DisputeStatusEnum.negotiating, DisputeStatusEnum.platform_intervening]:
                        query = query.filter(Dispute.status == status_enum)
                except ValueError:
                    # 无效的状态值，忽略此过滤条件
                    current_app.logger.warning(f"管理员争议查询：无效的状态值 {filters['status']}")
                    pass
            
            # 应用排序
            if sort_by == 'created_at_asc':
                query = query.order_by(Dispute.created_at.asc())  # 旧的先处理
            elif sort_by == 'created_at_desc':
                query = query.order_by(Dispute.created_at.desc())
            elif sort_by == 'status':
                # 按状态优先级排序：platform_intervening > negotiating > pending
                query = query.order_by(Dispute.status.desc(), Dispute.created_at.asc())
            else:
                # 默认按创建时间升序 (FIFO处理)
                query = query.order_by(Dispute.created_at.asc())
            
            # 执行分页
            paginated_disputes = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 记录日志
            current_app.logger.info(f"管理员查询待处理争议列表，过滤条件: {filters}, 页码: {page}, 每页: {per_page}, 总数: {paginated_disputes.total}")
            
            return paginated_disputes
            
        except Exception as e:
            current_app.logger.error(f"管理员获取待处理争议列表时出错: {str(e)}")
            raise BusinessException(message=f"获取待处理争议列表失败: {str(e)}", status_code=500, error_code=50001)
    
    def mediate_dispute(self, admin_user_id, dispute_id, mediation_data):
        """
        处理争议（管理员专用）
        :param admin_user_id: 管理员ID
        :param dispute_id: 争议ID
        :param mediation_data: 处理数据，包含status, resolution_result
        :return: 更新后的争议对象
        """
        from flask import current_app
        
        # 验证状态值
        if 'status' not in mediation_data or not mediation_data['status']:
            raise InvalidUsageException(message="争议状态不能为空", error_code=40001)
        
        try:
            new_status = DisputeStatusEnum(mediation_data['status'])
            # 只允许设置为这些状态
            if new_status not in [DisputeStatusEnum.resolved, DisputeStatusEnum.closed, DisputeStatusEnum.platform_intervening]:
                valid_statuses = [
                    DisputeStatusEnum.resolved.value, 
                    DisputeStatusEnum.closed.value, 
                    DisputeStatusEnum.platform_intervening.value
                ]
                raise InvalidUsageException(
                    message=f"无效的争议状态，管理员只能设置争议为: {', '.join(valid_statuses)}", 
                    error_code=40002
                )
        except ValueError:
            valid_statuses = [
                DisputeStatusEnum.resolved.value, 
                DisputeStatusEnum.closed.value, 
                DisputeStatusEnum.platform_intervening.value
            ]
            raise InvalidUsageException(
                message=f"无效的争议状态，有效值为: {', '.join(valid_statuses)}", 
                error_code=40003
            )
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 查询争议
                dispute = Dispute.query.options(
                    joinedload(Dispute.order)
                ).get(dispute_id)
                
                if not dispute:
                    raise NotFoundException(message="争议记录不存在", error_code=40401)
                
                # 只有特定状态的争议才能被管理员处理
                if dispute.status not in [DisputeStatusEnum.pending, DisputeStatusEnum.negotiating, DisputeStatusEnum.platform_intervening]:
                    raise InvalidUsageException(
                        message=f"该争议当前状态 ({dispute.status.value}) 不允许管理员处理", 
                        error_code=40004
                    )
                
                # 更新争议状态
                old_status = dispute.status
                dispute.status = new_status
                
                # 记录解决结果（如果提供）
                if 'resolution_result' in mediation_data and mediation_data['resolution_result']:
                    dispute.resolution_result = mediation_data['resolution_result']
                
                # 记录处理管理员
                dispute.platform_mediator_id = admin_user_id
                
                # 如果状态为已解决或已关闭，记录解决时间
                if new_status in [DisputeStatusEnum.resolved, DisputeStatusEnum.closed]:
                    dispute.resolved_at = datetime.utcnow()
                    
                    # 更新订单状态
                    order = dispute.order
                    if not order:
                        raise BusinessException(message="争议关联的订单不存在", status_code=500, error_code=50002)
                    
                    # 执行争议解决后的特定操作
                    if 'resolution_action' in mediation_data:
                        resolution_action = mediation_data['resolution_action']
                        
                        # 根据解决动作执行不同操作
                        if resolution_action == 'complete_order':
                            # 将订单标记为完成
                            order.status = OrderStatusEnum.completed
                            order.completed_at = datetime.utcnow()
                            # TODO: 可能需要触发完成后的结算流程
                            
                        elif resolution_action == 'cancel_order':
                            # 将订单取消
                            order.status = OrderStatusEnum.cancelled
                            order.cancellation_reason = f"争议处理结果：{dispute.resolution_result}"
                            
                        elif resolution_action == 'partial_refund' and 'refund_amount' in mediation_data:
                            # 部分退款
                            self._process_refund(
                                order, 
                                Decimal(str(mediation_data['refund_amount'])), 
                                f"争议部分退款: {dispute.resolution_result}"
                            )
                            # 标记订单为已完成但有争议
                            order.status = OrderStatusEnum.completed
                            order.completed_at = datetime.utcnow()
                            
                        elif resolution_action == 'full_refund':
                            # 全额退款
                            self._process_refund(
                                order, 
                                order.order_amount, 
                                f"争议全额退款: {dispute.resolution_result}"
                            )
                            # 标记订单为已取消
                            order.status = OrderStatusEnum.cancelled
                            order.cancellation_reason = f"争议处理结果全额退款：{dispute.resolution_result}"
                            
                        else:
                            # 默认情况，根据当前订单状态决定
                            if order.status == OrderStatusEnum.disputed:
                                # 恢复到争议前的状态（假设为进行中）
                                order.status = OrderStatusEnum.in_progress
                    else:
                        # 未指定解决动作，默认只是将订单从争议状态恢复到进行中
                        if order.status == OrderStatusEnum.disputed:
                            order.status = OrderStatusEnum.in_progress
                
                current_app.logger.info(f"管理员 {admin_user_id} 处理争议 {dispute_id}, 状态从 {old_status.value} 变更为 {new_status.value}")
            
            # 记录管理员操作日志
            # TODO: self._log_admin_action(admin_user_id, "mediate_dispute", dispute_id, f"状态变更为 {new_status.value}")
            
            # 通知争议相关方处理结果
            self._notify_dispute_mediation_result(dispute)
            
            return dispute
            
        except Exception as e:
            # 异常时事务已经回滚
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException) and not isinstance(e, BusinessException):
                current_app.logger.error(f"处理争议时出错: {str(e)}")
                raise BusinessException(message=f"处理争议失败: {str(e)}", status_code=500, error_code=50003)
            raise e
    
    def _process_refund(self, order, amount, description):
        """
        处理退款流程
        :param order: 订单对象
        :param amount: 退款金额
        :param description: 退款说明
        """
        from flask import current_app
        
        # 检查退款金额是否有效
        if amount <= 0 or amount > order.order_amount:
            raise InvalidUsageException(
                message=f"无效的退款金额: {amount}, 必须大于0且不超过订单金额 {order.order_amount}", 
                error_code=40005
            )
        
        # 查找原始支付记录
        original_payment = Payment.query.filter_by(
            order_id=order.id,
            status=PaymentStatusEnum.succeeded
        ).first()
        
        if not original_payment:
            raise BusinessException(message=f"未找到订单 {order.id} 的成功支付记录", status_code=500, error_code=50004)
        
        # 获取平台托管账户（假设为原支付的收款方）
        platform_wallet = UserWallet.query.filter_by(user_id=original_payment.payee_user_id).first()
        if not platform_wallet:
            raise BusinessException(message="平台托管账户钱包不存在", status_code=500, error_code=50005)
        
        # 获取付款方（雇主）钱包
        employer_wallet = UserWallet.query.filter_by(user_id=order.employer_user_id).first()
        if not employer_wallet:
            raise BusinessException(message=f"雇主 {order.employer_user_id} 的钱包不存在", status_code=500, error_code=50006)
        
        # 检查平台余额是否足够退款
        if platform_wallet.balance < amount:
            raise BusinessException(
                message=f"平台托管账户余额不足，当前余额: {platform_wallet.balance}，需要退款: {amount}", 
                status_code=500, 
                error_code=50007
            )
        
        # 创建退款支付记录
        refund_payment = Payment(
            order_id=order.id,
            payer_user_id=original_payment.payee_user_id,  # 平台作为退款方
            payee_user_id=original_payment.payer_user_id,  # 原付款方作为收款方
            amount=amount,
            payment_method="platform_refund",
            status=PaymentStatusEnum.succeeded,
            internal_transaction_id=f"refund_{original_payment.internal_transaction_id}",
            paid_at=datetime.utcnow(),
            description=description
        )
        db.session.add(refund_payment)
        db.session.flush()  # 获取生成的ID
        
        # 减少平台账户余额
        platform_wallet.balance -= amount
        
        # 创建平台支出交易记录
        platform_transaction = WalletTransaction(
            user_id=platform_wallet.user_id,
            transaction_type=TransactionTypeEnum.refund_out,
            amount=-amount,  # 负数表示支出
            balance_after=platform_wallet.balance,
            related_payment_id=refund_payment.id,
            related_order_id=order.id,
            description=f"向订单 #{order.id} 雇主退款"
        )
        db.session.add(platform_transaction)
        
        # 增加雇主账户余额
        employer_wallet.balance += amount
        
        # 创建雇主收入交易记录
        employer_transaction = WalletTransaction(
            user_id=employer_wallet.user_id,
            transaction_type=TransactionTypeEnum.refund_in,
            amount=amount,  # 正数表示收入
            balance_after=employer_wallet.balance,
            related_payment_id=refund_payment.id,
            related_order_id=order.id,
            description=f"订单 #{order.id} 退款"
        )
        db.session.add(employer_transaction)
        
        current_app.logger.info(f"订单 {order.id} 退款处理完成，金额：{amount}, 说明：{description}")
    
    def _notify_dispute_mediation_result(self, dispute):
        """
        通知争议相关方处理结果
        :param dispute: 争议对象
        """
        from flask import current_app
        
        try:
            # 调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            if not dispute.order:
                current_app.logger.warning(f"争议 {dispute.id} 无关联订单，无法发送通知")
                return
            
            # 确定通知接收者（争议双方）
            recipients = [dispute.initiator_user_id]
            
            # 添加订单另一方
            if dispute.initiator_user_id == dispute.order.employer_user_id:
                recipients.append(dispute.order.freelancer_user_id)
            else:
                recipients.append(dispute.order.employer_user_id)
            
            # 构建通知内容
            notification_title = "争议处理结果通知"
            
            status_display = {
                DisputeStatusEnum.resolved.value: "已解决",
                DisputeStatusEnum.closed.value: "已关闭",
                DisputeStatusEnum.platform_intervening.value: "平台干预中"
            }.get(dispute.status.value, dispute.status.value)
            
            notification_content = f"您的订单争议已被平台处理，当前状态：{status_display}。"
            
            if dispute.resolution_result:
                notification_content += f" 处理结果：{dispute.resolution_result}"
            
            notification_data = {
                'notification_type': 'dispute_mediation_result',
                'title': notification_title,
                'content': notification_content,
                'related_resource_type': 'dispute',
                'related_resource_id': dispute.id
            }
            
            # 向双方发送通知
            for user_id in recipients:
                notification_service.create_notification(user_id, notification_data)
            
            current_app.logger.info(f"已向用户 {recipients} 发送争议处理结果通知")
            
        except Exception as e:
            current_app.logger.error(f"发送争议处理结果通知失败: {str(e)}")
            # 通知失败不阻断主流程


class AdminReportService:
    def get_pending_reports(self, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取待处理的举报列表（管理员专用）
        :param filters: 过滤条件，例如report_type
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式
        :return: 分页后的举报列表
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        try:
            # 构建基础查询 - 获取待处理举报
            query = Report.query.filter_by(status=ReportStatusEnum.pending)
            
            # 预加载举报人信息以优化性能
            query = query.options(
                joinedload(Report.reporter)
            )
            
            # 应用过滤条件
            if 'report_type' in filters and filters['report_type']:
                try:
                    report_type_enum = ReportTypeEnum(filters['report_type'])
                    query = query.filter(Report.report_type == report_type_enum)
                except ValueError:
                    # 无效的举报类型，忽略此过滤条件
                    current_app.logger.warning(f"管理员举报查询：无效的举报类型 {filters['report_type']}")
                    pass
            
            # 应用排序
            if sort_by == 'created_at_asc':
                query = query.order_by(Report.created_at.asc())  # 旧的先处理
            elif sort_by == 'created_at_desc':
                query = query.order_by(Report.created_at.desc())
            elif sort_by == 'report_type':
                query = query.order_by(Report.report_type.asc(), Report.created_at.asc())
            else:
                # 默认按创建时间升序 (FIFO处理)
                query = query.order_by(Report.created_at.asc())
            
            # 执行分页
            paginated_reports = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 为每个举报项添加被举报对象摘要信息
            for report in paginated_reports.items:
                report.target_summary = self._get_report_target_summary(report)
            
            # 记录日志
            current_app.logger.info(f"管理员查询待处理举报列表，过滤条件: {filters}, 页码: {page}, 每页: {per_page}, 总数: {paginated_reports.total}")
            
            return paginated_reports
            
        except Exception as e:
            current_app.logger.error(f"管理员获取待处理举报列表时出错: {str(e)}")
            raise BusinessException(message=f"获取待处理举报列表失败: {str(e)}", status_code=500, error_code=50008)
    
    def _get_report_target_summary(self, report):
        """
        获取举报目标的摘要信息
        :param report: 举报记录
        :return: 摘要信息字符串
        """
        from flask import current_app
        
        try:
            report_type = report.report_type
            target_id = report.target_id
            
            if report_type == ReportTypeEnum.job:
                job = Job.query.get(target_id)
                if job:
                    return f"工作：{job.title} (ID: {job.id})"
            
            elif report_type == ReportTypeEnum.user:
                user = User.query.get(target_id)
                if user:
                    if hasattr(user, 'phone_number'):
                        return f"用户：{user.phone_number} (ID: {user.id})"
                    return f"用户 ID: {user.id}"
            
            elif report_type == ReportTypeEnum.order:
                order = Order.query.get(target_id)
                if order:
                    # 尝试通过关联的Job获取更多信息
                    job_title = "未知工作"
                    if hasattr(order, 'job') and order.job:
                        job_title = order.job.title
                    return f"订单：{job_title} (订单ID: {order.id})"
            
            elif report_type == ReportTypeEnum.message:
                message = Message.query.get(target_id)
                if message:
                    content_preview = message.content[:20] + "..." if len(message.content) > 20 else message.content
                    return f"消息：{content_preview} (ID: {message.id})"
            
            elif report_type == ReportTypeEnum.evaluation:
                evaluation = Evaluation.query.get(target_id)
                if evaluation:
                    return f"评价 ID: {evaluation.id}, 评分: {evaluation.rating}"
            
            return f"未知类型 {report_type.value if hasattr(report_type, 'value') else report_type} 的举报目标 ID: {target_id}"
            
        except Exception as e:
            current_app.logger.error(f"获取举报目标摘要时出错: {str(e)}")
            return f"目标 ID: {report.target_id} (获取详情出错)"
    
    def process_report(self, admin_user_id, report_id, process_data):
        """
        处理举报（管理员专用）
        :param admin_user_id: 管理员ID
        :param report_id: 举报ID
        :param process_data: 处理数据，包含status, processing_result
        :return: 更新后的举报对象
        """
        from flask import current_app
        
        # 验证处理状态
        if 'status' not in process_data or not process_data['status']:
            raise InvalidUsageException(message="处理状态不能为空", error_code=40010)
        
        valid_statuses = ['resolved_valid', 'resolved_invalid', 'resolved_duplicate', 'processing']
        if process_data['status'] not in valid_statuses:
            raise InvalidUsageException(
                message=f"无效的处理状态，有效值为: {', '.join(valid_statuses)}", 
                error_code=40011
            )
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 查询举报
                report = Report.query.options(
                    joinedload(Report.reporter)
                ).get(report_id)
                
                if not report:
                    raise NotFoundException(message="举报记录不存在", error_code=40401)
                
                # 验证举报状态
                if report.status not in [ReportStatusEnum.pending, ReportStatusEnum.processing]:
                    raise InvalidUsageException(
                        message=f"该举报当前状态 ({report.status.value}) 不允许处理", 
                        error_code=40012
                    )
                
                # 更新举报状态
                old_status = report.status
                report.status = ReportStatusEnum(process_data['status'])
                
                # 更新处理结果（如果提供）
                if 'processing_result' in process_data:
                    report.processing_result = process_data['processing_result']
                
                # 记录处理人和处理时间
                report.processor_id = admin_user_id
                report.processed_at = datetime.utcnow()
                
                current_app.logger.info(f"管理员 {admin_user_id} 处理举报 {report_id}, 状态从 {old_status.value if hasattr(old_status, 'value') else old_status} 变更为 {report.status.value if hasattr(report.status, 'value') else report.status}")
                
                # 如果举报被认为有效，执行后续处理
                if process_data['status'] == 'resolved_valid':
                    # 获取被举报对象类型和ID
                    report_type = report.report_type
                    target_id = report.target_id
                    
                    # 根据举报类型执行不同操作
                    if report_type == ReportTypeEnum.user:
                        # 查询被举报用户
                        reported_user = User.query.get(target_id)
                        if reported_user:
                            # 例如警告或禁用用户
                            self._handle_reported_user(reported_user, report, admin_user_id)
                    
                    elif report_type == ReportTypeEnum.job:
                        # 查询被举报工作
                        reported_job = Job.query.get(target_id)
                        if reported_job:
                            # 例如下架工作
                            self._handle_reported_job(reported_job, report)
                    
                    elif report_type == ReportTypeEnum.message:
                        # 处理被举报的消息
                        self._handle_reported_message(target_id, report)
                    
                    # ... 其他类型的举报处理 ...
            
            # 记录管理员操作日志
            # TODO: self._log_admin_action(admin_user_id, "process_report", report_id, f"状态变更为 {report.status.value}")
            
            # 通知举报人处理结果
            self._notify_report_processing_result(report)
            
            return report
            
        except Exception as e:
            # 异常时事务已经回滚
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException) and not isinstance(e, BusinessException):
                current_app.logger.error(f"处理举报时出错: {str(e)}")
                raise BusinessException(message=f"处理举报失败: {str(e)}", status_code=500, error_code=50009)
            raise e
    
    def _handle_reported_user(self, reported_user, report, admin_user_id):
        """
        处理被举报的用户
        :param reported_user: 用户对象
        :param report: 举报对象
        :param admin_user_id: 管理员ID
        """
        from flask import current_app
        
        # 根据举报严重性判断处理方式
        processing_result = report.processing_result or ""
        
        # 如果处理结果表明需要封禁用户
        if "禁用" in processing_result or "封禁" in processing_result:
            try:
                # 更新用户状态为封禁
                ban_reason = f"因违规被举报：{report.reason_category}" + (f" - {report.reason_description}" if report.reason_description else "")
                
                # 调用管理员用户服务进行封禁
                admin_user_service.update_user_status_by_admin(
                    admin_user_id, 
                    reported_user.uuid, 
                    {
                        "status": "banned",
                        "ban_reason": ban_reason
                    }
                )
                
                current_app.logger.info(f"因举报 {report.id}，用户 {reported_user.id} 已被封禁")
                
            except Exception as e:
                current_app.logger.error(f"封禁用户 {reported_user.id} 失败: {str(e)}")
                # 不阻断主流程
        else:
            # 仅发送警告
            try:
                # 发送警告通知
                from ..services.communication_service import notification_service
                
                notification_title = "账号警告通知"
                notification_content = f"您的账号收到违规举报并经平台核实，违规类型：{report.reason_category}。请严格遵守平台规则，避免账号被封禁。"
                
                notification_data = {
                    'notification_type': 'account_warning',
                    'title': notification_title,
                    'content': notification_content,
                    'related_resource_type': 'report',
                    'related_resource_id': report.id
                }
                
                notification_service.create_notification(reported_user.id, notification_data)
                current_app.logger.info(f"已向被举报用户 {reported_user.id} 发送警告通知")
                
            except Exception as e:
                current_app.logger.error(f"向用户 {reported_user.id} 发送警告失败: {str(e)}")
                # 不阻断主流程
    
    def _handle_reported_job(self, reported_job, report):
        """
        处理被举报的工作
        :param reported_job: 工作对象
        :param report: 举报对象
        """
        from flask import current_app
        
        try:
            # 将工作下架
            if reported_job.status == JobStatusEnum.active:
                reported_job.status = JobStatusEnum.inactive
                reported_job.updated_at = datetime.utcnow()
                reported_job.cancellation_reason = f"因违规被举报：{report.reason_category}" + (f" - {report.reason_description}" if report.reason_description else "")
                
                current_app.logger.info(f"因举报 {report.id}，工作 {reported_job.id} 已被下架")
                
                # 通知雇主工作被下架
                from ..services.communication_service import notification_service
                
                notification_title = "工作下架通知"
                notification_content = f"您发布的工作 \"{reported_job.title}\" 因违规被平台下架，违规类型：{report.reason_category}。"
                
                notification_data = {
                    'notification_type': 'job_takedown',
                    'title': notification_title,
                    'content': notification_content,
                    'related_resource_type': 'job',
                    'related_resource_id': reported_job.id
                }
                
                notification_service.create_notification(reported_job.employer_user_id, notification_data)
                
        except Exception as e:
            current_app.logger.error(f"处理被举报工作 {reported_job.id} 失败: {str(e)}")
            # 不阻断主流程
    
    def _handle_reported_message(self, message_id, report):
        """
        处理被举报的消息
        :param message_id: 消息ID
        :param report: 举报对象
        """
        from flask import current_app
        
        try:
            # 查询消息
            message = Message.query.get(message_id)
            if not message:
                current_app.logger.warning(f"举报 {report.id} 的目标消息 {message_id} 不存在")
                return
            
            # 标记消息违规或删除敏感内容
            message.is_flagged = True
            message.content = "[该消息因违规已被屏蔽]"
            message.updated_at = datetime.utcnow()
            
            current_app.logger.info(f"因举报 {report.id}，消息 {message_id} 已被标记违规并屏蔽内容")
            
        except Exception as e:
            current_app.logger.error(f"处理被举报消息 {message_id} 失败: {str(e)}")
            # 不阻断主流程
    
    def _notify_report_processing_result(self, report):
        """
        通知举报人处理结果
        :param report: 举报对象
        """
        from flask import current_app
        
        try:
            # 调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            # 只通知举报人
            reporter_id = report.reporter_user_id
            
            # 构建通知内容
            notification_title = "举报处理结果通知"
            
            status_display = {
                'resolved_valid': "处理有效",
                'resolved_invalid': "无效举报",
                'resolved_duplicate': "重复举报",
                'processing': "正在处理"
            }.get(report.status.value if hasattr(report.status, 'value') else report.status, "已处理")
            
            notification_content = f"您的举报已被平台处理，结果：{status_display}。"
            
            if report.processing_result:
                notification_content += f" 处理说明：{report.processing_result}"
            
            notification_data = {
                'notification_type': 'report_result',
                'title': notification_title,
                'content': notification_content,
                'related_resource_type': 'report',
                'related_resource_id': report.id
            }
            
            notification_service.create_notification(reporter_id, notification_data)
            
            current_app.logger.info(f"已向举报人 {reporter_id} 发送处理结果通知")
            
        except Exception as e:
            current_app.logger.error(f"发送举报处理结果通知失败: {str(e)}")
            # 通知失败不阻断主流程


# 服务实例
admin_dispute_service = AdminDisputeService()
admin_report_service = AdminReportService() 