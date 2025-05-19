from ..models.message import Message, MessageTypeEnum
from ..models.notification import Notification, NotificationTypeEnum
from ..models.user import User
from ..core.extensions import db
from ..utils.exceptions import NotFoundException, AuthorizationException, BusinessException, InvalidUsageException
from sqlalchemy.orm import joinedload
from datetime import datetime

class MessageService:
    def get_user_conversations_summary(self, user_id, page=1, per_page=10):
        """
        获取用户的会话列表摘要
        :param user_id: 用户ID
        :param page: 页码
        :param per_page: 每页数量
        :return: 会话摘要列表和分页信息
        """
        from flask import current_app
        
        # 获取该用户参与的所有会话ID
        subquery_sender = db.session.query(Message.conversation_id).filter(Message.sender_id == user_id)
        subquery_recipient = db.session.query(Message.conversation_id).filter(Message.recipient_id == user_id)
        distinct_conversation_ids_query = subquery_sender.union(subquery_recipient).distinct()
        
        try:
            # 获取所有会话ID
            conversation_ids = [row[0] for row in distinct_conversation_ids_query.all()]
            
            # 会话摘要列表
            conversation_summaries = []
            
            for cid in conversation_ids:
                # 获取最新一条消息
                last_message = Message.query.filter_by(conversation_id=cid).order_by(
                    Message.created_at.desc()).first()
                
                if not last_message:
                    continue
                
                # 确定对话的另一方ID
                other_party_id = last_message.sender_id if last_message.recipient_id == user_id else last_message.recipient_id
                
                # 查询另一方用户信息
                other_party_user = User.query.get(other_party_id)
                if not other_party_user:
                    current_app.logger.warning(f"会话 {cid} 的另一方用户 {other_party_id} 不存在")
                    continue
                
                # 获取用户昵称和头像
                nickname = None
                avatar_url = None
                
                if hasattr(other_party_user, 'freelancer_profile') and other_party_user.freelancer_profile:
                    nickname = other_party_user.freelancer_profile.nickname
                    avatar_url = other_party_user.freelancer_profile.avatar_url
                elif hasattr(other_party_user, 'employer_profile') and other_party_user.employer_profile:
                    nickname = other_party_user.employer_profile.nickname
                    avatar_url = other_party_user.employer_profile.avatar_url
                
                # 使用手机号作为备选
                if not nickname:
                    nickname = other_party_user.phone_number
                
                # 统计未读消息数
                unread_count = Message.query.filter_by(
                    conversation_id=cid, 
                    recipient_id=user_id, 
                    is_read=False
                ).count()
                
                # 构建会话摘要对象
                summary = {
                    "conversation_id": cid,
                    "other_party_id": other_party_id,
                    "other_party_nickname": nickname,
                    "other_party_avatar_url": avatar_url,
                    "last_message_content": last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                    "last_message_created_at": last_message.created_at,
                    "unread_count": unread_count
                }
                
                conversation_summaries.append(summary)
            
            # 按最新消息时间排序
            conversation_summaries.sort(key=lambda x: x["last_message_created_at"], reverse=True)
            
            # 手动分页
            total = len(conversation_summaries)
            total_pages = (total + per_page - 1) // per_page if total > 0 else 1
            start = (page - 1) * per_page
            end = min(start + per_page, total)
            
            paginated_summaries = conversation_summaries[start:end]
            
            # 构建分页信息
            pagination = {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total
            }
            
            return {
                "items": paginated_summaries,
                "pagination": pagination
            }
            
        except Exception as e:
            current_app.logger.error(f"获取用户会话摘要时出错: {str(e)}")
            raise BusinessException(message=f"获取会话列表失败: {str(e)}", status_code=500, error_code=50001)

    def get_messages_in_conversation(self, user_id, conversation_id, page=1, per_page=20, before_message_id=None):
        """
        获取会话中的消息
        :param user_id: 当前用户ID
        :param conversation_id: 会话ID
        :param page: 页码
        :param per_page: 每页数量
        :param before_message_id: 获取此ID之前的消息（用于加载更早消息）
        :return: 消息列表和分页信息
        """
        from flask import current_app
        
        # 权限校验：验证用户是否是会话参与者
        # 解析conversation_id（假设格式为"小ID_大ID"）
        try:
            user_ids = conversation_id.split('_')
            if len(user_ids) != 2:
                raise InvalidUsageException(message="会话ID格式不正确", error_code=40002)
            
            # 检查用户是否是会话参与者
            if str(user_id) not in user_ids:
                message_check = Message.query.filter_by(conversation_id=conversation_id).first()
                if not message_check or (message_check.sender_id != user_id and message_check.recipient_id != user_id):
                    raise AuthorizationException(message="您无权访问此会话", error_code=40301)
        except ValueError:
            # 如果conversation_id格式不是"ID_ID"
            # 直接查询消息表验证
            message_check = Message.query.filter_by(conversation_id=conversation_id).first()
            if not message_check or (message_check.sender_id != user_id and message_check.recipient_id != user_id):
                raise AuthorizationException(message="您无权访问此会话", error_code=40301)
        
        # 构建基础查询
        query = Message.query.filter_by(conversation_id=conversation_id)
        
        # 如果提供了before_message_id，则获取该消息之前的消息
        if before_message_id:
            query = query.filter(Message.id < before_message_id)
        
        # 按时间倒序排序（最新的在前）
        query = query.order_by(Message.created_at.desc())
        
        # 执行分页
        paginated_messages = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 标记消息为已读
        try:
            updated_count = Message.query.filter(
                Message.conversation_id == conversation_id,
                Message.recipient_id == user_id,
                Message.is_read == False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })
            
            if updated_count > 0:
                db.session.commit()
                current_app.logger.info(f"已将 {updated_count} 条消息标记为已读")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"标记消息为已读时出错: {str(e)}")
            # 不影响主流程，继续返回消息
        
        return paginated_messages

    def send_new_message(self, sender_id, message_data):
        """
        发送新消息
        :param sender_id: 发送者ID
        :param message_data: 消息数据，包含recipient_id, content等
        :return: 创建的Message对象
        """
        from flask import current_app
        
        # 校验接收者存在
        recipient_id = message_data.get('recipient_id')
        if not recipient_id:
            raise InvalidUsageException(message="未提供接收者ID", error_code=40003)
        
        recipient = User.query.get(recipient_id)
        if not recipient:
            raise NotFoundException(message="接收用户不存在", error_code=40401)
        
        # 校验不能给自己发消息
        if sender_id == recipient_id:
            raise InvalidUsageException(message="不能给自己发送消息", error_code=40004)
        
        # 生成会话ID（按ID大小排序）
        conversation_id = f"{min(sender_id, recipient_id)}_{max(sender_id, recipient_id)}"
        
        # 创建消息
        new_message = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            conversation_id=conversation_id,
            content=message_data.get('content', ''),
            message_type=message_data.get('message_type', MessageTypeEnum.text),
            related_resource_type=message_data.get('related_resource_type'),
            related_resource_id=message_data.get('related_resource_id'),
            is_read=False
        )
        
        try:
            db.session.add(new_message)
            db.session.commit()
            
            # TODO: 这里可以触发实时推送通知给接收方
            
            return new_message
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发送消息失败: {str(e)}")
            raise BusinessException(message=f"发送消息失败: {str(e)}", status_code=500, error_code=50002)


class NotificationService:
    def get_my_notifications(self, user_id, filters=None, page=1, per_page=20):
        """
        获取用户的通知列表
        :param user_id: 用户ID
        :param filters: 过滤条件，如is_read, notification_type
        :param page: 页码
        :param per_page: 每页数量
        :return: 通知列表和分页信息
        """
        if filters is None:
            filters = {}
        
        # 构建基础查询
        query = Notification.query.filter_by(user_id=user_id)
        
        # 应用过滤条件
        if 'is_read' in filters:
            query = query.filter(Notification.is_read == filters['is_read'])
        
        if 'notification_type' in filters:
            try:
                query = query.filter(Notification.notification_type == filters['notification_type'])
            except Exception:
                # 如果类型无效，忽略此过滤条件
                pass
        
        # 按时间倒序排序
        query = query.order_by(Notification.created_at.desc())
        
        # 执行分页
        paginated_notifications = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_notifications

    def mark_notification_read(self, user_id, notification_id):
        """
        标记单个通知为已读
        :param user_id: 用户ID
        :param notification_id: 通知ID
        :return: 更新后的通知对象
        """
        from flask import current_app
        
        # 查询通知
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            raise NotFoundException(message="通知未找到或无权限操作", error_code=40402)
        
        # 如果通知未读，则标记为已读
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            
            try:
                db.session.commit()
                current_app.logger.info(f"已将通知 {notification_id} 标记为已读")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"标记通知为已读时出错: {str(e)}")
                raise BusinessException(message=f"标记通知已读失败: {str(e)}", status_code=500, error_code=50003)
        
        return notification

    def mark_all_my_notifications_read(self, user_id):
        """
        标记用户所有通知为已读
        :param user_id: 用户ID
        :return: 更新的通知数量
        """
        from flask import current_app
        
        try:
            # 批量更新未读通知
            current_time = datetime.utcnow()
            updated_count = Notification.query.filter_by(
                user_id=user_id, is_read=False
            ).update({
                'is_read': True,
                'read_at': current_time
            })
            
            db.session.commit()
            current_app.logger.info(f"已将用户 {user_id} 的 {updated_count} 条通知标记为已读")
            
            return {"updated_count": updated_count}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"标记所有通知为已读时出错: {str(e)}")
            raise BusinessException(message=f"标记所有通知已读失败: {str(e)}", status_code=500, error_code=50004)
    
    def create_notification(self, user_id, notification_data):
        """
        创建新通知
        :param user_id: 接收通知的用户ID
        :param notification_data: 通知数据，包含type, title, content等
        :return: 创建的Notification对象
        """
        from flask import current_app
        
        try:
            # 创建通知
            new_notification = Notification(
                user_id=user_id,
                notification_type=notification_data.get('notification_type', NotificationTypeEnum.system_announcement),
                title=notification_data.get('title', '系统通知'),
                content=notification_data.get('content', ''),
                related_resource_type=notification_data.get('related_resource_type'),
                related_resource_id=notification_data.get('related_resource_id'),
                is_read=False
            )
            
            db.session.add(new_notification)
            db.session.commit()
            
            current_app.logger.info(f"已为用户 {user_id} 创建新通知 ID: {new_notification.id}")
            
            return new_notification
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建通知失败: {str(e)}")
            raise BusinessException(message=f"创建通知失败: {str(e)}", status_code=500, error_code=50005)


# 服务实例
message_service = MessageService()
notification_service = NotificationService() 