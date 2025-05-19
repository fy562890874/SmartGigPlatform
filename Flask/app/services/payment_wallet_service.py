from ..models.wallet import UserWallet, WalletTransaction, TransactionTypeEnum, WithdrawalRequest, WithdrawalStatusEnum
from ..models.order import Order, Payment, PaymentStatusEnum, OrderStatusEnum
from ..models.user import User
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime
from decimal import Decimal

class WalletService:
    def get_user_wallet_info(self, user_id):
        """
        获取用户钱包信息
        :param user_id: 用户ID
        :return: UserWallet对象
        """
        from flask import current_app
        
        # 查询钱包记录
        wallet = UserWallet.query.filter_by(user_id=user_id).first()
        
        # 如果未找到钱包
        if not wallet:
            # 查询用户是否存在
            user = User.query.get(user_id)
            if not user:
                raise NotFoundException(message="用户不存在", error_code=40401)
            
            # 记录错误但不自动创建
            current_app.logger.error(f"用户 {user_id} 的钱包信息不存在，请检查注册流程")
            raise NotFoundException(message="用户钱包信息未找到", error_code=40405)
        
        return wallet

    def get_wallet_transactions(self, user_id, filters=None, page=1, per_page=10, sort_by=None):
        """
        获取用户钱包交易流水
        :param user_id: 用户ID
        :param filters: 过滤条件，如transaction_type, start_date, end_date
        :param page: 页码
        :param per_page: 每页数量
        :param sort_by: 排序方式，例如"created_at_desc"
        :return: 交易流水列表和分页信息
        """
        if filters is None:
            filters = {}
        
        # 构建基础查询
        query = WalletTransaction.query.filter_by(user_id=user_id)
        
        # 应用过滤条件
        if 'transaction_type' in filters:
            try:
                # 尝试将字符串转换为枚举值
                transaction_type_str = filters['transaction_type']
                if transaction_type_str in [tt.value for tt in TransactionTypeEnum]:
                    query = query.filter(WalletTransaction.transaction_type == transaction_type_str)
            except Exception:
                # 忽略无效的过滤条件
                pass
        
        if 'start_date' in filters:
            try:
                start_date = datetime.fromisoformat(filters['start_date'].replace('Z', '+00:00'))
                query = query.filter(WalletTransaction.created_at >= start_date)
            except (ValueError, TypeError):
                # 忽略无效的日期格式
                pass
        
        if 'end_date' in filters:
            try:
                end_date = datetime.fromisoformat(filters['end_date'].replace('Z', '+00:00'))
                query = query.filter(WalletTransaction.created_at <= end_date)
            except (ValueError, TypeError):
                # 忽略无效的日期格式
                pass
        
        # 应用排序
        if sort_by:
            if sort_by == 'created_at_desc':
                query = query.order_by(WalletTransaction.created_at.desc())
            elif sort_by == 'created_at_asc':
                query = query.order_by(WalletTransaction.created_at.asc())
            elif sort_by == 'amount_desc':
                query = query.order_by(WalletTransaction.amount.desc())
            elif sort_by == 'amount_asc':
                query = query.order_by(WalletTransaction.amount.asc())
        else:
            # 默认按创建时间倒序
            query = query.order_by(WalletTransaction.created_at.desc())
        
        # 执行分页
        paginated_transactions = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_transactions

    def request_withdrawal(self, user_id, withdrawal_data):
        """
        申请提现
        :param user_id: 用户ID
        :param withdrawal_data: 提现数据，包含amount, withdrawal_method, account_info
        :return: 创建的WithdrawalRequest对象
        """
        from flask import current_app
        
        # 查询用户钱包
        wallet = UserWallet.query.filter_by(user_id=user_id).first()
        if not wallet:
            raise NotFoundException(message="用户钱包不存在", error_code=40405)
        
        # 金额校验
        try:
            requested_amount = Decimal(withdrawal_data.get('amount', '0'))
        except (ValueError, TypeError):
            raise InvalidUsageException(message="提现金额格式无效", error_code=40010)
        
        if requested_amount <= 0:
            raise InvalidUsageException(message="提现金额必须大于0", error_code=40011)
        
        if wallet.balance < requested_amount:
            raise InvalidUsageException(message="钱包余额不足", error_code=40012)
        
        # TODO: 从系统配置获取最小/最大提现限额和手续费率
        min_withdrawal = Decimal('10.00')  # 最小提现金额
        max_withdrawal = Decimal('50000.00')  # 最大提现金额
        fee_rate = Decimal('0.01')  # 1%手续费率
        
        if requested_amount < min_withdrawal:
            raise InvalidUsageException(message=f"提现金额不能低于{min_withdrawal}", error_code=40013)
        
        if requested_amount > max_withdrawal:
            raise InvalidUsageException(message=f"提现金额不能超过{max_withdrawal}", error_code=40014)
        
        # 手续费计算
        platform_fee = (requested_amount * fee_rate).quantize(Decimal('0.01'))
        actual_amount = requested_amount - platform_fee
        
        if actual_amount <= 0:
            raise InvalidUsageException(message="扣除手续费后实际到账金额必须大于0", error_code=40015)
        
        # 检查提现方式和账户信息
        withdrawal_method = withdrawal_data.get('withdrawal_method')
        if not withdrawal_method:
            raise InvalidUsageException(message="未提供提现方式", error_code=40016)
        
        account_info = withdrawal_data.get('account_info')
        if not account_info:
            raise InvalidUsageException(message="未提供账户信息", error_code=40017)
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 更新钱包余额
                wallet.balance -= requested_amount
                wallet.frozen_balance += requested_amount
                
                # 创建提现申请记录
                new_withdrawal_request = WithdrawalRequest(
                    user_id=user_id,
                    amount=requested_amount,
                    withdrawal_method=withdrawal_method,
                    account_info=account_info,
                    status=WithdrawalStatusEnum.pending,
                    platform_fee=platform_fee,
                    actual_amount=actual_amount
                )
                
                db.session.add(new_withdrawal_request)
                db.session.flush()  # 获取新记录的ID
                
                # 创建钱包交易记录
                new_transaction = WalletTransaction(
                    user_id=user_id,
                    transaction_type=TransactionTypeEnum.withdrawal,
                    amount=-requested_amount,
                    balance_after=wallet.balance,
                    related_withdrawal_id=new_withdrawal_request.id,
                    description=f"提现申请 ({withdrawal_method})"
                )
                
                db.session.add(new_transaction)
            
            # 事务已提交
            current_app.logger.info(f"用户 {user_id} 成功申请提现 {requested_amount}，实际到账 {actual_amount}，手续费 {platform_fee}")
            
            return new_withdrawal_request
            
        except Exception as e:
            # 事务已回滚
            current_app.logger.error(f"申请提现失败: {str(e)}")
            raise BusinessException(message=f"申请提现失败: {str(e)}", status_code=500, error_code=50001)

    def get_user_withdrawal_requests(self, user_id, filters=None, page=1, per_page=10):
        """
        获取用户提现申请记录
        :param user_id: 用户ID
        :param filters: 过滤条件，如status
        :param page: 页码
        :param per_page: 每页数量
        :return: 提现申请列表和分页信息
        """
        if filters is None:
            filters = {}
        
        # 构建基础查询
        query = WithdrawalRequest.query.filter_by(user_id=user_id)
        
        # 应用过滤条件
        if 'status' in filters:
            try:
                status_value = filters['status']
                if status_value in [s.value for s in WithdrawalStatusEnum]:
                    query = query.filter(WithdrawalRequest.status == status_value)
            except Exception:
                # 忽略无效的过滤条件
                pass
        
        # 按时间倒序排序
        query = query.order_by(WithdrawalRequest.created_at.desc())
        
        # 执行分页
        paginated_requests = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_requests


class PaymentService:
    def initiate_order_payment(self, payer_user_id, order_id, payment_data):
        """
        预支付订单（雇主托管资金）
        :param payer_user_id: 支付者（雇主）用户ID
        :param order_id: 订单ID
        :param payment_data: 支付数据，包含payment_method
        :return: 支付初始化信息，包含payment_id, gateway_payload等
        """
        from flask import current_app
        import uuid
        
        # 查询订单
        order = Order.query.get(order_id)
        if not order:
            raise NotFoundException(message="订单不存在", error_code=40401)
        
        # 权限校验：确认payer_user_id是雇主
        if payer_user_id != order.employer_user_id:
            raise AuthorizationException(message="您不是此订单的雇主，无权支付", error_code=40301)
        
        # 状态校验：确认订单状态允许支付
        if order.status not in [OrderStatusEnum.pending_start]:
            raise InvalidUsageException(
                message=f"订单当前状态（{order.status.value}）不允许支付", 
                error_code=40018
            )
        
        # 金额确定
        amount = order.order_amount
        
        # 收款方确定（平台托管账户）
        # 假设平台有一个系统用户ID用于资金托管
        platform_escrow_user_id = self._get_platform_user_id()
        
        # 检查是否已有待支付记录
        existing_payment = Payment.query.filter_by(
            order_id=order_id, 
            status=PaymentStatusEnum.pending
        ).first()
        
        if existing_payment:
            # 可以选择返回已存在的支付记录，或删除后重新创建
            # 这里选择返回已存在的记录
            return self._generate_payment_response(existing_payment)
        
        # 生成唯一的内部交易ID
        internal_transaction_id = f"plt_tx_{uuid.uuid4().hex[:12]}"
        
        # 确定支付方式
        payment_method = payment_data.get('payment_method', 'alipay')  # 默认支付宝
        
        try:
            # 创建Payment记录
            new_payment = Payment(
                status=PaymentStatusEnum.pending,
                order_id=order_id,
                payer_user_id=payer_user_id,
                payee_user_id=platform_escrow_user_id,
                amount=amount,
                payment_method=payment_method,
                internal_transaction_id=internal_transaction_id
            )
            
            db.session.add(new_payment)
            db.session.commit()
            
            # 与支付网关交互，生成支付参数
            gateway_payload = self._generate_payment_gateway_payload(new_payment)
            
            # 构建响应
            return self._generate_payment_response(new_payment, gateway_payload)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建订单支付记录失败: {str(e)}")
            raise BusinessException(message=f"发起支付失败: {str(e)}", status_code=500, error_code=50002)

    def _get_platform_user_id(self):
        """
        获取平台系统账户ID
        :return: 平台托管账户的用户ID
        """
        # TODO: 从系统配置获取平台账户ID，或查询具有特定角色的系统用户
        # 这里简化实现，返回一个固定的ID
        return 1  # 假设ID为1的用户是平台托管账户

    def _generate_payment_gateway_payload(self, payment):
        """
        生成支付网关所需的参数
        :param payment: Payment对象
        :return: 支付网关参数字典
        """
        # 模拟生成支付网关参数
        # 实际实现中，这里会调用第三方支付SDK，例如支付宝、微信支付等
        from flask import current_app
        import random
        
        current_app.logger.info(f"为支付记录 {payment.id} 生成支付网关参数")
        
        # 支付方式不同，返回的参数也不同
        if payment.payment_method == 'alipay':
            return {
                "qr_code_url": f"https://example.com/pay/alipay/qr/{payment.internal_transaction_id}",
                "redirect_url": f"https://example.com/pay/alipay/redirect/{payment.internal_transaction_id}"
            }
        elif payment.payment_method == 'wechat':
            return {
                "qr_code_url": f"https://example.com/pay/wechat/qr/{payment.internal_transaction_id}"
            }
        else:
            return {
                "redirect_url": f"https://example.com/pay/generic/{payment.internal_transaction_id}"
            }

    def _generate_payment_response(self, payment, gateway_payload=None):
        """
        生成支付API响应
        :param payment: Payment对象
        :param gateway_payload: 支付网关参数字典
        :return: 支付响应字典
        """
        # 如果未提供gateway_payload，重新生成
        if gateway_payload is None:
            gateway_payload = self._generate_payment_gateway_payload(payment)
        
        return {
            "internal_transaction_id": payment.internal_transaction_id,
            "order_id": payment.order_id,
            "amount": str(payment.amount),
            "payment_method": payment.payment_method,
            "gateway_payload": gateway_payload
        }

    def handle_payment_webhook(self, webhook_payload):
        """
        处理支付回调（来自支付网关的Webhook）
        :param webhook_payload: 支付网关回调数据
        :return: 处理结果
        """
        from flask import current_app
        
        # 验签：确保回调请求来自真实的支付网关
        # TODO: 实现签名验证逻辑
        is_signature_valid = True  # 简化实现
        
        if not is_signature_valid:
            current_app.logger.error("支付回调签名验证失败")
            return False
        
        # 解析回调数据
        # 假设webhook_payload包含以下字段：
        # - internal_transaction_id: 我们传给支付网关的内部交易ID
        # - external_transaction_id: 支付网关生成的外部交易ID
        # - status: 支付状态 (success, failed)
        # - amount: 支付金额
        
        internal_transaction_id = webhook_payload.get('internal_transaction_id')
        if not internal_transaction_id:
            current_app.logger.error("支付回调缺少internal_transaction_id")
            return False
        
        # 查找支付记录
        payment = Payment.query.filter_by(internal_transaction_id=internal_transaction_id).first()
        if not payment:
            current_app.logger.error(f"未找到匹配的支付记录: {internal_transaction_id}")
            return False
        
        # 状态检查与幂等性：避免重复处理
        if payment.status in [PaymentStatusEnum.succeeded, PaymentStatusEnum.failed]:
            current_app.logger.info(f"支付 {internal_transaction_id} 已处理，当前状态: {payment.status.value}")
            return True  # 已处理，返回成功
        
        # 获取支付状态
        payment_status = webhook_payload.get('status')
        if payment_status not in ['success', 'failed']:
            current_app.logger.error(f"支付回调状态无效: {payment_status}")
            return False
        
        try:
            # 开始数据库事务
            with db.session.begin():
                # 更新支付记录
                if payment_status == 'success':
                    payment.status = PaymentStatusEnum.succeeded
                    payment.paid_at = datetime.utcnow()
                else:
                    payment.status = PaymentStatusEnum.failed
                    payment.error_code = webhook_payload.get('error_code')
                    payment.error_message = webhook_payload.get('error_message')
                
                payment.external_transaction_id = webhook_payload.get('external_transaction_id')
                
                # 如果支付成功，执行后续业务逻辑
                if payment_status == 'success':
                    # 更新订单状态
                    order = Order.query.get(payment.order_id)
                    if order:
                        order.status = OrderStatusEnum.in_progress  # 假设支付成功后订单状态变为进行中
                    
                    # 资金操作
                    self._process_successful_payment(payment)
            
            # 事务已提交
            current_app.logger.info(f"支付回调处理成功: {internal_transaction_id}, 状态: {payment_status}")
            return True
            
        except Exception as e:
            # 事务已回滚
            current_app.logger.error(f"处理支付回调时出错: {str(e)}")
            return False

    def _process_successful_payment(self, payment):
        """
        处理成功支付的后续资金操作
        :param payment: Payment对象
        :return: None
        """
        from flask import current_app
        
        # 1. 雇主支出流水
        payer_wallet = UserWallet.query.filter_by(user_id=payment.payer_user_id).first()
        if not payer_wallet:
            current_app.logger.error(f"支付者 {payment.payer_user_id} 的钱包不存在")
            raise BusinessException(message="支付者钱包不存在", status_code=500, error_code=50003)
        
        # 记录雇主支出交易
        payer_transaction = WalletTransaction(
            user_id=payment.payer_user_id,
            transaction_type=TransactionTypeEnum.payment,
            amount=-payment.amount,
            balance_after=payer_wallet.balance,  # 不需要修改余额，因为是托管支付
            related_payment_id=payment.id,
            related_order_id=payment.order_id,
            description=f"支付订单 #{payment.order_id}"
        )
        
        db.session.add(payer_transaction)
        
        # 2. 平台托管账户收入流水
        platform_wallet = UserWallet.query.filter_by(user_id=payment.payee_user_id).first()
        if not platform_wallet:
            current_app.logger.error(f"平台托管账户 {payment.payee_user_id} 的钱包不存在")
            raise BusinessException(message="平台托管账户钱包不存在", status_code=500, error_code=50004)
        
        # 更新平台托管账户余额
        platform_wallet.balance += payment.amount
        
        # 记录平台托管收入交易
        platform_transaction = WalletTransaction(
            user_id=payment.payee_user_id,
            transaction_type=TransactionTypeEnum.deposit,
            amount=payment.amount,
            balance_after=platform_wallet.balance,
            related_payment_id=payment.id,
            related_order_id=payment.order_id,
            description=f"托管订单 #{payment.order_id} 资金"
        )
        
        db.session.add(platform_transaction)
        
        # 3. 计算零工应得收入（仅作计算，不实际入账）
        order = Order.query.get(payment.order_id)
        if order:
            # 假设有一个字段记录零工最终应得的收入
            freelancer_income = payment.amount * Decimal('0.9')  # 假设平台抽10%
            order.freelancer_income = freelancer_income
            
            current_app.logger.info(f"计算订单 {order.id} 的零工收入: {freelancer_income}")

    def confirm_payment_status(self, current_user_id, internal_transaction_id, confirmation_data):
        """
        手动确认支付状态（管理员功能）
        :param current_user_id: 操作者（管理员）用户ID
        :param internal_transaction_id: 内部交易ID
        :param confirmation_data: 确认数据，包含status等
        :return: 更新后的Payment对象
        """
        from flask import current_app
        
        # 权限校验：确认是管理员
        # TODO: 实现管理员权限检查
        is_admin = True  # 简化实现
        
        if not is_admin:
            raise AuthorizationException(message="您没有管理员权限", error_code=40302)
        
        # 查询支付记录
        payment = Payment.query.filter_by(internal_transaction_id=internal_transaction_id).first()
        if not payment:
            raise NotFoundException(message="支付记录不存在", error_code=40406)
        
        # 状态检查：避免修改已经是终态的支付
        if payment.status in [PaymentStatusEnum.succeeded, PaymentStatusEnum.failed]:
            raise InvalidUsageException(
                message=f"支付已是终态 ({payment.status.value})，无法修改", 
                error_code=40019
            )
        
        # 获取确认状态
        status = confirmation_data.get('status')
        if status not in ['succeeded', 'failed']:
            raise InvalidUsageException(message="无效的支付状态", error_code=40020)
        
        try:
            # 开始事务
            with db.session.begin():
                # 更新支付记录
                if status == 'succeeded':
                    payment.status = PaymentStatusEnum.succeeded
                    payment.paid_at = confirmation_data.get('paid_at', datetime.utcnow())
                else:
                    payment.status = PaymentStatusEnum.failed
                    payment.error_code = confirmation_data.get('error_code')
                    payment.error_message = confirmation_data.get('error_message', '管理员手动确认失败')
                
                payment.external_transaction_id = confirmation_data.get('external_transaction_id', f"manual_{internal_transaction_id}")
                
                # 如果确认为成功，执行后续业务逻辑
                if status == 'succeeded':
                    # 更新订单状态
                    order = Order.query.get(payment.order_id)
                    if order:
                        order.status = OrderStatusEnum.in_progress
                    
                    # 资金操作
                    self._process_successful_payment(payment)
            
            # 事务已提交
            current_app.logger.info(f"管理员 {current_user_id} 手动确认支付 {internal_transaction_id} 状态为 {status}")
            return payment
            
        except Exception as e:
            # 事务已回滚
            current_app.logger.error(f"手动确认支付状态时出错: {str(e)}")
            raise BusinessException(message=f"确认支付状态失败: {str(e)}", status_code=500, error_code=50005)


# 服务实例
wallet_service = WalletService()
payment_service = PaymentService() 