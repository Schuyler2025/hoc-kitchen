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
