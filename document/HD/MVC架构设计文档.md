# 智慧零工平台 - 后端 MVC (变体) 架构设计文档 (完整版 v1.0)

**文档版本:** 1.0
**更新日期:** 2025年4月25日

**1. 引言**

**1.1. 目的**

本文档旨在详细

**1.2. 范围**
本文档聚焦于单个微服务内部的逻辑分层，重点描述模型层 (Model)、服务层 (Service) 和 API 接口层 (API/Controller) 的设计原则、职责划分、交互方式以及关键模块的设计细节。数据库设计细节（表结构）和具体的 API 规范将分别在 `database_design.txt` 和 `API规范文档.txt` 中详细定义，本文档侧重于架构层面的分析和指导。

**1.3. 术语定义**
*   **Model (模型层):** 负责数据持久化和数据结构定义。直接映射数据库表结构，使用 SQLAlchemy ORM 进行实现。包含数据验证、关系定义等。
*   **Service (服务层):** 负责核心业务逻辑的处理。编排 Model 操作，处理复杂的业务规则、事务管理、与外部服务（如缓存、消息队列、其他微服务）的交互。是业务功能的聚合点。
*   **API/Controller (接口层):** 负责处理 HTTP 请求和响应。接收用户输入，进行基础验证（格式、类型），调用 Service 层处理业务，序列化结果并返回给客户端。使用 Flask-RESTX 实现。
*   **DTO (Data Transfer Object):** 数据传输对象，用于在不同层之间（尤其是 API 层和 Service 层）传递数据，避免直接暴露 Model。通常使用 Marshmallow Schemas 实现。
*   **ORM (Object-Relational Mapping):** 对象关系映射，将数据库表映射为 Python 对象 (SQLAlchemy)。

**2. 架构概述**

**2.1. 分层架构**
平台后端微服务内部采用经典的三层架构：

```
+---------------------+      +-----------------+      +-----------------+
|   API/Controller    |<---->|     Service     |<---->|      Model      |
| (Flask-RESTX Views) |      | (Business Logic)|      | (SQLAlchemy ORM)|
+---------------------+      +-----------------+      +-----------------+
       |                            |                       |  /|\
       | (HTTP Request/Response)    | (Method Calls)        |   | (DB Operations)
      \|/                           |                       |   |
+---------------------+             |                       |   |
|      Client         |             |                       |   |
| (Web/App/MiniApp)   |             |                       |   |
+---------------------+             |                       |   |
                                   \|/                     \|/ \|/
                      +--------------------------+    +-------------+
                      | External Services/Utils  |    |  Database   |
                      | (Cache, MQ, Other Micro) |    |   (MySQL)   |
                      +--------------------------+    +-------------+
```

**2.2. 职责划分**
*   **API/Controller 层:**
    *   定义 RESTful API 路由和端点。
    *   接收 HTTP 请求，解析请求参数 (路径、查询、请求体)。
    *   使用 Marshmallow Schemas 对输入数据进行初步验证和反序列化为 DTO。
    *   调用相应的 Service 层方法处理业务逻辑。
    *   处理 Service 层返回的数据或异常。
    *   使用 Marshmallow Schemas 将 Service 层返回的数据序列化为 JSON 响应。
    *   处理认证 (JWT 验证) 和基本授权检查。
    *   不包含任何业务逻辑或数据库操作。
*   **Service 层:**
    *   实现核心业务逻辑，是业务用例 (Use Case) 的主要实现者。
    *   根据业务需求，调用一个或多个 Model 进行数据读写操作。
    *   编排跨多个 Model 的操作，确保业务流程的完整性。
    *   处理复杂的业务验证和规则。
    *   管理数据库事务。
    *   与缓存 (Redis)、消息队列 (Celery)、搜索引擎 (Elasticsearch) 等基础服务交互。
    *   调用其他微服务的接口（通过 HTTP Client 或 RPC）。
    *   封装业务异常。
    *   输入和输出通常是 DTO 或基本数据类型，避免直接依赖 HTTP 上下文。
*   **Model 层:**
    *   定义数据模型，映射数据库表 (使用 SQLAlchemy)。
    *   定义模型之间的关系 (一对一、一对多、多对多)。
    *   包含基础的数据验证规则 (如字段长度、非空约束)。
    *   提供数据的 CRUD (创建、读取、更新、删除) 基础接口（由 SQLAlchemy 提供）。
    *   不包含业务逻辑，仅关注数据持久化。

**2.3. 数据流**
一个典型的请求处理流程如下：
1.  客户端发起 HTTP 请求到 API 网关。
2.  网关进行认证、限流等处理后，将请求路由到具体的业务微服务 API/Controller 层。
3.  API/Controller 层接收请求，解析参数，使用 Marshmallow Schema 反序列化请求体为输入 DTO。
4.  API/Controller 层调用对应的 Service 层方法，传递输入 DTO。
5.  Service 层执行业务逻辑：
    *   进行详细的业务规则校验。
    *   调用一个或多个 Model 对象进行数据库查询或修改。
    *   (可能) 与 Redis 缓存交互。
    *   (可能) 发送异步任务到 Celery。
    *   (可能) 调用其他微服务。
    *   组装处理结果（可能是 DTO 或基本类型）。
6.  Service 层将处理结果或业务异常返回给 API/Controller 层。
7.  API/Controller 层接收 Service 返回结果：
    *   如果成功，使用 Marshmallow Schema 将结果序列化为 JSON。
    *   如果失败 (业务异常)，转换为标准的错误响应格式。
8.  API/Controller 层将 HTTP 响应返回给客户端。

**3. Model 层设计**

**3.1. ORM 与数据库**
*   **ORM:** SQLAlchemy。提供强大的对象关系映射能力。
*   **数据库:** MySQL。关系型数据库，适用于结构化数据存储。
*   **数据库迁移:** Alembic。用于管理数据库模式的变更，确保开发、测试、生产环境的模式一致性。

**3.2. 核心模型设计 (示例)**
*(注意：以下仅为示例，详细设计需参考 `database_design.txt`)*

*   **User (用户模型):**
    *   `id`: 主键, INT, Auto Increment
    *   `uuid`: 唯一标识符, VARCHAR(36), Unique, Indexed
    *   `phone_number`: 手机号, VARCHAR(20), Unique, Indexed (用于登录)
    *   `password_hash`: 加密密码, VARCHAR(255)
    *   `nickname`: 昵称, VARCHAR(50)
    *   `avatar_url`: 头像链接, VARCHAR(255)
    *   `user_type`: 用户类型 (Enum: 'individual', 'employer'), VARCHAR(20), Indexed
    *   `status`: 账户状态 (Enum: 'active', 'inactive', 'banned'), VARCHAR(20), Indexed
    *   `created_at`: 创建时间, DATETIME
    *   `updated_at`: 更新时间, DATETIME
    *   **关系:**
        *   One-to-One with `UserProfile` (可选，如果信息复杂)
        *   One-to-Many with `Work` (作为发布者)
        *   One-to-Many with `Application` (作为申请者)
        *   One-to-Many with `Order` (作为雇主或零工)
        *   One-to-Many with `Review` (作为评价者或被评价者)
        *   One-to-Many with `Message` (作为发送者或接收者)
        *   One-to-One with `Wallet` (用户钱包)
        *   Many-to-Many with `Role` (角色/权限)

*   **Work (工作/零工任务模型):**
    *   `id`: 主键, INT, Auto Increment
    *   `uuid`: 唯一标识符, VARCHAR(36), Unique, Indexed
    *   `employer_id`: 发布者用户 ID, INT, ForeignKey('user.id'), Indexed
    *   `title`: 标题, VARCHAR(100), Indexed (可能需要全文索引)
    *   `description`: 详细描述, TEXT
    *   `category_id`: 工作分类 ID, INT, ForeignKey('category.id'), Indexed
    *   `tags`: 标签 (JSON or separate table), VARCHAR(255) / Many-to-Many
    *   `location`: 工作地点/区域, VARCHAR(255)
    *   `salary_type`: 薪资类型 (Enum: 'hourly', 'fixed', 'negotiable'), VARCHAR(20)
    *   `salary_min`: 最低薪资, DECIMAL(10, 2)
    *   `salary_max`: 最高薪资, DECIMAL(10, 2)
    *   `status`: 工作状态 (Enum: 'open', 'closed', 'in_progress', 'completed', 'cancelled'), VARCHAR(20), Indexed
    *   `start_time`: 预计开始时间, DATETIME (可选)
    *   `end_time`: 预计结束时间, DATETIME (可选)
    *   `required_skills`: 所需技能 (JSON or separate table)
    *   `view_count`: 浏览次数, INT, Default 0
    *   `application_deadline`: 申请截止日期, DATE (可选)
    *   `created_at`: 创建时间, DATETIME
    *   `updated_at`: 更新时间, DATETIME
    *   **关系:**
        *   Many-to-One with `User` (发布者)
        *   One-to-Many with `Application`
        *   Many-to-One with `Category`
        *   Many-to-Many with `Tag` (如果使用关联表)

*   **Application (工作申请模型):**
    *   `id`: 主键, INT, Auto Increment
    *   `work_id`: 申请的工作 ID, INT, ForeignKey('work.id'), Indexed
    *   `applicant_id`: 申请人用户 ID, INT, ForeignKey('user.id'), Indexed
    *   `status`: 申请状态 (Enum: 'pending', 'accepted', 'rejected', 'withdrawn'), VARCHAR(20), Indexed
    *   `message`: 申请留言 (可选), TEXT
    *   `created_at`: 申请时间, DATETIME
    *   `updated_at`: 更新时间, DATETIME
    *   **关系:**
        *   Many-to-One with `Work`
        *   Many-to-One with `User` (申请人)

*   **Order (订单模型):**
    *   `id`: 主键, INT, Auto Increment
    *   `order_sn`: 订单号, VARCHAR(64), Unique, Indexed
    *   `work_id`: 关联工作 ID, INT, ForeignKey('work.id'), Indexed
    *   `employer_id`: 雇主用户 ID, INT, ForeignKey('user.id'), Indexed
    *   `employee_id`: 零工用户 ID, INT, ForeignKey('user.id'), Indexed
    *   `amount`: 订单金额, DECIMAL(10, 2)
    *   `status`: 订单状态 (Enum: 'pending_payment', 'paid', 'in_progress', 'completed', 'cancelled', 'dispute'), VARCHAR(20), Indexed
    *   `payment_id`: 关联支付记录 ID (可选), INT, ForeignKey('payment.id'), Nullable
    *   `start_time`: 实际开始时间, DATETIME (可选)
    *   `end_time`: 实际完成时间, DATETIME (可选)
    *   `created_at`: 创建时间, DATETIME
    *   `updated_at`: 更新时间, DATETIME
    *   **关系:**
        *   Many-to-One with `Work`
        *   Many-to-One with `User` (雇主)
        *   Many-to-One with `User` (零工)
        *   One-to-One/Many-to-One with `Payment`
        *   One-to-Many with `Review` (一个订单可能有多方评价)

*   **(其他模型):** `Category`, `Tag`, `Payment`, `Review`, `Message`, `Notification`, `Wallet`, `Transaction`, `Role`, `Permission`, `AdminUser` 等，根据具体业务需求设计。

**3.3. 设计原则与考虑**
*   **命名规范:** 模型类名使用驼峰式 (PascalCase)，表名使用下划线式 (snake_case)。字段名使用下划线式。
*   **主键与 UUID:** 推荐使用自增 INT 作为主键 (`id`) 以获得最佳数据库性能，同时为需要对外暴露或跨服务引用的实体增加一个 `uuid` 字段，避免暴露自增 ID。
*   **索引:** 对经常用于查询条件的字段 (如外键、状态、类型、唯一标识符) 添加索引。
*   **关系:** 明确定义模型间的关系 (One-to-One, One-to-Many, Many-to-Many)，并设置合适的外键约束和级联操作 (如 `ondelete='CASCADE'` 或 `'SET NULL'`)。
*   **数据类型:** 选择最合适的数据类型 (如 `VARCHAR`, `TEXT`, `INT`, `DECIMAL`, `DATETIME`, `BOOLEAN`, `JSON`)。
*   **枚举类型:** 对于状态、类型等字段，优先使用数据库的 ENUM 类型或在 SQLAlchemy 中定义 Enum 类型，以增强可读性和约束性。
*   **时间戳:** 普遍添加 `created_at` 和 `updated_at` 字段，并设置自动更新。
*   **软删除:** 对于需要保留历史记录的数据，可以考虑添加 `deleted_at` 字段实现软删除，但这会增加查询复杂性，需谨慎评估。
*   **冗余与反范式:** 在性能要求高的场景下，可适度进行数据冗余（反范式设计），如在订单表中冗余部分工作信息，但需注意数据一致性维护。

**4. Service 层设计**

**4.1. 职责与定位**
Service 层是业务逻辑的核心，它连接 API 层和 Model 层，负责：
*   封装和实现具体的业务用例。
*   编排对 Model 的操作，隐藏数据访问细节。
*   执行复杂的业务规则和数据校验。
*   管理数据库事务，保证操作的原子性。
*   与缓存、消息队列、搜索引擎等基础设施交互。
*   调用其他微服务接口，处理服务间协作。
*   处理业务异常并向上层抛出。

**4.2. 核心服务设计 (示例)**

*   **UserService:**
    *   `register(phone, password, user_type)`: 用户注册，包括密码加密、创建用户记录、初始化钱包等。
    *   `login(phone, password)`: 用户登录，验证密码，生成 JWT Token。
    *   `get_user_by_id(user_id)`: 根据 ID 获取用户信息。
    *   `get_user_by_uuid(uuid)`: 根据 UUID 获取用户信息。
    *   `update_profile(user_id, profile_data)`: 更新用户资料。
    *   `change_password(user_id, old_password, new_password)`: 修改密码。
    *   `ban_user(user_id, reason)`: 禁用用户。
    *   `get_user_wallet(user_id)`: 获取用户钱包信息。
    *   (可能涉及与认证服务交互进行实名认证等)

*   **WorkService:**
    *   `publish_work(employer_id, work_data)`: 发布新工作，校验数据，创建 Work 记录。
    *   `get_work_details(work_id, user_id=None)`: 获取工作详情 (可能需要判断用户是否已申请)。
    *   `search_works(query, filters, sort, page, per_page)`: 搜索/筛选工作列表 (可能调用 Elasticsearch 服务)。
    *   `update_work(work_id, employer_id, update_data)`: 更新工作信息 (需要权限检查)。
    *   `close_work(work_id, employer_id)`: 关闭工作招聘。
    *   `apply_for_work(applicant_id, work_id, message)`: 用户申请工作，创建 Application 记录，可能发送通知给雇主。
    *   `get_applications_for_work(work_id, employer_id, status=None)`: 获取某工作的申请列表 (雇主视角)。
    *   `get_user_applications(applicant_id, status=None)`: 获取用户自己的申请列表。
    *   `accept_application(application_id, employer_id)`: 雇主接受申请，更新申请状态，可能触发创建订单流程 (调用 OrderService 或发送消息)。
    *   `reject_application(application_id, employer_id)`: 雇主拒绝申请。

*   **OrderService:**
    *   `create_order_from_application(application_id)`: (由 WorkService 接受申请后触发) 创建订单，初始化状态为待支付。
    *   `get_order_details(order_id, user_id)`: 获取订单详情 (需要判断用户是雇主还是零工)。
    *   `pay_order(order_id, user_id, payment_method)`: 用户支付订单 (调用支付服务，更新订单状态)。
    *   `confirm_work_start(order_id, user_id)`: 确认工作开始 (雇主或零工操作，更新订单状态)。
    *   `confirm_work_completion(order_id, user_id)`: 确认工作完成 (雇主操作，触发结算流程)。
    *   `cancel_order(order_id, user_id, reason)`: 取消订单 (根据状态和规则判断是否允许)。
    *   `handle_dispute(order_id, user_id, description)`: 处理订单争议。
    *   `process_order_settlement(order_id)`: (由确认完成或定时任务触发) 处理订单结算，资金划转 (调用 WalletService 或支付服务)。

*   **(其他服务):** `PaymentService`, `ReviewService`, `MessageService`, `NotificationService`, `CacheService`, `SearchService` (可能封装对 ES 的调用), `WalletService` 等。

**4.3. 设计原则与考虑**
*   **单一职责:** 每个 Service 类应聚焦于特定的业务领域。
*   **无状态:** Service 实例本身应尽量无状态，依赖通过方法参数传入。
*   **依赖注入:** 虽然 Python 不像 Java/C# 那样有强框架支持，但应遵循依赖注入原则。Service 的依赖 (如其他 Service、Repository/DAO、外部客户端) 应在构造时传入或通过某种形式的容器管理，便于测试和替换。
*   **事务管理:** 对于涉及多个数据库写操作的业务方法，应使用事务确保原子性。可以使用 `try...except...finally` 结合 SQLAlchemy 的 `session.commit()` 和 `session.rollback()`，或使用装饰器简化事务管理。
*   **错误处理:** Service 层应捕获数据访问层或下游服务的异常，并转换为明确的业务异常 (自定义 Exception 类) 抛出给 API 层。不应直接将底层异常暴露给上层。
*   **DTO 使用:** Service 方法的输入和输出推荐使用 DTO (如 Marshmallow Schema 加载/导出的字典或简单对象)，而不是直接操作 Model 对象，以实现层间解耦。
*   **缓存应用:** 对于读多写少的数据，Service 层应负责与 CacheService 交互，实现缓存读取和失效逻辑。
*   **异步任务:** 对于耗时操作 (如发送邮件/短信、复杂计算、调用慢速第三方 API)，Service 层应将任务发送到 Celery 消息队列进行异步处理。
*   **幂等性:** 对于可能重复调用的操作 (尤其是在异步或重试场景下)，需要设计保证幂等性 (如检查状态、使用唯一请求 ID)。

**5. API/Controller 层设计**

**5.1. 框架与工具**
*   **Web 框架:** Flask。
*   **API 构建:** Flask-RESTX。提供路由、请求解析、响应格式化、Swagger 文档自动生成等功能。
*   **序列化/反序列化/验证:** Marshmallow。定义 Schema 来验证输入数据、序列化输出数据。

**5.2. 核心 API 设计 (示例)**
*(注意：仅为示例，详细设计需参考 `API规范文档.txt`)*

*   **用户 API (`/users`)**
    *   `POST /users/register`: 用户注册 (调用 `UserService.register`)
    *   `POST /users/login`: 用户登录 (调用 `UserService.login`)
    *   `GET /users/me`: 获取当前用户信息 (需要认证, 调用 `UserService.get_user_by_id`)
    *   `PUT /users/me/profile`: 更新当前用户资料 (需要认证, 调用 `UserService.update_profile`)
    *   `PUT /users/me/password`: 修改当前用户密码 (需要认证, 调用 `UserService.change_password`)
    *   `GET /users/{user_uuid}`: 获取指定用户信息 (管理员或公开信息)

*   **工作 API (`/works`)**
    *   `POST /works`: 发布新工作 (需要雇主认证, 调用 `WorkService.publish_work`)
    *   `GET /works`: 搜索/获取工作列表 (调用 `WorkService.search_works`)
    *   `GET /works/{work_uuid}`: 获取工作详情 (调用 `WorkService.get_work_details`)
    *   `PUT /works/{work_uuid}`: 更新工作信息 (需要发布者认证, 调用 `WorkService.update_work`)
    *   `POST /works/{work_uuid}/close`: 关闭工作 (需要发布者认证, 调用 `WorkService.close_work`)
    *   `POST /works/{work_uuid}/apply`: 申请工作 (需要零工认证, 调用 `WorkService.apply_for_work`)
    *   `GET /works/{work_uuid}/applications`: 获取工作申请列表 (需要发布者认证, 调用 `WorkService.get_applications_for_work`)

*   **申请 API (`/applications`)**
    *   `GET /applications/my`: 获取我的申请列表 (需要零工认证, 调用 `WorkService.get_user_applications`)
    *   `POST /applications/{application_id}/accept`: 接受申请 (需要对应工作发布者认证, 调用 `WorkService.accept_application`)
    *   `POST /applications/{application_id}/reject`: 拒绝申请 (需要对应工作发布者认证, 调用 `WorkService.reject_application`)

*   **订单 API (`/orders`)**
    *   `GET /orders`: 获取我的订单列表 (需要认证, 根据用户类型调用 `OrderService.get_user_orders`)
    *   `GET /orders/{order_sn}`: 获取订单详情 (需要认证且为订单参与方, 调用 `OrderService.get_order_details`)
    *   `POST /orders/{order_sn}/pay`: 支付订单 (需要认证且为雇主, 调用 `OrderService.pay_order`)
    *   `POST /orders/{order_sn}/confirm_start`: 确认工作开始 (需要认证且为订单参与方, 调用 `OrderService.confirm_work_start`)
    *   `POST /orders/{order_sn}/confirm_completion`: 确认工作完成 (需要认证且为雇主, 调用 `OrderService.confirm_work_completion`)
    *   `POST /orders/{order_sn}/cancel`: 取消订单 (需要认证且为订单参与方, 调用 `OrderService.cancel_order`)

**5.3. 设计原则与考虑**
*   **RESTful:** 遵循 REST 设计原则，使用标准的 HTTP 方法 (GET, POST, PUT, DELETE, PATCH)，面向资源进行设计。
*   **资源命名:** 使用名词复数形式命名资源路径 (e.g., `/users`, `/works`)。
*   **版本控制:** 在 API 路径中加入版本号 (e.g., `/api/v1/users`)，方便未来升级。
*   **输入验证:** 使用 Marshmallow Schema 在 API 入口处对请求参数和请求体进行严格验证，对无效输入返回 400 Bad Request。
*   **序列化:** 使用 Marshmallow Schema 将 Service 返回的数据（通常是 DTO 或 Model 对象）序列化为统一的 JSON 格式。控制暴露给客户端的字段。
*   **认证与授权:**
    *   **认证:** 通过 JWT (Flask-JWT-Extended) 实现。需要认证的接口应添加相应装饰器，验证 Token 有效性并获取用户身份。
    *   **授权:** 在 API 层进行基本的角色检查或资源所有权检查（例如，用户只能修改自己的资料）。复杂的权限逻辑应委托给 Service 层处理。
*   **错误处理:** 统一处理 Service 层抛出的业务异常和框架自身的异常，将其映射为标准的 HTTP 错误响应 (如 400, 401, 403, 404, 500) 和统一的错误消息格式。
*   **响应格式:** 定义统一的 JSON 响应结构，例如：
    ```json
    // 成功
    {
      "code": 0, // 或 20000 等成功码
      "message": "Success",
      "data": { ... } // 或 [...]
    }
    // 失败
    {
      "code": 40001, // 自定义错误码
      "message": "Invalid input: phone number is required.",
      "data": null
    }
    ```
*   **文档生成:** 利用 Flask-RESTX 自动生成 Swagger/OpenAPI 文档，方便前后端协作和 API 测试。
*   **限流:** 在网关或 API 层实现接口限流，防止恶意请求。

**6. 跨层关注点**

*   **日志记录:** 在各层都应进行日志记录。API 层记录请求入口和出口信息；Service 层记录关键业务步骤和异常；Model 层（或 Repository）记录数据库操作。使用标准 `logging` 库，配置统一的日志格式 (JSON)，包含 Trace ID 以便追踪。
*   **配置管理:** 配置信息（数据库连接、密钥、第三方服务地址等）应通过环境变量或配置文件管理，由应用启动时加载，各层按需读取。
*   **依赖管理:** 使用 `requirements.txt` 或 `Pipfile`/`pyproject.toml` 管理项目依赖。

**7. 可扩展性设计**

*   **模块化:** 清晰的层级划分和模块化设计使得添加新功能或修改现有功能时，影响范围可控。
*   **面向接口 (服务层):** Service 层定义清晰的业务接口，未来可以方便地替换实现或增加新的实现。
*   **配置驱动:** 将易变部分（如第三方服务地址、业务规则阈值）放入配置，便于调整。
*   **异步化:** 对于可异步处理的流程，使用消息队列解耦，提高系统的响应能力和吞吐量。
*   **事件驱动:** 考虑引入事件驱动机制，当核心业务发生变化时发布事件，其他服务可以订阅这些事件进行响应，进一步降低耦合度。

**8. 总结**

本架构采用 Model-Service-API 的分层模式，结合 Flask、SQLAlchemy、Flask-RESTX、Marshmallow 等技术栈，旨在构建结构清晰、职责分明、易于维护和扩展的后端微服务。通过明确各层职责、规范交互方式、统一处理通用关注点，为智慧零工平台的稳定运行和未来发展奠定坚实的基础。后续开发应严格遵循本文档定义的架构原则。