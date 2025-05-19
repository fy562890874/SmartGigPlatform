from flask_restx import Namespace, Resource, fields, reqparse
from flask import current_app # For logging

from app.services.skill_service import skill_service # Assuming skill_service is in app.services
from app.schemas.skill_schema import SkillSchema
from app.utils.exceptions import BusinessException
from app.utils.helpers import api_success_response
from app.models import db, Skill # For direct query for categories if service doesn't have it yet
from sqlalchemy.exc import SQLAlchemyError


ns = Namespace('skills', description='公共技能信息库与分类')

# --- API Models ---
skill_output_model = ns.model('SkillOutput', {
    'id': fields.Integer(readonly=True, description='技能ID'),
    'name': fields.String(readonly=True, description='技能名称'),
    'category': fields.String(readonly=True, description='技能分类'),
    'description': fields.String(readonly=True, description='技能描述'),
    'is_hot': fields.Boolean(readonly=True, description='是否热门技能'),
    'created_at': fields.DateTime(readonly=True, description='创建时间'),
    'updated_at': fields.DateTime(readonly=True, description='更新时间')
})

paginated_skill_model = ns.model('PaginatedSkillResponse', {
    'items': fields.List(fields.Nested(skill_output_model)),
    'page': fields.Integer(description='当前页码'),
    'per_page': fields.Integer(description='每页数量'),
    'total_pages': fields.Integer(description='总页数'),
    'total_items': fields.Integer(description='总条目数')
})

skill_category_list_model = ns.model('SkillCategoryList', {
    'categories': fields.List(fields.String, description='技能分类列表')
})

# --- Parsers ---
skill_list_parser = reqparse.RequestParser()
skill_list_parser.add_argument('page', type=int, location='args', default=1, help='页码')
skill_list_parser.add_argument('per_page', type=int, location='args', default=20, help='每页数量')
skill_list_parser.add_argument('q', type=str, location='args', help='按名称搜索技能')
skill_list_parser.add_argument('category', type=str, location='args', help='按分类筛选技能')
skill_list_parser.add_argument('is_hot', type=bool, location='args', help='筛选热门技能 (true/false)')


# --- Routes for /api/v1/skills ---
@ns.route('')
class SkillListResource(Resource):
    @ns.expect(skill_list_parser)
    @ns.response(200, '获取技能列表成功', model=paginated_skill_model)
    def get(self):
        """获取平台技能标签库 (公开)"""
        args = skill_list_parser.parse_args()
        filters = {
            'q': args.get('q'),
            'category': args.get('category'),
            # is_hot needs careful handling for boolean from query args
            'is_hot': args.get('is_hot') if args.get('is_hot') is not None else None 
        }
        # Remove None filters to avoid passing them to service if they mean "don't filter"
        active_filters = {k: v for k, v in filters.items() if v is not None}

        try:
            paginated_skills = skill_service.get_all_skills(
                filters=active_filters,
                page=args.get('page'),
                per_page=args.get('per_page')
            )
            items_data = SkillSchema(many=True).dump(paginated_skills.items)
            return api_success_response({
                'items': items_data,
                'pagination': {
                    'page': paginated_skills.page,
                    'per_page': paginated_skills.per_page,
                    'total_pages': paginated_skills.pages,
                    'total_items': paginated_skills.total
                }
            })
        except Exception as e:
            current_app.logger.error(f"获取技能列表失败: {str(e)}")
            raise BusinessException(message="获取技能列表失败", internal_message=str(e))

@ns.route('/categories')
class SkillCategoriesResource(Resource):
    @ns.response(200, '获取技能分类成功', model=skill_category_list_model)
    @ns.doc(description="2.2. 获取技能分类 (Public)")
    def get(self):
        """获取所有唯一的技能分类列表"""
        try:
            # 调用服务方法获取所有技能分类
            categories = skill_service.get_all_skill_categories()
            return api_success_response({"categories": categories})
        except BusinessException as e:
            raise e
        except Exception as e:
            current_app.logger.error(f"获取技能分类失败: {str(e)}")
            raise BusinessException(message="获取技能分类失败", internal_message=str(e))
