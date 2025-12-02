# 隔空手势操作设置指南

## 功能说明

本应用支持完整的离线隔空手势操作，覆盖厨房看菜谱的所有动作：

### 支持的手势

1. **缩放** 🤏
   - 捏合（拇指和食指靠近）：缩小
   - 张开（手指分开）：放大

2. **滚动** 👆
   - 单指向上：向上滚动
   - 单指向下：向下滚动

3. **切换菜品** 👋
   - 手掌向左滑动：下一个菜品
   - 手掌向右滑动：上一个菜品

4. **返回** ✊
   - 握拳（保持0.5秒）：返回列表

## 离线模式设置

### 方法1：使用CDN（需要网络）

默认情况下，应用会尝试从CDN加载MediaPipe模型。如果网络可用，会自动使用CDN。

### 方法2：完全离线（推荐）

要实现完全离线模式，需要下载MediaPipe模型文件到本地：

#### 步骤1：创建目录结构

```bash
mkdir -p public/wasm
mkdir -p public/models
```

#### 步骤2：下载MediaPipe文件

1. **下载JavaScript文件**：
   - 访问：https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/
   - 下载 `vision_bundle.js` 到 `public/wasm/` 目录
   - 或者直接使用：`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js`

2. **下载WASM文件**：
   - 访问：https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm/
   - 下载所有 `.wasm` 和 `.js` 文件到 `public/wasm/` 目录
   - 主要文件包括：
     - `hand_landmarker_wasm_internal.js`
     - `hand_landmarker_wasm_internal.wasm`
     - 以及其他相关的 wasm 文件

3. **下载模型文件**：
   - 访问：https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/
   - 下载 `hand_landmarker.task` 到 `public/models/` 目录
   - 或者直接使用：`https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`

#### 步骤3：验证文件结构

最终的文件结构应该是：

```
public/
├── wasm/
│   ├── vision_bundle.js          # 主JavaScript文件
│   ├── hand_landmarker_wasm_internal.js
│   ├── hand_landmarker_wasm_internal.wasm
│   └── ... (其他wasm文件)
└── models/
    └── hand_landmarker.task      # 手势识别模型
```

**快速下载方法**：

**方法1：使用提供的脚本（推荐）**

- **Linux/Mac**: 运行 `bash download-mediapipe.sh`
- **Windows**: 在 PowerShell 中运行 `.\download-mediapipe.ps1`

**方法2：手动下载命令**

```bash
# 下载 vision_bundle.js
curl -L -o public/wasm/vision_bundle.js https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js

# 下载模型文件
curl -L -o public/models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

**Windows PowerShell**:
```powershell
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js" -OutFile "public\wasm\vision_bundle.js"
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -OutFile "public\models\hand_landmarker.task"
```

**注意**：WASM 文件会在运行时自动从 CDN 加载。如果需要完全离线，请手动访问 `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm/` 下载所有文件到 `public/wasm/` 目录。

## 使用方法

1. **启用手势模式**：
   - 点击右上角的手势图标按钮
   - 绿色表示已启用，灰色表示已禁用

2. **允许摄像头权限**：
   - 首次使用时，浏览器会请求摄像头权限
   - 必须允许才能使用手势功能

3. **手势操作**：
   - 在详情页面，将手放在摄像头前
   - 按照手势说明进行操作
   - 右上角会显示摄像头预览

## 技术说明

- **手势识别**：使用MediaPipe HandLandmarker模型
- **离线支持**：优先使用本地文件，CDN作为后备
- **性能优化**：使用GPU加速，60fps流畅识别
- **兼容性**：支持所有现代浏览器（Chrome、Firefox、Safari、Edge）

## 故障排除

### 摄像头无法启动
- 检查浏览器权限设置
- 确保没有其他应用占用摄像头
- 尝试刷新页面

### 手势识别不准确
- 确保光线充足
- 手部与摄像头保持适当距离（30-60cm）
- 背景简洁，避免干扰

### 离线模式不工作
- 检查文件是否正确下载到public目录
- 查看浏览器控制台错误信息
- 确保文件路径正确

## 注意事项

- 手势识别需要摄像头权限
- 建议在光线充足的环境中使用
- 手势操作有300ms冷却时间，避免误触发
- 在详情页面才能使用所有手势功能

