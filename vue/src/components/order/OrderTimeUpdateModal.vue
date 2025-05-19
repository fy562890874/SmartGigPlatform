<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isCompleteAction ? '完成工作并填写工作时间' : '更新工作时间'"
    width="600px"
    destroy-on-close
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="实际开始时间" prop="startTimeActual">
        <el-date-picker
          v-model="form.startTimeActual"
          type="datetime"
          placeholder="选择实际开始时间"
          format="YYYY-MM-DD HH:mm"
          value-format="YYYY-MM-DD HH:mm:ss"
          :disabled="submitting"
          style="width: 100%;"
        />
      </el-form-item>
      
      <el-form-item label="实际结束时间" prop="endTimeActual">
        <el-date-picker
          v-model="form.endTimeActual"
          type="datetime"
          placeholder="选择实际结束时间"
          format="YYYY-MM-DD HH:mm"
          value-format="YYYY-MM-DD HH:mm:ss"
          :disabled="submitting"
          style="width: 100%;"
        />
      </el-form-item>
      
      <div class="time-hint" v-if="calculatedDuration !== null">
        <el-alert
          type="info"
          :closable="false"
          show-icon
        >
          <template #title>
            根据您填写的时间，实际工作时长约为 <strong>{{ calculatedDuration }}</strong> 小时
          </template>
        </el-alert>
      </div>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog" :disabled="submitting">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        {{ isCompleteAction ? '确认完成工作' : '更新时间' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, defineProps, defineEmits, withDefaults } from 'vue';
import { ElMessage, FormInstance } from 'element-plus';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import dayjs from 'dayjs';

// 属性定义
interface Props {
  modelValue: boolean;  // 控制对话框显示/隐藏的v-model值
  orderId: number;      // 订单ID
  initialStartTime?: string | null; // 初始的实际开始时间
  initialEndTime?: string | null;   // 初始的实际结束时间
  isCompleteAction?: boolean;       // 是否是完成工作的操作
}

const props = withDefaults(defineProps<Props>(), {
  initialStartTime: null,
  initialEndTime: null,
  isCompleteAction: false
});

// 事件定义
const emit = defineEmits(['update:modelValue', 'success']);

// 获取authStore
const authStore = useAuthStore();

// 表单引用
const formRef = ref<FormInstance>();

// 状态变量
const submitting = ref(false);
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
});

// 表单数据
const form = reactive({
  startTimeActual: props.initialStartTime || '',
  endTimeActual: props.initialEndTime || ''
});

// 计算工作时长
const calculatedDuration = computed(() => {
  if (!form.startTimeActual || !form.endTimeActual) return null;
  
  const start = dayjs(form.startTimeActual);
  const end = dayjs(form.endTimeActual);
  
  if (!start.isValid() || !end.isValid() || end.isBefore(start)) return null;
  
  // 计算时间差（小时）
  const diffHours = end.diff(start, 'hour', true);
  return diffHours.toFixed(2);
});

// 表单验证规则
const rules = {
  startTimeActual: [
    { required: true, message: '请选择实际开始时间', trigger: 'change' }
  ],
  endTimeActual: [
    { required: true, message: '请选择实际结束时间', trigger: 'change' },
    { 
      validator: (rule: any, value: string, callback: Function) => {
        if (form.startTimeActual && value) {
          const start = dayjs(form.startTimeActual);
          const end = dayjs(value);
          if (end.isBefore(start)) {
            callback(new Error('结束时间不能早于开始时间'));
          } else {
            callback();
          }
        } else {
          callback();
        }
      }, 
      trigger: 'change' 
    }
  ]
};

// 关闭对话框
const closeDialog = () => {
  dialogVisible.value = false;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请检查表单填写是否正确');
      return;
    }
    
    submitting.value = true;
    
    try {
      const token = authStore.token;
      if (!token) {
        ElMessage.error('您尚未登录或登录已过期');
        closeDialog();
        return;
      }
      
      if (props.isCompleteAction) {
        // 是完成工作操作，调用action接口
        await completeWorkWithTimes();
      } else {
        // 仅更新时间，调用时间更新接口
        await updateWorkTimes();
      }
      
      // 操作成功
      ElMessage.success(props.isCompleteAction ? '工作已完成' : '工作时间已更新');
      emit('success');
      closeDialog();
    } catch (error: any) {
      console.error('提交失败:', error);
      ElMessage.error(error.response?.data?.message || '操作失败，请稍后重试');
    } finally {
      submitting.value = false;
    }
  });
};

// 更新工作时间
const updateWorkTimes = async () => {
  const payload = {
    start_time_actual: form.startTimeActual,
    end_time_actual: form.endTimeActual
  };
  
  await axios.put(
    `http://127.0.0.1:5000/api/v1/orders/${props.orderId}/actual_times`,
    payload,
    {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      }
    }
  );
};

// 完成工作并提交时间
const completeWorkWithTimes = async () => {
  const payload = {
    action: 'complete_work',
    start_time_actual: form.startTimeActual,
    end_time_actual: form.endTimeActual
  };
  
  await axios.post(
    `http://127.0.0.1:5000/api/v1/orders/${props.orderId}/actions`,
    payload,
    {
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      }
    }
  );
};

// 初始化默认时间
onMounted(() => {
  // 如果没有初始时间，则设置默认值
  if (!form.startTimeActual && props.isCompleteAction) {
    // 对于完成工作操作，默认开始时间可以是当前时间向前推几小时
    form.startTimeActual = dayjs().subtract(4, 'hour').format('YYYY-MM-DD HH:mm:ss');
  }
  
  if (!form.endTimeActual && props.isCompleteAction) {
    // 对于完成工作操作，默认结束时间为当前时间
    form.endTimeActual = dayjs().format('YYYY-MM-DD HH:mm:ss');
  }
});
</script>

<style scoped>
.time-hint {
  margin-top: 16px;
}
</style> 