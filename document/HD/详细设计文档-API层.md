智慧零工平台 - API 层详细设计文档
版本: 2.0
更新日期: 2025年5月16日

1. 引言

本文档定义了智慧零工平台后端 RESTful API 的端点、请求/响应格式以及相关规范。API 层作为系统的入口，负责处理来自客户端 (Web/App/小程序) 的 HTTP 请求，调用相应的 Service 层方法执行业务逻辑，并使用已定义的 Marshmallow Schema 进行数据验证和序列化。本文档严格遵循 API规范文档.md 中定义的基本原则和规范，并与 Service 层详细设计文档 和已有的 Model 及 Schema 定义保持一致。

2. API 层核心原则与规约

RESTful 设计:
使用标准的 HTTP 方法:
GET: 获取资源。
POST: 创建新资源或执行动作。
PUT: 完整替换资源 (谨慎使用，优先考虑 PATCH)。
PATCH: 部分更新资源。
DELETE: 删除资源。
面向资源: API 端点围绕名词复数形式的资源进行设计 (e.g., /api/v1/jobs, /api/v1/users)。
路径参数用于标识单个资源 (e.g., /api/v1/jobs/{job_id})。
URL 规范:
根路径: 所有 API 均以 /api/v1/ 开头。
资源名称和路径参数: 采用 snake_case 命名。
嵌套资源: 适度使用，建议最多一层嵌套 (e.g., /api/v1/jobs/{job_id}/applications)。
非 CRUD 操作: 对于难以映射到标准 CRUD 的操作，使用动词，放在资源路径末尾 (e.g., /api/v1/job_applications/{application_id}/accept)。
版本控制: 通过 URL 进行版本控制 (/api/v1/)。
请求/响应格式:
Content-Type: application/json (对于 POST, PUT, PATCH 请求)。
Accept: application/json (客户端期望接收 JSON 响应)。
字段命名: 请求体和响应体字段名统一使用 snake_case。
日期时间: 统一使用 ISO 8601 格式字符串 (带时区信息，e.g., 2025-05-16T10:30:00+08:00)。
空值处理: 对于不存在或无值的字段，返回 null。
认证与授权:
认证: 通过 JWT (Bearer Token) 实现，在 Authorization Header 中传递。需要认证的接口应明确指出。
授权: API 层进行基本的角色检查或资源所有权检查。复杂权限逻辑委托给 Service 层处理。
数据验证与序列化:
使用对应的 Marshmallow Schema 对请求参数和请求体进行严格验证和反序列化。
使用 Marshmallow Schema 将 Service 层返回的数据序列化为 JSON 响应。
统一响应结构 (参照 API规范文档.md):
成功 (2xx):
JSON

{
  "code": 0, // 固定为 0
  "message": "Success",
  "data": { /* 单个资源对象 */ }
}
或对于列表资源:
JSON

{
  "code": 0,
  "message": "Success",
  "data": {
    "items": [ /* 资源列表 */ ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_items": 150,
      "total_pages": 8
    }
  }
}
或对于无返回内容的操作 (如 DELETE, 部分 PUT): HTTP 204 No Content，或:
JSON

{
  "code": 0,
  "message": "Operation successful", // 或具体操作成功的消息
  "data": null
}
失败 (4xx, 5xx):
JSON

{
  "code": 40001, // 业务错误码
  "message": "Invalid input parameter: email format is incorrect.",
  "errors": { // 可选，详细字段错误
    "email": ["Invalid email format."]
  },
  "data": null
}
错误处理:
API 层捕获 Service 层抛出的业务异常及框架自身的异常。
将其映射为标准的 HTTP 状态码和上述统一的错误响应结构。
常见的 HTTP 状态码：
200 OK: 请求成功，通常用于 GET, PUT, PATCH。
201 Created: 资源创建成功，通常用于 POST。
204 No Content: 操作成功，无返回内容 (如 DELETE)。
400 Bad Request: 请求无效 (如参数错误、格式错误，由 Schema 验证捕获)。
401 Unauthorized: 未认证或认证失败。
403 Forbidden: 已认证，但无权限访问。
404 Not Found: 请求的资源不存在。
409 Conflict: 资源冲突 (如尝试创建已存在的唯一资源)。
422 Unprocessable Entity: 请求格式正确，但语义错误导致无法处理 (如业务规则校验失败)。
429 Too Many Requests: 请求过于频繁 (限流)。
500 Internal Server Error: 服务器内部错误。
分页、排序与过滤 (针对列表 GET 请求):
分页: 使用查询参数 page (页码, 默认 1) 和 per_page (每页数量, 默认 20，可设最大值)。响应中包含分页信息 (total_items, total_pages)。
排序: 使用查询参数 sort_by (e.g., created_at_desc, salary_amount_asc)。支持多字段排序。
过滤: 根据具体资源的需求，提供明确的查询参数进行过滤 (e.g., status=active, job_category=IT)。
文档生成: 利用 Flask-RESTX 自动生成 Swagger/OpenAPI 3.0 文档，包含每个端点的描述、参数、请求体、响应体示例及错误码。
3. API 端点详细设计

(以下 API 设计将严格对应已提供的 Schema。current_user 指通过 JWT 认证解析出的用户对象或其标识。)

3.1. 认证与授权模块 (/api/v1/auth)

POST /register
描述: 用户注册 (手机号、密码、用户类型)。
请求体 Schema: UserRegistrationSchema
响应 (201 Created): UserSchema (不含密码) 及 JWT Token (在 data 或响应头中)。
JSON

{
  "code": 0,
  "message": "User registered successfully.",
  "data": {
    "token": "<jwt_token>",
    "user": { /* UserSchema (excluding password) */ }
  }
}
Service 方法: UserService.register_user()
POST /login
描述: 用户登录 (手机号、密码)。
请求体 Schema: UserLoginSchema
响应 (200 OK):
JSON

{
  "code": 0,
  "message": "Login successful.",
  "data": {
    "token": "<jwt_token>",
    "user": { /* UserSchema (excluding password) */ }
  }
}
Service 方法: UserService.login_user()
POST /refresh
描述: 刷新 JWT Access Token (通常需要有效的 Refresh Token，或在 Access Token 短期内过期时使用)。
认证: 需要 (有效的 JWT 或 Refresh Token)。
响应 (200 OK):
JSON

{
  "code": 0,
  "message": "Token refreshed successfully.",
  "data": {
    "token": "<new_access_token>"
  }
}
Service 方法: UserService.refresh_jwt_token()
POST /logout
描述: 用户登出。后端可实现 Token 黑名单机制。
认证: 需要。
响应 (200 OK / 204 No Content):
JSON

{
  "code": 0,
  "message": "Logout successful.",
  "data": null
}
Service 方法: (后端可能无特定操作，或将 Token 加入黑名单)
POST /forgot_password (若实现)
描述: 用户发起忘记密码流程，请求发送密码重置指令 (如验证码)。
请求体 Schema: (新增) ForgotPasswordSchema { phone_number: str }
响应 (200 OK): { "code": 0, "message": "Password reset instructions sent.", "data": null }
Service 方法: UserService.send_password_reset_instructions()
POST /reset_password (若实现)
描述: 用户通过验证码或链接重置密码。
请求体 Schema: (新增) ResetPasswordSchema { token_or_code: str, new_password: str }
响应 (200 OK): { "code": 0, "message": "Password reset successfully.", "data": null }
Service 方法: UserService.reset_password_with_token()
3.2. 用户信息与档案模块 (/api/v1/users, /api/v1/profiles)

GET /users/me
描述: 获取当前登录用户的详细信息 (聚合了 User, FreelancerProfile, EmployerProfile 等)。
认证: 需要。
响应 (200 OK) Schema: UserSchema (可能需要扩展UserSchema以包含profile的嵌套或有独立字段聚合) 或一个聚合了多档案信息的自定义Schema。
为对齐现有 Schema，可能返回 UserSchema，并通过独立的 profile 接口获取档案。或者 UserSchema 嵌套 Profile 信息 (如果 User Model 有直接关系)。
假设 UserSchema 本身不含 Profile 详情，客户端需分开调用。
响应 (200 OK): UserSchema (仅用户基础信息)。
Service 方法: UserService.get_user_by_id(current_user.id)
PUT /users/me
描述: 更新当前登录用户的基本资料 (如昵称、头像，这些字段在 User 表中没有，应更新 UserProfileUpdateSchema 对应的User基础信息，或指更新 FreelancerProfile/EmployerProfile 中的通用字段如 nickname, avatar_url)。
鉴于 UserProfileUpdateSchema 只有 nickname, avatar_url，这更像是更新用户在 User 表或其直接关联的基础 Profile 表（如果有）的字段。如果 nickname/avatar_url 分别在 FreelancerProfile 和 EmployerProfile，则应调用对应的Profile更新接口。
假设是更新 User 表中不敏感的，或一个共享的基础Profile信息：
认证: 需要。
请求体 Schema: UserProfileUpdateSchema
响应 (200 OK) Schema: UserSchema (更新后的用户)。
Service 方法: UserService.update_user_basic_profile(current_user.id, data)
PUT /users/me/password
描述: 当前用户修改密码。
认证: 需要。
请求体 Schema: (新增) PasswordChangeSchema { old_password: str, new_password: str }
响应 (200 OK / 204 No Content): { "code": 0, "message": "Password updated successfully.", "data": null }
Service 方法: UserService.change_password(current_user.id, old_password, new_password)
POST /users/me/switch_role
描述: 当前用户切换活动角色 (在 available_roles 范围内)。
认证: 需要。
请求体 Schema: (新增) UserRoleSwitchSchema { new_role: str } (validate against UserRoleEnum)
响应 (200 OK) Schema: UserSchema (包含更新后的 current_role)
Service 方法: UserService.switch_user_role(current_user.id, new_role)
GET /profiles/me/freelancer
描述: 获取当前用户的零工档案。
认证: 需要。
响应 (200 OK) Schema: FreelancerProfileSchema (如果不存在则返回 404 或带 null 数据的成功响应)。
Service 方法: UserProfileService.get_freelancer_profile(current_user.id)
PUT /profiles/me/freelancer
描述: 创建或更新当前用户的零工档案。
认证: 需要。
请求体 Schema: FreelancerProfileUpdateSchema
响应 (200 OK / 201 Created) Schema: FreelancerProfileSchema
Service 方法: UserProfileService.create_or_update_freelancer_profile(current_user.id, data)
GET /profiles/me/employer
描述: 获取当前用户的雇主档案。
认证: 需要。
响应 (200 OK) Schema: EmployerProfileSchema (如果不存在则返回 404 或带 null 数据的成功响应)。
Service 方法: UserProfileService.get_employer_profile(current_user.id)
PUT /profiles/me/employer
描述: 创建或更新当前用户的雇主档案。
认证: 需要。
请求体 Schema: EmployerProfileUpdateSchema (创建时可能需要 profile_type 字段，如果 EmployerProfileSchema 中的 profile_type 是 required=True，则此 Schema 也应包含)。
响应 (200 OK / 201 Created) Schema: EmployerProfileSchema
Service 方法: UserProfileService.create_or_update_employer_profile(current_user.id, data, profile_type_from_data_or_existing)
GET /users/{user_uuid}/profile (公开档案查看，需明确是零工还是雇主，或两者聚合)
描述: 查看指定用户的公开档案 (具体哪个档案或聚合信息需明确)。
查询参数: role_type=freelancer|employer (可选，如果一个接口提供两种)
响应 (200 OK) Schema: FreelancerProfileSchema 或 EmployerProfileSchema (筛选公开字段)
Service 方法: UserProfileService.get_public_freelancer_profile(user_uuid) 或 UserProfileService.get_public_employer_profile(user_uuid)
3.3. 认证管理模块 (/api/v1/verifications)

POST /submit
描述: 用户提交认证申请 (个人实名认证、企业资质认证)。
认证: 需要。
请求体 Schema: VerificationRecordCreateSchema
响应 (201 Created) Schema: VerificationRecordSchema
Service 方法: VerificationService.submit_verification(current_user.id, data)
GET /me
描述: 用户获取自己的认证记录。
认证: 需要。
查询参数: profile_type (可选, 筛选特定类型的认证记录, e.g., 'freelancer')
响应 (200 OK) Schema: { "items": List[VerificationRecordSchema] }
Service 方法: VerificationService.get_user_verification_records(current_user.id, profile_type)
3.4. 工作模块 (/api/v1/jobs)

POST /
描述: 雇主发布新工作。
认证: 需要 (雇主角色)。
请求体 Schema: JobCreateSchema
响应 (201 Created) Schema: JobSchema
Service 方法: JobService.create_job(current_user.id, data)
GET /
描述: 搜索/筛选工作列表 (公开接口)。
查询参数:
q (关键词: 标题, 描述)
job_category
location_province, location_city, location_district
latitude, longitude, radius_km (用于地理位置范围搜索)
salary_min, salary_max, salary_type
job_tags (e.g., tags=tag1,tag2 or tags=tag1&tags=tag2)
is_urgent (boolean)
start_time_from, start_time_to (ISO DateTime)
page (int, default 1), per_page (int, default 20)
sort_by (e.g., created_at_desc, salary_amount_asc, distance_asc [若有地理位置搜索])
响应 (200 OK) Schema: { "data": { "items": List[JobSchema], "pagination": { ... } } }
Service 方法: JobService.search_jobs(filters, sort_by, page, per_page)
GET /{job_id}
描述: 获取指定工作详情 (公开接口)。
响应 (200 OK) Schema: JobSchema
Service 方法: JobService.get_job_by_id(job_id, increment_view_count=True)
PUT /{job_id}
描述: 雇主更新已发布的工作信息。
认证: 需要 (工作发布者)。
路径参数: job_id (int)
请求体 Schema: JobUpdateSchema
响应 (200 OK) Schema: JobSchema
Service 方法: JobService.update_job(job_id, current_user.id, data)
DELETE /{job_id}
描述: 雇主删除已发布的工作。
认证: 需要 (工作发布者)。
路径参数: job_id (int)
响应 (204 No Content):
Service 方法: JobService.delete_job(job_id, current_user.id)
POST /{job_id}/close
描述: 雇主关闭工作招聘 (将状态改为 filled 或 cancelled)。
认证: 需要 (工作发布者)。
路径参数: job_id (int)
响应 (200 OK) Schema: JobSchema
Service 方法: JobService.close_job_listing(job_id, current_user.id)
POST /{job_id}/duplicate
描述: 雇主复制现有工作以快速创建新工作。
认证: 需要 (工作发布者)。
路径参数: job_id (int)
响应 (201 Created) Schema: JobSchema (新创建的工作)
Service 方法: JobService.duplicate_job(job_id, current_user.id)
GET /my_posted
描述: 雇主获取自己发布的工作列表。
认证: 需要 (雇主角色)。
查询参数: status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[JobSchema], "pagination": { ... } } }
Service 方法: JobService.get_jobs_by_employer(current_user.id, filters, page, per_page)
GET /recommendations
描述: (零工) 获取个性化推荐工作列表。
认证: 需要 (零工角色)。
查询参数: count (int, default 10)
响应 (200 OK) Schema: { "data": { "items": List[JobSchema] } }
Service 方法: JobService.get_recommended_jobs(current_user.id, count)
工作技能要求子资源 (/api/v1/jobs/{job_id}/required_skills)
POST /
描述: 为工作添加技能要求。
认证: 需要 (工作发布者)。
请求体 Schema: JobRequiredSkillSchema (只含 skill_id, is_mandatory)
响应 (201 Created) Schema: JobRequiredSkillSchema (包含嵌套的 SkillSchema)
Service 方法: JobService.add_required_skill_to_job(job_id, current_user.id, skill_data)
DELETE /{skill_id}
描述: 移除工作的指定技能要求。
认证: 需要 (工作发布者)。
响应 (204 No Content):
Service 方法: JobService.remove_required_skill_from_job(job_id, current_user.id, skill_id)
3.5. 工作申请模块 (/api/v1/job_applications, /api/v1/jobs/{job_id}/applications)

POST /jobs/{job_id}/apply
描述: 零工申请工作。
认证: 需要 (零工角色)。
路径参数: job_id (int)
请求体 Schema: JobApplicationCreateSchema (只含 apply_message)
响应 (201 Created) Schema: JobApplicationSchema
Service 方法: JobApplicationService.create_job_application(current_user.id, job_id, data)
GET /job_applications/my
描述: 零工查看自己提交的申请列表。
认证: 需要 (零工角色)。
查询参数: status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[JobApplicationSchema], "pagination": { ... } } }
Service 方法: JobApplicationService.get_applications_by_freelancer(current_user.id, filters, page, per_page)
GET /job_applications/{application_id}
描述: 获取单个申请详情。
认证: 需要 (申请人或相关雇主)。
响应 (200 OK) Schema: JobApplicationSchema
Service 方法: JobApplicationService.get_application_by_id(application_id, current_user.id)
POST /job_applications/{application_id}/cancel
描述: 零工取消已提交的申请。
认证: 需要 (申请提交者)。
路径参数: application_id (int)
请求体 Schema: JobApplicationCancelSchema (空)
响应 (200 OK) Schema: JobApplicationSchema (更新后的申请)
Service 方法: JobApplicationService.cancel_application_by_freelancer(application_id, current_user.id)
GET /jobs/{job_id}/applications
描述: 雇主查看其发布工作的申请列表。
认证: 需要 (工作发布者)。
路径参数: job_id (int)
查询参数: status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[JobApplicationSchema], "pagination": { ... } } }
Service 方法: JobApplicationService.get_applications_for_job(job_id, current_user.id, filters, page, per_page)
PUT /job_applications/{application_id}/process
描述: 雇主处理申请 (接受/拒绝)。
认证: 需要 (相关工作的发布者)。
路径参数: application_id (int)
请求体 Schema: JobApplicationUpdateSchema (status, rejection_reason)
响应 (200 OK) Schema: JobApplicationSchema
Service 方法: JobApplicationService.process_application(application_id, current_user.id, data)
3.6. 订单模块 (/api/v1/orders)

GET /
描述: 用户 (零工/雇主) 获取自己的订单列表。
认证: 需要。
查询参数: status, role (可选, 'freelancer'/'employer', 若不从JWT推断), page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[OrderSchema], "pagination": { ... } } }
Service 方法: OrderService.get_orders_for_user(current_user.id, current_user.current_role, filters, page, per_page)
GET /{order_id}
描述: 获取指定订单详情。
认证: 需要 (订单参与方)。
路径参数: order_id (int)
响应 (200 OK) Schema: OrderSchema
Service 方法: OrderService.get_order_by_id(order_id, current_user.id)
POST /{order_id}/actions
描述: 用户执行订单相关操作 (如开始工作、完成工作、确认完成、取消订单)。
认证: 需要 (订单参与方, 具体操作权限由Service层判断)。
路径参数: order_id (int)
请求体 Schema: OrderActionSchema (action, cancellation_reason [可选])
响应 (200 OK) Schema: OrderSchema
Service 方法: 根据 action 调用 OrderService 中对应的方法 (e.g., freelancer_start_work, employer_confirm_completion, cancel_order)。
PUT /{order_id}/actual_times
描述: (若独立) 零工更新订单的实际工作开始和结束时间。
认证: 需要 (订单零工)。
路径参数: order_id (int)
请求体 Schema: OrderTimeUpdateSchema
响应 (200 OK) Schema: OrderSchema
Service 方法: (可能集成在 OrderService.freelancer_complete_work 中或独立) OrderService.update_order_actual_times(order_id, current_user.id, data)
3.7. 支付模块 (/api/v1/payments - 主要为回调和特定查询)

POST /notify/wechat (通常由微信服务器调用，需验签)
描述: 微信支付回调接口。
请求体: XML (微信支付格式)
响应: XML (符合微信支付规范)
Service 方法: PaymentService.process_wechat_payment_notification(request_data)
POST /notify/alipay (通常由支付宝服务器调用，需验签)
描述: 支付宝支付回调接口。
请求体: Form Data (支付宝格式)
响应: "success" / "failure" (符合支付宝规范)
Service 方法: PaymentService.process_alipay_payment_notification(request_data)
GET /orders/{order_id}/info (获取订单支付信息)
描述: 获取特定订单的支付记录信息。
认证: 需要 (订单参与方或管理员)。
响应 (200 OK) Schema: { "data": { "items": List[PaymentSchema] } } (一个订单可能有多条支付/退款记录)
Service 方法: PaymentService.get_payment_by_order_id(order_id)
POST /orders/{order_id}/initiate (用户主动发起支付)
描述: 用户为订单发起支付，获取前端调用第三方支付所需的参数。
认证: 需要 (订单支付方，通常是雇主)。
请求体 Schema: (新增) PaymentInitiateSchema { payment_method: str } (e.g., "alipay_app", "wechat_jsapi")
响应 (200 OK): { "data": { /* 支付参数，结构取决于 payment_method */ } }
Service 方法: PaymentService.initiate_order_payment(order_id, current_user.id, payment_method)
3.8. 评价模块 (/api/v1/orders/{order_id}/evaluations, /api/v1/evaluations)

POST /orders/{order_id}/evaluations
描述: 用户 (零工或雇主) 提交对已完成订单的评价。
认证: 需要 (订单参与方)。
路径参数: order_id (int)
请求体 Schema: EvaluationCreateSchema
响应 (201 Created) Schema: EvaluationSchema
Service 方法: EvaluationService.create_evaluation(current_user.id, order_id, data)
GET /orders/{order_id}/evaluations
描述: 获取指定订单的所有评价。
路径参数: order_id (int)
响应 (200 OK) Schema: { "data": { "items": List[EvaluationSchema] } }
Service 方法: EvaluationService.get_evaluations_for_order(order_id)
GET /users/{user_uuid}/evaluations/received
描述: 获取指定用户收到的评价列表。
路径参数: user_uuid (str)
查询参数: page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[EvaluationSchema], "pagination": { ... } } }
Service 方法: EvaluationService.get_evaluations_for_user(user_uuid, as_role_evaluatee=True)
GET /users/{user_uuid}/evaluations/given
描述: 获取指定用户给出的评价列表。
路径参数: user_uuid (str)
查询参数: page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[EvaluationSchema], "pagination": { ... } } }
Service 方法: EvaluationService.get_evaluations_for_user(user_uuid, as_role_evaluator=True)
3.9. 技能模块 (/api/v1/skills, /api/v1/profiles/me/freelancer/skills)

GET /skills (公开)
描述: 获取平台技能标签库。
查询参数: q (搜索名称), category, is_hot, page, per_page
响应 (200 OK) Schema: { "data": { "items": List[SkillSchema], "pagination": { ... } } }
Service 方法: SkillService.get_all_skills(filters, page, per_page)
GET /profiles/me/freelancer/skills
描述: 当前零工获取自己的技能列表。
认证: 需要 (零工角色)。
响应 (200 OK) Schema: { "data": { "items": List[FreelancerSkillSchema] } }
Service 方法: SkillService.get_freelancer_skills(current_user.id)
POST /profiles/me/freelancer/skills
描述: 当前零工为自己的档案添加技能。
认证: 需要 (零工角色)。
请求体 Schema: FreelancerSkillCreateSchema
响应 (201 Created) Schema: FreelancerSkillSchema
Service 方法: SkillService.add_skill_to_freelancer(current_user.id, data)
PUT /profiles/me/freelancer/skills/{skill_id}
描述: 当前零工更新已关联的技能信息 (熟练度、经验、证书URL)。
认证: 需要 (零工角色)。
路径参数: skill_id (int)
请求体 Schema: FreelancerSkillUpdateSchema
响应 (200 OK) Schema: FreelancerSkillSchema
Service 方法: SkillService.update_freelancer_skill(current_user.id, skill_id, data)
DELETE /profiles/me/freelancer/skills/{skill_id}
描述: 当前零工从自己的档案中移除技能。
认证: 需要 (零工角色)。
路径参数: skill_id (int)
响应 (204 No Content):
Service 方法: SkillService.remove_skill_from_freelancer(current_user.id, skill_id)
3.10. 消息与会话模块 (/api/v1/messages, /api/v1/conversations)

POST /messages
描述: 发送私信。
认证: 需要。
请求体 Schema: MessageCreateSchema
响应 (201 Created) Schema: MessageSchema
Service 方法: MessageService.send_message(current_user.id, data)
GET /conversations
描述: 获取当前用户的会话列表 (通常包含最新消息摘要和未读数)。
认证: 需要。
查询参数: page, per_page
响应 (200 OK) Schema: { "data": { "items": List[ConversationSummarySchema], "pagination": { ... } } } (需要定义 ConversationSummarySchema)
Service 方法: MessageService.get_user_conversations(current_user.id, page, per_page)
GET /conversations/{conversation_id}/messages
描述: 获取指定会话的消息历史。
认证: 需要 (会话参与方)。
路径参数: conversation_id (str)
查询参数: page, per_page, before_message_id (用于向上翻页加载更多)
响应 (200 OK) Schema: { "data": { "items": List[MessageSchema], "pagination": { ... } } }
Service 方法: MessageService.get_messages_in_conversation(current_user.id, conversation_id, page, per_page, before_message_id)
POST /messages/mark_read
描述: 批量标记消息为已读。
认证: 需要。
请求体 Schema: MessageMarkReadSchema (包含 message_ids 列表)
响应 (200 OK / 204 No Content): { "code": 0, "message": "Messages marked as read.", "data": null }
Service 方法: MessageService.mark_messages_as_read(current_user.id, message_ids)
POST /conversations/{conversation_id}/mark_read
描述: 将指定会话的所有消息标记为已读。
认证: 需要 (会话参与方)。
响应 (200 OK / 204 No Content):
Service方法: MessageService.mark_conversation_as_read(current_user.id, conversation_id)
GET /messages/unread_count
描述: 获取当前用户所有会话的未读消息总数。
认证: 需要。
响应 (200 OK): { "data": { "unread_count": int } }
Service 方法: MessageService.get_unread_message_count_for_user(current_user.id)
3.11. 通知模块 (/api/v1/notifications)

GET /
描述: 获取当前用户的通知列表。
认证: 需要。
查询参数: notification_type, is_read (boolean), page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[NotificationSchema], "pagination": { ... } } }
Service 方法: NotificationService.get_user_notifications(current_user.id, filters, page, per_page)
POST /mark_read
描述: 用户标记通知为已读 (可批量或全部)。
认证: 需要。
请求体 Schema: NotificationMarkReadSchema
响应 (200 OK / 204 No Content): { "code": 0, "message": "Notifications marked as read.", "data": null }
Service 方法: NotificationService.mark_notifications_as_read(current_user.id, data)
DELETE /{notification_id}
描述: 用户删除自己的某条通知。
认证: 需要 (通知接收者)。
路径参数: notification_id (int)
响应 (204 No Content):
Service 方法: NotificationService.delete_notification(current_user.id, notification_id)
GET /unread_count
描述: 获取当前用户未读通知的总数。
认证: 需要。
响应 (200 OK): { "data": { "unread_count": int } }
Service 方法: NotificationService.get_unread_notification_count_for_user(current_user.id)
3.12. 收藏夹模块 (/api/v1/favorites)

POST /
描述: 用户添加收藏 (工作、零工用户、雇主用户)。
认证: 需要。
请求体 Schema: FavoriteCreateSchema
响应 (201 Created) Schema: FavoriteSchema (包含动态嵌套的 target 对象基本信息)
Service 方法: FavoriteService.add_favorite(current_user.id, data)
DELETE /{favorite_id}
描述: 用户取消收藏。
认证: 需要 (收藏的创建者)。
路径参数: favorite_id (int)
响应 (204 No Content):
Service 方法: FavoriteService.remove_favorite(current_user.id, favorite_id)
GET /
描述: 用户获取自己的收藏列表。
认证: 需要。
查询参数: favorite_type (enum: 'job', 'freelancer', 'employer'), page, per_page
响应 (200 OK) Schema: { "data": { "items": List[FavoriteListSchema], "pagination": { ... } } }
Service 方法: FavoriteService.get_user_favorites(current_user.id, favorite_type, page, per_page)
3.13. 举报模块 (/api/v1/reports)

POST /
描述: 用户提交举报 (针对工作、用户、订单、消息、评价等)。
认证: 需要。
请求体 Schema: ReportCreateSchema
响应 (201 Created) Schema: ReportSchema
Service 方法: ReportService.create_report(current_user.id, data)
GET /my
描述: 用户获取自己提交的举报列表及其处理状态。
认证: 需要。
查询参数: status, report_type, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[ReportSchema], "pagination": { ... } } }
Service 方法: ReportService.get_user_reports(current_user.id, filters, page, per_page)
3.14. 纠纷处理模块 (/api/v1/disputes)

POST /
描述: 用户针对订单发起纠纷。
认证: 需要 (订单参与方)。
请求体 Schema: DisputeCreateSchema
响应 (201 Created) Schema: DisputeSchema
Service 方法: DisputeService.create_dispute(current_user.id, data)
GET /my
描述: 用户获取与自己相关的纠纷列表 (作为发起方或订单另一方)。
认证: 需要。
查询参数: status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[DisputeSchema], "pagination": { ... } } }
Service 方法: DisputeService.get_disputes_for_user(current_user.id, filters, page, per_page)
GET /{dispute_id}
描述: 获取特定纠纷的详细信息。
认证: 需要 (纠纷参与方或管理员)。
路径参数: dispute_id (int)
响应 (200 OK) Schema: DisputeSchema
Service 方法: DisputeService.get_dispute_by_id(dispute_id, current_user.id)
GET /orders/{order_id}/dispute
描述: 获取特定订单关联的纠纷信息。
认证: 需要 (订单参与方或管理员)。
路径参数: order_id (int)
响应 (200 OK) Schema: DisputeSchema (如果存在，否则 404 或带 null data)
Service 方法: DisputeService.get_dispute_by_order_id(order_id, current_user.id)
3.15. 钱包与提现模块 (/api/v1/wallet)

GET /me
描述: 获取当前用户的钱包信息 (余额、冻结金额)。
认证: 需要。
响应 (200 OK) Schema: UserWalletSchema
Service 方法: WalletService.get_user_wallet(current_user.id)
GET /me/transactions
描述: 获取当前用户的钱包交易流水。
认证: 需要。
查询参数: transaction_type, date_from, date_to, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[WalletTransactionSchema], "pagination": { ... } } }
Service 方法: WalletService.get_wallet_transactions(current_user.id, filters, page, per_page)
POST /me/withdrawal_requests
描述: 用户发起提现请求。
认证: 需要。
请求体 Schema: WithdrawalRequestCreateSchema
响应 (201 Created) Schema: WithdrawalRequestSchema
Service 方法: WalletService.create_withdrawal_request(current_user.id, data)
GET /me/withdrawal_requests
描述: 用户查询自己的提现申请记录。
认证: 需要。
查询参数: status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[WithdrawalRequestSchema], "pagination": { ... } } }
Service 方法: WalletService.get_user_withdrawal_requests(current_user.id, filters, page, per_page)
3.16. 后台管理接口 (/api/v1/admin)

认证与授权 (/auth)
POST /login
描述: 后台管理员登录。
请求体 Schema: AdminUserLoginSchema
响应 (200 OK): { "data": { "token": "<jwt_token>", "user": AdminUserSchema } }
Service 调用: AdminAuthService.login_admin(data)
管理员用户管理 (/management/admins)
GET /
认证: 需要 (特定高权限管理员角色)。
查询参数: role, status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[AdminUserSchema], "pagination": { ... } } }
Service 调用: AdminManagementService.get_all_admin_users(filters, page, per_page)
POST /
认证: 需要 (特定高权限管理员角色)。
请求体 Schema: AdminUserSchema (创建时 password 字段应为必填)
响应 (201 Created) Schema: AdminUserSchema (不含密码)
Service 调用: AdminManagementService.create_admin_user(data)
GET /{admin_id}
认证: 需要 (特定高权限管理员角色)。
响应 (200 OK) Schema: AdminUserSchema
Service 调用: AdminManagementService.get_admin_user_by_id(admin_id)
PUT /{admin_id}
认证: 需要 (特定高权限管理员角色)。
请求体 Schema: AdminUserUpdateSchema
响应 (200 OK) Schema: AdminUserSchema
Service 调用: AdminManagementService.update_admin_user(admin_id, data)
DELETE /{admin_id}
认证: 需要 (特定高权限管理员角色)。
响应 (204 No Content):
Service 调用: AdminManagementService.delete_admin_user(admin_id)
平台用户管理 (/users)
GET /
认证: 需要 (管理员)。
查询参数: q (搜索手机号/昵称), status, role, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[UserSchema], "pagination": { ... } } }
Service 调用: UserService.admin_get_users(filters, page, per_page)
GET /{user_id}
认证: 需要 (管理员)。
响应 (200 OK) Schema: UserSchema (可能需要扩展或包含 Profile 概要)
Service 调用: UserService.get_user_by_id(user_id)
PUT /{user_id}/status
认证: 需要 (管理员)。
请求体 Schema: (新增) AdminUserStatusUpdateSchema { status: str, reason: str (可选) } (status 校验 UserStatusEnum)
响应 (200 OK) Schema: UserSchema
Service 调用: UserService.admin_update_user_status(user_id, new_status, reason)
工作管理 (/jobs)
GET /
认证: 需要 (管理员)。
查询参数: 同用户端 GET /jobs，但可能有额外管理视角参数。
响应 (200 OK) Schema: { "data": { "items": List[JobSchema], "pagination": { ... } } }
Service 调用: JobService.admin_get_jobs(filters, page, per_page) (或复用 search_jobs 并增加权限判断)
PUT /{job_id}/status
认证: 需要 (管理员)。
请求体 Schema: (新增) AdminJobStatusUpdateSchema { status: str, reason: str (可选) } (status 校验 JobStatusEnum, e.g., rejected, active, cancelled)
响应 (200 OK) Schema: JobSchema
Service 调用: JobService.admin_manage_job_status(job_id, new_status, reason)
认证审核 (/verifications)
GET /
认证: 需要 (管理员)。
查询参数: status, profile_type, user_id, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[VerificationRecordSchema], "pagination": { ... } } }
Service 调用: VerificationService.admin_get_verification_requests(filters, page, per_page)
GET /{record_id}
认证: 需要 (管理员)。
响应 (200 OK) Schema: VerificationRecordSchema
Service 调用: (新增) VerificationService.admin_get_verification_by_id(record_id)
PUT /{record_id}/review
认证: 需要 (管理员)。
请求体 Schema: VerificationRecordReviewSchema
响应 (200 OK) Schema: VerificationRecordSchema
Service 调用: VerificationService.admin_review_verification(record_id, current_admin_user.id, data)
订单管理 (/orders)
GET /
认证: 需要 (管理员)。
查询参数: user_id, job_id, status, date_from, date_to, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[OrderSchema], "pagination": { ... } } }
Service 调用: OrderService.admin_get_orders(filters, page, per_page)
PUT /{order_id}/status
认证: 需要 (管理员)。
请求体 Schema: (新增) AdminOrderStatusUpdateSchema { status: str, reason: str (可选) } (status 校验 OrderStatusEnum)
响应 (200 OK) Schema: OrderSchema
Service 调用: OrderService.admin_update_order_status(order_id, new_status, reason)
支付管理 (/payments)
GET /
认证: 需要 (管理员)。
查询参数: order_id, user_id (payer/payee), status, payment_method, date_from, date_to, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[PaymentSchema], "pagination": { ... } } }
Service 调用: PaymentService.admin_get_payments(filters, page, per_page)
评价管理 (/evaluations)
GET /
认证: 需要 (管理员)。
查询参数: user_id (evaluator/evaluatee), order_id, job_id, rating, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[EvaluationSchema], "pagination": { ... } } }
Service 调用: EvaluationService.admin_get_evaluations(filters, page, per_page)
DELETE /{evaluation_id}
认证: 需要 (管理员)。
请求体 Schema: (新增) AdminEvaluationDeleteSchema { reason: str }
响应 (204 No Content):
Service 调用: EvaluationService.admin_delete_evaluation(evaluation_id, reason)
技能库管理 (/skills)
POST /
认证: 需要 (管理员)。
请求体 Schema: SkillCreateSchema
响应 (201 Created) Schema: SkillSchema
Service 调用: SkillService.admin_create_skill(data)
PUT /{skill_id}
认证: 需要 (管理员)。
请求体 Schema: SkillUpdateSchema
响应 (200 OK) Schema: SkillSchema
Service 调用: SkillService.admin_update_skill(skill_id, data)
DELETE /{skill_id}
认证: 需要 (管理员)。
响应 (204 No Content):
Service 调用: SkillService.admin_delete_skill(skill_id)
零工技能证书审核 (/freelancer_skills/{user_id}/{skill_id}/verify)
PUT /
认证: 需要 (管理员)。
请求体 Schema: (新增) AdminFreelancerSkillVerifySchema { is_verified: bool }
响应 (200 OK) Schema: FreelancerSkillSchema
Service 调用: SkillService.admin_verify_skill_certificate(user_id, skill_id, is_verified)
举报管理 (/reports)
GET /
认证: 需要 (管理员)。
查询参数: reporter_user_id, target_id, report_type, status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[ReportSchema], "pagination": { ... } } }
Service 调用: ReportService.admin_get_reports(filters, page, per_page)
GET /{report_id}
认证: 需要 (管理员)。
响应 (200 OK) Schema: ReportSchema
Service 调用: (新增) ReportService.admin_get_report_by_id(report_id)
PUT /{report_id}/process
认证: 需要 (管理员)。
请求体 Schema: ReportUpdateSchema
响应 (200 OK) Schema: ReportSchema
Service 调用: ReportService.admin_process_report(report_id, current_admin_user.id, data)
纠纷管理 (/disputes)
GET /
认证: 需要 (管理员)。
查询参数: order_id, initiator_user_id, status, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[DisputeSchema], "pagination": { ... } } }
Service 调用: DisputeService.admin_get_disputes(filters, page, per_page)
GET /{dispute_id}
认证: 需要 (管理员)。
响应 (200 OK) Schema: DisputeSchema
Service 调用: (新增) DisputeService.admin_get_dispute_by_id(dispute_id)
PUT /{dispute_id}/process
认证: 需要 (管理员)。
请求体 Schema: DisputeUpdateSchema
响应 (200 OK) Schema: DisputeSchema
Service 调用: DisputeService.admin_process_dispute(dispute_id, current_admin_user.id, data)
提现管理 (/withdrawal_requests)
GET /
认证: 需要 (管理员)。
查询参数: user_id, status, withdrawal_method, page, per_page, sort_by
响应 (200 OK) Schema: { "data": { "items": List[WithdrawalRequestSchema], "pagination": { ... } } }
Service 调用: WalletService.admin_get_withdrawal_requests(filters, page, per_page)
PUT /{request_id}/process
认证: 需要 (管理员)。
请求体 Schema: WithdrawalRequestUpdateSchema
响应 (200 OK) Schema: WithdrawalRequestSchema
Service 调用: WalletService.admin_process_withdrawal_request(request_id, current_admin_user.id, data)
系统配置 (/system_configs)
GET /
认证: 需要 (特定高权限管理员)。
响应 (200 OK) Schema: { "data": { "items": List[SystemConfigSchema] } }
Service 调用: SystemConfigService.get_all_configs()
GET /{config_key}
认证: 需要 (特定高权限管理员)。
响应 (200 OK) Schema: SystemConfigSchema
Service 调用: SystemConfigService.get_config_by_key(config_key)
PUT /{config_key}
认证: 需要 (特定高权限管理员)。
请求体 Schema: SystemConfigUpdateSchema
响应 (200 OK) Schema: SystemConfigSchema
Service 调用: SystemConfigService.update_config(config_key, data)
POST / (如果允许动态添加配置)
认证: 需要 (特定高权限管理员)。
请求体 Schema: SystemConfigSchema
响应 (201 Created) Schema: SystemConfigSchema
Service 调用: (新增) SystemConfigService.create_config(data)
DELETE /{config_key} (如果允许删除配置)
认证: 需要 (特定高权限管理员)。
响应 (204 No Content):
Service 调用: (新增) SystemConfigService.delete_config(config_key)
4. API 开发规约补充

控制器 (Controller/Resource) 职责:
从 HTTP 请求中提取路径参数、查询参数、请求体。
使用对应的 Marshmallow Schema 对请求体验证和反序列化。
调用相关的 Service 方法，传递处理后的数据。
接收 Service 返回结果或捕获 Service 抛出的业务异常。
使用对应的 Marshmallow Schema 将成功结果序列化为 JSON。
将业务异常转换为标准的 HTTP 错误响应。
处理 JWT 认证和基本的角色/权限检查 (可使用 Flask-RESTX 或 Flask-JWT-Extended 装饰器)。
不应包含任何业务逻辑。
Schema 实例化和使用:
在每个 API 方法中，根据操作类型（创建、更新、读取）实例化相应的 Schema。
使用 load(request.json) 进行反序列化和验证。
使用 dump(service_result) 进行序列化。
对于列表，使用 dump(service_result, many=True)。
日志记录:
在请求开始时记录：请求方法, URL, 客户端IP, User-Agent, Trace ID。
若请求体验证失败 (Schema validation error)，记录详细的验证错误信息。
在请求结束时记录：响应状态码, 响应体摘要 (可选, 注意敏感信息), 处理时长。
安全性:
所有需要认证的端点必须有 @jwt_required (或类似) 装饰器。
需要特定角色的端点应有角色检查装饰器 (e.g., @roles_required(['admin', 'employer']))。
Flask-RESTX 提供了 @expect 装饰器来声明期望的输入 Schema，有助于自动生成 Swagger 文档和进行基本验证。
文件上传 (如头像、认证附件、工作附件):
当前 Schema 定义中，附件多为 fields.URL() 或 fields.List(fields.URL())，这通常意味着文件上传是独立处理的（比如上传到 OSS/S3 后，将 URL 存入业务表）。API 层可能需要单独的文件上传接口 (POST /uploads)，该接口返回文件 URL，然后在业务接口中提交这些 URL。
如果采用直接通过业务接口上传文件，需要使用如 werkzeug.datastructures.FileStorage 并结合 Flask-Uploads 或自定义逻辑处理。Schema 中对应字段类型需要调整。
