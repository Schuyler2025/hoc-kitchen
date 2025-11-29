import { GoogleGenAI } from "@google/genai";
import { Recipe } from "../types";

const apiKey = process.env.API_KEY || '';
const ai = new GoogleGenAI({ apiKey });

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

    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });

    return response.text || "Sorry, I couldn't think of an answer right now.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "The chef is currently busy (API Error). Please try again.";
  }
};
