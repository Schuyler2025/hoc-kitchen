#!/bin/bash

# MediaPipe 离线文件下载脚本
# 用于下载 MediaPipe 手势识别所需的文件

echo "开始下载 MediaPipe 离线文件..."

# 创建目录
mkdir -p public/wasm
mkdir -p public/models

# 下载 vision_bundle.js
echo "下载 vision_bundle.js..."
curl -L -o public/wasm/vision_bundle.js \
  https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/vision_bundle.js

# 下载模型文件
echo "下载 hand_landmarker.task..."
curl -L -o public/models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task

echo ""
echo "✓ 下载完成！"
echo ""
echo "文件结构："
echo "  public/wasm/vision_bundle.js"
echo "  public/models/hand_landmarker.task"
echo ""
echo "注意：WASM 文件会在运行时自动从 CDN 加载，"
echo "     如果需要完全离线，请手动下载 wasm 目录下的所有文件。"


