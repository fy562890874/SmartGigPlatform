from ..models.job import Job, JobStatusEnum, SalaryTypeEnum # Added SalaryTypeEnum
from ..models.user import User # To verify employer existence or role
from ..models.skill import Skill, JobRequiredSkill # Corrected import: JobRequiredSkill is in skill.py
from ..core.extensions import db
from ..utils.exceptions import InvalidUsageException, NotFoundException, AuthorizationException, BusinessException
from datetime import datetime
from sqlalchemy import or_, and_
from flask import current_app # For logging

class JobService:
    def create_job(self, employer_user_identity, data):
        """
        创建新工作
        :param employer_user_identity: 发布工作的雇主用户身份 (UUID string from JWT or user ID)
        :param data: 包含工作详情的字典 (title, description, job_category, location_address, etc.)
        :return: 创建的 Job 对象
        """
        current_app.logger.info(f"[JobService] Attempting to find employer with identity: {employer_user_identity}")
        
        # 首先尝试将identity作为ID直接查找用户
        employer = None
        
        try:
            # 尝试将identity转换为整数ID
            user_id = int(employer_user_identity)
            employer = User.query.get(user_id)
            if employer:
                current_app.logger.info(f"[JobService] Found employer by ID: {user_id}")
        except (ValueError, TypeError):
            # 如果不是有效的整数ID，可能是UUID
            current_app.logger.info(f"[JobService] Identity {employer_user_identity} is not a valid integer ID, trying as UUID")
        
        # 如果通过ID未找到，尝试通过UUID查找
        if not employer and isinstance(employer_user_identity, str):
            employer = User.query.filter_by(uuid=employer_user_identity).first()
            if employer:
                current_app.logger.info(f"[JobService] Found employer by UUID: {employer_user_identity}")
        
        if not employer:
            current_app.logger.warning(f"[JobService] Employer not found with identity: {employer_user_identity}")
            raise NotFoundException(message="发布工作的用户不存在。", error_code=40401)

        current_app.logger.info(f"[JobService] Employer found: ID {employer.id}, UUID {employer.uuid}, Role: {employer.current_role}, Available: {employer.available_roles}")

        # 角色检查
        user_roles = employer.available_roles if isinstance(employer.available_roles, list) else []
        if hasattr(employer, 'current_role') and hasattr(employer, 'available_roles'):
            if 'employer' not in user_roles and employer.current_role != 'employer':
                current_app.logger.warning(f"[JobService] User {employer_user_identity} is not authorized to post jobs. Roles: {user_roles}, Current: {employer.current_role}")
                raise AuthorizationException(message="用户无权发布工作。", error_code=40302)
        else:
            current_app.logger.error(f"[JobService] User {employer_user_identity} object is missing role attributes.")
            raise BusinessException(message="用户信息不完整，无法验证角色。")

        # Validate required fields from data (schemas should handle this mostly at API layer)
        required_fields = ['title', 'description', 'job_category', 'location_address', 'start_time', 'end_time', 'salary_amount', 'salary_type', 'required_people']
        for field in required_fields:
            if field not in data or data[field] is None: # Check for None as well
                 raise InvalidUsageException(message=f"缺少必填字段: {field}")


        # Handle location_point: if lat/lon provided, convert to GeoJSON
        location_point_data = None
        if 'location_point' in data and isinstance(data['location_point'], dict) and \
           'coordinates' in data['location_point'] and 'type' in data['location_point']:
            location_point_data = data['location_point']
        elif data.get('longitude') is not None and data.get('latitude') is not None:
            try:
                longitude = float(data['longitude'])
                latitude = float(data['latitude'])
                location_point_data = {"type": "Point", "coordinates": [longitude, latitude]}
            except (ValueError, TypeError):
                raise InvalidUsageException("经纬度必须是有效的数字。")
        
        try:
            start_time = datetime.fromisoformat(str(data['start_time']).replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(str(data['end_time']).replace('Z', '+00:00'))
            application_deadline = None
            if data.get('application_deadline'):
                application_deadline = datetime.fromisoformat(str(data['application_deadline']).replace('Z', '+00:00'))
        except ValueError as ve:
            raise InvalidUsageException(f"日期时间格式无效: {str(ve)}. 请使用 ISO 8601 格式 (例如 YYYY-MM-DDTHH:MM:SSZ)")


        new_job = Job(
            employer_user_id=employer.id, # Use the validated employer's ID
            title=data['title'],
            description=data['description'],
            job_category=data['job_category'],
            job_tags=data.get('job_tags'),
            location_address=data['location_address'],
            location_province=data.get('location_province'),
            location_city=data.get('location_city'),
            location_district=data.get('location_district'),
            location_point=location_point_data,
            start_time=start_time,
            end_time=end_time,
            salary_amount=data['salary_amount'],
            salary_type=data['salary_type'],
            salary_negotiable=data.get('salary_negotiable', False),
            required_people=data['required_people'],
            skill_requirements=data.get('skill_requirements'),
            is_urgent=data.get('is_urgent', False),
            application_deadline=application_deadline,
            status=JobStatusEnum.active # 直接使用枚举对象，而不是枚举值
        )

        if new_job.salary_type not in [e.value for e in SalaryTypeEnum]:
            raise InvalidUsageException(f"无效的薪资类型: {new_job.salary_type}. 可选值: {[e.value for e in SalaryTypeEnum]}")


        db.session.add(new_job)
        try:
            db.session.commit()
            current_app.logger.info(f"[JobService] Job created successfully with ID: {new_job.id} by employer {employer.id}")
            return new_job
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[JobService] Error committing new job to database: {str(e)}", exc_info=True)
            raise BusinessException(message=f"创建工作时数据库操作失败。", status_code=500)

    def get_job_by_id(self, job_id, increment_view_count=False):
        """根据ID获取工作详情"""
        job = Job.query.get(job_id)
        if not job:
            raise NotFoundException(message="未找到指定的工作。", error_code=40401)
        
        if increment_view_count:
            try:
                job.view_count = (job.view_count or 0) + 1
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error incrementing view count for job {job_id}: {e}")

        return job

    def search_jobs(self, filters=None, sort_by=None, page=1, per_page=20):
        query = Job.query

        if filters:
            filter_conditions = []
            if filters.get('q'): # Keyword search
                term = f"%{filters['q']}%"
                filter_conditions.append(or_(Job.title.ilike(term), Job.description.ilike(term)))
            
            # 状态过滤处理
            if filters.get('status'):
                # 根据传入的状态值类型进行适当处理
                status_filter = filters['status']
                # 字符串值转换为枚举对象
                if isinstance(status_filter, str) and status_filter in [s.value for s in JobStatusEnum]:
                    try:
                        # 转换为枚举对象
                        status_enum = JobStatusEnum(status_filter)
                        filter_conditions.append(Job.status == status_enum)
                    except ValueError:
                        # 如果字符串值不是有效的枚举值
                        current_app.logger.warning(f"Invalid status value: {status_filter}")
                elif isinstance(status_filter, JobStatusEnum):
                    # 已经是枚举对象
                    filter_conditions.append(Job.status == status_filter) 
            else:
                # 默认显示活跃工作
                filter_conditions.append(Job.status == JobStatusEnum.active)

            for field in ['job_category', 'location_province', 'location_city', 'location_district', 'salary_type', 'employer_user_id']:
                if filters.get(field):
                    filter_conditions.append(getattr(Job, field) == filters[field])
            
            if filters.get('is_urgent') is not None:
                 filter_conditions.append(Job.is_urgent == filters['is_urgent'])

            if filters.get('salary_min'):
                filter_conditions.append(Job.salary_amount >= filters['salary_min'])
            if filters.get('salary_max'):
                filter_conditions.append(Job.salary_amount <= filters['salary_max'])

            if filters.get('start_time_from'):
                try:
                    start_time = datetime.fromisoformat(str(filters['start_time_from']).replace('Z', '+00:00'))
                    filter_conditions.append(Job.start_time >= start_time)
                except ValueError:
                    current_app.logger.warning(f"Invalid start_time_from format: {filters['start_time_from']}")
                
            if filters.get('start_time_to'):
                try:
                    end_time = datetime.fromisoformat(str(filters['start_time_to']).replace('Z', '+00:00'))
                    filter_conditions.append(Job.start_time <= end_time)
                except ValueError:
                    current_app.logger.warning(f"Invalid start_time_to format: {filters['start_time_to']}")
            
            # Geo-spatial search (placeholder for actual geo-queries)
            # if filters.get('latitude') and filters.get('longitude') and filters.get('radius_km'):
            #     # This requires specific DB functions (e.g., PostGIS ST_DWithin or custom calculation)
            #     # For now, this filter is illustrative and won't be fully functional without geo-extensions
            #     pass

            # Job tags (assuming job_tags is a JSON array of strings)
            # if filters.get('job_tags'):
            #     # This might require JSON_CONTAINS or similar, depending on DB
            #     # Example: query = query.filter(Job.job_tags.contains(filters['job_tags']))
            #     pass
            if filter_conditions:
                query = query.filter(and_(*filter_conditions))


        # Sorting (example: 'created_at_desc', 'salary_amount_asc')
        if sort_by:
            if sort_by == 'created_at_desc':
                query = query.order_by(Job.created_at.desc())
            elif sort_by == 'created_at_asc':
                query = query.order_by(Job.created_at.asc())
            elif sort_by == 'salary_amount_desc':
                query = query.order_by(Job.salary_amount.desc())
            elif sort_by == 'salary_amount_asc':
                query = query.order_by(Job.salary_amount.asc())
            # Add more sort options as needed
        else:
            query = query.order_by(Job.created_at.desc()) # Default sort
        
        paginated_jobs = query.paginate(page=page, per_page=per_page, error_out=False)
        return paginated_jobs

    def update_job(self, job_id, employer_user_id, data):
        """
        更新工作信息
        :param job_id: 要更新的工作ID
        :param employer_user_id: 操作用户ID (应为该工作的发布者)
        :param data: 包含要更新字段的字典
        :return: 更新后的 Job 对象
        """
        job = self.get_job_by_id(job_id) # Reuses get_job_by_id for existence check

        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权修改此工作信息。", error_code=40301)
        
        # 获取当前状态的字符串值以进行比较
        current_status = job.status
        if hasattr(job.status, 'value'):
            current_status = job.status.value
        
        # Prevent updates on jobs in certain statuses (e.g., completed, cancelled)
        if current_status in [JobStatusEnum.completed.value, JobStatusEnum.cancelled.value, JobStatusEnum.in_progress.value, JobStatusEnum.filled.value]:
            raise InvalidUsageException(message=f"工作状态为 {current_status}，不允许修改。", error_code=40902) # 状态冲突

        # Update fields (add more as needed)
        allowed_to_update = [
            'title', 'description', 'job_category', 'job_tags', 'location_address',
            'location_province', 'location_city', 'location_district', 'location_point',
            'start_time', 'end_time', 'salary_amount', 'salary_type', 'salary_negotiable',
            'required_people', 'skill_requirements', 'is_urgent', 'application_deadline', 'status'
        ]
        
        if 'longitude' in data and 'latitude' in data:
            try:
                data['location_point'] = {
                    "type": "Point",
                    "coordinates": [float(data['longitude']), float(data['latitude'])]
                }
            except ValueError:
                raise InvalidUsageException(message="经纬度格式不正确。")
        
        for key, value in data.items():
            if key in allowed_to_update:
                if value is not None:
                    if key in ['start_time', 'end_time', 'application_deadline'] and isinstance(value, str):
                        setattr(job, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    elif key == 'status':
                        # 特殊处理状态字段
                        if isinstance(value, str) and value in [s.value for s in JobStatusEnum]:
                            try:
                                # 字符串转换为枚举对象
                                status_enum = JobStatusEnum(value)
                                setattr(job, key, status_enum)
                            except ValueError:
                                raise InvalidUsageException(f"无效的工作状态: {value}")
                        elif isinstance(value, JobStatusEnum):
                            # 已经是枚举对象
                            setattr(job, key, value)
                        else:
                            raise InvalidUsageException(f"无效的工作状态: {value}")
                    else:
                        setattr(job, key, value)
                # Allow clearing fields with null if appropriate by passing null value for a key
                elif key in data and value is None:
                     setattr(job, key, None)

        try:
            db.session.commit()
            return job
        except Exception as e:
            db.session.rollback()
            # Log error e
            current_app.logger.error(f"[JobService] Error updating job: {str(e)}", exc_info=True)
            raise BusinessException(message=f"更新工作失败: {str(e)}", status_code=500, error_code=50001)

    def delete_job(self, job_id, employer_user_id, reason="由发布者删除"):
        """
        删除工作 (逻辑删除或硬删除，取决于业务需求)
        For now, let's assume logical delete by changing status to 'cancelled' or a new 'deleted' status.
        If hard delete: db.session.delete(job)
        """
        job = self.get_job_by_id(job_id)
        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权删除此工作。", error_code=40301)

        # 获取当前状态的字符串值以进行比较
        current_status = job.status
        if hasattr(job.status, 'value'):
            current_status = job.status.value
        
        # Prevent deletion if job has active applications or orders, or change to a specific status.
        if current_status in [JobStatusEnum.completed.value, JobStatusEnum.in_progress.value, JobStatusEnum.filled.value]:
            raise InvalidUsageException(message=f"工作状态为 {current_status}，无法直接删除，请先处理相关订单或申请。", error_code=40902)
        
        # Example: Logical delete by setting status to cancelled (or a dedicated 'deleted' status)
        job.status = JobStatusEnum.cancelled # 直接使用枚举对象
        job.cancellation_reason = reason
        
        try:
            db.session.commit()
            return True # Indicate success
        except Exception as e:
            db.session.rollback()
            # Log error e
            current_app.logger.error(f"[JobService] Error deleting job: {str(e)}", exc_info=True)
            raise BusinessException(message=f"删除工作失败: {str(e)}", status_code=500, error_code=50001)

    def close_job_listing(self, job_id, employer_user_id, reason="招聘结束"):
        job = self.get_job_by_id(job_id)
        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权关闭此工作。", error_code=40301)
        
        # 获取当前状态的字符串值以进行比较
        current_status = job.status
        if hasattr(job.status, 'value'):
            current_status = job.status.value
        
        if current_status not in [JobStatusEnum.active.value, JobStatusEnum.pending_review.value]: # Can close active or pending
            raise InvalidUsageException(f"工作当前状态为 {current_status}, 无法关闭。")

        # Typically, closing means it's filled or no longer accepting applications.
        # If it has accepted people less than required, 'cancelled' might be more appropriate.
        # If accepted_people >= required_people, 'filled' is good.
        # For simplicity, let's use 'filled' as a general "closed" status if not already terminal.
        job.status = JobStatusEnum.filled # 直接使用枚举对象
        # job.cancellation_reason = reason # Or a different field for "closing_reason"
        
        try:
            db.session.commit()
            return job
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[JobService] Error closing job: {str(e)}", exc_info=True)
            raise BusinessException(message=f"关闭工作失败: {str(e)}", status_code=500)

    def duplicate_job(self, job_id, employer_user_id):
        original_job = self.get_job_by_id(job_id)
        if original_job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权复制此工作。", error_code=40301)

        # 获取salary_type的值
        salary_type = original_job.salary_type
        if hasattr(original_job.salary_type, 'value'):
            salary_type = original_job.salary_type.value

        new_job_data = {
            "title": f"复制 - {original_job.title}",
            "description": original_job.description,
            "job_category": original_job.job_category,
            "job_tags": original_job.job_tags,
            "location_address": original_job.location_address,
            "location_province": original_job.location_province,
            "location_city": original_job.location_city,
            "location_district": original_job.location_district,
            "location_point": original_job.location_point, # copy GeoJSON
            "start_time": original_job.start_time.isoformat(), # convert to string for create_job
            "end_time": original_job.end_time.isoformat(),
            "salary_amount": original_job.salary_amount,
            "salary_type": salary_type, # 使用处理后的值
            "salary_negotiable": original_job.salary_negotiable,
            "required_people": original_job.required_people,
            "skill_requirements": original_job.skill_requirements,
            "is_urgent": original_job.is_urgent,
            "application_deadline": original_job.application_deadline.isoformat() if original_job.application_deadline else None,
        }
        # New job starts fresh
        # status will be pending_review by default in create_job
        # accepted_people, view_count will be 0
        
        try:
            # Call create_job with the new data
            duplicated_job = self.create_job(employer_user_id, new_job_data)
            
            # Optionally, copy required skills
            # for req_skill_assoc in original_job.required_skills_assoc:
            #    self.add_required_skill_to_job(
            #        duplicated_job.id,
            #        employer_user_id,
            #        {"skill_id": req_skill_assoc.skill_id, "is_mandatory": req_skill_assoc.is_mandatory}
            #    )
            # db.session.commit() # Commit skill additions if any
            return duplicated_job
        except Exception as e:
            current_app.logger.error(f"[JobService] Error duplicating job: {str(e)}", exc_info=True)
            raise

    def get_jobs_by_employer(self, employer_user_id, filters=None, sort_by=None, page=1, per_page=10):
        if filters is None:
            filters = {}
        filters['employer_user_id'] = employer_user_id
        # Can add specific statuses relevant for "my posted jobs" view, e.g., not 'cancelled' by default
        return self.search_jobs(filters=filters, sort_by=sort_by, page=page, per_page=per_page)

    def get_recommended_jobs(self, freelancer_user_id, count=10):
        # Placeholder for recommendation logic
        # This would typically involve user profile, skills, application history, job similarity etc.
        # For now, return a few recent active jobs, not personalized.
        user = User.query.get(freelancer_user_id)
        if not user:
            raise NotFoundException("用户不存在")
            
        query = Job.query.filter(Job.status == JobStatusEnum.active.value)\
                         .order_by(Job.created_at.desc())\
                         .limit(count)
        return query.all()

    def add_required_skill_to_job(self, job_id, employer_user_id, skill_data):
        job = self.get_job_by_id(job_id)
        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权修改此工作的技能要求。", error_code=40301)

        skill_id = skill_data.get('skill_id')
        if not skill_id:
            raise InvalidUsageException("技能ID不能为空。")

        skill = Skill.query.get(skill_id)
        if not skill:
            raise NotFoundException(f"技能ID {skill_id} 不存在。")

        existing_req = JobRequiredSkill.query.filter_by(job_id=job_id, skill_id=skill_id).first()
        if existing_req:
            raise InvalidUsageException(f"该工作已要求技能 '{skill.name}'。", error_code=40901)

        new_required_skill = JobRequiredSkill(
            job_id=job_id,
            skill_id=skill_id,
            is_mandatory=skill_data.get('is_mandatory', True) # Default to mandatory
            # proficiency_level=skill_data.get('proficiency_level') # If you add this to JobRequiredSkill model
        )
        db.session.add(new_required_skill)
        try:
            db.session.commit()
            # To return the object with skill details, you might need to eager load or query again.
            # For now, returning the created association object.
            return new_required_skill
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"为工作添加技能要求失败: {str(e)}", status_code=500, error_code=50001)

    def remove_required_skill_from_job(self, job_id, employer_user_id, skill_id):
        job = self.get_job_by_id(job_id)
        if job.employer_user_id != employer_user_id:
            raise AuthorizationException(message="您无权修改此工作的技能要求。", error_code=40301)

        required_skill = JobRequiredSkill.query.filter_by(job_id=job_id, skill_id=skill_id).first()
        if not required_skill:
            raise NotFoundException("该工作未要求此技能，无法移除。")

        db.session.delete(required_skill)
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise BusinessException(message=f"移除工作技能要求失败: {str(e)}", status_code=500, error_code=50001)

job_service = JobService()