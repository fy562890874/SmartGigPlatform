# 智慧零工平台 - 后端 API 设计规范 (修订版)

## 1. 基本原则
*   **RESTful 风格:** 使用标准的 HTTP 方法 (GET, POST, PUT, PATCH, DELETE) 对资源进行操作。
*   **无状态:** 每个请求都应包含所有必要信息，服务器不依赖之前的请求状态 (使用 JWT 进行认证)。
*   **资源导向:** API 端点应围绕资源进行设计 (名词复数)。
*   **清晰一致:** 命名、格式、行为保持一致性。
*   **版本控制:** API 通过 URL 进行版本控制。

## 2. URL 规范
*   **根路径:** 所有 API 均以 `/api/v1/` 开头，`v1` 代表当前主版本号。
    *   示例: `/api/v1/users`, `/api/v1/jobs`
*   **资源名称:** 使用名词复数形式，采用 `snake_case` 命名。
    *   示例: `/api/v1/user_profiles`, `/api/v1/job_applications`
*   **资源标识:** 使用路径参数表示单个资源，参数名也用 `snake_case`。
    *   示例: `/api/v1/users/{user_id}`, `/api/v1/jobs/{job_id}`
*   **嵌套资源:** 表示资源间的从属关系，层级不宜过深 (建议最多一层嵌套)。
    *   示例: 获取某工作的申请列表: `GET /api/v1/jobs/{job_id}/applications`
    *   示例: 获取某用户的零工档案: `GET /api/v1/users/{user_id}/freelancer_profile`
*   **非 CRUD 操作:** 对于难以映射到标准 CRUD 的操作，使用动词，放在资源路径末尾。
    *   示例: 用户激活: `POST /api/v1/users/{user_id}/activate`
    *   示例: 接受申请: `POST /api/v1/job_applications/{application_id}/accept`
    *   示例: 刷新 Token: `POST /api/v1/auth/refresh`

## 3. HTTP 方法
*   **GET:** 获取资源 (单个或列表)。安全且幂等。
*   **POST:** 创建新资源，或执行某个动作。非幂等。
*   **PUT:** 完整替换资源。幂等。 (谨慎使用，通常 PATCH 更合适)
*   **PATCH:** 部分更新资源。非幂等。
*   **DELETE:** 删除资源。幂等。

## 4. 请求规范
*   **Headers:**
    *   `Content-Type: application/json` (对于 POST, PUT, PATCH 请求)
    *   `Accept: application/json` (客户端期望接收 JSON 响应)
    *   `Authorization: Bearer <jwt_access_token>` (对于需要认证的接口)
*   **参数:**
    *   **路径参数 (Path Parameters):** 用于标识资源，如 `{user_id}`。
    *   **查询参数 (Query Parameters):** 用于过滤、排序、分页。参数名使用 `snake_case`。
        *   过滤: `?status=active&min_salary=5000`
        *   排序: `?sort_by=created_at_desc,salary_asc` (字段名 + `_asc` 或 `_desc`)
        *   分页: `?page=1&per_page=20`
        *   字段选择 (可选): `?fields=id,title,salary_amount` (减少传输数据量)
    *   **请求体 (Request Body):** 用于 POST, PUT, PATCH 请求，包含要创建或更新的数据 (JSON 格式)。字段名使用 `snake_case`。
        ```json
        // POST /api/v1/jobs
        {
          "title": "紧急招聘周末传单派发员",
          "description": "负责在指定区域派发宣传单页...",
          "job_type": "派发",
          "location_address": "厦门市思明区XX路XX号",
          "start_time": "2025-05-10T09:00:00+08:00",
          "end_time": "2025-05-10T17:00:00+08:00",
          "salary_amount": 150.00,
          "salary_type": "fixed",
          "required_people": 5
        }
        ```

## 5. 响应规范
*   **Content-Type:** `application/json`
*   **状态码:** 使用标准的 HTTP 状态码。
*   **响应体结构:**
    *   **成功响应 (2xx):**
        ```json
        {
          "code": 0, // 固定为 0 表示业务成功
          "message": "Success", // 固定为 "Success"
          "data": { ... } // 单个资源对象 或 分页对象
          // 或
          "data": null // 对于 201 (有时返回创建的资源), 204 (无内容)
        }
        ```
        *   **分页对象结构:**
            ```json
            {
              "items": [ ... ], // 当前页的资源列表
              "pagination": {
                "page": 1,          // 当前页码
                "per_page": 20,     // 每页数量
                "total_items": 150, // 总条目数
                "total_pages": 8      // 总页数
              }
            }
            ```
    *   **失败响应 (4xx, 5xx):**
        ```json
        {
          "code": 40001, // 自定义业务错误码 (见下文)
          "message": "Invalid input parameter: email format is incorrect.", // 清晰的错误信息 (可直接展示给用户)
          "errors": { // 可选，提供详细字段错误 (用于表单校验)
            "email": ["Invalid email format.", "Email domain not allowed."],
            "password": ["Password is too short."]
          },
          "data": null // 固定为 null
        }
        ```
*   **字段命名:** 响应体字段名统一使用 `snake_case`。
*   **日期时间:** 统一使用 ISO 8601 格式字符串 (带时区信息)，如 `2025-04-27T10:30:00+08:00`。
*   **空值处理:** 对于不存在或无值的字段，返回 `null`，而不是省略该字段。

## 6. 业务错误码 (Code)
*   `0`: 成功
*   **4xxxx (客户端错误):**
    *   `400xx`: 通用参数错误 (如格式错误、缺失)
        *   `40001`: 无效输入参数
        *   `40002`: 请求体 JSON 解析失败
    *   `401xx`: 认证错误
        *   `40101`: 未提供认证信息 (Token missing)
        *   `40102`: 认证信息无效 (Token invalid/expired)
        *   `40103`: 用户名或密码错误
    *   `403xx`: 权限错误
        *   `40301`: 无权访问该资源
        *   `40302`: 角色权限不足
    *   `404xx`: 资源未找到
        *   `40401`: 请求的资源不存在
    *   `409xx`: 资源冲突
        *   `40901`: 手机号已被注册
        *   `40902`: 订单状态冲突，无法执行操作
    *   `422xx`: 语义错误 (请求格式正确，但业务逻辑无法处理)
        *   `42201`: 验证码错误
        *   `42202`: 余额不足
        *   `42203`: 工作时间冲突
    *   `429xx`: 请求过于频繁 (限流)
        *   `42901`: 请求次数过多
*   **5xxxx (服务器错误):**
    *   `500xx`: 服务器内部错误
        *   `50001`: 服务器内部未知错误
        *   `50002`: 数据库错误
        *   `50003`: 缓存服务错误
        *   `50004`: 异步任务执行失败
    *   `503xx`: 服务不可用
        *   `50301`: 服务暂时不可用 (如维护中)

## 7. API 文档
*   使用 Flask-RESTX 自动生成 Swagger/OpenAPI 3.0 文档。
*   为每个 API 端点、参数 (路径、查询、请求体)、响应体 (包括成功和失败结构)、业务错误码编写清晰、准确的描述。
*   提供请求和响应示例。
*   明确每个接口所需的认证和权限。

## 8. 版本管理策略
*   在 URL 中使用主版本号 (`/api/v1/`)。
*   对于不兼容的 API 变更，增加主版本号 (`/api/v2/`)。
*   对于向后兼容的变更 (如增加可选参数、增加响应字段)，保持主版本号不变。
*   旧版本 API 应在一段时间内继续维护 (至少 6-12 个月)，并通过文档和响应头 (如 `Warning` 或自定义头) 通知废弃计划。
