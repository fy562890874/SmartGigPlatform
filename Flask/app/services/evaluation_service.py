from ..models.evaluation import Evaluation, EvaluatorRoleEnum
from ..models.order import Order, OrderStatusEnum
from ..models.user import User
from ..models.profile import FreelancerProfile, EmployerProfile
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime

class EvaluationService:
    def create_evaluation(self, evaluator_user_id, order_id, evaluation_data):
        """
        提交订单评价
        :param evaluator_user_id: 评价者用户ID
        :param order_id: 订单ID
        :param evaluation_data: 评价数据，包含rating, comment等
        :return: 创建的Evaluation对象
        """
        from flask import current_app
        
        # 查询订单
        order = Order.query.get(order_id)
        if not order:
            raise NotFoundException(message="订单不存在", error_code=40401)
        
        # 校验订单状态
        if order.status != OrderStatusEnum.completed:
            raise InvalidUsageException(message="订单尚未完成，不能评价", error_code=40001)
        
        # 确定评价者角色和被评价者ID
        evaluator_role = None
        evaluatee_user_id = None
        
        if evaluator_user_id == order.freelancer_user_id:
            evaluator_role = EvaluatorRoleEnum.freelancer
            evaluatee_user_id = order.employer_user_id
        elif evaluator_user_id == order.employer_user_id:
            evaluator_role = EvaluatorRoleEnum.employer
            evaluatee_user_id = order.freelancer_user_id
        else:
            raise AuthorizationException(message="无权评价此订单", error_code=40301)
        
        # 检查是否已评价
        existing_eval = Evaluation.query.filter_by(
            order_id=order_id,
            evaluator_user_id=evaluator_user_id
        ).first()
        
        if existing_eval:
            raise BusinessException(message="您已评价过此订单", status_code=409, error_code=40901)
        
        try:
            # 创建评价记录
            new_evaluation = Evaluation(
                order_id=order_id,
                job_id=order.job_id,
                evaluator_user_id=evaluator_user_id,
                evaluatee_user_id=evaluatee_user_id,
                evaluator_role=evaluator_role,
                rating=evaluation_data.get('rating'),
                comment=evaluation_data.get('comment', ''),
                tags=evaluation_data.get('tags', []),
                is_anonymous=evaluation_data.get('is_anonymous', False)
            )
            
            db.session.add(new_evaluation)
            db.session.commit()
            
            # 更新被评价者平均评分（可以改为异步任务）
            self._update_user_average_rating(evaluatee_user_id)
            
            return new_evaluation
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建评价时出错: {str(e)}")
            raise BusinessException(message=f"提交评价失败: {str(e)}", status_code=500, error_code=50001)

    def _update_user_average_rating(self, user_id):
        """
        更新用户平均评分
        :param user_id: 用户ID
        :return: None
        """
        from flask import current_app
        
        try:
            # 查询用户所有有效评分
            ratings = [e.rating for e in Evaluation.query.filter_by(evaluatee_user_id=user_id).all() if e.rating]
            
            if not ratings:
                current_app.logger.info(f"用户 {user_id} 没有有效评分，不更新平均分")
                return
            
            # 计算新平均分
            new_avg_rating = sum(ratings) / len(ratings)
            
            # 查询被评价者
            evaluatee_user = User.query.get(user_id)
            if not evaluatee_user:
                current_app.logger.warning(f"被评价用户 {user_id} 不存在，无法更新平均分")
                return
            
            # 更新对应档案
            updated = False
            
            # 检查是否有自由职业者角色
            if hasattr(evaluatee_user, 'freelancer_profile') and evaluatee_user.freelancer_profile:
                evaluatee_user.freelancer_profile.average_rating = new_avg_rating
                updated = True
            
            # 检查是否有雇主角色
            if hasattr(evaluatee_user, 'employer_profile') and evaluatee_user.employer_profile:
                evaluatee_user.employer_profile.average_rating = new_avg_rating
                updated = True
            
            if updated:
                db.session.commit()
                current_app.logger.info(f"已更新用户 {user_id} 的平均评分为 {new_avg_rating}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户平均评分时出错: {str(e)}")
            # 不抛出异常，因为这是次要操作
    
    def get_evaluations_for_order(self, order_id, current_user_id=None):
        """
        获取订单评价
        :param order_id: 订单ID
        :param current_user_id: 当前用户ID（用于处理匿名评价）
        :return: 评价列表
        """
        # 查询评价列表，并关联用户信息
        evaluations_query = Evaluation.query.filter_by(order_id=order_id)
        evaluations = evaluations_query.options(
            joinedload(Evaluation.evaluator).joinedload(User.freelancer_profile),
            joinedload(Evaluation.evaluator).joinedload(User.employer_profile)
        ).all()
        
        # 处理匿名评价
        for eval_item in evaluations:
            # 如果评价是匿名的，且当前用户是被评价者（且非管理员）
            if eval_item.is_anonymous and current_user_id == eval_item.evaluatee_user_id:
                # 隐藏评价者信息（在API层序列化时处理）
                eval_item._hide_evaluator_info = True
        
        return evaluations
    
    def get_received_evaluations_for_user(self, user_uuid, requesting_user_id=None, filters=None, page=1, per_page=10):
        """
        获取用户收到的评价
        :param user_uuid: 用户UUID
        :param requesting_user_id: 请求查看的用户ID（用于处理匿名评价）
        :param filters: 过滤条件，如rating
        :param page: 页码
        :param per_page: 每页数量
        :return: 评价列表和分页信息
        """
        if filters is None:
            filters = {}
            
        # 查询被评价用户
        evaluatee_user = User.query.filter_by(uuid=user_uuid).first()
        if not evaluatee_user:
            raise NotFoundException(message="用户不存在", error_code=40401)
        
        # 基础查询
        query = Evaluation.query.filter_by(evaluatee_user_id=evaluatee_user.id)
        
        # 关联评价者信息
        query = query.options(
            joinedload(Evaluation.evaluator).joinedload(User.freelancer_profile),
            joinedload(Evaluation.evaluator).joinedload(User.employer_profile)
        )
        
        # 应用过滤条件
        if 'rating' in filters:
            try:
                rating = int(filters['rating'])
                if 1 <= rating <= 5:
                    query = query.filter(Evaluation.rating == rating)
            except (ValueError, TypeError):
                pass  # 忽略无效的评分过滤
        
        # 按时间倒序排序
        query = query.order_by(Evaluation.created_at.desc())
        
        # 执行分页
        paginated_evaluations = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 处理匿名评价
        for eval_item in paginated_evaluations.items:
            # 如果评价是匿名的，且当前用户是被评价者（且非管理员）
            if eval_item.is_anonymous and requesting_user_id != eval_item.evaluator_user_id:
                # 在对象中添加标记，供API层处理
                eval_item._hide_evaluator_info = True
        
        return paginated_evaluations
    
    def get_given_evaluations_by_user(self, evaluator_user_id, page=1, per_page=10):
        """
        获取用户给出的评价
        :param evaluator_user_id: 评价者用户ID
        :param page: 页码
        :param per_page: 每页数量
        :return: 评价列表和分页信息
        """
        # 基础查询
        query = Evaluation.query.filter_by(evaluator_user_id=evaluator_user_id)
        
        # 关联被评价者信息和工作信息
        query = query.options(
            joinedload(Evaluation.evaluatee).joinedload(User.freelancer_profile),
            joinedload(Evaluation.evaluatee).joinedload(User.employer_profile),
            joinedload(Evaluation.job)
        )
        
        # 按时间倒序排序
        query = query.order_by(Evaluation.created_at.desc())
        
        # 执行分页
        paginated_evaluations = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_evaluations


# 服务实例
evaluation_service = EvaluationService() 