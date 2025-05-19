/**
 * 验证码工具函数
 * 用于生成图片验证码
 */

/**
 * 生成指定长度的随机字符串
 * @param length 字符串长度
 * @returns 随机字符串
 */
export const generateRandomString = (length: number = 4): string => {
  // 验证码字符集，去除了容易混淆的字符
  const characters = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * characters.length));
  }
  return result;
};

/**
 * 生成验证码图片
 * @param code 验证码字符串
 * @param width 图片宽度
 * @param height 图片高度
 * @returns 图片的 Data URL
 */
export const generateCaptchaImage = (code: string, width: number = 120, height: number = 40): string => {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  
  if (!ctx) return '';
  
  // 绘制背景
  ctx.fillStyle = '#f0f0f0';
  ctx.fillRect(0, 0, width, height);
  
  // 绘制干扰线
  for (let i = 0; i < 3; i++) {
    ctx.strokeStyle = getRandomColor(40, 180);
    ctx.beginPath();
    ctx.moveTo(Math.random() * width, Math.random() * height);
    ctx.lineTo(Math.random() * width, Math.random() * height);
    ctx.stroke();
  }
  
  // 绘制干扰点
  for (let i = 0; i < 20; i++) {
    ctx.fillStyle = getRandomColor(0, 255);
    ctx.beginPath();
    ctx.arc(Math.random() * width, Math.random() * height, 1, 0, 2 * Math.PI);
    ctx.fill();
  }
  
  // 绘制验证码
  ctx.fillStyle = '#333';
  ctx.font = 'bold 24px Arial';
  ctx.textBaseline = 'middle';
  const textWidth = ctx.measureText(code).width;
  const startX = (width - textWidth) / 2;
  
  // 每个字符单独绘制，并添加随机旋转
  for (let i = 0; i < code.length; i++) {
    const char = code.charAt(i);
    const charX = startX + i * (textWidth / code.length);
    const charY = height / 2 + Math.random() * 8 - 4;
    
    ctx.save();
    ctx.translate(charX, charY);
    ctx.rotate((Math.random() * 30 - 15) * Math.PI / 180);
    ctx.fillStyle = getRandomColor(10, 100);
    ctx.fillText(char, 0, 0);
    ctx.restore();
  }
  
  // 返回图片的 Data URL
  return canvas.toDataURL('image/png');
};

/**
 * 获取随机颜色
 * @param min RGB最小值
 * @param max RGB最大值
 * @returns 随机颜色
 */
const getRandomColor = (min: number, max: number): string => {
  const r = Math.floor(Math.random() * (max - min) + min);
  const g = Math.floor(Math.random() * (max - min) + min);
  const b = Math.floor(Math.random() * (max - min) + min);
  return `rgb(${r},${g},${b})`;
};
