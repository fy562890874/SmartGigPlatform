from ..models.dispute import Dispute, DisputeStatusEnum
from ..models.report import Report, ReportTypeEnum
from ..models.order import Order, OrderStatusEnum
from ..models.job import Job
from ..models.message import Message
from ..models.user import User
from ..models.evaluation import Evaluation
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime

class DisputeService:
    def initiate_order_dispute(self, initiator_user_id, order_id, dispute_data):
        """
        发起订单争议
        :param initiator_user_id: 发起争议的用户ID
        :param order_id: 订单ID
        :param dispute_data: 争议信息，包含reason等
        :return: 创建的Dispute对象
        """
        from flask import current_app
        
        # 查询订单
        order = Order.query.get(order_id)
        if not order:
            raise NotFoundException(message="订单不存在", error_code=40401)
        
        # 权限校验：确认用户是订单的参与方
        if initiator_user_id != order.freelancer_user_id and initiator_user_id != order.employer_user_id:
            raise AuthorizationException(message="您无权对此订单发起争议", error_code=40301)
        
        # 状态校验：确认订单状态允许发起争议
        invalid_statuses = [OrderStatusEnum.cancelled, OrderStatusEnum.pending_start]
        if order.status in invalid_statuses:
            raise InvalidUsageException(
                message=f"订单当前状态（{order.status.value}）不允许发起争议", 
                error_code=40003
            )
        
        # 重复性校验：检查订单是否已有争议
        existing_dispute = Dispute.query.filter_by(order_id=order_id).first()
        if existing_dispute:
            raise BusinessException(message="该订单已有争议", status_code=409, error_code=40901)
        
        try:
            # 创建争议记录
            new_dispute = Dispute(
                order_id=order_id,
                initiator_user_id=initiator_user_id,
                reason=dispute_data.get('reason', ''),
                expected_resolution=dispute_data.get('expected_resolution'),
                attachments=dispute_data.get('attachments', []),
                status=DisputeStatusEnum.pending
            )
            
            # 更新订单状态为争议中
            order.status = OrderStatusEnum.disputed
            
            db.session.add(new_dispute)
            db.session.commit()
            
            # 可选：通知订单另一方及平台管理员
            # TODO: 调用通知服务发送通知
            
            return new_dispute
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建订单争议时出错: {str(e)}")
            raise BusinessException(message=f"创建订单争议失败: {str(e)}", status_code=500, error_code=50001)

    def get_dispute_details_for_order(self, user_id, order_id):
        """
        获取订单的争议信息
        :param user_id: 当前用户ID
        :param order_id: 订单ID
        :return: Dispute对象
        """
        from flask import current_app
        
        # 查询争议记录及相关信息
        dispute = Dispute.query.filter_by(order_id=order_id).options(
            joinedload(Dispute.order),
            joinedload(Dispute.initiator),
            joinedload(Dispute.platform_mediator)
        ).first()
        
        if not dispute:
            raise NotFoundException(message="未找到该订单的争议记录", error_code=40402)
        
        # 权限校验：只有订单参与方和管理员可以查看
        is_admin = False  # 假设有管理员角色检查的函数
        is_order_participant = (user_id == dispute.initiator_user_id or 
                                user_id == dispute.order.employer_user_id or 
                                user_id == dispute.order.freelancer_user_id)
        
        if not (is_admin or is_order_participant):
            raise AuthorizationException(message="您无权查看此争议信息", error_code=40302)
        
        return dispute

    def update_dispute_information_or_status(self, current_user_id, dispute_id, action_data):
        """
        更新争议信息/状态
        :param current_user_id: 当前操作用户ID
        :param dispute_id: 争议ID
        :param action_data: 操作数据，根据角色不同而内容不同
        :return: 更新后的Dispute对象
        """
        from flask import current_app
        
        # 查询争议记录
        dispute = Dispute.query.get(dispute_id)
        if not dispute:
            raise NotFoundException(message="争议记录不存在", error_code=40403)
        
        order = Order.query.get(dispute.order_id)
        if not order:
            current_app.logger.error(f"争议 {dispute_id} 关联的订单 {dispute.order_id} 不存在")
            raise BusinessException(message="争议关联的订单不存在", status_code=500, error_code=50002)
        
        is_admin = False  # TODO: 实现管理员身份检查
        is_order_participant = (current_user_id == dispute.initiator_user_id or 
                               current_user_id == order.employer_user_id or 
                               current_user_id == order.freelancer_user_id)
        
        try:
            # 用户追加信息
            if not is_admin and is_order_participant:
                # 用户只能添加评论或附件
                if 'comment' in action_data:
                    # 追加评论到reason字段（非最佳实践，理想情况下应有独立的评论表）
                    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                    user_comment = f"\n[{current_time}] 用户 {current_user_id} 评论: {action_data['comment']}"
                    dispute.reason += user_comment
                
                if 'new_attachment_url' in action_data and action_data['new_attachment_url']:
                    # 追加附件
                    current_attachments = dispute.attachments or []
                    if action_data['new_attachment_url'] not in current_attachments:
                        current_attachments.append(action_data['new_attachment_url'])
                        dispute.attachments = current_attachments
            
            # 管理员处理争议
            if is_admin:
                if 'status' in action_data:
                    try:
                        new_status = action_data['status']
                        # 验证状态值有效
                        if new_status in [status.value for status in DisputeStatusEnum]:
                            dispute.status = new_status
                    except Exception as e:
                        current_app.logger.error(f"更新争议状态时出错: {str(e)}")
                        raise InvalidUsageException(message="无效的争议状态", error_code=40004)
                
                if 'resolution_result' in action_data:
                    dispute.resolution_result = action_data['resolution_result']
                
                # 如果状态变为已解决或关闭
                if dispute.status in [DisputeStatusEnum.resolved, DisputeStatusEnum.closed]:
                    dispute.platform_mediator_id = current_user_id
                    dispute.resolved_at = datetime.utcnow()
                    
                    # 可能需要更新订单状态
                    # 例如，如果争议解决，订单可能回到之前的状态或进入新状态
                    # order.status = OrderStatusEnum.in_progress  # 根据实际业务逻辑确定
            
            db.session.commit()
            return dispute
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新争议信息时出错: {str(e)}")
            raise BusinessException(message=f"更新争议信息失败: {str(e)}", status_code=500, error_code=50003)


class ReportService:
    def submit_new_report(self, reporter_user_id, report_data):
        """
        提交举报
        :param reporter_user_id: 举报者ID
        :param report_data: 举报信息，包含report_type, target_id等
        :return: 创建的Report对象
        """
        from flask import current_app
        
        # 校验举报类型
        report_type = report_data.get('report_type')
        if not report_type or report_type not in [rt.value for rt in ReportTypeEnum]:
            raise InvalidUsageException(message="无效的举报类型", error_code=40005)
        
        # 校验目标ID存在对应的实体
        target_id = report_data.get('target_id')
        if not target_id:
            raise InvalidUsageException(message="未提供举报目标ID", error_code=40006)
        
        target_exists = False
        target_type = ReportTypeEnum(report_type)
        
        # 根据举报类型检查目标是否存在
        if target_type == ReportTypeEnum.job:
            target_exists = Job.query.get(target_id) is not None
        elif target_type == ReportTypeEnum.user:
            target_exists = User.query.get(target_id) is not None
        elif target_type == ReportTypeEnum.order:
            target_exists = Order.query.get(target_id) is not None
        elif target_type == ReportTypeEnum.message:
            target_exists = Message.query.get(target_id) is not None
        elif target_type == ReportTypeEnum.evaluation:
            target_exists = Evaluation.query.get(target_id) is not None
        
        if not target_exists:
            raise NotFoundException(message="举报对象不存在", error_code=40404)
        
        try:
            # 创建举报记录
            new_report = Report(
                reporter_user_id=reporter_user_id,
                report_type=target_type,
                target_id=target_id,
                reason_category=report_data.get('reason_category', '其他'),
                reason_description=report_data.get('reason_description', ''),
                attachments=report_data.get('attachments', []),
                status=ReportStatusEnum.pending if hasattr(Report, 'status') else None  # 假设Report有status字段
            )
            
            db.session.add(new_report)
            db.session.commit()
            
            # 可选：通知平台管理员有新举报
            # TODO: 调用通知服务发送通知
            
            return new_report
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建举报时出错: {str(e)}")
            raise BusinessException(message=f"提交举报失败: {str(e)}", status_code=500, error_code=50004)

    def get_my_submitted_reports(self, reporter_user_id, filters=None, page=1, per_page=10):
        """
        获取我的举报记录
        :param reporter_user_id: 举报者ID
        :param filters: 过滤条件，如status, report_type
        :param page: 页码
        :param per_page: 每页数量
        :return: 举报列表和分页信息
        """
        if filters is None:
            filters = {}
        
        # 构建基础查询
        query = Report.query.filter_by(reporter_user_id=reporter_user_id)
        
        # 应用过滤条件
        if 'status' in filters and hasattr(Report, 'status'):
            try:
                status_value = filters['status']
                query = query.filter(Report.status == status_value)
            except Exception:
                # 如果状态无效，忽略此过滤条件
                pass
        
        if 'report_type' in filters:
            try:
                report_type_value = filters['report_type']
                query = query.filter(Report.report_type == report_type_value)
            except Exception:
                # 如果类型无效，忽略此过滤条件
                pass
        
        # 按时间倒序排序
        query = query.order_by(Report.created_at.desc())
        
        # 执行分页
        paginated_reports = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_reports


# 服务实例
dispute_service = DisputeService()
report_service = ReportService() 