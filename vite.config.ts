/*
 * @Author: Schuyler schuylerhu@gmail.com
 * @Date: 2025-11-29 22:01:03
 * @LastEditors: Schuyler schuylerhu@gmail.com
 * @LastEditTime: 2025-11-30 10:21:23
 * @FilePath: \hoc-kitchen\vite.config.ts
 * @Description:
 *
 * Copyright (c) 2025 by Schuyler, All Rights Reserved.
 */
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
      },
      preview: {
        port: 4173,
        host: '0.0.0.0',
      },
      plugins: [react()],
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        }
      },
      publicDir: 'public',
      build: {
        outDir: 'dist',
        assetsDir: 'assets',
        rollupOptions: {
          external: ['/wasm/vision_bundle.js'],
          output: {
            paths: {
              '/wasm/vision_bundle.js': '/wasm/vision_bundle.js'
            }
          }
        }
      }
    };
});
// import path from 'path';
// import { defineConfig, loadEnv } from 'vite';
// import react from '@vitejs/plugin-react';
// import { VitePWA } from 'vite-plugin-pwa';

// export default defineConfig(({ mode }) => {
//     const env = loadEnv(mode, '.', '');
//     return {
//       server: {
//         port: 3000,
//         host: '0.0.0.0',
//       },
//       plugins: [
//         react(),
//         VitePWA({
//           registerType: 'autoUpdate',
//           includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
//           manifest: {
//             name: 'HOC Kitchen',
//             short_name: 'HOC Kitchen',
//             description: '智能厨房助手 - 隔空手势控制',
//             theme_color: '#ffffff',
//             background_color: '#ffffff',
//             display: 'standalone',
//             orientation: 'portrait',
//             scope: '/',
//             start_url: '/',
//             icons: [
//               {
//                 src: 'pwa-192x192.png',
//                 sizes: '192x192',
//                 type: 'image/png'
//               },
//               {
//                 src: 'pwa-512x512.png',
//                 sizes: '512x512',
//                 type: 'image/png'
//               },
//               {
//                 src: 'pwa-512x512.png',
//                 sizes: '512x512',
//                 type: 'image/png',
//                 purpose: 'any maskable'
//               }
//             ]
//           },
//           workbox: {
//             globPatterns: ['**/*.{js,css,html,ico,png,svg,json}'],
//             runtimeCaching: [
//               {
//                 urlPattern: /^https:\/\/cdn\.jsdelivr\.net\/.*/i,
//                 handler: 'CacheFirst',
//                 options: {
//                   cacheName: 'cdn-cache',
//                   expiration: {
//                     maxEntries: 10,
//                     maxAgeSeconds: 60 * 60 * 24 * 365 // 一年
//                   }
//                 }
//               },
//               {
//                 urlPattern: /^https:\/\/storage\.googleapis\.com\/.*/i,
//                 handler: 'CacheFirst',
//                 options: {
//                   cacheName: 'google-cache',
//                   expiration: {
//                     maxEntries: 10,
//                     maxAgeSeconds: 60 * 60 * 24 * 365
//                   }
//                 }
//               }
//             ]
//           }
//         })
//       ],
//       resolve: {
//         alias: {
//           '@': path.resolve(__dirname, '.'),
//         }
//       },
//       publicDir: 'public',
//       build: {
//         outDir: 'dist',
//         assetsDir: 'assets',
//       }
//     };
// });

// import { defineConfig } from 'vite';
// import react from '@vitejs/plugin-react';

// export default defineConfig({
//   server: {
//     headers: {
//       'Access-Control-Allow-Origin': '*',
//     }
//   },
//   plugins: [react()],
//   publicDir: 'public',
//   // 关键1：设置基础路径为相对路径（适配 App 本地访问）
//   base: './',  // 必须写 ./，否则打包后 JS/CSS 路径错误，导致白屏
//   build: {
//     // 关键2：指定输出目录（默认是 dist，可自定义，后续要导入这个目录）
//     outDir: 'dist',  // 建议保持默认，后续直接导入 dist 文件夹
//     assetsDir: 'assets',
//     // 可选：优化打包体积（按需配置）
//     chunkSizeWarningLimit: 1500,  // 增大 chunk 体积警告阈值
//     rollupOptions: {
//       output: {
//         // 拆分大文件，优化加载
//         manualChunks(id) {
//           if (id.includes('node_modules')) {
//             return id.toString().split('node_modules/')[1].split('/')[0].toString();
//           }
//         }
//       }
//     }
//   }
// });