# MediaPipe 离线文件下载脚本 (PowerShell)
# 用于下载 MediaPipe 手势识别所需的文件

Write-Host "开始下载 MediaPipe 离线文件..." -ForegroundColor Green

# 创建目录
New-Item -ItemType Directory -Force -Path "public\wasm" | Out-Null
New-Item -ItemType Directory -Force -Path "public\models" | Out-Null

# 下载 vision_bundle.js
Write-Host "下载 vision_bundle.js..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js" `
  -OutFile "public\wasm\vision_bundle.js"

# 下载模型文件
Write-Host "下载 hand_landmarker.task..." -ForegroundColor Yellow
Invoke-WebRequest -Uri "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" `
  -OutFile "public\models\hand_landmarker.task"

Write-Host ""
Write-Host "✓ 下载完成！" -ForegroundColor Green
Write-Host ""
Write-Host "文件结构："
Write-Host "  public\wasm\vision_bundle.js"
Write-Host "  public\models\hand_landmarker.task"
Write-Host ""
Write-Host "注意：WASM 文件会在运行时自动从 CDN 加载，" -ForegroundColor Cyan
Write-Host "     如果需要完全离线，请手动下载 wasm 目录下的所有文件。" -ForegroundColor Cyan


