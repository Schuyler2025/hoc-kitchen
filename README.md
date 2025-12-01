<!--
 * @Author: Schuyler schuylerhu@gmail.com
 * @Date: 2025-11-29 22:01:03
 * @LastEditors: Schuyler schuylerhu@gmail.com
 * @LastEditTime: 2025-12-01 11:03:51
 * @FilePath: \hoc-kitchen\README.md
 * @Description:
 *
 * Copyright (c) 2025 by Schuyler, All Rights Reserved.
-->
<div align="center">
<img width="250" height="600" alt="HOC-Kitchen" src="hoc.jpg" />
</div>

# HOC-Kitchen 🍳

**基于手势控制的智能厨房助手应用**

## 📖 项目简介

HOC-Kitchen 是一个创新的厨房助手应用，结合了现代Web技术和手势控制功能，为用户提供智能化的烹饪体验。应用内置丰富的菜品数据库，支持手势缩放查看菜品详情。

### ✨ 核心特性

- **📱 现代化界面** - 基于React + TypeScript构建的响应式UI
- **👋 手势控制** - 支持手势缩放查看菜品详情
- **🍲 丰富菜品库** - 包含正餐、早餐、炸品、饮品等各类菜品
- **🔍 智能分类** - 按菜品类别快速筛选浏览
- **📊 详细工艺** - 完整的菜品制作工艺和配料信息
- **⚡ 快速启动** - 基于Vite的快速开发体验

## 🚀 快速开始

### 环境要求

- Node.js 16+
- npm 或 yarn

### 安装与运行

1. **克隆项目**
```bash
git clone https://github.com/schuyler2025/hoc-kitchen.git
cd hoc-kitchen
```

2. **安装依赖**
```bash
npm install
```

3. **配置环境变量**
创建 `.env.local` 文件并添加Gemini API密钥：
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. **启动开发服务器**
```bash
npm run dev
```

5. **访问应用**
打开浏览器访问 `http://localhost:4173`

### 构建生产版本

```bash
npm run build
npm run preview
```

## 🎯 功能演示

### 菜品浏览
- 查看各类菜品的基本信息和图片
- 按类别筛选（正餐、早餐、炸品、饮品、主食）
- 点击菜品查看详细制作工艺

### 手势控制
- 开启手势模式后，在详情页面可以通过手势缩放图片
- 张开手指放大，合拢手指缩小

## 📊 数据源

项目使用 `dish_info_category_page_img.json` 作为主要数据源，包含：
- 200+ 菜品数据
- 完整的制作工艺说明
- 分类信息（正餐、早餐、炸品、饮品、主食）
- 本地图片资源

## 🤝 贡献指南

我们欢迎任何形式的贡献！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [React](https://reactjs.org/) - 优秀的前端框架
- [Vite](https://vitejs.dev/) - 快速的构建工具
- [Google Gemini](https://ai.google.dev/) - AI服务支持
- [MediaPipe](https://mediapipe.dev/) - 手势识别技术

## 📞 联系我们

- 作者: Schuyler
- 邮箱: schuylerhu@gmail.com


