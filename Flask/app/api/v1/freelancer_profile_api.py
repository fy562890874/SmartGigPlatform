from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.freelancer_profile_service import freelancer_profile_service
from ...services.skill_service import skill_service # Added for skill operations
from ...schemas import FreelancerProfileSchema
from ...schemas.skill_schema import SkillSchema as PublicSkillSchema # For nested skill details
from ...schemas.skill_schema import FreelancerSkillSchema # For input/output of freelancer skills
from ...utils.exceptions import BusinessException, InvalidUsageException, NotFoundException, AuthorizationException
from ...utils.helpers import api_success_response
from ...models.profile import FreelancerProfile # For profile_exists check

ns = Namespace('profiles/freelancer', description='零工用户档案及技能操作 (需要认证)') # Updated description

# === Freelancer Profile API Models ===
freelancer_profile_model = ns.model('FreelancerProfileOutput', {
    'user_id': fields.Integer(readonly=True, description='关联的用户ID'),
    'real_name': fields.String(description='真实姓名'),
    'gender': fields.String(description='性别', enum=['male', 'female', 'other', 'unknown']),
    'birth_date': fields.Date(description='出生日期 (YYYY-MM-DD)'),
    'avatar_url': fields.String(description='头像 URL'),
    'nickname': fields.String(description='昵称'),
    'location_province': fields.String(description='常驻省份'),
    'location_city': fields.String(description='常驻城市'),
    'location_district': fields.String(description='常驻区县'),
    'bio': fields.String(description='个人简介'),
    'work_preference': fields.Raw(description='工作偏好 (JSON对象)'),
    'verification_status': fields.String(readonly=True, description='实名认证状态'),
    'credit_score': fields.Integer(readonly=True, description='信用分'),
    'average_rating': fields.Float(readonly=True, description='平均评分'),
    'total_orders_completed': fields.Integer(readonly=True, description='累计完成订单数'),
    'created_at': fields.DateTime(readonly=True),
    'updated_at': fields.DateTime(readonly=True)
})

freelancer_profile_input_model = ns.model('FreelancerProfileInput', {
    'real_name': fields.String(description='真实姓名'),
    'gender': fields.String(description='性别', enum=['male', 'female', 'other', 'unknown']),
    'birth_date': fields.Date(description='出生日期 (YYYY-MM-DD)'),
    'avatar_url': fields.String(description='头像 URL'),
    'nickname': fields.String(description='昵称'),
    'location_province': fields.String(description='常驻省份'),
    'location_city': fields.String(description='常驻城市'),
    'location_district': fields.String(description='常驻区县'),
    'bio': fields.String(description='个人简介'),
    'work_preference': fields.Raw(description='工作偏好 (JSON对象)', example={'categories': ['家政'], 'time_slots':['weekend']})
})

# === Freelancer Skill API Models (moved here) ===
# Nested skill model for output (reusing public skill structure)
nested_skill_output_model = ns.model('NestedSkillOutputForFreelancer', {
    'id': fields.Integer(readonly=True, description='技能ID'),
    'name': fields.String(readonly=True, description='技能名称'),
    'category': fields.String(readonly=True, description='技能分类')
    # Add other fields from PublicSkillSchema if needed in this context
})

freelancer_skill_output_model = ns.model('FreelancerSkillOutput', {
    'freelancer_user_id': fields.Integer(readonly=True, description='零工用户ID'),
    'skill_id': fields.Integer(readonly=True, description='技能ID'),
    'skill': fields.Nested(nested_skill_output_model, description='技能详情'),
    'proficiency_level': fields.String(description='熟练度 (e.g., beginner, intermediate, advanced, expert)'),
    'years_of_experience': fields.Integer(description='相关经验年限'),
    'certificate_url': fields.String(description='证书链接'),
    'certificate_verified': fields.Boolean(readonly=True, description='证书是否已验证'),
    'created_at': fields.DateTime(readonly=True, description='关联创建时间'),
    'updated_at': fields.DateTime(readonly=True, description='关联更新时间')
})

freelancer_skill_add_input_model = ns.model('FreelancerSkillAddInput', {
    'skill_id': fields.Integer(required=True, description='要添加的技能ID'),
    'proficiency_level': fields.String(description='熟练度', example='intermediate'),
    'years_of_experience': fields.Integer(description='经验年限', example=3),
    'certificate_url': fields.String(description='证书链接 (可选)', example='http://example.com/certificate.pdf')
})

freelancer_skill_update_input_model = ns.model('FreelancerSkillUpdateInput', {
    'proficiency_level': fields.String(description='熟练度', example='advanced'),
    'years_of_experience': fields.Integer(description='经验年限', example=5),
    'certificate_url': fields.String(description='证书链接 (可选)', example='http://example.com/new_certificate.pdf')
})


@ns.route('/me') 
class FreelancerProfileSelfResource(Resource):
    @jwt_required()
    @ns.response(200, '获取零工档案成功', model=freelancer_profile_model)
    def get(self):
        """获取当前登录用户的零工档案"""
        current_user_id = get_jwt_identity()
        try:
            profile = freelancer_profile_service.get_profile_by_user_id(current_user_id)
            profile_data = FreelancerProfileSchema().dump(profile)
            return api_success_response(profile_data)
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message="获取零工档案时发生意外错误。", status_code=500, error_code=50001)

    @jwt_required()
    @ns.expect(freelancer_profile_input_model, validate=True)
    @ns.response(200, '零工档案更新成功', model=freelancer_profile_model)
    @ns.response(201, '零工档案创建成功', model=freelancer_profile_model)
    def put(self):
        """创建或更新当前登录用户的零工档案"""
        current_user_id = get_jwt_identity()
        data = request.json
        try:
            profile_is_present = FreelancerProfile.query.filter_by(user_id=current_user_id).first() is not None
            profile = freelancer_profile_service.create_or_update_profile(current_user_id, data, is_creation=not profile_is_present)
            profile_data = FreelancerProfileSchema().dump(profile)
            status_code = 200 if profile_is_present else 201
            return api_success_response(profile_data, status_code)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            action = "更新" if profile_is_present else "创建"
            raise BusinessException(message=f"{action}零工档案时发生意外错误: {str(e)}", status_code=500, error_code=50001)

# === Freelancer Skill Routes (now part of this namespace) ===
@ns.route('/me/skills') # Path: /api/v1/profiles/freelancer/me/skills
class FreelancerProfileSkillsResource(Resource):
    @jwt_required()
    @ns.doc(description="当前零工获取自己的技能列表。需要零工角色。")
    @ns.response(200, '获取零工技能列表成功', model=fields.List(fields.Nested(freelancer_skill_output_model)))
    @ns.response(403, '用户非零工角色或零工档案不存在')
    def get(self):
        """当前零工获取自己的技能列表"""
        current_user_id = get_jwt_identity()
        try:
            freelancer_skills = skill_service.get_freelancer_skills(current_user_id)
            result_data = FreelancerSkillSchema(many=True).dump(freelancer_skills)
            return api_success_response(result_data)
        except (AuthorizationException, NotFoundException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"获取零工技能列表失败: {str(e)}", status_code=500)

    @jwt_required()
    @ns.doc(description="当前零工为自己的档案添加技能。需要零工角色。")
    @ns.expect(freelancer_skill_add_input_model, validate=True)
    @ns.response(201, '零工技能添加成功', model=freelancer_skill_output_model)
    @ns.response(400, '输入无效或技能已存在')
    @ns.response(403, '用户非零工角色或零工档案不存在')
    @ns.response(404, '指定技能ID不存在')
    def post(self):
        """当前零工为自己的档案添加技能"""
        current_user_id = get_jwt_identity()
        data = request.json
        try:
            new_freelancer_skill = skill_service.add_skill_to_freelancer(current_user_id, data)
            result_data = FreelancerSkillSchema().dump(new_freelancer_skill)
            return api_success_response(result_data, status_code=201)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"添加零工技能失败: {str(e)}", status_code=500)

@ns.route('/me/skills/<int:skill_id>') # Path: /api/v1/profiles/freelancer/me/skills/<skill_id>
@ns.param('skill_id', '零工已关联的技能ID')
class FreelancerProfileSkillDetailResource(Resource):
    @jwt_required()
    @ns.doc(description="当前零工更新已关联的技能信息。需要零工角色。")
    @ns.expect(freelancer_skill_update_input_model, validate=True)
    @ns.response(200, '零工技能更新成功', model=freelancer_skill_output_model)
    @ns.response(400, '输入无效')
    @ns.response(403, '用户非零工角色')
    @ns.response(404, '零工未关联此技能或技能ID不存在')
    def put(self, skill_id):
        """当前零工更新已关联的技能信息"""
        current_user_id = get_jwt_identity()
        data = request.json
        try:
            updated_skill_assoc = skill_service.update_freelancer_skill(current_user_id, skill_id, data)
            result_data = FreelancerSkillSchema().dump(updated_skill_assoc)
            return api_success_response(result_data)
        except (InvalidUsageException, NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"更新零工技能失败: {str(e)}", status_code=500)

    @jwt_required()
    @ns.doc(description="当前零工从自己的档案中移除技能。需要零工角色。")
    @ns.response(204, '零工技能移除成功') # No model for 204
    @ns.response(403, '用户非零工角色')
    @ns.response(404, '零工未关联此技能或技能ID不存在')
    def delete(self, skill_id):
        """当前零工从自己的档案中移除技能"""
        current_user_id = get_jwt_identity()
        try:
            skill_service.remove_skill_from_freelancer(current_user_id, skill_id)
            return api_success_response(None, status_code=204) # No content
        except (NotFoundException, AuthorizationException, BusinessException) as e:
            raise e
        except Exception as e:
            raise BusinessException(message=f"移除零工技能失败: {str(e)}", status_code=500)

# Optionally, add public GET endpoint for profiles if needed (e.g., /<int:user_id>)
# This would require careful consideration of privacy and what data is exposed. 