/*
 * @Author: Schuyler schuylerhu@gmail.com
 * @Date: 2025-11-29 22:01:03
 * @LastEditors: Schuyler schuylerhu@gmail.com
 * @LastEditTime: 2025-11-30 11:04:23
 * @FilePath: \hoc-kitchen\services\data.ts
 * @Description: 包含所有食谱数据的数组
 *
 * Copyright (c) 2025 by Schuyler, All Rights Reserved.
 */
import { Recipe } from '../types';
import recipeData from '../dish_info_category_page_img.json'

// 修正图片路径，将相对路径转换为正确的URL路径
export const RECIPE_DATA: Recipe[] = recipeData.map((item) => ({
  ...item,
  图片: item.图片.replace('/images/', './images/'),
})) as Recipe[];


export const getUniqueCategories = (): string[] => {
  const categories = new Set(RECIPE_DATA.map(r => r.类别));
  return ["全部", ...Array.from(categories)];
};
