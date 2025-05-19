import { ElMessage, ElMessageBox } from 'element-plus';
import { Router } from 'vue-router';
import axios from 'axios';
import apiConfig from './apiConfig';

/**
 * 检查用户认证状态，如果未认证则提示进行认证
 * @param token JWT token
 * @param router Vue Router实例，用于导航
 * @param profileType 档案类型，freelancer或employer
 * @param requiredAction 需要认证才能进行的操作描述
 * @returns Promise<boolean> 是否已认证
 */
export async function checkVerificationStatus(
  token: string,
  router: Router,
  profileType: 'freelancer' | 'employer',
  requiredAction: string = '此操作'
): Promise<boolean> {
  try {
    // 发起请求检查认证状态
    const endpoint = profileType === 'freelancer' 
      ? 'profiles/freelancer/me'
      : 'profiles/employer/me';
    
    const response = await axios.get(
      apiConfig.getApiUrl(endpoint), 
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );

    // 如果请求成功并返回了数据
    if (response.data && response.data.code === 0) {
      const profileData = response.data.data;
      
      // 如果认证状态为已验证，则直接返回true
      if (profileData.verification_status === 'verified') {
        return true;
      } 
      // 如果认证状态为审核中
      else if (profileData.verification_status === 'pending') {
        ElMessage.warning('您的认证申请正在审核中，暂时无法' + requiredAction);
        return false;
      }
      // 如果未认证或认证被拒绝
      else {
        // 弹窗提示用户去认证
        await ElMessageBox.confirm(
          `${requiredAction}需要完成实名认证，是否立即前往认证？`,
          '未认证提示',
          {
            confirmButtonText: '去认证',
            cancelButtonText: '取消',
            type: 'warning'
          }
        );
        
        // 用户点击"去认证"后，跳转到认证页面
        router.push('/verifications/submit');
        return false;
      }
    } else {
      // API返回了错误
      ElMessage.error('获取认证状态失败，请稍后重试');
      return false;
    }
  } catch (error: any) {
    // 处理请求错误
    if (error.response && error.response.status === 404) {
      // 档案不存在，提示用户创建档案
      try {
        await ElMessageBox.confirm(
          `您尚未创建${profileType === 'freelancer' ? '零工' : '雇主'}档案，是否立即创建？`,
          '未创建档案',
          {
            confirmButtonText: '去创建',
            cancelButtonText: '取消',
            type: 'info'
          }
        );
        
        // 用户点击"去创建"后，跳转到相应的档案创建页面
        if (profileType === 'freelancer') {
          router.push('/profile/freelancer/edit');
        } else {
          router.push('/profile/employer/edit');
        }
      } catch {
        // 用户取消，不执行操作
      }
    } else if (!error.message.includes('canceled')) {
      // 不是用户取消造成的错误，显示错误消息
      ElMessage.error('检查认证状态时发生错误，请稍后重试');
      console.error('检查认证状态失败:', error);
    }
    return false;
  }
}

/**
 * 格式化认证状态为显示文本
 * @param status 认证状态
 * @returns 格式化后的文本
 */
export function formatVerificationStatus(status: string | null | undefined): string {
  if (!status) return '未认证';
  
  const statusMap: Record<string, string> = {
    'verified': '已认证',
    'pending': '审核中',
    'failed': '认证失败',
    'not_verified': '未认证'
  };
  
  return statusMap[status] || status;
}

/**
 * 获取认证状态对应的tag类型
 * @param status 认证状态
 * @returns Element Plus的tag类型
 */
export function getVerificationStatusType(status: string | null | undefined): string {
  if (!status) return 'info';
  
  const typeMap: Record<string, string> = {
    'verified': 'success',
    'pending': 'warning',
    'failed': 'danger',
    'not_verified': 'info'
  };
  
  return typeMap[status] || 'info';
}
