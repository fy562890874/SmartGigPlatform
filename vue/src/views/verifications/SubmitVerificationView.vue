<template>
  <div class="submit-verification page-container">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <h1>用户实名认证</h1>
          <p class="hint-text">请提交真实有效的个人或企业认证资料，审核通过后可获得更多平台权益</p>
        </div>
      </template>

      <el-form 
        ref="verificationFormRef" 
        :model="verificationForm" 
        :rules="verificationRules" 
        label-width="120px" 
        class="verification-form"
        v-loading="loading"
      >
        <!-- 认证类型选择 -->
        <el-form-item label="认证类型" prop="profile_type">
          <el-radio-group v-model="verificationForm.profile_type" @change="handleTypeChange">
            <el-radio :disabled="userRole !== 'freelancer' && userRole !== 'employer'" label="freelancer">零工个人认证</el-radio>
            <el-radio :disabled="userRole !== 'employer'" label="employer_individual">雇主个人认证</el-radio>
            <el-radio :disabled="userRole !== 'employer'" label="employer_company">雇主企业认证</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 个人认证表单 (零工或雇主) -->
        <template v-if="verificationForm.profile_type === 'freelancer' || verificationForm.profile_type === 'employer_individual'">
          <el-form-item label="真实姓名" prop="submitted_data.real_name">
            <el-input v-model="verificationForm.submitted_data.real_name" placeholder="请输入与身份证一致的真实姓名" />
          </el-form-item>
          
          <el-form-item label="身份证号" prop="submitted_data.id_card_number">
            <el-input v-model="verificationForm.submitted_data.id_card_number" placeholder="请输入18位身份证号码" maxlength="18" />
          </el-form-item>

          <el-form-item label="身份证正面照" prop="submitted_data.id_card_photo_front_url">
            <el-upload
              class="avatar-uploader"
              action="#"
              :http-request="uploadIdCardFront"
              :show-file-list="false"
              accept="image/jpeg,image/png,image/jpg"
            >
              <img v-if="verificationForm.submitted_data.id_card_photo_front_url" :src="verificationForm.submitted_data.id_card_photo_front_url" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <div class="upload-hint">请上传清晰的身份证人像面照片，确保信息完整可见</div>
          </el-form-item>

          <el-form-item label="身份证背面照" prop="submitted_data.id_card_photo_back_url">
            <el-upload
              class="avatar-uploader"
              action="#"
              :http-request="uploadIdCardBack"
              :show-file-list="false"
              accept="image/jpeg,image/png,image/jpg"
            >
              <img v-if="verificationForm.submitted_data.id_card_photo_back_url" :src="verificationForm.submitted_data.id_card_photo_back_url" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <div class="upload-hint">请上传清晰的身份证国徽面照片，确保信息完整可见</div>
          </el-form-item>
        </template>

        <!-- 企业认证表单 -->
        <template v-if="verificationForm.profile_type === 'employer_company'">
          <el-form-item label="企业名称" prop="submitted_data.company_name">
            <el-input v-model="verificationForm.submitted_data.company_name" placeholder="请输入营业执照上的企业全称" />
          </el-form-item>
          
          <el-form-item label="统一社会信用代码" prop="submitted_data.business_license_number">
            <el-input v-model="verificationForm.submitted_data.business_license_number" placeholder="请输入18位统一社会信用代码" maxlength="18" />
          </el-form-item>

          <el-form-item label="法人代表姓名" prop="submitted_data.legal_representative">
            <el-input v-model="verificationForm.submitted_data.legal_representative" placeholder="请输入法人代表姓名" />
          </el-form-item>

          <el-form-item label="营业执照照片" prop="submitted_data.business_license_photo_url">
            <el-upload
              class="avatar-uploader"
              action="#"
              :http-request="uploadBusinessLicense"
              :show-file-list="false"
              accept="image/jpeg,image/png,image/jpg"
            >
              <img v-if="verificationForm.submitted_data.business_license_photo_url" :src="verificationForm.submitted_data.business_license_photo_url" class="avatar" />
              <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <div class="upload-hint">请上传清晰的营业执照照片，确保企业名称、统一社会信用代码等关键信息清晰可见</div>
          </el-form-item>
        </template>

        <!-- 提交按钮 -->
        <el-form-item class="form-actions">
          <el-checkbox v-model="agreeToTerms">我已阅读并同意<el-link type="primary" @click="showTerms">《平台认证服务协议》</el-link></el-checkbox>
        </el-form-item>

        <el-form-item class="form-actions">
          <el-button type="primary" @click="submitVerification" :disabled="!agreeToTerms || loading">提交认证申请</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 服务条款对话框 -->
    <el-dialog
      v-model="termsDialogVisible"
      title="平台认证服务协议"
      width="70%"
    >
      <div class="terms-content">
        <h3>实名认证须知</h3>
        <p>1. 本平台严格按照相关法律法规收集、使用和保护您提供的个人信息。</p>
        <p>2. 您提交的证件照片仅用于身份认证，我们将采取严格的安全措施保护您的敏感信息。</p>
        <p>3. 请确保您提供的信息真实、准确、完整，如有虚假将承担相应法律责任。</p>
        <p>4. 认证审核通常需要1-3个工作日，请耐心等待。</p>
        <p>5. 认证通过后，您将获得平台完整的权限和服务。</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="termsDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="agreeTerms">同意并继续</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { ElMessage, FormInstance } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import apiConfig from '@/utils/apiConfig';

// 路由和状态管理
const router = useRouter();
const authStore = useAuthStore();

// 表单和状态
const verificationFormRef = ref<FormInstance>();
const loading = ref(false);
const termsDialogVisible = ref(false);
const agreeToTerms = ref(false);

// 计算属性获取当前用户角色
const userRole = computed(() => {
  return authStore.user?.current_role || '';
});

// 表单数据
const verificationForm = reactive({
  profile_type: '',
  submitted_data: {
    real_name: '',
    id_card_number: '',
    id_card_photo_front_url: '',
    id_card_photo_back_url: '',
    company_name: '',
    business_license_number: '',
    legal_representative: '',
    business_license_photo_url: '',
  }
});

// 表单验证规则
const verificationRules = {
  profile_type: [
    { required: true, message: '请选择认证类型', trigger: 'change' }
  ],
  'submitted_data.real_name': [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  'submitted_data.id_card_number': [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/, message: '请输入正确的身份证号码', trigger: 'blur' }
  ],
  'submitted_data.id_card_photo_front_url': [
    { required: true, message: '请上传身份证正面照片', trigger: 'change' }
  ],
  'submitted_data.id_card_photo_back_url': [
    { required: true, message: '请上传身份证背面照片', trigger: 'change' }
  ],
  'submitted_data.company_name': [
    { required: true, message: '请输入企业名称', trigger: 'blur' }
  ],
  'submitted_data.business_license_number': [
    { required: true, message: '请输入统一社会信用代码', trigger: 'blur' },
    { pattern: /^[0-9A-HJ-NPQRTUWXY]{2}\d{6}[0-9A-HJ-NPQRTUWXY]{10}$/, message: '请输入正确的统一社会信用代码', trigger: 'blur' }
  ],
  'submitted_data.legal_representative': [
    { required: true, message: '请输入法人代表姓名', trigger: 'blur' }
  ],
  'submitted_data.business_license_photo_url': [
    { required: true, message: '请上传营业执照照片', trigger: 'change' }
  ]
};

// 认证类型切换处理
const handleTypeChange = (type: string) => {
  // 根据类型重置表单
  if (type === 'freelancer' || type === 'employer_individual') {
    verificationForm.submitted_data = {
      real_name: '',
      id_card_number: '',
      id_card_photo_front_url: '',
      id_card_photo_back_url: '',
      company_name: '',
      business_license_number: '',
      legal_representative: '',
      business_license_photo_url: ''
    };
  } else if (type === 'employer_company') {
    verificationForm.submitted_data = {
      real_name: '',
      id_card_number: '',
      id_card_photo_front_url: '',
      id_card_photo_back_url: '',
      company_name: '',
      business_license_number: '',
      legal_representative: '',
      business_license_photo_url: ''
    };
  }
};

// 初始化默认认证类型
onMounted(() => {
  // 根据用户当前角色设置默认认证类型
  if (userRole.value === 'freelancer') {
    verificationForm.profile_type = 'freelancer';
  } else if (userRole.value === 'employer') {
    verificationForm.profile_type = 'employer_individual';
  } else {
    // 如果没有角色或未登录，默认为零工认证
    verificationForm.profile_type = 'freelancer';
  }
});

// 文件上传处理函数 - 通常会对接云存储服务如阿里云OSS、七牛云等
// 这里为了演示，直接使用模拟的URL
const uploadIdCardFront = (options: any) => {
  const { file, onSuccess } = options;
  // 模拟上传，实际应该调用上传API
  setTimeout(() => {
    // 假设得到了一个URL
    const url = URL.createObjectURL(file);
    verificationForm.submitted_data.id_card_photo_front_url = url;
    onSuccess();
  }, 1000);
};

const uploadIdCardBack = (options: any) => {
  const { file, onSuccess } = options;
  // 模拟上传，实际应该调用上传API
  setTimeout(() => {
    const url = URL.createObjectURL(file);
    verificationForm.submitted_data.id_card_photo_back_url = url;
    onSuccess();
  }, 1000);
};

const uploadBusinessLicense = (options: any) => {
  const { file, onSuccess } = options;
  // 模拟上传，实际应该调用上传API
  setTimeout(() => {
    const url = URL.createObjectURL(file);
    verificationForm.submitted_data.business_license_photo_url = url;
    onSuccess();
  }, 1000);
};

// 显示服务条款
const showTerms = () => {
  termsDialogVisible.value = true;
};

// 同意服务条款
const agreeTerms = () => {
  agreeToTerms.value = true;
  termsDialogVisible.value = false;
};

// 提交认证申请
const submitVerification = async () => {
  if (!verificationFormRef.value) return;

  await verificationFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!agreeToTerms.value) {
        ElMessage.warning('请先同意认证服务协议');
        return;
      }

      try {
        loading.value = true;
        
        // 准备提交数据，保留必要字段
        const submitData = {
          profile_type: verificationForm.profile_type,
          submitted_data: {}
        };

        // 根据认证类型设置提交数据
        if (verificationForm.profile_type === 'freelancer' || verificationForm.profile_type === 'employer_individual') {
          submitData.submitted_data = {
            real_name: verificationForm.submitted_data.real_name,
            id_card_number: verificationForm.submitted_data.id_card_number,
            id_card_photo_front_url: verificationForm.submitted_data.id_card_photo_front_url,
            id_card_photo_back_url: verificationForm.submitted_data.id_card_photo_back_url
          };
        } else if (verificationForm.profile_type === 'employer_company') {
          submitData.submitted_data = {
            company_name: verificationForm.submitted_data.company_name,
            business_license_number: verificationForm.submitted_data.business_license_number,
            legal_representative: verificationForm.submitted_data.legal_representative,
            business_license_photo_url: verificationForm.submitted_data.business_license_photo_url
          };
        }

        // 发送认证请求到后端API
        const response = await axios.post(
          apiConfig.getApiUrl('verifications/submit'), 
          submitData,
          {
            headers: {
              'Authorization': `Bearer ${authStore.token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        if (response.data.code === 0) {
          ElMessage.success('认证申请提交成功，请耐心等待审核');
          // 跳转到认证记录页面
          router.push('/verifications/records');
        } else {
          ElMessage.error(response.data.message || '提交失败，请稍后重试');
        }
      } catch (error: any) {
        console.error('提交认证申请失败:', error);
        ElMessage.error(error.response?.data?.message || '提交失败，请稍后重试');
      } finally {
        loading.value = false;
      }
    } else {
      ElMessage.error('请填写所有必要的认证信息');
    }
  });
};

// 返回上一页
const goBack = () => {
  router.back();
};
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 900px;
  margin: 20px auto;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h1 {
  font-size: 1.8em;
  font-weight: bold;
  margin-bottom: 8px;
  color: var(--primary-red, #F56C6C);
}

.hint-text {
  color: #606266;
  font-size: 14px;
}

.verification-form {
  padding: 20px 0;
}

.avatar-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 240px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 178px;
  height: 178px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.upload-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.form-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

.terms-content {
  max-height: 400px;
  overflow-y: auto;
  padding: 0 20px;
}

.terms-content h3 {
  margin-top: 20px;
  margin-bottom: 15px;
  color: #303133;
}

.terms-content p {
  line-height: 1.7;
  margin-bottom: 10px;
  color: #606266;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
