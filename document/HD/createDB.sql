-- SQL script to create the database and tables for the SmartGigPlatform

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS smart_gig_platform
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Use the created database
USE smart_gig_platform;

-- Set default storage engine
SET default_storage_engine=InnoDB;

-- --- Core Tables ---

-- 1. 用户表 (users)
-- Responsibilities: Stores basic login information and core status for all platform users.
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一ID',
    uuid VARCHAR(36) UNIQUE NOT NULL COMMENT '对外暴露的用户UUID',
    phone_number VARCHAR(20) NOT NULL UNIQUE COMMENT '手机号 (主要登录凭证)',
    password_hash VARCHAR(255) NOT NULL COMMENT '哈希后的密码 (使用 Werkzeug security 或类似库)',
    email VARCHAR(100) UNIQUE COMMENT '邮箱 (可选登录或通知方式)',
    wechat_openid VARCHAR(128) UNIQUE COMMENT '微信 OpenID (用于微信登录)',
    alipay_userid VARCHAR(128) UNIQUE COMMENT '支付宝 UserID (用于支付宝登录)',
    current_role ENUM('freelancer', 'employer') NOT NULL DEFAULT 'freelancer' COMMENT '用户当前活跃角色',
    available_roles JSON NOT NULL COMMENT '用户拥有的角色列表, e.g., ["freelancer", "employer"]',
    status ENUM('pending_verification', 'active', 'inactive', 'banned') NOT NULL DEFAULT 'pending_verification' COMMENT '账号状态 (pending_verification: 待验证手机/邮箱, active: 正常, inactive: 停用, banned: 封禁)',
    last_login_at DATETIME(6) NULL COMMENT '最后登录时间',
    registered_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '注册时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    INDEX idx_status (status),
    INDEX idx_registered_at (registered_at),
    INDEX idx_email (email), -- 索引可选登录方式
    INDEX idx_wechat_openid (wechat_openid), -- 索引第三方登录标识
    INDEX idx_alipay_userid (alipay_userid) -- 索引第三方登录标识
) COMMENT '用户基础信息表 (存储核心认证和状态)';

-- 2. 零工档案表 (freelancer_profiles)
-- Responsibilities: Stores detailed information, verification status, and preferences for freelancer users.
CREATE TABLE freelancer_profiles (
    user_id BIGINT UNSIGNED PRIMARY KEY COMMENT '关联的用户ID (外键, users.id)',
    real_name VARCHAR(100) NULL COMMENT '真实姓名 (实名认证后填写)',
    gender ENUM('male', 'female', 'other', 'unknown') NULL DEFAULT 'unknown' COMMENT '性别',
    birth_date DATE NULL COMMENT '出生日期',
    avatar_url VARCHAR(512) NULL COMMENT '头像 URL (建议使用 OSS/CDN)',
    nickname VARCHAR(100) NULL COMMENT '昵称',
    location_province VARCHAR(50) NULL COMMENT '常驻省份',
    location_city VARCHAR(50) NULL COMMENT '常驻城市',
    location_district VARCHAR(50) NULL COMMENT '常驻区县',
    bio TEXT NULL COMMENT '个人简介/自我介绍',
    work_preference JSON NULL COMMENT '工作偏好 (JSON 格式, e.g., {"categories": ["家政", "派发"], "time_slots": ["weekday_evening", "weekend"], "salary_min": 100, "salary_type": "daily"})',
    verification_status ENUM('unverified', 'pending_review', 'verified', 'rejected') NOT NULL DEFAULT 'unverified' COMMENT '实名认证状态',
    verification_record_id BIGINT UNSIGNED NULL COMMENT '关联的最新认证记录ID (外键, verification_records.id)',
    credit_score INT NOT NULL DEFAULT 100 COMMENT '信用分 (初始100, 根据评价、履约、违规等动态调整)',
    average_rating DECIMAL(3, 2) NULL COMMENT '平均评分 (冗余字段, 由评价表计算定期更新, 用于排序和展示)',
    total_orders_completed INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计完成订单数 (冗余字段, 订单完成后更新, 用于展示和筛选)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_verification_status (verification_status),
    INDEX idx_credit_score (credit_score),
    INDEX idx_location (location_province, location_city, location_district),
    INDEX idx_average_rating (average_rating),
    INDEX idx_total_orders_completed (total_orders_completed)
) COMMENT '零工详细档案表 (存储零工身份的扩展信息)';

-- 3. 雇主档案表 (employer_profiles)
-- Responsibilities: Stores detailed information and verification status for employer users (individual or company).
CREATE TABLE employer_profiles (
    user_id BIGINT UNSIGNED PRIMARY KEY COMMENT '关联的用户ID (外键, users.id)',
    profile_type ENUM('individual', 'company') NOT NULL COMMENT '档案类型 (个人雇主/企业雇主)',
    real_name VARCHAR(100) NULL COMMENT '真实姓名 (个人或法人/联系人)',
    avatar_url VARCHAR(512) NULL COMMENT '头像/Logo URL (建议使用 OSS/CDN)',
    nickname VARCHAR(100) NULL COMMENT '昵称/简称',
    location_province VARCHAR(50) NULL COMMENT '所在省份',
    location_city VARCHAR(50) NULL COMMENT '所在城市',
    location_district VARCHAR(50) NULL COMMENT '所在区县',
    contact_phone VARCHAR(30) NULL COMMENT '联系电话 (优先使用 users 表的 phone_number, 此处可备用)',
    verification_status ENUM('unverified', 'pending_review', 'verified', 'rejected') NOT NULL DEFAULT 'unverified' COMMENT '认证状态 (个人/企业)',
    verification_record_id BIGINT UNSIGNED NULL COMMENT '关联的最新认证记录ID (外键, verification_records.id)',
    credit_score INT NOT NULL DEFAULT 100 COMMENT '信用分 (初始100, 根据评价、履约、违规等动态调整)',
    average_rating DECIMAL(3, 2) NULL COMMENT '平均评分 (冗余字段, 由评价表计算定期更新, 用于排序和展示)',
    total_jobs_posted INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计发布工作数 (冗余字段, 发布工作后更新, 用于展示和统计)',
    company_name VARCHAR(200) NULL COMMENT '公司名称 (企业认证后填写)',
    company_address VARCHAR(255) NULL COMMENT '公司地址',
    company_description TEXT NULL COMMENT '公司简介',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_profile_type (profile_type),
    INDEX idx_verification_status (verification_status),
    INDEX idx_credit_score (credit_score),
    INDEX idx_location (location_province, location_city, location_district),
    INDEX idx_company_name (company_name),
    INDEX idx_average_rating (average_rating),
    INDEX idx_total_jobs_posted (total_jobs_posted)
) COMMENT '雇主详细档案表 (存储雇主身份的扩展信息)';

-- 4. 工作信息表 (jobs)
-- Responsibilities: Stores job requirement details posted by employers.
CREATE TABLE jobs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '工作唯一ID',
    employer_user_id BIGINT UNSIGNED NOT NULL COMMENT '发布者用户ID (外键, users.id)',
    title VARCHAR(100) NOT NULL COMMENT '工作标题',
    description TEXT NOT NULL COMMENT '工作描述 (支持 Markdown 或富文本)',
    job_category VARCHAR(50) NOT NULL COMMENT '工作类别/行业 (如 家政, 搬运, IT, 派发)',
    job_tags JSON NULL COMMENT '工作标签 (JSON 数组, 用于精确匹配), e.g., ["传单派发", "周末兼职", "日结"]',
    location_address VARCHAR(200) NOT NULL COMMENT '详细工作地点',
    location_province VARCHAR(50) NULL COMMENT '省份 (冗余, 便于查询)',
    location_city VARCHAR(50) NULL COMMENT '城市 (冗余, 便于查询)',
    location_district VARCHAR(50) NULL COMMENT '区县 (冗余, 便于查询)',
    location_point JSON NULL COMMENT '地理坐标 (GeoJSON)',
    start_time DATETIME(6) NOT NULL COMMENT '预计开始时间',
    end_time DATETIME(6) NOT NULL COMMENT '预计结束时间',
    duration_estimate DECIMAL(10, 2) NULL COMMENT '预计工时 (小时, 可由起止时间计算)',
    salary_amount DECIMAL(10, 2) NOT NULL COMMENT '薪资金额',
    salary_type ENUM('hourly', 'daily', 'weekly', 'monthly', 'fixed', 'negotiable') NOT NULL COMMENT '计薪方式 (hourly:时薪, daily:日薪, weekly:周薪, monthly:月薪, fixed:总价, negotiable:面议)',
    salary_negotiable BOOLEAN NOT NULL DEFAULT FALSE COMMENT '薪资是否可议价 (若为 true, salary_amount 可视为参考)',
    required_people INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '需求人数',
    accepted_people INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '已接受人数 (冗余字段, 订单创建或状态变更时更新)',
    skill_requirements TEXT NULL COMMENT '技能要求描述 (文本补充说明)',
    is_urgent BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否急聘 (用于排序或特殊标记)',
    status ENUM('pending_review', 'rejected', 'active', 'filled', 'in_progress', 'completed', 'cancelled', 'expired') NOT NULL DEFAULT 'pending_review' COMMENT '工作状态 (pending_review:待审核, rejected:审核拒绝, active:招聘中, filled:招满, in_progress:进行中, completed:已完成, cancelled:已取消, expired:已过期)',
    cancellation_reason TEXT NULL COMMENT '取消原因 (如果状态是 cancelled)',
    view_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '浏览次数 (每次查看详情时增加)',
    application_deadline DATETIME(6) NULL COMMENT '报名截止时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (employer_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_employer_user_id (employer_user_id),
    INDEX idx_status_created (status, created_at DESC),
    INDEX idx_job_category (job_category),
    INDEX idx_location (location_province, location_city, location_district),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    INDEX idx_salary_amount (salary_amount),
    INDEX idx_is_urgent (is_urgent),
    INDEX idx_application_deadline (application_deadline),
    FULLTEXT INDEX ft_title_description (title, description)
) COMMENT '工作信息表 (核心业务实体)';

-- 5. 报名/应聘表 (job_applications)
-- Responsibilities: Records freelancer applications for jobs and their status.
CREATE TABLE job_applications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '申请唯一ID',
    job_id BIGINT UNSIGNED NOT NULL COMMENT '关联的工作ID (外键, jobs.id)',
    freelancer_user_id BIGINT UNSIGNED NOT NULL COMMENT '申请的零工用户ID (外键, users.id)',
    employer_user_id BIGINT UNSIGNED NOT NULL COMMENT '工作的发布者用户ID (冗余, 便于雇主查询, 外键, users.id)',
    apply_message TEXT NULL COMMENT '申请留言/备注',
    status ENUM('pending', 'viewed', 'accepted', 'rejected', 'cancelled_by_freelancer') NOT NULL DEFAULT 'pending' COMMENT '申请状态 (pending:待处理, viewed:已查看, accepted:已接受, rejected:已拒绝, cancelled_by_freelancer:申请者取消)',
    applied_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '申请时间',
    processed_at DATETIME(6) NULL COMMENT '雇主处理时间 (接受/拒绝的时间)',
    rejection_reason TEXT NULL COMMENT '拒绝原因 (如果 status 是 rejected)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (freelancer_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (employer_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_job_freelancer (job_id, freelancer_user_id),
    INDEX idx_freelancer_status (freelancer_user_id, status),
    INDEX idx_employer_status (employer_user_id, status),
    INDEX idx_job_status (job_id, status),
    INDEX idx_applied_at (applied_at)
) COMMENT '工作申请表 (连接零工和工作)';

-- 6. 订单表 (orders)
-- Responsibilities: Records confirmed work relationships (starting from application acceptance) and their execution process.
CREATE TABLE orders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '订单唯一ID',
    job_id BIGINT UNSIGNED NOT NULL COMMENT '关联的工作ID (外键, jobs.id)',
    application_id BIGINT UNSIGNED NULL UNIQUE COMMENT '关联的申请ID (外键, job_applications.id, 可为空如果非申请流程创建, 如直接邀请)',
    freelancer_user_id BIGINT UNSIGNED NOT NULL COMMENT '零工用户ID (外键, users.id)',
    employer_user_id BIGINT UNSIGNED NOT NULL COMMENT '雇主用户ID (外键, users.id)',
    order_amount DECIMAL(10, 2) NOT NULL COMMENT '订单最终确认金额 (可能因协商调整)',
    platform_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '平台服务费 (向雇主或零工收取, 或双方分摊)',
    freelancer_income DECIMAL(10, 2) NOT NULL COMMENT '零工预计/实际收入 (order_amount - 零工承担的平台费)',
    start_time_scheduled DATETIME(6) NOT NULL COMMENT '计划开始时间 (来自 job 或协商确认)',
    end_time_scheduled DATETIME(6) NOT NULL COMMENT '计划结束时间 (来自 job 或协商确认)',
    start_time_actual DATETIME(6) NULL COMMENT '实际开始时间 (零工打卡/双方确认)',
    end_time_actual DATETIME(6) NULL COMMENT '实际结束时间 (零工打卡/双方确认)',
    work_duration_actual DECIMAL(10, 2) NULL COMMENT '实际工时 (小时, 根据实际起止时间计算)',
    status ENUM('pending_start', 'in_progress', 'pending_confirmation', 'completed', 'disputed', 'cancelled') NOT NULL DEFAULT 'pending_start' COMMENT '订单状态 (pending_start:待开始, in_progress:进行中, pending_confirmation:待双方确认完成, completed:已完成, disputed:争议中, cancelled:已取消)',
    freelancer_confirmation_status ENUM('pending', 'confirmed', 'disputed') NOT NULL DEFAULT 'pending' COMMENT '零工确认完成状态',
    employer_confirmation_status ENUM('pending', 'confirmed', 'disputed') NOT NULL DEFAULT 'pending' COMMENT '雇主确认完成状态',
    confirmation_deadline DATETIME(6) NULL COMMENT '双方确认截止时间 (超时可能自动确认或进入争议)',
    cancellation_reason TEXT NULL COMMENT '取消原因 (如果 status 是 cancelled)',
    cancelled_by ENUM('freelancer', 'employer', 'platform') NULL COMMENT '取消操作方',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (application_id) REFERENCES job_applications(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (freelancer_user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (employer_user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_freelancer_status (freelancer_user_id, status),
    INDEX idx_employer_status (employer_user_id, status),
    INDEX idx_job_status (job_id, status),
    INDEX idx_status_created (status, created_at DESC),
    INDEX idx_created_at (created_at)
) COMMENT '订单信息表 (核心交易流程)';

-- 7. 支付记录表 (payments)
-- Responsibilities: Records payment transactions and status related to orders.
CREATE TABLE payments (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '支付记录唯一ID',
    order_id BIGINT UNSIGNED NOT NULL COMMENT '关联的订单ID (外键, orders.id)',
    payer_user_id BIGINT UNSIGNED NOT NULL COMMENT '支付方用户ID (通常是雇主, 外键, users.id)',
    payee_user_id BIGINT UNSIGNED NOT NULL COMMENT '收款方用户ID (通常是零工, 外键, users.id)',
    amount DECIMAL(10, 2) NOT NULL COMMENT '支付金额 (通常等于订单的 order_amount)',
    payment_method VARCHAR(50) NULL COMMENT '支付方式 (如 wechat_pay, alipay, wallet_balance)',
    external_transaction_id VARCHAR(128) NULL UNIQUE COMMENT '第三方支付平台流水号 (用于对账)',
    internal_transaction_id VARCHAR(64) NOT NULL UNIQUE COMMENT '平台内部交易流水号 (用于追踪)',
    status ENUM('pending', 'processing', 'succeeded', 'failed', 'refund_pending', 'refunded') NOT NULL DEFAULT 'pending' COMMENT '支付状态 (pending:待支付, processing:处理中, succeeded:成功, failed:失败, refund_pending:退款中, refunded:已退款)',
    paid_at DATETIME(6) NULL COMMENT '支付成功时间',
    refund_amount DECIMAL(10, 2) NULL COMMENT '退款金额 (如果发生退款)',
    refunded_at DATETIME(6) NULL COMMENT '退款成功时间',
    error_code VARCHAR(50) NULL COMMENT '支付/退款失败时的错误码',
    error_message TEXT NULL COMMENT '支付/退款失败时的错误信息',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (payer_user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (payee_user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_payer_status (payer_user_id, status),
    INDEX idx_payee_status (payee_user_id, status),
    INDEX idx_status (status),
    INDEX idx_paid_at (paid_at),
    INDEX idx_external_transaction_id (external_transaction_id),
    INDEX idx_internal_transaction_id (internal_transaction_id)
) COMMENT '支付记录表 (记录资金流动)';

-- 8. 评价表 (evaluations)
-- Responsibilities: Stores mutual evaluation information after order completion.
CREATE TABLE evaluations (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '评价唯一ID',
    order_id BIGINT UNSIGNED NOT NULL COMMENT '关联的订单ID (外键, orders.id)',
    job_id BIGINT UNSIGNED NOT NULL COMMENT '关联的工作ID (冗余, 便于基于工作查询评价, 外键, jobs.id)',
    evaluator_user_id BIGINT UNSIGNED NOT NULL COMMENT '评价者用户ID (外键, users.id)',
    evaluatee_user_id BIGINT UNSIGNED NOT NULL COMMENT '被评价者用户ID (外键, users.id)',
    evaluator_role ENUM('freelancer', 'employer') NOT NULL COMMENT '评价者角色',
    rating TINYINT UNSIGNED NOT NULL COMMENT '评分 (1-5 星)',
    comment TEXT NULL COMMENT '评价内容',
    tags JSON NULL COMMENT '评价标签 (JSON 数组, 基于预定义标签库), e.g., ["沟通顺畅", "技能娴熟", "态度恶劣"]',
    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否匿名评价 (对被评价者隐藏评价者信息)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (evaluator_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (evaluatee_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_order_evaluator (order_id, evaluator_user_id),
    INDEX idx_evaluatee_rating (evaluatee_user_id, rating),
    INDEX idx_job_id (job_id),
    INDEX idx_created_at (created_at)
) COMMENT '订单评价表 (用于信用体系)';

-- 9. 技能表 (skills)
-- Responsibilities: Stores predefined skill tags for the platform.
CREATE TABLE skills (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '技能唯一ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '技能名称 (如 驾驶, 保洁, Python, UI设计)',
    category VARCHAR(50) NULL COMMENT '技能分类 (如 生活服务, IT技术, 设计创意)',
    description TEXT NULL COMMENT '技能描述',
    is_hot BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否热门技能 (运营标记, 用于推荐)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    INDEX idx_category (category),
    INDEX idx_is_hot (is_hot)
) COMMENT '技能标签表 (平台统一管理)';

-- 10. 零工技能关联表 (freelancer_skills)
-- Responsibilities: Stores skills possessed by freelancers, proficiency, and certification info (Many-to-Many).
CREATE TABLE freelancer_skills (
    freelancer_user_id BIGINT UNSIGNED NOT NULL COMMENT '零工用户ID (外键, users.id)',
    skill_id INT UNSIGNED NOT NULL COMMENT '技能ID (外键, skills.id)',
    proficiency_level ENUM('beginner', 'intermediate', 'advanced', 'expert') NULL COMMENT '熟练度 (用户自评或平台认证)',
    years_of_experience TINYINT UNSIGNED NULL COMMENT '相关经验年限 (用户自填)',
    certificate_url VARCHAR(512) NULL COMMENT '相关技能证书 URL (可选, OSS/CDN)',
    certificate_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT '证书是否已由平台认证审核',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    PRIMARY KEY (freelancer_user_id, skill_id),
    FOREIGN KEY (freelancer_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_skill_id (skill_id)
) COMMENT '零工技能关联表 (多对多)';

-- 11. 工作技能要求关联表 (job_required_skills)
-- Responsibilities: Stores required skills for jobs (Many-to-Many).
CREATE TABLE job_required_skills (
    job_id BIGINT UNSIGNED NOT NULL COMMENT '工作ID (外键, jobs.id)',
    skill_id INT UNSIGNED NOT NULL COMMENT '技能ID (外键, skills.id)',
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否必须具备的技能',

    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_skill_id (skill_id)
) COMMENT '工作技能要求关联表 (多对多)';

-- 12. 消息表 (messages)
-- Responsibilities: Stores private messages between users and some system notifications (focus on instant messaging).
CREATE TABLE messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '消息唯一ID',
    conversation_id VARCHAR(64) NOT NULL COMMENT '会话ID (由 sender_id 和 recipient_id 按固定顺序生成, 如 min(id)_max(id))',
    sender_id BIGINT UNSIGNED NULL COMMENT '发送者用户ID (系统消息时为空, 外键, users.id)',
    recipient_id BIGINT UNSIGNED NOT NULL COMMENT '接收者用户ID (外键, users.id)',
    content TEXT NOT NULL COMMENT '消息内容 (文本, 或 JSON 包含 URL 等)',
    message_type ENUM('text', 'image', 'audio', 'file', 'system_notification', 'order_update', 'application_update') NOT NULL DEFAULT 'text' COMMENT '消息类型',
    related_resource_type VARCHAR(50) NULL COMMENT '关联业务资源类型 (如 order, job, user)',
    related_resource_id BIGINT UNSIGNED NULL COMMENT '关联业务资源ID (用于点击跳转)',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '接收方是否已读',
    read_at DATETIME(6) NULL COMMENT '接收方阅读时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_conversation_created (conversation_id, created_at DESC),
    INDEX idx_recipient_read_created (recipient_id, is_read, created_at DESC),
    INDEX idx_created_at (created_at)
) COMMENT '消息表 (用于用户间私信和部分即时系统通知)';

-- --- Auxiliary Tables ---

-- 21. 后台管理员表 (admin_users)
-- Responsibilities: Stores backend management system user information.
CREATE TABLE admin_users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '管理员登录账号',
    password_hash VARCHAR(255) NOT NULL COMMENT '哈希后的密码',
    real_name VARCHAR(50) NULL COMMENT '真实姓名',
    role VARCHAR(50) NOT NULL COMMENT '管理员角色 (如 super_admin, content_moderator, customer_support, finance_operator)',
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active' COMMENT '账号状态',
    last_login_at DATETIME(6) NULL COMMENT '最后登录时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) COMMENT '后台管理员用户表';

-- 16. 认证记录表 (verification_records)
-- Responsibilities: Stores audit records for user identity or enterprise verification submissions.
CREATE TABLE verification_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '认证记录ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '申请用户ID (外键, users.id)',
    profile_type ENUM('freelancer', 'employer_individual', 'employer_company') NOT NULL COMMENT '申请认证的档案类型',
    submitted_data JSON NOT NULL COMMENT '提交的认证资料 (JSON 格式, 包含姓名, 证件号, 照片URL等, 敏感信息需脱敏或加密引用)',
    status ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending' COMMENT '审核状态',
    reviewer_id BIGINT UNSIGNED NULL COMMENT '审核管理员ID (外键, admin_users.id)',
    reviewed_at DATETIME(6) NULL COMMENT '审核时间',
    rejection_reason TEXT NULL COMMENT '拒绝原因 (如果 status 是 rejected)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES admin_users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_user_profile_status (user_id, profile_type, status),
    INDEX idx_status_created (status, created_at DESC)
) COMMENT '用户认证审核记录表';

-- Add deferred foreign keys for freelancer_profiles and employer_profiles
ALTER TABLE freelancer_profiles
ADD CONSTRAINT fk_freelancer_verification_record
FOREIGN KEY (verification_record_id) REFERENCES verification_records(id) ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE employer_profiles
ADD CONSTRAINT fk_employer_verification_record
FOREIGN KEY (verification_record_id) REFERENCES verification_records(id) ON DELETE SET NULL ON UPDATE CASCADE;


-- 15. 提现申请表 (withdrawal_requests)
-- Responsibilities: Records user withdrawal requests.
CREATE TABLE withdrawal_requests (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '提现申请ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '申请用户ID (外键, users.id)',
    amount DECIMAL(10, 2) NOT NULL COMMENT '申请提现金额',
    withdrawal_method VARCHAR(50) NOT NULL COMMENT '提现方式 (如 alipay, bank_card)',
    account_info JSON NOT NULL COMMENT '提现账户信息 (JSON 格式, e.g., {"account": "user@example.com", "name": "张三"}, 敏感信息需加密处理)',
    status ENUM('pending', 'processing', 'succeeded', 'failed', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '申请状态 (pending:待处理, processing:处理中, succeeded:成功, failed:失败, cancelled:已取消)',
    platform_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '提现手续费',
    actual_amount DECIMAL(10, 2) NOT NULL COMMENT '实际到账金额 (amount - platform_fee)',
    processed_at DATETIME(6) NULL COMMENT '后台处理时间',
    external_transaction_id VARCHAR(128) NULL UNIQUE COMMENT '外部转账流水号 (打款成功后记录)',
    failure_reason TEXT NULL COMMENT '失败原因 (如果 status 是 failed)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_status_created (status, created_at DESC),
    INDEX idx_created_at (created_at)
) COMMENT '用户提现申请表';


-- 13. 钱包流水表 (wallet_transactions)
-- Responsibilities: Records detailed changes in user wallet balances, ensuring account accuracy.
CREATE TABLE wallet_transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '流水唯一ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '关联用户ID (外键, users.id)',
    transaction_type ENUM('deposit', 'withdrawal', 'income', 'payment', 'refund', 'platform_fee', 'adjustment') NOT NULL COMMENT '交易类型 (deposit:充值, withdrawal:提现, income:收款, payment:付款, refund:退款, platform_fee:平台费, adjustment:调账)',
    amount DECIMAL(10, 2) NOT NULL COMMENT '交易金额 (正数表示增加, 负数表示减少)',
    balance_after DECIMAL(10, 2) NOT NULL COMMENT '本次交易后该用户的钱包余额快照',
    related_payment_id BIGINT UNSIGNED NULL COMMENT '关联的支付记录ID (外键, payments.id)',
    related_order_id BIGINT UNSIGNED NULL COMMENT '关联的订单ID (外键, orders.id, 冗余)',
    related_withdrawal_id BIGINT UNSIGNED NULL COMMENT '关联的提现申请ID (外键, withdrawal_requests.id)',
    description VARCHAR(255) NULL COMMENT '交易描述 (如 "订单 #123 收入", "提现申请 #456")',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (related_payment_id) REFERENCES payments(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (related_order_id) REFERENCES orders(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (related_withdrawal_id) REFERENCES withdrawal_requests(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_created_at (created_at)
) COMMENT '用户钱包流水表 (记录每一次余额变动)';

-- 14. 用户钱包表 (user_wallets)
-- Responsibilities: Stores current wallet balance and frozen amount for users (redundant table for performance).
CREATE TABLE user_wallets (
    user_id BIGINT UNSIGNED PRIMARY KEY COMMENT '关联用户ID (外键, users.id)',
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '当前可用余额 (实时更新, 需保证事务一致性)',
    frozen_balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '冻结金额 (如提现处理中、活动奖励待解锁等)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
) COMMENT '用户钱包余额表 (冗余快照, 用于快速查询)';

-- 17. 平台通知表 (notifications)
-- Responsibilities: Stores various platform notifications pushed to users (distinct from private messages, usually system-triggered, more structured).
CREATE TABLE notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '通知ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '接收用户ID (外键, users.id)',
    notification_type ENUM('system_announcement', 'job_recommendation', 'application_update', 'order_update', 'payment_update', 'evaluation_reminder', 'policy_update', 'verification_result', 'report_result', 'dispute_update') NOT NULL COMMENT '通知类型',
    title VARCHAR(100) NOT NULL COMMENT '通知标题',
    content TEXT NOT NULL COMMENT '通知内容 (可包含简单格式)',
    related_resource_type VARCHAR(50) NULL COMMENT '关联业务资源类型 (如 order, job, user, verification_record)',
    related_resource_id BIGINT UNSIGNED NULL COMMENT '关联业务资源ID (用于点击跳转)',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已读',
    read_at DATETIME(6) NULL COMMENT '阅读时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_user_read_created (user_id, is_read, created_at DESC),
    INDEX idx_created_at (created_at)
) COMMENT '平台通知表 (结构化系统通知)';

-- 18. 用户收藏表 (favorites)
-- Responsibilities: Stores user-favorited jobs or freelancers/employers.
CREATE TABLE favorites (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL COMMENT '收藏者用户ID (外键, users.id)',
    favorite_type ENUM('job', 'freelancer', 'employer') NOT NULL COMMENT '收藏类型',
    target_id BIGINT UNSIGNED NOT NULL COMMENT '被收藏对象的ID (根据 favorite_type 对应 jobs.id 或 users.id)',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_user_type_target (user_id, favorite_type, target_id),
    INDEX idx_user_type_created (user_id, favorite_type, created_at DESC)
) COMMENT '用户收藏表';

-- 19. 举报记录表 (reports)
-- Responsibilities: Stores report information submitted by users.
CREATE TABLE reports (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    reporter_user_id BIGINT UNSIGNED NOT NULL COMMENT '举报者用户ID (外键, users.id)',
    report_type ENUM('job', 'user', 'order', 'message', 'evaluation') NOT NULL COMMENT '举报对象类型',
    target_id BIGINT UNSIGNED NOT NULL COMMENT '被举报对象的ID (根据 report_type 对应相关表的 ID)',
    reason_category VARCHAR(50) NOT NULL COMMENT '举报原因分类 (如 虚假信息, 违规内容, 欺诈, 人身攻击)',
    reason_description TEXT NULL COMMENT '举报原因详述',
    attachments JSON NULL COMMENT '附件URL列表 (JSON 数组, 截图等证据, OSS/CDN)',
    status ENUM('pending', 'processing', 'resolved_valid', 'resolved_invalid', 'resolved_duplicate') NOT NULL DEFAULT 'pending' COMMENT '处理状态 (pending:待处理, processing:处理中, resolved_valid:有效举报已处理, resolved_invalid:无效举报, resolved_duplicate:重复举报)',
    processor_id BIGINT UNSIGNED NULL COMMENT '处理管理员ID (外键, admin_users.id)',
    processed_at DATETIME(6) NULL COMMENT '处理时间',
    processing_result TEXT NULL COMMENT '处理结果描述/操作记录',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (reporter_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (processor_id) REFERENCES admin_users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_reporter_status (reporter_user_id, status),
    INDEX idx_target (report_type, target_id),
    INDEX idx_status_created (status, created_at DESC)
) COMMENT '用户举报记录表';

-- 20. 争议处理表 (disputes)
-- Responsibilities: Records the handling process when disputes arise in orders.
CREATE TABLE disputes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT UNSIGNED NOT NULL UNIQUE COMMENT '关联的订单ID (外键, orders.id, 一个订单最多一个争议)',
    initiator_user_id BIGINT UNSIGNED NOT NULL COMMENT '发起争议的用户ID (外键, users.id)',
    reason TEXT NOT NULL COMMENT '争议原因描述',
    expected_resolution TEXT NULL COMMENT '发起者期望的解决方案',
    attachments JSON NULL COMMENT '相关证据附件URL列表 (JSON 数组, OSS/CDN)',
    status ENUM('pending', 'negotiating', 'platform_intervening', 'resolved', 'closed') NOT NULL DEFAULT 'pending' COMMENT '争议状态 (pending:待处理, negotiating:双方协商中, platform_intervening:平台介入中, resolved:已解决, closed:已关闭)',
    resolution_result TEXT NULL COMMENT '最终解决方案/处理结果',
    platform_mediator_id BIGINT UNSIGNED NULL COMMENT '平台介入处理人ID (外键, admin_users.id)',
    resolved_at DATETIME(6) NULL COMMENT '解决时间',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),

    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (initiator_user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (platform_mediator_id) REFERENCES admin_users(id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_initiator_status (initiator_user_id, status),
    INDEX idx_status_created (status, created_at DESC)
) COMMENT '订单争议处理表';

-- 22. 系统配置表 (system_configs)
-- Responsibilities: Stores configurable parameters for the platform.
CREATE TABLE system_configs (
    config_key VARCHAR(100) PRIMARY KEY COMMENT '配置项键名 (英文, snake_case)',
    config_value TEXT NOT NULL COMMENT '配置项值 (根据类型可能是文本, 数字, JSON字符串等)',
    description VARCHAR(255) NULL COMMENT '配置项描述',
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) COMMENT '系统配置表 (存储可动态调整的参数)';

-- --- End of Script ---