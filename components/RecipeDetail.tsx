import React, { useState, useEffect } from 'react';
import { Recipe } from '../types';
import { askChefAboutRecipe } from '../services/aiService';

interface RecipeDetailProps {
  recipe: Recipe;
  onBack: () => void;
  zoomScale: number;
}

const RecipeDetail: React.FC<RecipeDetailProps> = ({ recipe, onBack, zoomScale }) => {
  const [aiResponse, setAiResponse] = useState<string>('');
  const [isAsking, setIsAsking] = useState(false);

  // Smooth out the raw zoom input for better visual experience
  const [smoothScale, setSmoothScale] = useState(1);

  useEffect(() => {
    // Simple lerp for smoothing
    const timer = requestAnimationFrame(() => {
      setSmoothScale(prev => prev + (zoomScale - prev) * 0.1);
    });
    return () => cancelAnimationFrame(timer);
  }, [zoomScale]);

  const handleAskAI = async () => {
    setIsAsking(true);
    const answer = await askChefAboutRecipe(recipe, "What is a good tip for making this perfectly?");
    setAiResponse(answer);
    setIsAsking(false);
  };

  return (
    <div className="fixed inset-0 bg-white z-40 overflow-y-auto pb-20">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 flex items-center justify-between p-4 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <button
          onClick={onBack}
          className="p-2 rounded-full hover:bg-gray-100 text-gray-700 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
        </button>
        <h1 className="text-lg font-bold text-gray-900 truncate max-w-[200px]">{recipe.基本信息.品名}</h1>
        <div className="w-10"></div>
      </div>

      <div className="p-4 space-y-6">
        {/* Scalable Image Area */}
        <div className="relative w-full aspect-square rounded-2xl overflow-hidden bg-gray-100 shadow-inner group">
          <div
            className="w-full h-full transition-transform duration-75 origin-center will-change-transform"
            style={{ transform: `scale(${smoothScale})` }}
          >
            <img
              src={recipe.图片}
              alt={recipe.基本信息.品名}
              className="w-full h-full object-cover"
            />
          </div>
          {/* Zoom Indicator
          <div className="absolute bottom-4 right-4 bg-black/60 text-white px-3 py-1 rounded-full text-xs backdrop-blur-sm pointer-events-none">
             Air Zoom: {smoothScale.toFixed(1)}x
          </div> */}
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-orange-50 p-4 rounded-xl">
            <p className="text-xs text-orange-500 font-semibold mb-1">口味</p>
            <p className="font-medium text-gray-800">{recipe.基本信息.味型}</p>
          </div>
          <div className="bg-blue-50 p-4 rounded-xl">
            <p className="text-xs text-blue-500 font-semibold mb-1">最佳风味期</p>
            <p className="font-medium text-gray-800">{recipe.基本信息.最佳风味期}</p>
          </div>
        </div>

        {/* Ingredients */}
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-3">配料</h2>
          <div className="flex flex-wrap gap-2">
            {recipe.基本信息.配料.map((item, idx) => (
              <span key={idx} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-700">
                {item}
              </span>
            ))}
          </div>
        </div>

        {/* Method */}
        <div className="bg-gray-50 p-5 rounded-2xl border border-gray-100">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center font-bold text-sm">
              {recipe.餐厅操作工艺.烹饪方式[0]? recipe.餐厅操作工艺.烹饪方式[0] : '🍽️'}
            </span>
            <h2 className="text-xl font-bold text-gray-900">制作工艺</h2>
          </div>
          <p className="text-gray-600 leading-relaxed">
            {recipe.餐厅操作工艺.制作工艺}
          </p>
        </div>

        {/* AI Chef Assistant */}
        <div className="pt-4 border-t border-gray-100">
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 p-5 rounded-2xl border border-indigo-100">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-indigo-900 flex items-center gap-2">
                        <span className="text-xl">✨</span> AI Chef Tips
                    </h3>
                    <button
                        onClick={handleAskAI}
                        disabled={isAsking}
                        className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg font-medium shadow-md hover:bg-indigo-700 active:scale-95 transition-all disabled:opacity-50"
                    >
                        {isAsking ? 'Thinking...' : 'Get Pro Tip'}
                    </button>
                </div>

                {aiResponse && (
                    <div className="bg-white/80 p-3 rounded-lg text-indigo-800 text-sm leading-relaxed animate-fade-in">
                        "{aiResponse}"
                    </div>
                )}
                {!aiResponse && (
                    <p className="text-xs text-indigo-400">
                        Tap "Get Pro Tip" to ask for cooking secrets.
                    </p>
                )}
            </div>
        </div>
      </div>
    </div>
  );
};

export default RecipeDetail;
