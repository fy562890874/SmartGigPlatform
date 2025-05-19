<template>
  <div class="order-action-panel">
    <!-- 零工操作按钮 -->
    <template v-if="currentRole === 'freelancer'">
      <!-- 待开工状态 -->
      <el-button 
        v-if="order.status === 'pending_start'" 
        type="success" 
        @click="startWork"
      >
        开始工作
      </el-button>
      
      <!-- 进行中状态 -->
      <el-button 
        v-if="order.status === 'in_progress'" 
        type="success" 
        @click="completeWork"
      >
        完成工作
      </el-button>
      
      <!-- 进行中状态 - 可以更新实际工作时间 -->
      <el-button 
        v-if="order.status === 'in_progress' || order.status === 'pending_confirmation'" 
        type="primary" 
        @click="updateWorkTimes"
      >
        更新工作时间
      </el-button>
      
      <!-- 订单可取消的状态 -->
      <el-button 
        v-if="['pending_payment', 'pending_start'].includes(order.status)" 
        type="danger" 
        @click="cancelOrder"
      >
        取消订单
      </el-button>
    </template>
    
    <!-- 雇主操作按钮 -->
    <template v-else-if="currentRole === 'employer'">
      <!-- 零工完成工作，待确认状态 -->
      <el-button 
        v-if="order.status === 'pending_confirmation'" 
        type="success" 
        @click="confirmCompletion"
      >
        确认完成
      </el-button>
      
      <!-- 零工完成工作，待确认状态 - 拒绝确认 -->
      <el-button 
        v-if="order.status === 'pending_confirmation'" 
        type="warning" 
        @click="rejectCompletion"
      >
        有问题
      </el-button>
      
      <!-- 订单可取消的状态 -->
      <el-button 
        v-if="['pending_payment', 'pending_start'].includes(order.status)" 
        type="danger" 
        @click="cancelOrder"
      >
        取消订单
      </el-button>
    </template>
    
    <!-- 通用操作按钮 -->
    <el-button 
      v-if="order.status === 'completed'" 
      type="primary" 
      icon="Star"
      @click="goToEvaluate"
    >
      评价
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, getCurrentInstance } from 'vue';
import { ElMessageBox } from 'element-plus';

// 定义属性
const props = defineProps({
  order: {
    type: Object,
    required: true
  },
  currentRole: {
    type: String,
    required: true
  }
});

// 定义事件
const emit = defineEmits(['action-performed', 'update-work-times']);

// 开始工作
const startWork = async () => {
  try {
    await ElMessageBox.confirm('确定要开始这项工作吗？', '开始工作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    });
    
    emit('action-performed', {
      action: 'start_work'
    });
  } catch {
    // 用户取消操作
  }
};

// 完成工作 (打开工作时间模态框)
const completeWork = () => {
  // 触发父组件打开工作时间更新模态框，模态框中包含完成工作逻辑
  emit('update-work-times', true, true); // 第二个参数表示是完成工作操作
};

// 更新工作时间
const updateWorkTimes = () => {
  emit('update-work-times', true, false); // 第二个参数表示不是完成工作操作，仅更新时间
};

// 确认完成
const confirmCompletion = async () => {
  try {
    await ElMessageBox.confirm('确认工作已完成且符合要求吗？', '确认完成', {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'success'
    });
    
    emit('action-performed', {
      action: 'confirm_completion'
    });
  } catch {
    // 用户取消操作
  }
};

// 拒绝确认 (有问题)
const rejectCompletion = async () => {
  try {
    const reason = await ElMessageBox.prompt('请说明有什么问题', '拒绝确认', {
      confirmButtonText: '提交',
      cancelButtonText: '取消',
      inputPlaceholder: '请描述问题...',
      type: 'warning',
      inputValidator: (value) => {
        return value.trim().length > 0 ? true : '请填写拒绝原因';
      }
    });
    
    if (reason.value) {
      emit('action-performed', {
        action: 'reject_completion',
        rejection_reason: reason.value
      });
    }
  } catch {
    // 用户取消操作
  }
};

// 取消订单
const cancelOrder = async () => {
  // 通知父组件打开取消订单对话框
  try {
    // 默认直接调用包含在父组件中的取消订单对话框
    // 这里假设父组件有个 openCancelDialog 方法
    const parent = getCurrentInstance()?.parent?.exposed;
    if (parent && 'openCancelDialog' in parent) {
      (parent as any).openCancelDialog();
    } else {
      // 如果父组件没有提供对话框，则在此处理
      const reason = await ElMessageBox.prompt('请填写取消订单的原因', '取消订单', {
        confirmButtonText: '确认取消',
        cancelButtonText: '返回',
        inputType: 'textarea',
        inputPlaceholder: '请输入取消原因...',
        type: 'warning',
        inputValidator: (value) => {
          return value.trim().length > 0 ? true : '请填写取消原因';
        }
      });
      
      if (reason.value) {
        emit('action-performed', {
          action: 'cancel_order',
          cancellation_reason: reason.value
        });
      }
    }
  } catch {
    // 用户取消操作
  }
};

// 去评价
const goToEvaluate = () => {
  // 跳转到评价页面
  // 暂时使用alert代替
  ElMessageBox.alert('评价功能暂未实现', '提示', {
    confirmButtonText: '确定'
  });
};
</script>

<style scoped>
.order-action-panel {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style> 