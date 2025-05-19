from ..models.wallet import UserWallet, WalletTransaction, TransactionTypeEnum, WithdrawalRequest, WithdrawalStatusEnum
from ..models.user import User
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime
from decimal import Decimal

class AdminFinanceService:
    def get_pending_withdrawal_requests(self, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取待处理的提现申请列表（管理员专用）
        :param filters: 过滤条件，例如withdrawal_method, amount_min, amount_max
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式
        :return: 分页后的提现申请列表
        """
        from flask import current_app
        
        if filters is None:
            filters = {}
        
        try:
            # 构建基础查询 - 获取待处理提现申请
            query = WithdrawalRequest.query.filter_by(status=WithdrawalStatusEnum.pending)
            
            # 预加载用户信息以优化性能
            query = query.options(
                joinedload(WithdrawalRequest.user).joinedload(User.freelancer_profile),
                joinedload(WithdrawalRequest.user).joinedload(User.employer_profile)
            )
            
            # 应用过滤条件
            if 'withdrawal_method' in filters and filters['withdrawal_method']:
                query = query.filter(WithdrawalRequest.withdrawal_method == filters['withdrawal_method'])
            
            if 'amount_min' in filters and filters['amount_min']:
                try:
                    amount_min = Decimal(filters['amount_min'])
                    query = query.filter(WithdrawalRequest.amount >= amount_min)
                except (ValueError, TypeError):
                    current_app.logger.warning(f"管理员提现查询：无效的最小金额值 {filters['amount_min']}")
            
            if 'amount_max' in filters and filters['amount_max']:
                try:
                    amount_max = Decimal(filters['amount_max'])
                    query = query.filter(WithdrawalRequest.amount <= amount_max)
                except (ValueError, TypeError):
                    current_app.logger.warning(f"管理员提现查询：无效的最大金额值 {filters['amount_max']}")
            
            # 应用排序
            if sort_by == 'created_at_asc':
                query = query.order_by(WithdrawalRequest.created_at.asc())  # 旧的先处理
            elif sort_by == 'created_at_desc':
                query = query.order_by(WithdrawalRequest.created_at.desc())
            elif sort_by == 'amount_asc':
                query = query.order_by(WithdrawalRequest.amount.asc())
            elif sort_by == 'amount_desc':
                query = query.order_by(WithdrawalRequest.amount.desc())
            else:
                # 默认按创建时间升序 (FIFO处理)
                query = query.order_by(WithdrawalRequest.created_at.asc())
            
            # 执行分页
            paginated_withdrawals = query.paginate(page=page, per_page=per_page, error_out=False)
            
            # 记录日志
            current_app.logger.info(f"管理员查询待处理提现列表，过滤条件: {filters}, 页码: {page}, 每页: {per_page}, 总数: {paginated_withdrawals.total}")
            
            return paginated_withdrawals
            
        except Exception as e:
            current_app.logger.error(f"管理员获取待处理提现列表时出错: {str(e)}")
            raise BusinessException(message=f"获取待处理提现列表失败: {str(e)}", status_code=500, error_code=50001)
    
    def process_withdrawal_request(self, admin_user_id, withdrawal_id, process_data):
        """
        处理提现申请（管理员专用）
        :param admin_user_id: 管理员ID
        :param withdrawal_id: 提现申请ID
        :param process_data: 处理数据，包含action (succeeded/failed)，
                           external_transaction_id (如果成功， 可选),
                           failure_reason (如果失败)
        :return: 更新后的提现申请对象
        """
        from flask import current_app
        
        # 验证处理动作
        if 'action' not in process_data or not process_data['action']:
            raise InvalidUsageException(message="处理动作不能为空", error_code=40001)
        
        if process_data['action'] not in ['succeeded', 'failed']:
            raise InvalidUsageException(message="无效的处理动作，必须是 succeeded 或 failed", error_code=40002)
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 查询提现申请
                withdrawal_req = WithdrawalRequest.query.get(withdrawal_id)
                if not withdrawal_req:
                    raise NotFoundException(message="提现申请不存在", error_code=40401)
                
                # 验证提现申请状态必须是待处理
                if withdrawal_req.status != WithdrawalStatusEnum.pending:
                    raise InvalidUsageException(
                        message=f"该提现申请不在待处理状态，当前状态: {withdrawal_req.status.value}", 
                        error_code=40003
                    )
                
                # 查询用户钱包
                wallet = UserWallet.query.filter_by(user_id=withdrawal_req.user_id).first()
                if not wallet:
                    raise BusinessException(
                        message=f"用户 {withdrawal_req.user_id} 的钱包不存在", 
                        status_code=500, 
                        error_code=50002
                    )
                
                # 更新提现申请
                withdrawal_req.processor_id = admin_user_id
                withdrawal_req.processed_at = datetime.utcnow()
                
                if process_data['action'] == 'succeeded':
                    withdrawal_req.status = WithdrawalStatusEnum.succeeded
                    
                    # 记录外部交易ID（如支付平台返回的交易号）
                    if 'external_transaction_id' in process_data and process_data['external_transaction_id']:
                        withdrawal_req.external_transaction_id = process_data['external_transaction_id']
                    
                    # 资金操作：从冻结余额中减去提现金额（因为这笔钱已经打给用户）
                    if wallet.frozen_balance < withdrawal_req.amount:
                        raise BusinessException(
                            message=f"用户 {withdrawal_req.user_id} 的冻结余额不足，当前: {wallet.frozen_balance}，需要: {withdrawal_req.amount}",
                            status_code=500,
                            error_code=50003
                        )
                    
                    wallet.frozen_balance -= withdrawal_req.amount
                    
                    # 创建交易记录 - 确认提现（资金实际流出）
                    transaction = WalletTransaction(
                        user_id=withdrawal_req.user_id,
                        transaction_type=TransactionTypeEnum.withdrawal_completed,
                        amount=-withdrawal_req.amount,  # 负值表示资金流出
                        balance_after=wallet.balance,  # 可用余额未变
                        related_withdrawal_id=withdrawal_req.id,
                        description=f"提现成功 ({withdrawal_req.withdrawal_method})"
                    )
                    
                    db.session.add(transaction)
                    
                    current_app.logger.info(f"管理员 {admin_user_id} 标记提现申请 {withdrawal_id} 为成功处理，金额: {withdrawal_req.amount}")
                    
                elif process_data['action'] == 'failed':
                    withdrawal_req.status = WithdrawalStatusEnum.failed
                    
                    # 记录失败原因
                    failure_reason = process_data.get('failure_reason', '提现处理失败')
                    withdrawal_req.failure_reason = failure_reason
                    
                    # 资金操作：解冻资金并退回到可用余额
                    wallet.frozen_balance -= withdrawal_req.amount
                    wallet.balance += withdrawal_req.amount
                    
                    # 创建交易记录 - 提现失败退款
                    transaction = WalletTransaction(
                        user_id=withdrawal_req.user_id,
                        transaction_type=TransactionTypeEnum.withdrawal_failed_refund,
                        amount=withdrawal_req.amount,  # 正值表示资金回流
                        balance_after=wallet.balance,
                        related_withdrawal_id=withdrawal_req.id,
                        description=f"提现失败退款 ({failure_reason})"
                    )
                    
                    db.session.add(transaction)
                    
                    current_app.logger.info(f"管理员 {admin_user_id} 标记提现申请 {withdrawal_id} 为处理失败，原因: {failure_reason}")
            
            # 记录管理员操作日志
            # TODO: self._log_admin_action(admin_user_id, f"{process_data['action']}_withdrawal", withdrawal_id)
            
            # 通知用户提现处理结果
            self._notify_withdrawal_process_result(withdrawal_req, process_data['action'], process_data.get('failure_reason'))
            
            return withdrawal_req
            
        except Exception as e:
            # 异常时事务已经回滚
            if not isinstance(e, NotFoundException) and not isinstance(e, InvalidUsageException) and not isinstance(e, BusinessException):
                current_app.logger.error(f"处理提现申请时出错: {str(e)}")
                raise BusinessException(message=f"处理提现申请失败: {str(e)}", status_code=500, error_code=50004)
            raise e
    
    def _notify_withdrawal_process_result(self, withdrawal_request, action, failure_reason=None):
        """
        通知用户提现处理结果
        :param withdrawal_request: 提现申请对象
        :param action: 处理动作 (succeeded/failed)
        :param failure_reason: 失败原因（如果是失败）
        """
        from flask import current_app
        
        try:
            # 调用通知服务发送系统通知
            from ..services.communication_service import notification_service
            
            notification_title = "提现申请处理结果通知"
            
            withdrawal_method = withdrawal_request.withdrawal_method
            amount = withdrawal_request.amount
            
            if action == 'succeeded':
                notification_content = f"您的提现申请已成功处理。金额: {amount} 元，提现方式: {withdrawal_method}。"
                if withdrawal_request.external_transaction_id:
                    notification_content += f" 交易单号: {withdrawal_request.external_transaction_id}"
            else:  # failed
                notification_content = f"您的提现申请处理失败。金额: {amount} 元，提现方式: {withdrawal_method}。"
                if failure_reason:
                    notification_content += f" 原因: {failure_reason}"
                notification_content += " 资金已退回您的钱包可用余额。"
            
            notification_data = {
                'notification_type': 'wallet_withdrawal_result',
                'title': notification_title,
                'content': notification_content,
                'related_resource_type': 'withdrawal',
                'related_resource_id': withdrawal_request.id
            }
            
            notification_service.create_notification(withdrawal_request.user_id, notification_data)
            current_app.logger.info(f"已向用户 {withdrawal_request.user_id} 发送提现处理结果通知")
            
        except Exception as e:
            current_app.logger.error(f"发送提现处理结果通知失败: {str(e)}")
            # 通知失败不阻断主流程


# 服务实例
admin_finance_service = AdminFinanceService() 