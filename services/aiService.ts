/*
 * @Author: Schuyler schuylerhu@gmail.com
 * @Date: 2025-11-29 22:01:03
 * @LastEditors: Schuyler schuylerhu@gmail.com
 * @LastEditTime: 2025-11-30 14:07:42
 * @FilePath: \hoc-kitchen\services\aiService.ts
 * @Description:
 *
 * Copyright (c) 2025 by Schuyler, All Rights Reserved.
 */
import { Recipe } from "../types";



export const askChefAboutRecipe = async (recipe: Recipe, question: string): Promise<string> => {
  try {
    const prompt = `
    You are a professional Michelin-star chef assistant in a mobile app.

    Current Recipe Context:
    Name: ${recipe.基本信息.品名}
    Flavor: ${recipe.基本信息.味型}
    Ingredients: ${recipe.基本信息.配料.join(', ')}
    Method: ${recipe.餐厅操作工艺.制作工艺}

    User Question: "${question}"

    Answer briefly, helpfully, and encouragingly. Keep it under 50 words if possible.
    `;
    // // 调用 DeepInfra API（使用 Qwen2 中文模型）
    // const response = await fetch('https://api.deepinfra.com/v1/openai/chat/completions', {
    //   method: 'POST',
    //   headers: {
    //     'Authorization': `Bearer ${process.env.DEEPINFRA_API_KEY}`, // 从环境变量读取
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify({
    //     model: "Qwen/Qwen2-7B-Instruct", // 中文优化模型
    //     messages: [{ role: "user", content: prompt }],
    //     max_tokens: 80,      // 控制回答长度
    //     temperature: 0.6,    // 创造性（0.5~0.8 合适）
    //     top_p: 0.9,
    //     stream: false
    //   })
    // });

    // if (!response.ok) {
    //   const errorText = await response.text();
    //   throw new Error(`DeepInfra API error: ${response.status} - ${errorText}`);
    // }



    // const data = await response.json();
    // return data[0].generated_text.replace(prompt.trim(), '').trim() || "Let's make this dish amazing! Ask me anything~";




  } catch (error) {
    console.error("API Error:", error);
    return "The chef is currently busy with other orders. Please try again.";
  }
};
