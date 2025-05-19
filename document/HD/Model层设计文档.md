
# 智慧零工平台 - 后端 Model 层设计方案文档

**文档版本:** 1.0
**更新日期:** 2025年4月26日

**1. 引言**

**1.1. 目的**
本文档旨在详细定义智慧零工平台后端微服务中 Model 层的逻辑结构、核心模型及其关系。本文档基于已确定的数据库 Schema (`createDB.sql`) 和整体 MVC 架构设计原则 (`MVC架构设计文档.txt`)，为后续使用 SQLAlchemy ORM 进行具体实现提供清晰的蓝图。

**1.2. 范围**
本文档聚焦于 Model 层的逻辑设计，包括：
*   定义与数据库表一一对应的核心模型。
*   描述每个模型的主要属性及其数据类型和约束。
*   阐明模型之间的主要关系（一对一、一对多、多对多）及其含义。
*   强调 Model 层的职责边界，不涉及具体的业务逻辑实现或数据库操作代码。

**1.3. 术语定义**
*   **Model (模型):** 代表应用程序核心数据结构的 Python 类，直接映射数据库中的表。负责数据的持久化表示。
*   **Attribute (属性):** 模型类中的变量，对应数据库表中的列。
*   **Relationship (关系):** 模型之间通过外键建立的连接，如一对一、一对多、多对多。
*   **ORM (Object-Relational Mapping):** 对象关系映射，本文档基于使用 SQLAlchemy 作为 ORM。
*   **Schema:** 数据库的结构定义，来源于 `createDB.sql`。

**2. Model 层核心原则**

遵循 `MVC架构设计文档.txt` 中定义的原则：
*   **数据持久化:** Model 层是数据持久化的唯一接口，封装了与数据库表的交互。
*   **结构映射:** 每个 Model 类严格对应 `createDB.sql` 中的一个数据库表。模型的属性对应表的列。
*   **关系定义:** 模型之间显式定义由外键产生的关系，便于 ORM 进行关联查询和操作。
*   **基础验证:** 模型包含由数据库约束定义的基础验证（如非空、唯一、长度限制）。
*   **无业务逻辑:** Model 层不包含任何业务处理逻辑，仅关注数据的结构和存储。业务逻辑由 Service 层负责。

**3. 核心模型定义**

以下是根据 `createDB.sql` 设计的核心模型及其属性和关系：

**3.1. User (用户基础信息模型)**
*   **对应表:** `users`
*   **描述:** 存储平台所有用户的核心认证信息、角色和基本状态。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `phone_number`: 手机号, String(20), Unique, Not Null (主要登录凭证)
    *   `password_hash`: 哈希密码, String(255), Not Null
    *   `email`: 邮箱, String(100), Unique, Nullable (可选登录/通知)
    *   `wechat_openid`: 微信 OpenID, String(128), Unique, Nullable
    *   `alipay_userid`: 支付宝 UserID, String(128), Unique, Nullable
    *   `current_role`: 当前活跃角色, Enum('freelancer', 'employer'), Not Null, Default 'freelancer'
    *   `available_roles`: 拥有的角色列表, JSON, Not Null (e.g., ["freelancer", "employer"])
    *   `status`: 账号状态, Enum('pending_verification', 'active', 'inactive', 'banned'), Not Null, Default 'pending_verification'
    *   `last_login_at`: 最后登录时间, DateTime(6), Nullable
    *   `registered_at`: 注册时间, DateTime(6), Not Null, Default CURRENT_TIMESTAMP(6)
    *   `created_at`: 创建时间, DateTime(6), Not Null, Default CURRENT_TIMESTAMP(6)
    *   `updated_at`: 更新时间, DateTime(6), Not Null, Default CURRENT_TIMESTAMP(6) on update
*   **关系:**
    *   One-to-One with `FreelancerProfile` (通过 `FreelancerProfile.user_id`)
    *   One-to-One with `EmployerProfile` (通过 `EmployerProfile.user_id`)
    *   One-to-Many with `Job` (作为雇主, 通过 `Job.employer_user_id`)
    *   One-to-Many with `JobApplication` (作为零工申请者, 通过 `JobApplication.freelancer_user_id`)
    *   One-to-Many with `JobApplication` (作为工作发布者, 通过 `JobApplication.employer_user_id`)
    *   One-to-Many with `Order` (作为零工, 通过 `Order.freelancer_user_id`)
    *   One-to-Many with `Order` (作为雇主, 通过 `Order.employer_user_id`)
    *   One-to-Many with `Payment` (作为支付方, 通过 `Payment.payer_user_id`)
    *   One-to-Many with `Payment` (作为收款方, 通过 `Payment.payee_user_id`)
    *   One-to-Many with `Evaluation` (作为评价者, 通过 `Evaluation.evaluator_user_id`)
    *   One-to-Many with `Evaluation` (作为被评价者, 通过 `Evaluation.evaluatee_user_id`)
    *   Many-to-Many with `Skill` (通过 `FreelancerSkill` 关联表)
    *   One-to-Many with `Message` (作为发送者, 通过 `Message.sender_id`)
    *   One-to-Many with `Message` (作为接收者, 通过 `Message.recipient_id`)
    *   One-to-Many with `VerificationRecord` (通过 `VerificationRecord.user_id`)
    *   One-to-Many with `WithdrawalRequest` (通过 `WithdrawalRequest.user_id`)
    *   One-to-Many with `WalletTransaction` (通过 `WalletTransaction.user_id`)
    *   One-to-One with `UserWallet` (通过 `UserWallet.user_id`)
    *   One-to-Many with `Notification` (通过 `Notification.user_id`)
    *   One-to-Many with `Favorite` (通过 `Favorite.user_id`)
    *   One-to-Many with `Report` (作为举报者, 通过 `Report.reporter_user_id`)
    *   One-to-Many with `Dispute` (作为争议发起者, 通过 `Dispute.initiator_user_id`)

**3.2. FreelancerProfile (零工档案模型)**
*   **对应表:** `freelancer_profiles`
*   **描述:** 存储零工用户的详细信息、认证状态、偏好和统计数据。
*   **核心属性:**
    *   `user_id`: 主键 & 外键 (-> users.id), BigInt (Unsigned)
    *   `real_name`: 真实姓名, String(50), Nullable
    *   `id_card_number_encrypted`: 加密身份证号, String(255), Nullable
    *   `gender`: 性别, Enum('male', 'female', 'other', 'unknown'), Not Null, Default 'unknown'
    *   `birth_date`: 出生日期, Date, Nullable
    *   `avatar_url`: 头像 URL, String(512), Nullable
    *   `nickname`: 昵称, String(50), Nullable
    *   `location_province`: 省份, String(50), Nullable
    *   `location_city`: 城市, String(50), Nullable
    *   `location_district`: 区县, String(50), Nullable
    *   `bio`: 个人简介, Text, Nullable
    *   `work_preference`: 工作偏好, JSON, Nullable
    *   `verification_status`: 实名认证状态, Enum('unverified', 'pending', 'verified', 'failed'), Not Null, Default 'unverified'
    *   `verification_record_id`: 最新认证记录ID (-> verification_records.id), BigInt (Unsigned), Nullable
    *   `credit_score`: 信用分, Integer, Not Null, Default 100
    *   `average_rating`: 平均评分, Decimal(3, 2), Nullable (冗余)
    *   `total_orders_completed`: 累计完成订单数, Integer (Unsigned), Not Null, Default 0 (冗余)
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   One-to-One with `User` (通过 `user_id`)
    *   Many-to-One with `VerificationRecord` (通过 `verification_record_id`, ON DELETE SET NULL)

**3.3. EmployerProfile (雇主档案模型)**
*   **对应表:** `employer_profiles`
*   **描述:** 存储雇主用户（个人或企业）的详细信息和认证状态。
*   **核心属性:**
    *   `user_id`: 主键 & 外键 (-> users.id), BigInt (Unsigned)
    *   `profile_type`: 档案类型, Enum('individual', 'company'), Not Null
    *   `real_name`: 真实姓名/联系人, String(50), Nullable
    *   `id_card_number_encrypted`: 加密身份证号, String(255), Nullable
    *   `avatar_url`: 头像/Logo URL, String(512), Nullable
    *   `nickname`: 昵称/简称, String(50), Nullable
    *   `location_province`, `location_city`, `location_district`: String(50), Nullable
    *   `contact_phone`: 联系电话, String(20), Nullable
    *   `verification_status`: 认证状态, Enum('unverified', 'pending', 'verified', 'failed'), Not Null, Default 'unverified'
    *   `verification_record_id`: 最新认证记录ID (-> verification_records.id), BigInt (Unsigned), Nullable
    *   `credit_score`: 信用分, Integer, Not Null, Default 100
    *   `average_rating`: 平均评分, Decimal(3, 2), Nullable (冗余)
    *   `total_jobs_posted`: 累计发布工作数, Integer (Unsigned), Not Null, Default 0 (冗余)
    *   `company_name`: 公司名称, String(100), Nullable
    *   `business_license_number`: 统一社会信用代码, String(50), Unique, Nullable
    *   `business_license_photo_url`: 营业执照照片 URL, String(512), Nullable
    *   `company_address`: 公司地址, String(200), Nullable
    *   `company_description`: 公司简介, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   One-to-One with `User` (通过 `user_id`)
    *   Many-to-One with `VerificationRecord` (通过 `verification_record_id`, ON DELETE SET NULL)

**3.4. Job (工作信息模型)**
*   **对应表:** `jobs`
*   **描述:** 存储雇主发布的工作需求详情。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `employer_user_id`: 发布者用户ID (-> users.id), BigInt (Unsigned), Not Null
    *   `title`: 标题, String(100), Not Null (Fulltext Indexed)
    *   `description`: 描述, Text, Not Null (Fulltext Indexed)
    *   `job_category`: 工作类别, String(50), Not Null
    *   `job_tags`: 工作标签, JSON, Nullable
    *   `location_address`: 详细地址, String(200), Not Null
    *   `location_province`, `location_city`, `location_district`: String(50), Nullable (冗余)
    *   `location_point`: 地理坐标, Point, Not Null (Spatial Indexed)
    *   `start_time`, `end_time`: 预计起止时间, DateTime(6), Not Null
    *   `duration_estimate`: 预计工时, Decimal(10, 2), Nullable
    *   `salary_amount`: 薪资金额, Decimal(10, 2), Not Null
    *   `salary_type`: 计薪方式, Enum('hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable'), Not Null
    *   `salary_negotiable`: 薪资是否可议, Boolean, Not Null, Default False
    *   `required_people`: 需求人数, Integer (Unsigned), Not Null, Default 1
    *   `accepted_people`: 已接受人数, Integer (Unsigned), Not Null, Default 0 (冗余)
    *   `skill_requirements`: 技能要求描述, Text, Nullable
    *   `is_urgent`: 是否急聘, Boolean, Not Null, Default False
    *   `status`: 工作状态, Enum('pending_review', 'rejected', 'active', 'filled', 'in_progress', 'completed', 'cancelled', 'expired'), Not Null, Default 'pending_review'
    *   `cancellation_reason`: 取消原因, Text, Nullable
    *   `view_count`: 浏览次数, Integer (Unsigned), Not Null, Default 0
    *   `application_deadline`: 报名截止时间, DateTime(6), Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (雇主, 通过 `employer_user_id`, ON DELETE CASCADE)
    *   One-to-Many with `JobApplication` (通过 `JobApplication.job_id`)
    *   One-to-Many with `Order` (通过 `Order.job_id`)
    *   One-to-Many with `Evaluation` (通过 `Evaluation.job_id`)
    *   Many-to-Many with `Skill` (通过 `JobRequiredSkill` 关联表)

**3.5. JobApplication (工作申请模型)**
*   **对应表:** `job_applications`
*   **描述:** 记录零工对工作的申请及其状态。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `job_id`: 关联工作ID (-> jobs.id), BigInt (Unsigned), Not Null
    *   `freelancer_user_id`: 申请零工ID (-> users.id), BigInt (Unsigned), Not Null
    *   `employer_user_id`: 工作发布者ID (-> users.id), BigInt (Unsigned), Not Null (冗余)
    *   `apply_message`: 申请留言, Text, Nullable
    *   `status`: 申请状态, Enum('pending', 'viewed', 'accepted', 'rejected', 'cancelled_by_freelancer'), Not Null, Default 'pending'
    *   `applied_at`: 申请时间, DateTime(6), Not Null, Default CURRENT_TIMESTAMP(6)
    *   `processed_at`: 处理时间, DateTime(6), Nullable
    *   `rejection_reason`: 拒绝原因, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
    *   Unique Constraint on (`job_id`, `freelancer_user_id`)
*   **关系:**
    *   Many-to-One with `Job` (通过 `job_id`, ON DELETE CASCADE)
    *   Many-to-One with `User` (零工, 通过 `freelancer_user_id`, ON DELETE CASCADE)
    *   Many-to-One with `User` (雇主, 通过 `employer_user_id`, ON DELETE CASCADE)
    *   One-to-One with `Order` (通过 `Order.application_id`, Nullable)

**3.6. Order (订单模型)**
*   **对应表:** `orders`
*   **描述:** 记录已确认的工作关系（通常由申请接受后创建）及其执行过程。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `job_id`: 关联工作ID (-> jobs.id), BigInt (Unsigned), Not Null
    *   `application_id`: 关联申请ID (-> job_applications.id), BigInt (Unsigned), Unique, Nullable
    *   `freelancer_user_id`: 零工用户ID (-> users.id), BigInt (Unsigned), Not Null
    *   `employer_user_id`: 雇主用户ID (-> users.id), BigInt (Unsigned), Not Null
    *   `order_amount`: 订单金额, Decimal(10, 2), Not Null
    *   `platform_fee`: 平台服务费, Decimal(10, 2), Not Null, Default 0.00
    *   `freelancer_income`: 零工收入, Decimal(10, 2), Not Null
    *   `start_time_scheduled`, `end_time_scheduled`: 计划起止时间, DateTime(6), Not Null
    *   `start_time_actual`, `end_time_actual`: 实际起止时间, DateTime(6), Nullable
    *   `work_duration_actual`: 实际工时, Decimal(10, 2), Nullable
    *   `status`: 订单状态, Enum('pending_start', 'in_progress', 'pending_confirmation', 'completed', 'disputed', 'cancelled'), Not Null, Default 'pending_start'
    *   `freelancer_confirmation_status`, `employer_confirmation_status`: 双方确认状态, Enum('pending', 'confirmed', 'disputed'), Not Null, Default 'pending'
    *   `confirmation_deadline`: 确认截止时间, DateTime(6), Nullable
    *   `cancellation_reason`: 取消原因, Text, Nullable
    *   `cancelled_by`: 取消方, Enum('freelancer', 'employer', 'platform'), Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `Job` (通过 `job_id`, ON DELETE RESTRICT)
    *   One-to-One with `JobApplication` (通过 `application_id`, ON DELETE SET NULL)
    *   Many-to-One with `User` (零工, 通过 `freelancer_user_id`, ON DELETE RESTRICT)
    *   Many-to-One with `User` (雇主, 通过 `employer_user_id`, ON DELETE RESTRICT)
    *   One-to-Many with `Payment` (通过 `Payment.order_id`)
    *   One-to-Many with `Evaluation` (通过 `Evaluation.order_id`)
    *   One-to-Many with `WalletTransaction` (通过 `WalletTransaction.related_order_id`)
    *   One-to-One with `Dispute` (通过 `Dispute.order_id`)

**3.7. Payment (支付记录模型)**
*   **对应表:** `payments`
*   **描述:** 记录与订单相关的支付交易和状态。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `order_id`: 关联订单ID (-> orders.id), BigInt (Unsigned), Not Null
    *   `payer_user_id`: 支付方ID (-> users.id), BigInt (Unsigned), Not Null
    *   `payee_user_id`: 收款方ID (-> users.id), BigInt (Unsigned), Not Null
    *   `amount`: 支付金额, Decimal(10, 2), Not Null
    *   `payment_method`: 支付方式, String(50), Nullable
    *   `external_transaction_id`: 第三方流水号, String(128), Unique, Nullable
    *   `internal_transaction_id`: 内部流水号, String(64), Unique, Not Null
    *   `status`: 支付状态, Enum('pending', 'processing', 'succeeded', 'failed', 'refund_pending', 'refunded'), Not Null, Default 'pending'
    *   `paid_at`: 支付成功时间, DateTime(6), Nullable
    *   `refund_amount`: 退款金额, Decimal(10, 2), Nullable
    *   `refunded_at`: 退款成功时间, DateTime(6), Nullable
    *   `error_code`: 错误码, String(50), Nullable
    *   `error_message`: 错误信息, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `Order` (通过 `order_id`, ON DELETE RESTRICT)
    *   Many-to-One with `User` (支付方, 通过 `payer_user_id`, ON DELETE RESTRICT)
    *   Many-to-One with `User` (收款方, 通过 `payee_user_id`, ON DELETE RESTRICT)
    *   One-to-Many with `WalletTransaction` (通过 `WalletTransaction.related_payment_id`)

**3.8. Evaluation (评价模型)**
*   **对应表:** `evaluations`
*   **描述:** 存储订单完成后双方的互评信息。
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `order_id`: 关联订单ID (-> orders.id), BigInt (Unsigned), Not Null
    *   `job_id`: 关联工作ID (-> jobs.id), BigInt (Unsigned), Not Null (冗余)
    *   `evaluator_user_id`: 评价者ID (-> users.id), BigInt (Unsigned), Not Null
    *   `evaluatee_user_id`: 被评价者ID (-> users.id), BigInt (Unsigned), Not Null
    *   `evaluator_role`: 评价者角色, Enum('freelancer', 'employer'), Not Null
    *   `rating`: 评分, TinyInt (Unsigned), Not Null (1-5)
    *   `comment`: 评价内容, Text, Nullable
    *   `tags`: 评价标签, JSON, Nullable
    *   `is_anonymous`: 是否匿名, Boolean, Not Null, Default False
    *   `created_at`, `updated_at`: DateTime(6)
    *   Unique Constraint on (`order_id`, `evaluator_user_id`)
*   **关系:**
    *   Many-to-One with `Order` (通过 `order_id`, ON DELETE CASCADE)
    *   Many-to-One with `Job` (通过 `job_id`, ON DELETE CASCADE)
    *   Many-to-One with `User` (评价者, 通过 `evaluator_user_id`, ON DELETE CASCADE)
    *   Many-to-One with `User` (被评价者, 通过 `evaluatee_user_id`, ON DELETE CASCADE)

**3.9. Skill (技能模型)**
*   **对应表:** `skills`
*   **描述:** 存储平台预定义的技能标签。
*   **核心属性:**
    *   `id`: 主键, Integer (Unsigned)
    *   `name`: 技能名称, String(50), Unique, Not Null
    *   `category`: 技能分类, String(50), Nullable
    *   `description`: 技能描述, Text, Nullable
    *   `is_hot`: 是否热门, Boolean, Not Null, Default False
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-Many with `User` (通过 `FreelancerSkill` 关联表)
    *   Many-to-Many with `Job` (通过 `JobRequiredSkill` 关联表)

**3.10. FreelancerSkill (零工技能关联模型)**
*   **对应表:** `freelancer_skills`
*   **描述:** 存储零工掌握的技能、熟练度及认证信息（多对多关联）。
*   **主键:** (`freelancer_user_id`, `skill_id`)
*   **核心属性:**
    *   `freelancer_user_id`: 零工用户ID (-> users.id), BigInt (Unsigned), Not Null, PK, FK
    *   `skill_id`: 技能ID (-> skills.id), Int (Unsigned), Not Null, PK, FK
    *   `proficiency_level`: 熟练度, Enum('beginner', 'intermediate', 'advanced', 'expert'), Nullable
    *   `years_of_experience`: 相关经验年限, TinyInt (Unsigned), Nullable
    *   `certificate_url`: 相关技能证书 URL, String(512), Nullable
    *   `certificate_verified`: 证书是否已认证, Boolean, Not Null, Default False
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (通过 `freelancer_user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `Skill` (通过 `skill_id`, ON DELETE CASCADE, ON UPDATE CASCADE)

**3.11. JobRequiredSkill (工作技能要求关联模型)**
*   **对应表:** `job_required_skills`
*   **描述:** 存储工作要求的技能（多对多关联）。
*   **主键:** (`job_id`, `skill_id`)
*   **核心属性:**
    *   `job_id`: 工作ID (-> jobs.id), BigInt (Unsigned), Not Null, PK, FK
    *   `skill_id`: 技能ID (-> skills.id), Int (Unsigned), Not Null, PK, FK
    *   `is_mandatory`: 是否必须, Boolean, Not Null, Default True
*   **关系:**
    *   Many-to-One with `Job` (通过 `job_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `Skill` (通过 `skill_id`, ON DELETE CASCADE, ON UPDATE CASCADE)

**3.12. Message (消息模型)**
*   **对应表:** `messages`
*   **描述:** 存储用户间的私信和部分即时系统通知。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `conversation_id`: 会话ID, String(64), Not Null
    *   `sender_id`: 发送者用户ID (-> users.id), BigInt (Unsigned), Nullable, FK
    *   `recipient_id`: 接收者用户ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `content`: 消息内容, Text, Not Null
    *   `message_type`: 消息类型, Enum('text', 'image', 'audio', 'file', 'system_notification', 'order_update', 'application_update'), Not Null, Default 'text'
    *   `related_resource_type`: 关联资源类型, String(50), Nullable
    *   `related_resource_id`: 关联资源ID, BigInt (Unsigned), Nullable
    *   `is_read`: 是否已读, Boolean, Not Null, Default False
    *   `read_at`: 阅读时间, DateTime(6), Nullable
    *   `created_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (发送者, 通过 `sender_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   Many-to-One with `User` (接收者, 通过 `recipient_id`, ON DELETE CASCADE, ON UPDATE CASCADE)

**3.13. AdminUser (后台管理员模型)**
*   **对应表:** `admin_users`
*   **描述:** 存储后台管理系统用户信息。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `username`: 管理员登录账号, String(50), Not Null, Unique
    *   `password_hash`: 哈希后的密码, String(255), Not Null
    *   `real_name`: 真实姓名, String(50), Nullable
    *   `role`: 管理员角色, String(50), Not Null
    *   `status`: 账号状态, Enum('active', 'inactive'), Not Null, Default 'active'
    *   `last_login_at`: 最后登录时间, DateTime(6), Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   One-to-Many with `VerificationRecord` (作为审核员, 通过 `VerificationRecord.reviewer_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   One-to-Many with `Report` (作为处理员, 通过 `Report.processor_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   One-to-Many with `Dispute` (作为调解员, 通过 `Dispute.platform_mediator_id`, ON DELETE SET NULL, ON UPDATE CASCADE)

**3.14. VerificationRecord (认证记录模型)**
*   **对应表:** `verification_records`
*   **描述:** 存储用户身份或企业资质认证的提交和审核记录。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `user_id`: 申请用户ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `profile_type`: 申请认证类型, Enum('freelancer', 'employer_individual', 'employer_company'), Not Null
    *   `submitted_data`: 提交资料, JSON, Not Null
    *   `status`: 审核状态, Enum('pending', 'approved', 'rejected'), Not Null, Default 'pending'
    *   `reviewer_id`: 审核管理员ID (-> admin_users.id), BigInt (Unsigned), Nullable, FK
    *   `reviewed_at`: 审核时间, DateTime(6), Nullable
    *   `rejection_reason`: 拒绝原因, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (通过 `user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `AdminUser` (审核员, 通过 `reviewer_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   Many-to-One relationship *from* `FreelancerProfile` (通过 `FreelancerProfile.verification_record_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   Many-to-One relationship *from* `EmployerProfile` (通过 `EmployerProfile.verification_record_id`, ON DELETE SET NULL, ON UPDATE CASCADE)

**3.15. WithdrawalRequest (提现申请模型)**
*   **对应表:** `withdrawal_requests`
*   **描述:** 记录用户的提现申请。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `user_id`: 申请用户ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `amount`: 申请金额, Decimal(10, 2), Not Null
    *   `withdrawal_method`: 提现方式, String(50), Not Null
    *   `account_info`: 提现账户信息, JSON, Not Null
    *   `status`: 申请状态, Enum('pending', 'processing', 'succeeded', 'failed', 'cancelled'), Not Null, Default 'pending'
    *   `platform_fee`: 手续费, Decimal(10, 2), Not Null, Default 0.00
    *   `actual_amount`: 实际到账金额, Decimal(10, 2), Not Null
    *   `processed_at`: 处理时间, DateTime(6), Nullable
    *   `external_transaction_id`: 外部转账流水号, String(128), Unique, Nullable
    *   `failure_reason`: 失败原因, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (通过 `user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One relationship *from* `WalletTransaction` (通过 `WalletTransaction.related_withdrawal_id`, ON DELETE SET NULL, ON UPDATE CASCADE)

**3.16. WalletTransaction (钱包流水模型)**
*   **对应表:** `wallet_transactions`
*   **描述:** 记录用户钱包余额的详细变动。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `user_id`: 用户ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `transaction_type`: 交易类型, Enum('deposit', 'withdrawal', 'income', 'payment', 'refund', 'platform_fee', 'adjustment'), Not Null
    *   `amount`: 交易金额 (正增负减), Decimal(10, 2), Not Null
    *   `balance_after`: 交易后余额快照, Decimal(10, 2), Not Null
    *   `related_payment_id`: 关联支付ID (-> payments.id), BigInt (Unsigned), Nullable, FK
    *   `related_order_id`: 关联订单ID (-> orders.id), BigInt (Unsigned), Nullable, FK (冗余)
    *   `related_withdrawal_id`: 关联提现ID (-> withdrawal_requests.id), BigInt (Unsigned), Nullable, FK
    *   `description`: 交易描述, String(255), Nullable
    *   `created_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (通过 `user_id`, ON DELETE RESTRICT, ON UPDATE CASCADE)
    *   Many-to-One with `Payment` (通过 `related_payment_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   Many-to-One with `Order` (通过 `related_order_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   Many-to-One with `WithdrawalRequest` (通过 `related_withdrawal_id`, ON DELETE SET NULL, ON UPDATE CASCADE)

**3.17. UserWallet (用户钱包模型)**
*   **对应表:** `user_wallets`
*   **描述:** 存储用户当前的钱包余额和冻结金额（冗余表，用于性能优化）。
*   **主键:** `user_id`, BigInt (Unsigned) & FK
*   **核心属性:**
    *   `user_id`: 主键 & 外键 (-> users.id), BigInt (Unsigned)
    *   `balance`: 可用余额, Decimal(10, 2), Not Null, Default 0.00
    *   `frozen_balance`: 冻结金额, Decimal(10, 2), Not Null, Default 0.00
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   One-to-One with `User` (通过 `user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)

**3.18. Notification (平台通知模型)**
*   **对应表:** `notifications`
*   **描述:** 存储推送给用户的各类平台通知（区别于私信）。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `user_id`: 接收用户ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `notification_type`: 通知类型, Enum('system_announcement', 'job_recommendation', 'application_update', 'order_update', 'payment_update', 'evaluation_reminder', 'policy_update', 'verification_result', 'report_result', 'dispute_update'), Not Null
    *   `title`: 标题, String(100), Not Null
    *   `content`: 内容, Text, Not Null
    *   `related_resource_type`: 关联资源类型, String(50), Nullable
    *   `related_resource_id`: 关联资源ID, BigInt (Unsigned), Nullable
    *   `is_read`: 是否已读, Boolean, Not Null, Default False
    *   `read_at`: 阅读时间, DateTime(6), Nullable
    *   `created_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (通过 `user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)

**3.19. Favorite (用户收藏模型)**
*   **对应表:** `favorites`
*   **描述:** 存储用户收藏的工作或用户（零工/雇主）。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `user_id`: 收藏者ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `favorite_type`: 收藏类型, Enum('job', 'freelancer', 'employer'), Not Null
    *   `target_id`: 被收藏对象ID (jobs.id 或 users.id), BigInt (Unsigned), Not Null
    *   `created_at`: DateTime(6)
    *   Unique Constraint on (`user_id`, `favorite_type`, `target_id`)
*   **关系:**
    *   Many-to-One with `User` (收藏者, 通过 `user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   (逻辑关系) Many-to-One with `Job` or `User` (被收藏对象, 通过 `target_id` 和 `favorite_type` 判断)

**3.20. Report (举报记录模型)**
*   **对应表:** `reports`
*   **描述:** 存储用户提交的举报信息。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `reporter_user_id`: 举报者ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `report_type`: 举报对象类型, Enum('job', 'user', 'order', 'message', 'evaluation'), Not Null
    *   `target_id`: 被举报对象ID, BigInt (Unsigned), Not Null
    *   `reason_category`: 举报原因分类, String(50), Not Null
    *   `reason_description`: 原因详述, Text, Nullable
    *   `attachments`: 附件URL列表, JSON, Nullable
    *   `status`: 处理状态, Enum('pending', 'processing', 'resolved_valid', 'resolved_invalid', 'resolved_duplicate'), Not Null, Default 'pending'
    *   `processor_id`: 处理管理员ID (-> admin_users.id), BigInt (Unsigned), Nullable, FK
    *   `processed_at`: 处理时间, DateTime(6), Nullable
    *   `processing_result`: 处理结果描述, Text, Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   Many-to-One with `User` (举报者, 通过 `reporter_user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `AdminUser` (处理员, 通过 `processor_id`, ON DELETE SET NULL, ON UPDATE CASCADE)
    *   (逻辑关系) Many-to-One with `Job`, `User`, `Order`, `Message`, `Evaluation` (被举报对象, 通过 `target_id` 和 `report_type` 判断)

**3.21. Dispute (争议处理模型)**
*   **对应表:** `disputes`
*   **描述:** 记录订单发生争议时的处理过程。
*   **主键:** `id`, BigInt (Unsigned)
*   **核心属性:**
    *   `id`: 主键, BigInt (Unsigned)
    *   `order_id`: 关联订单ID (-> orders.id), BigInt (Unsigned), Unique, Not Null, FK
    *   `initiator_user_id`: 发起者ID (-> users.id), BigInt (Unsigned), Not Null, FK
    *   `reason`: 争议原因, Text, Not Null
    *   `expected_resolution`: 期望解决方案, Text, Nullable
    *   `attachments`: 证据附件URL列表, JSON, Nullable
    *   `status`: 争议状态, Enum('pending', 'negotiating', 'platform_intervening', 'resolved', 'closed'), Not Null, Default 'pending'
    *   `resolution_result`: 最终解决方案, Text, Nullable
    *   `platform_mediator_id`: 平台处理人ID (-> admin_users.id), BigInt (Unsigned), Nullable, FK
    *   `resolved_at`: 解决时间, DateTime(6), Nullable
    *   `created_at`, `updated_at`: DateTime(6)
*   **关系:**
    *   One-to-One with `Order` (通过 `order_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `User` (发起者, 通过 `initiator_user_id`, ON DELETE CASCADE, ON UPDATE CASCADE)
    *   Many-to-One with `AdminUser` (调解员, 通过 `platform_mediator_id`, ON DELETE SET NULL, ON UPDATE CASCADE)

**3.22. SystemConfig (系统配置模型)**
*   **对应表:** `system_configs`
*   **描述:** 存储平台可动态配置的参数。
*   **主键:** `config_key`, String(100)
*   **核心属性:**
    *   `config_key`: 配置项键名, String(100), Primary Key
    *   `config_value`: 配置项值, Text, Not Null
    *   `description`: 配置项描述, String(255), Nullable
    *   `updated_at`: DateTime(6)
*   **关系:** 无直接外键关系。

**4. 设计考虑与规范**

*   **命名:** 模型类名采用 PascalCase，属性名（对应列名）采用 snake_case。
*   **主键:** 优先使用自增 BigInt `id` 作为主键。对于需要对外暴露或跨服务引用的实体，可考虑增加 `uuid` 字段（如 User, Job, Order 等，虽然 `createDB.sql` 中未全部包含，但架构文档中有提及，可按需添加）。`system_configs` 使用 `config_key` 作为主键。
*   **外键与关系:** 明确定义模型间的关系，并根据业务逻辑设置合适的 `ON DELETE` 和 `ON UPDATE` 行为（`CASCADE`, `SET NULL`, `RESTRICT`）。已在各模型关系中补充说明。
*   **数据类型:** 逻辑类型（String, Integer, Decimal, DateTime, Boolean, Enum, JSON, Point）需在实现时映射为 SQLAlchemy 及数据库的具体类型 (如 VARCHAR, BIGINT UNSIGNED, DECIMAL(10, 2), DATETIME(6), BOOLEAN/TINYINT(1), ENUM, JSON, POINT)。
*   **枚举 (Enum):** 对于状态、类型等字段，使用 Enum 类型增强可读性和约束性。SQL 中已定义具体的 ENUM 值。
*   **时间戳:** `created_at` 和 `updated_at` 为标准字段，用于追踪记录的生命周期。SQL 中已包含 `DEFAULT CURRENT_TIMESTAMP(6)` 和 `ON UPDATE CURRENT_TIMESTAMP(6)`。
*   **软删除:** 当前设计未包含软删除字段 (`deleted_at`)。如需此功能，需在模型和查询逻辑中添加相应支持。
*   **冗余字段:** 设计中包含的冗余字段（如 `average_rating`, `total_orders_completed`, `accepted_people`, `job_applications.employer_user_id`, `evaluations.job_id`, `wallet_transactions.related_order_id`）是为了查询性能。其数据一致性必须由 Service 层负责维护。
*   **索引:** `createDB.sql` 中定义的索引（普通索引、唯一索引、空间索引、全文索引）需要在 SQLAlchemy 模型映射中体现或单独创建，以优化查询性能。建议在各模型描述中也提及关键索引（如外键索引、状态索引、地理空间索引、全文索引等）。

**5. 总结**

本文档详细描述了智慧零工平台后端 Model 层的逻辑设计，严格映射了 `createDB.sql` 定义的数据库结构，并明确了各模型及其关系。此设计为 Service 层提供了清晰的数据访问基础，并确保了 Model 层职责的单一性，符合整体 MVC 架构要求。后续开发应基于此逻辑设计，使用 SQLAlchemy 实现具体的模型类。

---