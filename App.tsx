import React, { useState, useMemo } from 'react';
import { RECIPE_DATA, getUniqueCategories } from './services/data';
import { Recipe, AppView } from './types';
import RecipeDetail from './components/RecipeDetail';
import GestureController from './components/GestureController';

const App: React.FC = () => {
  const [view, setView] = useState<AppView>(AppView.LIST);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("全部");
  const [gestureMode, setGestureMode] = useState(false);
  const [currentZoomScale, setCurrentZoomScale] = useState(1);

  const categories = useMemo(() => getUniqueCategories(), []);

  const filteredRecipes = useMemo(() => {
    if (selectedCategory === "全部") return RECIPE_DATA;
    return RECIPE_DATA.filter(r => r.类别 === selectedCategory);
  }, [selectedCategory]);

  const handleRecipeClick = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setView(AppView.DETAIL);
    setCurrentZoomScale(1); // Reset zoom
  };

  const handleBack = () => {
    setView(AppView.LIST);
    setSelectedRecipe(null);
  };

  // Callback from MediaPipe Gesture Controller
  const handleGestureZoom = (scale: number) => {
    if (view === AppView.DETAIL) {
      setCurrentZoomScale(scale);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900 relative">

      {/* Global Header */}
      <header className="bg-white/80 backdrop-blur-md sticky top-0 z-30 border-b border-gray-200/50 supports-[backdrop-filter]:bg-white/60">
        <div className="max-w-md mx-auto px-4 pt-4 pb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 bg-gradient-to-br from-orange-400 to-orange-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-orange-200 shadow-lg">H</div>
            <h1 className="text-xl font-bold tracking-tight text-gray-900">HOC-Kitchen</h1>
          </div>
          {/* <button
            onClick={() => setGestureMode(!gestureMode)}
            className={`p-2.5 rounded-full transition-all duration-300 ${gestureMode ? 'bg-green-100 text-green-700 shadow-inner' : 'bg-gray-100/50 text-gray-500 hover:bg-gray-100'}`}
            title="Toggle Air Gestures"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
          </button> */}
        </div>

        {/* Categories Bar (Only in List View) */}
        {view === AppView.LIST && (
          <div className="px-4 pb-4 pt-1 overflow-x-auto no-scrollbar flex items-center">
            <div className="flex space-x-2">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-300 ${
                    selectedCategory === cat
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                      : 'bg-gray-100/80 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="max-w-md mx-auto pb-24 pt-4">
        {view === AppView.LIST ? (
          <div className="px-4 grid gap-5">
            {filteredRecipes.map((recipe, index) => (
              <div
                key={index}
                onClick={() => handleRecipeClick(recipe)}
                className="bg-white rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 overflow-hidden active:scale-[0.98] transition-all duration-300 flex hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)]"
              >
                <div className="w-28 h-28 sm:w-32 sm:h-32 bg-gray-100 flex-shrink-0 relative overflow-hidden">
                  <img src={recipe.图片} alt={recipe.基本信息.品名} className="w-full h-full object-cover transition-transform duration-500 hover:scale-110" />
                </div>
                <div className="p-4 flex flex-col justify-between flex-1">
                  <div>
                    <div className="flex justify-between items-start mb-1">
                      <h3 className="font-bold text-gray-900 line-clamp-1 text-lg">{recipe.基本信息.品名}</h3>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-2 leading-relaxed">{recipe.餐厅操作工艺.制作工艺}</p>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-[10px] font-semibold text-orange-700 bg-orange-50 px-2 py-1 rounded-md">
                      {recipe.基本信息.味型}
                    </span>
                    <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded-md">
                      {recipe.基本信息.最佳风味期}
                    </span>
                    <div className="flex-1"></div>
                    <span className="text-[10px] px-2 py-1 bg-gray-100 rounded-full text-gray-500">{recipe.基本信息.加工等级}</span>
                  </div>
                </div>
              </div>
            ))}

            {filteredRecipes.length === 0 && (
              <div className="text-center py-20 text-gray-400 flex flex-col items-center">
                 <div className="text-4xl mb-2">🥗</div>
                 <p>No recipes found in this category.</p>
              </div>
            )}
          </div>
        ) : (
          <RecipeDetail
            recipe={selectedRecipe!}
            onBack={handleBack}
            zoomScale={currentZoomScale}
          />
        )}
      </main>

      {/* Gesture Controller (Overlay) */}
      <GestureController
        isActive={gestureMode}
        onZoomChange={handleGestureZoom}
      />

      {/* Usage Hint */}
      {/* {gestureMode && view === AppView.DETAIL && (
        <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 bg-black/70 text-white text-xs px-4 py-2 rounded-full backdrop-blur pointer-events-none z-50 animate-bounce">
          Spread fingers to Zoom In
        </div>
      )} */}
    </div>
  );
};

export default App;