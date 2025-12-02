export interface RecipeBasicInfo {
  品名: string;
  味型: string;
  最佳风味期: string;
  加工等级: string;
  配料: string[];
}

export interface RecipeProcess {
  烹饪方式: string;
  制作工艺: string;
}

export interface Recipe {
  基本信息: RecipeBasicInfo;
  餐厅操作工艺: RecipeProcess;
  图片: string;
  类别: string;
}

export enum AppView {
  LIST = 'LIST',
  DETAIL = 'DETAIL'
}

export interface HandLandmarkerResult {
  landmarks: { x: number; y: number; z: number }[][];
}

export enum GestureType {
  NONE = 'NONE',
  ZOOM_IN = 'ZOOM_IN',
  ZOOM_OUT = 'ZOOM_OUT',
  SCROLL_UP = 'SCROLL_UP',
  SCROLL_DOWN = 'SCROLL_DOWN',
  SWIPE_LEFT = 'SWIPE_LEFT',
  SWIPE_RIGHT = 'SWIPE_RIGHT',
  BACK = 'BACK',
  NEXT = 'NEXT',
  PREV = 'PREV'
}

export interface GestureCallbacks {
  onZoomChange?: (scale: number) => void;
  onScroll?: (direction: 'up' | 'down', amount: number) => void;
  onSwipe?: (direction: 'left' | 'right') => void;
  onBack?: () => void;
  onNext?: () => void;
  onPrev?: () => void;
}
