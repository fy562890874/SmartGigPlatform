/**
 * 调试工具类，用于快速切换调试模式和显示调试信息
 */

// 检查是否在开发环境
const isDevelopment = process.env.NODE_ENV === 'development';

export const DebugUtil = {
  /**
   * 启用或禁用调试模式
   * @param enabled 是否启用调试模式
   */
  setDebugMode(enabled = true): void {
    localStorage.setItem('debug_mode', enabled.toString());
    console.log(`调试模式: ${enabled ? '已启用' : '已禁用'}`);
    
    if (enabled) {
      console.log('提示: 你可以在控制台使用以下命令快速切换调试模式:');
      console.log('- window.enableDebug(): 启用调试模式');
      console.log('- window.disableDebug(): 禁用调试模式');
    }
  },
  
  /**
   * 检查调试模式是否启用
   * @returns 调试模式状态
   */
  isDebugEnabled(): boolean {
    return localStorage.getItem('debug_mode') === 'true';
  },
  
  /**
   * 日志输出（仅在调试模式下显示）
   * @param message 日志消息
   * @param data 要显示的数据
   */
  log(message: string, data?: any): void {
    if (this.isDebugEnabled()) {
      console.log(`[DEBUG] ${message}`, data !== undefined ? data : '');
    }
  },
  
  /**
   * 在页面上显示调试信息浮层
   * 仅在开发环境和启用调试模式时显示
   * @param app Vue应用实例
   */
  setupDebugTools(): void {
    // 添加全局调试方法到window
    if (isDevelopment) {
      (window as any).enableDebug = () => this.setDebugMode(true);
      (window as any).disableDebug = () => this.setDebugMode(false);
      (window as any).showApiConfig = () => {
        import('./apiConfig').then(module => {
          console.log('API配置:', module.default);
        });
      };
    }
  }
};

// 自动设置调试工具
DebugUtil.setupDebugTools();

export default DebugUtil;
