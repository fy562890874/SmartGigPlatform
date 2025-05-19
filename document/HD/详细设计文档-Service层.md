智慧零工平台 - API 层详细设计文档
版本: 1.0
更新日期: 2025年5月16日

1. 引言

本文档定义了智慧零工平台后端 RESTful API 的端点、请求/响应格式以及相关规范。API 层负责处理 HTTP 请求，调用 Service 层执行业务逻辑，并使用已定义的 Schema 进行数据验证和序列化。设计遵循 API规范文档.md。

2. API 层核心原则

RESTful 设计: 使用标准的 HTTP 方法 (GET, POST, PUT, DELETE, PATCH)。
资源导向: API 端点围绕资源进行设计 (名词复数，snake_case)。
版本控制: 所有 API 均以 /api/v1/ 开头。
请求/响应格式: Content-Type: application/json，Accept: application/json。
认证: 使用 JWT (Bearer Token) 进行认证，通过 HTTP Authorization Header 传递。
数据验证与序列化: 使用对应的 Marshmallow Schema 进行请求数据的反序列化、验证，以及响应数据的序列化。
统一响应结构:
成功: {"code": 0, "message": "Success", "data": { ... } / [ ... ] / null}
失败: {"code": <业务错误码>, "message": "<错误信息>", "errors": { ... } / null, "data": null}
错误处理: 将 Service 层抛出的业务异常映射为合适的 HTTP 状态码和统一的错误响应体。
分页与排序: 列表接口 (GET) 支持 page (页码, 默认1), per_page (每页数量, 默认20), sort_by (排序字段及方向, e.g., created_at_desc) 等查询参数。
权限控制: 在 API 端点级别进行必要的认证检查和角色/权限检查（通常通过装饰器实现）。复杂权限逻辑委托给 Service 层。
3. API 端点详细设计

(注: current_user 代表通过 JWT 认证后获得的用户对象或用户ID。所有需要认证的接口都应有相应的安全校验。)

3.1. 认证与授权 (/api/v1/auth)

POST /register
描述: 用户注册。
请求体 Schema: UserRegistrationSchema
响应 Schema (成功): UserSchema (通常返回创建的用户信息，不含密码) 及 JWT Token (可能在响应头或响应体中)。
Service 调用: UserService.register_user()
POST /login
描述: 用户登录。
请求体 Schema: UserLoginSchema
响应 (成功): { "token": "<jwt_token>", "user": UserSchema }
Service 调用: UserService.login_user()
POST /refresh
描述: 刷新 JWT Token (需要有效的旧 Token 或 Refresh Token)。
认证: 需要。
响应 (成功): { "token": "<new_jwt_token>" }
Service 调用: UserService.refresh_jwt_token()
POST /logout
描述: 用户登出 (通常是客户端清除 Token，后端可加入 Token 黑名单机制)。
认证: 需要。
响应 (成功): HTTP 204 No Content 或成功消息。
POST /forgot_password (如果实现)
描述: 发起忘记密码流程 (如发送验证码)。
请求体: { "phone_number": "..." } (需要简单 Schema)
响应 (成功): 成功消息。
POST /reset_password (如果实现)
描述: 使用验证码重置密码。
请求体: { "phone_number": "...", "verification_code": "...", "new_password": "..." } (需要 Schema)
响应 (成功): 成功消息。
3.2. 用户管理 (/api/v1/users)

GET /me
描述: 获取当前登录用户信息。
认证: 需要。
响应 Schema (成功): UserSchema (包含 uuid, phone_number, nickname, avatar_url, current_role, available_roles, status)
Service 调用: UserService.get_user_by_id(current_user.id)
PUT /me
描述: 更新当前登录用户的基本信息 (昵称、头像)。
认证: 需要。
请求体 Schema: UserProfileUpdateSchema
响应 Schema (成功): UserSchema
Service 调用: UserService.update_user_basic_profile(current_user.id, data)
PUT /me/password
描述: 当前用户修改密码。
认证: 需要。
请求体 Schema: PasswordChangeSchema (新增: old_password, new_password)
响应 (成功): HTTP 204 No Content 或成功消息。
Service 调用: UserService.change_password()
POST /me/switch_role
描述: 当前用户切换活动角色。
认证: 需要。
请求体 Schema: { "new_role": "freelancer" | "employer" } (可定义简单 Schema)
响应 Schema (成功): UserSchema (更新后的用户信息)
Service 调用: UserService.switch_user_role()
GET /{user_uuid} (公开接口)
描述: 获取指定用户的公开基本信息 (如果允许)。
响应 Schema (成功): UserSchema (筛选部分公开字段)
Service 调用: UserService.get_user_by_uuid()
3.3. 用户档案 (/api/v1/profiles)

GET /me/freelancer
描述: 获取当前用户的零工档案。
认证: 需要。
响应 Schema (成功): FreelancerProfileSchema
Service 调用: UserProfileService.get_freelancer_profile(current_user.id)
PUT /me/freelancer
描述: 创建或更新当前用户的零工档案。
认证: 需要。
请求体 Schema: FreelancerProfileUpdateSchema
响应 Schema (成功): FreelancerProfileSchema
Service 调用: UserProfileService.create_or_update_freelancer_profile()
GET /me/employer
描述: 获取当前用户的雇主档案。
认证: 需要。
响应 Schema (成功): EmployerProfileSchema
Service 调用: UserProfileService.get_employer_profile(current_user.id)
PUT /me/employer
描述: 创建或更新当前用户的雇主档案。
认证: 需要。
请求体 Schema: EmployerProfileUpdateSchema (创建时可能需要 profile_type)
响应 Schema (成功): EmployerProfileSchema
Service 调用: UserProfileService.create_or_update_employer_profile()
GET /users/{user_uuid}/freelancer (公开接口)
描述: 获取指定用户的公开零工档案。
响应 Schema (成功): FreelancerProfileSchema (筛选公开字段)
Service 调用: UserProfileService.get_public_freelancer_profile()
GET /users/{user_uuid}/employer (公开接口)
描述: 获取指定用户的公开雇主档案。
响应 Schema (成功): EmployerProfileSchema (筛选公开字段)
Service 调用: UserProfileService.get_public_employer_profile()
3.4. 认证管理 (/api/v1/verifications)

POST /submit
描述: 用户提交认证申请 (个人实名/企业)。
认证: 需要。
请求体 Schema: VerificationRecordCreateSchema
响应 Schema (成功): VerificationRecordSchema
Service 调用: VerificationService.submit_verification()
GET /me
描述: 用户获取自己的认证记录。
认证: 需要。
查询参数: profile_type (可选)
响应 Schema (成功): List[VerificationRecordSchema]
Service 调用: VerificationService.get_user_verification_records()
3.5. 工作 (/api/v1/jobs)

POST /
描述: 雇主发布新工作。
认证: 需要 (雇主角色)。
请求体 Schema: JobCreateSchema
响应 Schema (成功): JobSchema
Service 调用: JobService.create_job()
GET /
描述: 搜索/筛选工作列表。
查询参数: category, province, city, district, min_salary, max_salary, salary_type, job_tags (可以是逗号分隔字符串或多个同名参数), q (关键词搜索), is_urgent, start_time_from, start_time_to, page, per_page, sort_by (e.g., created_at_desc, salary_amount_asc)
响应 Schema (成功): { "items": List[JobSchema], "pagination": { ... } }
Service 调用: JobService.search_jobs()
GET /map_search
描述: 地图视野内搜索工作。
查询参数: sw_lat, sw_lon, ne_lat, ne_lon (视野边界), 其他过滤参数同上。
响应 Schema (成功): List[JobSchema] (可能为简化版，仅含ID、标题、薪资、坐标)
Service 调用: JobService.get_jobs_for_map_view()
GET /{job_id}
描述: 获取工作详情。
响应 Schema (成功): JobSchema
Service 调用: JobService.get_job_by_id(increment_view_count=True)
PUT /{job_id}
描述: 雇主更新工作信息。
认证: 需要 (工作发布者)。
请求体 Schema: JobUpdateSchema
响应 Schema (成功): JobSchema
Service 调用: JobService.update_job()
DELETE /{job_id}
描述: 雇主删除工作。
认证: 需要 (工作发布者)。
响应 (成功): HTTP 204 No Content。
Service 调用: JobService.delete_job()
POST /{job_id}/close
描述: 雇主关闭工作招聘。
认证: 需要 (工作发布者)。
响应 Schema (成功): JobSchema
Service 调用: JobService.close_job_listing()
POST /{job_id}/duplicate (需求提及“复制功能”)
描述: 雇主复制已发布的工作。
认证: 需要 (工作发布者)。
响应 Schema (成功): JobSchema (新创建的工作)
Service 调用: (新增) JobService.duplicate_job()
POST /{job_id}/required_skills
描述: 为工作添加技能要求。
认证: 需要 (工作发布者)。
请求体 Schema: JobRequiredSkillSchema
响应 Schema (成功): JobRequiredSkillSchema
Service 调用: JobService.add_required_skill_to_job()
DELETE /{job_id}/required_skills/{skill_id}
描述: 移除工作的技能要求。
认证: 需要 (工作发布者)。
响应 (成功): HTTP 204 No Content。
Service 调用: JobService.remove_required_skill_from_job()
GET /my_posted
描述: 雇主获取自己发布的工作列表。
认证: 需要 (雇主角色)。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[JobSchema], "pagination": { ... } }
Service 调用: JobService.get_jobs_by_employer()
GET /recommendations
描述: 获取个性化推荐工作列表。
认证: 需要 (零工角色)。
查询参数: count (数量)
响应 Schema (成功): List[JobSchema]
Service 调用: JobService.get_recommended_jobs()
3.6. 工作申请 (/api/v1/job_applications) & (/api/v1/jobs/{job_id}/applications)

POST /jobs/{job_id}/apply (或 POST /job_applications 并将 job_id 放入请求体)
描述: 零工申请工作。
认证: 需要 (零工角色)。
请求体 Schema: JobApplicationCreateSchema (如果 job_id 在URL中，则Schema中可省略)
响应 Schema (成功): JobApplicationSchema
Service 调用: JobApplicationService.create_job_application()
GET /my (端点: /api/v1/job_applications/my)
描述: 零工查看我的申请列表。
认证: 需要 (零工角色)。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[JobApplicationSchema], "pagination": { ... } }
Service 调用: JobApplicationService.get_applications_by_freelancer()
POST /{application_id}/cancel (端点: /api/v1/job_applications/{application_id}/cancel)
描述: 零工取消申请。
认证: 需要 (申请提交者)。
请求体 Schema: JobApplicationCancelSchema (通常为空)
响应 Schema (成功): JobApplicationSchema (更新后的申请)
Service 调用: JobApplicationService.cancel_application_by_freelancer()
GET /jobs/{job_id}/applications
描述: 雇主查看指定工作的申请列表。
认证: 需要 (工作发布者)。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[JobApplicationSchema], "pagination": { ... } }
Service 调用: JobApplicationService.get_applications_for_job()
PUT /job_applications/{application_id}/process
描述: 雇主处理申请 (接受/拒绝)。
认证: 需要 (相关工作发布者)。
请求体 Schema: JobApplicationUpdateSchema
响应 Schema (成功): JobApplicationSchema
Service 调用: JobApplicationService.process_application()
3.7. 订单 (/api/v1/orders)

GET /
描述: 用户获取自己的订单列表 (根据角色区分是零工还是雇主)。
认证: 需要。
查询参数: status, role (freelancer/employer, 若不从JWT角色判断), page, per_page, sort_by
响应 Schema (成功): { "items": List[OrderSchema], "pagination": { ... } }
Service 调用: OrderService.get_orders_for_user()
GET /{order_id}
描述: 获取订单详情。
认证: 需要 (订单参与方)。
响应 Schema (成功): OrderSchema
Service 调用: OrderService.get_order_by_id()
POST /{order_id}/actions
描述: 执行订单操作 (开始工作、完成工作、确认完成、取消订单)。
认证: 需要 (订单参与方，具体操作权限由Service判断)。
请求体 Schema: OrderActionSchema
响应 Schema (成功): OrderSchema
Service 调用: OrderService.freelancer_start_work(), OrderService.freelancer_complete_work(), OrderService.employer_confirm_completion(), OrderService.cancel_order() (根据 action 字段分发)
PUT /{order_id}/actual_times
描述: (如果独立) 更新实际工作开始/结束时间。
认证: 需要 (通常是零工)。
请求体 Schema: OrderTimeUpdateSchema
响应 Schema (成功): OrderSchema
Service 调用: (可能集成到 freelancer_complete_work 中)
GET /{order_id}/payment_info (如果需要前端展示支付状态/方式)
描述: 获取订单的支付信息。
认证: 需要 (订单参与方或管理员)。
响应 Schema (成功): List[PaymentSchema] (订单可能有多笔支付或退款记录)
Service 调用: PaymentService.get_payment_by_order_id()
POST /{order_id}/initiate_payment (如果不是接受申请后自动创建支付)
描述: 雇主为订单发起支付。
认证: 需要 (雇主)。
请求体 Schema: { "payment_method": "alipay" | "wechat_pay" } (简单 Schema)
响应 (成功): 包含前端调起第三方支付所需的参数。
Service 调用: PaymentService.initiate_order_payment()
3.8. 评价 (/api/v1/evaluations) & (/api/v1/orders/{order_id}/evaluations)

POST /orders/{order_id}/evaluations
描述: 用户提交订单评价。
认证: 需要 (订单参与方)。
请求体 Schema: EvaluationCreateSchema
响应 Schema (成功): EvaluationSchema
Service 调用: EvaluationService.create_evaluation()
GET /orders/{order_id}/evaluations
描述: 获取订单的评价信息。
响应 Schema (成功): List[EvaluationSchema]
Service 调用: EvaluationService.get_evaluations_for_order()
GET /users/{user_uuid}/evaluations/received
描述: 获取指定用户收到的评价。
查询参数: page, per_page, sort_by
响应 Schema (成功): { "items": List[EvaluationSchema], "pagination": { ... } }
Service 调用: EvaluationService.get_evaluations_for_user(as_role=evaluatee)
GET /users/{user_uuid}/evaluations/given
描述: 获取指定用户给出的评价。
查询参数: page, per_page, sort_by
响应 Schema (成功): { "items": List[EvaluationSchema], "pagination": { ... } }
Service 调用: EvaluationService.get_evaluations_for_user(as_role=evaluator)
3.9. 技能 (/api/v1/skills) & (/api/v1/profiles/me/freelancer/skills)

GET /skills (公开接口)
描述: 获取平台技能标签列表。
查询参数: category, is_hot, q (搜索技能名称), page, per_page
响应 Schema (成功): { "items": List[SkillSchema], "pagination": { ... } }
Service 调用: SkillService.get_all_skills()
GET /profiles/me/freelancer/skills
描述: 零工获取自己的技能列表。
认证: 需要 (零工角色)。
响应 Schema (成功): List[FreelancerSkillSchema]
Service 调用: SkillService.get_freelancer_skills()
POST /profiles/me/freelancer/skills
描述: 零工添加个人技能。
认证: 需要 (零工角色)。
请求体 Schema: FreelancerSkillCreateSchema
响应 Schema (成功): FreelancerSkillSchema
Service 调用: SkillService.add_skill_to_freelancer()
PUT /profiles/me/freelancer/skills/{skill_id}
描述: 零工更新个人技能信息。
认证: 需要 (零工角色)。
请求体 Schema: FreelancerSkillUpdateSchema
响应 Schema (成功): FreelancerSkillSchema
Service 调用: SkillService.update_freelancer_skill()
DELETE /profiles/me/freelancer/skills/{skill_id}
描述: 零工移除个人技能。
认证: 需要 (零工角色)。
响应 (成功): HTTP 204 No Content。
Service 调用: SkillService.remove_skill_from_freelancer()
3.10. 消息与会话 (/api/v1/messages, /api/v1/conversations)

POST /messages
描述: 发送私信。
认证: 需要。
请求体 Schema: MessageCreateSchema
响应 Schema (成功): MessageSchema
Service 调用: MessageService.send_message()
GET /conversations
描述: 获取当前用户的会话列表。
认证: 需要。
查询参数: page, per_page
响应 Schema (成功): { "items": List[ConversationSummarySchema], "pagination": { ... } } (需要定义 ConversationSummarySchema，包含对方用户、最新消息摘要、未读数)
Service 调用: MessageService.get_user_conversations()
GET /conversations/{conversation_id}/messages
描述: 获取指定会话的消息历史。
认证: 需要 (会话参与方)。
查询参数: page, per_page, before_message_id (用于加载更早消息)
响应 Schema (成功): { "items": List[MessageSchema], "pagination": { ... } }
Service 调用: MessageService.get_messages_in_conversation()
POST /messages/mark_read
描述: 标记消息已读。
认证: 需要。
请求体 Schema: MessageMarkReadSchema (包含 message_ids 列表)
响应 (成功): HTTP 204 No Content。
Service 调用: MessageService.mark_messages_as_read()
GET /messages/unread_count
描述: 获取用户未读消息总数。
认证: 需要。
响应 (成功): { "unread_count": int }
Service 调用: MessageService.get_unread_message_count_for_user()
3.11. 通知 (/api/v1/notifications)

GET /
描述: 用户获取自己的通知列表。
认证: 需要。
查询参数: type, is_read, page, per_page, sort_by
响应 Schema (成功): { "items": List[NotificationSchema], "pagination": { ... } }
Service 调用: NotificationService.get_user_notifications()
POST /mark_read
描述: 用户标记通知已读。
认证: 需要。
请求体 Schema: NotificationMarkReadSchema
响应 (成功): HTTP 204 No Content。
Service 调用: NotificationService.mark_notifications_as_read()
DELETE /{notification_id}
描述: 用户删除通知。
认证: 需要 (通知接收者)。
响应 (成功): HTTP 204 No Content。
Service 调用: NotificationService.delete_notification()
GET /unread_count
描述: 获取用户未读通知总数。
认证: 需要。
响应 (成功): { "unread_count": int }
Service 调用: NotificationService.get_unread_notification_count_for_user()
3.12. 收藏夹 (/api/v1/favorites)

POST /
描述: 用户添加收藏。
认证: 需要。
请求体 Schema: FavoriteCreateSchema
响应 Schema (成功): FavoriteSchema
Service 调用: FavoriteService.add_favorite()
DELETE /{favorite_id}
描述: 用户取消收藏。
认证: 需要 (收藏者)。
响应 (成功): HTTP 204 No Content。
Service 调用: FavoriteService.remove_favorite()
GET /
描述: 用户获取自己的收藏列表。
认证: 需要。
查询参数: favorite_type (job, freelancer, employer), page, per_page
响应 Schema (成功): { "items": List[FavoriteListSchema], "pagination": { ... } }
Service 调用: FavoriteService.get_user_favorites()
3.13. 举报 (/api/v1/reports)

POST /
描述: 用户提交举报。
认证: 需要。
请求体 Schema: ReportCreateSchema
响应 Schema (成功): ReportSchema
Service 调用: ReportService.create_report()
GET /my
描述: 用户获取自己提交的举报列表。
认证: 需要。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[ReportSchema], "pagination": { ... } }
Service 调用: ReportService.get_user_reports()
3.14. 纠纷 (/api/v1/disputes)

POST /
描述: 用户针对订单发起纠纷。
认证: 需要 (订单参与方)。
请求体 Schema: DisputeCreateSchema
响应 Schema (成功): DisputeSchema
Service 调用: DisputeService.create_dispute()
GET /my
描述: 用户获取与自己相关的纠纷列表。
认证: 需要。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[DisputeSchema], "pagination": { ... } }
Service 调用: DisputeService.get_disputes_for_user()
GET /{dispute_id}
描述: 获取特定纠纷详情。
认证: 需要 (纠纷参与方或管理员)。
响应 Schema (成功): DisputeSchema
Service 调用: DisputeService.get_dispute_by_id()
GET /orders/{order_id}/dispute
描述: 获取特定订单的纠纷信息。
认证: 需要 (订单参与方或管理员)。
响应 Schema (成功): DisputeSchema (如果存在)
Service 调用: (可能通过 OrderService 间接调用 DisputeService 或 DisputeService 直接提供)
3.15. 钱包 (/api/v1/wallet)

GET /me
描述: 获取当前用户钱包信息。
认证: 需要。
响应 Schema (成功): UserWalletSchema
Service 调用: WalletService.get_user_wallet()
GET /me/transactions
描述: 获取当前用户钱包交易流水。
认证: 需要。
查询参数: transaction_type, date_from, date_to, page, per_page, sort_by
响应 Schema (成功): { "items": List[WalletTransactionSchema], "pagination": { ... } }
Service 调用: WalletService.get_wallet_transactions()
POST /me/withdrawal_requests
描述: 用户发起提现请求。
认证: 需要。
请求体 Schema: WithdrawalRequestCreateSchema
响应 Schema (成功): WithdrawalRequestSchema
Service 调用: WalletService.create_withdrawal_request()
GET /me/withdrawal_requests
描述: 用户查询自己的提现记录。
认证: 需要。
查询参数: status, page, per_page, sort_by
响应 Schema (成功): { "items": List[WithdrawalRequestSchema], "pagination": { ... } }
Service 调用: WalletService.get_user_withdrawal_requests()
3.16. 后台管理 API (/api/v1/admin)

认证与授权 (/auth)

POST /login
描述: 后台管理员登录。
请求体 Schema: AdminUserLoginSchema
响应 (成功): { "token": "<jwt_token>", "user": AdminUserSchema }
Service 调用: AdminAuthService.login_admin()
管理员用户管理 (/management/admins)

GET /
响应 Schema: List[AdminUserSchema]
Service: AdminManagementService.get_all_admin_users()
POST /
请求 Schema: AdminUserSchema (密码需在Service处理)
响应 Schema: AdminUserSchema
Service: AdminManagementService.create_admin_user()
GET /{admin_id}
响应 Schema: AdminUserSchema
Service: AdminManagementService.get_admin_user_by_id()
PUT /{admin_id}
请求 Schema: AdminUserUpdateSchema
响应 Schema: AdminUserSchema
Service: AdminManagementService.update_admin_user()
DELETE /{admin_id}
响应: HTTP 204
Service: AdminManagementService.delete_admin_user()
用户管理 (/users) (已在 UserService 中提及部分接口，这里指管理员操作)

GET /
响应: List[UserSchema] 和分页信息。
Service: UserService.admin_get_users()
PUT /{user_id}/status
请求: { "status": "active" | "inactive" | "banned", "reason": "..." }
响应: UserSchema
Service: UserService.admin_update_user_status()
工作管理 (/jobs)

GET /: Service: JobService.admin_get_jobs() (类似 search_jobs 但有管理员权限)
PUT /{job_id}/status: Service: JobService.admin_manage_job_status() (审核、下架等)
认证审核 (/verifications)

GET /: Service: VerificationService.admin_get_verification_requests()
GET /{record_id}
PUT /{record_id}/review: Service: VerificationService.admin_review_verification()
订单管理 (/orders): Service: OrderService.admin_get_orders(), OrderService.admin_update_order_status()

支付管理 (/payments): Service: PaymentService.admin_get_payments()

评价管理 (/evaluations): Service: EvaluationService.admin_get_evaluations(), EvaluationService.admin_delete_evaluation()

技能库管理 (/skills): Service: SkillService.admin_create_skill(), SkillService.admin_update_skill(), SkillService.admin_delete_skill()

零工技能证书审核 (/freelancer_skills/{user_id}/{skill_id}/verify): Service: SkillService.admin_verify_skill_certificate()

举报管理 (/reports): Service: ReportService.admin_get_reports(), ReportService.admin_process_report()

纠纷管理 (/disputes): Service: DisputeService.admin_get_disputes(), DisputeService.admin_process_dispute()

提现管理 (/withdrawal_requests): Service: WalletService.admin_get_withdrawal_requests(), WalletService.admin_process_withdrawal_request()

系统配置 (/system_configs)

GET /: Service: SystemConfigService.get_all_configs()
GET /{config_key}: Service: SystemConfigService.get_config_by_key()
PUT /{config_key}: Service: SystemConfigService.update_config()
4. 开发细节与规约补充

事务边界: Service 层方法应是主要的事务边界。对于涉及多个写操作的业务逻辑，确保它们在同一个数据库事务中执行。
幂等性: 对于 POST, PUT, DELETE 等可能引起副作用的请求，尤其是在需要重试的场景（如网络问题），应考虑接口的幂等性设计。例如，创建资源时，如果客户端使用相同的唯一请求ID重试，则不应重复创建。
并发控制: 对于如更新工作已接受人数、扣减钱包余额等操作，需考虑并发问题，可使用数据库乐观锁或悲观锁机制。
日志记录:
API 层: 记录请求入口 (URL, Method, Headers, Body摘要) 和响应出口 (Status Code, Body摘要)。
Service 层: 记录关键业务步骤的执行、重要参数、以及任何业务异常。
所有日志应包含 Trace ID 以便链路追踪。
安全性:
除了 JWT 认证，还需实现基于角色的授权 (RBAC)。
对用户输入进行严格过滤和清理，防止 XSS, SQL注入等。
敏感数据 (如密码、身份证号) 在传输和存储时必须加密。Schema 中 load_only=True 对密码是好的实践。
性能考虑:
对于列表查询，合理使用数据库索引。
避免在单个请求中加载过多或过深的嵌套关联数据；按需加载。
对高频读取且不经常变化的数据，考虑在 Service 层引入缓存机制 (如 Redis)。
代码组织:
Service 和 API 按模块/资源组织在不同文件/目录中。
定义清晰的 Service 接口 (如果使用接口抽象)。
异步处理:
需求文档提及的智能匹配、AI辅助、部分通知发送等耗时或非核心链路操作，应由 Service 层调用异步任务队列 (如 Celery) 处理。API 接口应快速返回，告知任务已提交。
