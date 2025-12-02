import pdfplumber
import json
import re
from collections import defaultdict
import jieba

# ---------------------- 配置参数（重点修改这里！）----------------------
PDF_PATH = "老乡鸡.pdf"  # 你的PDF文件路径
OUTPUT_JSON = "dish_info_category_page_img_exp5.json"  # 输出JSON路径
WATERMARK_CHARS = {"告", "报", "源", "溯", "品", "鸡", "乡", "老", "菜", "验", "证", "合", "格"}  # 水印碎字
COMMON_FIELDS = {
    "基本信息", "品名", "味型", "最佳风味期", "加工等级", "配料",
    "原料来源", "原料加工", "原料配送", "配送方式", "配送周期",
    "餐厅操作工艺", "烹饪方式", "制作工艺", "操作工艺"
}
SINGLE_CHAR_WHITELIST = {"炒", "蒸", "煮", "炸", "烤", "炖", "焖", "烩", "拌", "卤", "腌", "煎", "焗",
                         "咸", "鲜", "甜", "辣", "酸", "麻", "淡", "冷", "热"}  # 单字有效值
START_PAGE = 14  # 起始页码（从1开始）
END_PAGE = 210    # 结束页码（可设为None表示读取到最后一页）

# 核心配置：页码范围→类别映射（按需修改！）
# 格式：[(起始页, 结束页, 类别名称), ...]，范围包含边界，未匹配到的页码默认"其他类"
PAGE_TO_CATEGORY = [
    (14, 138, "正餐菜品", "main"),    # 1-50页 → 
    (139, 150, "炸品", "fried"),  # 51-150页 → 
    (151, 186, "主食", "staple"), # 151-200页 → 
    (187, 207, "早餐", "breakfast"), # 201-250页 → 
    (208, 210, "饮品", "beverage")
]
DEFAULT_CATEGORY = "其他"  # 未匹配到页码范围时的默认类别
# -------------------------------------------------------------------

def get_category_by_page(page_num):
    """根据当前页码获取对应类别（核心函数）"""
    for start, end, category, category_eng in PAGE_TO_CATEGORY:
        if start <= page_num <= end:
            return (category,category_eng)
    return DEFAULT_CATEGORY

def is_valid_word(phrase):
    """判断是否为有效词（支持单字白名单）"""
    if len(phrase) == 1 and phrase in SINGLE_CHAR_WHITELIST:
        return True
    if len(phrase) < 2:
        return False
    words = jieba.lcut(phrase)
    return phrase in words

def split_stuck_content(content):
    """拆分粘连的“水印字+有效内容”"""
    if not content:
        return ""

    words = jieba.lcut(content)
    valid_parts = []
    for word in words:
        if all(c in WATERMARK_CHARS for c in word):
            continue

        cleaned_word = []
        for c in word:
            if c in WATERMARK_CHARS:
                watermark_count = sum(1 for ch in word if ch in WATERMARK_CHARS)
                if watermark_count / len(word) <= 0.5:
                    cleaned_word.append(c)
            else:
                cleaned_word.append(c)

        cleaned_word = "".join(cleaned_word).strip()
        if cleaned_word:
            valid_parts.append(cleaned_word)

    merged = "".join(valid_parts)
    # 改进：保护数字格式，避免在数字和小数点之间插入水印字符
    # 先处理数字前后的水印，但要保护小数点
    merged = re.sub(r"[" + "".join(WATERMARK_CHARS) + r"](\d+\.?\d*)", r"\1", merged)
    merged = re.sub(r"(\d+\.?\d*)[" + "".join(WATERMARK_CHARS) + r"]", r"\1", merged)
    # 清理数字中间的水印字符（但要保护小数点）
    merged = re.sub(r"(\d)[" + "".join(WATERMARK_CHARS) + r"]+(\.\d+)", r"\1\2", merged)
    merged = re.sub(r"(\d+\.)[" + "".join(WATERMARK_CHARS) + r"]+(\d)", r"\1\2", merged)

    field_name = ""
    for field in COMMON_FIELDS:
        if field in merged:
            field_name = field
            break
    if field_name:
        content_after_field = re.sub(r"^.*?" + re.escape(field_name), "", merged)
        if content_after_field and (content_after_field[0].isdigit() or content_after_field[0] == '.'):
            # 改进：支持小数格式（如0.5, 1.等）
            num_unit = re.match(r"(\d+\.?\d*[^\u4e00-\u9fa5]*?)", content_after_field).group(1) if re.match(r"\d+\.?\d*", content_after_field) else ""
            rest_content = re.sub(r"^\d+\.?\d*[^\u4e00-\u9fa5]*?", "", content_after_field)
            merged = f"{field_name}（{num_unit}）{rest_content}"
        else:
            merged = f"{field_name}{content_after_field}"

    return merged.strip()

def fix_brackets(text):
    """修复文本中的括号匹配问题"""
    if not text:
        return text

    # 修复常见的括号错误：右括号被替换成逗号的情况
    # 模式1：左括号 + 数字+单位 + 逗号/分号（如"（3g，"应该是"（3g）"）
    # 注意：需要确保后面不是已经匹配的右括号
    text = re.sub(r"（(\d+[a-zA-Z]+)([，；])(?![^）]*?）)", r"（\1）", text)
    # 模式2：左括号 + 纯数字 + 逗号/分号（如"（1，"应该是"（1）"）
    text = re.sub(r"（(\d+)([，；])(?![^）]*?）)", r"（\1）", text)
    # 模式3：左括号 + 内容 + 逗号 + 空格或结束（可能是右括号位置）
    # 这个模式更宽松，用于处理其他情况
    text = re.sub(r"（([^）]+?)([，；])(\s|$)(?![^）]*?）)", r"（\1）\3", text)

    # 再次检查：如果左括号后直接是数字+单位+逗号，且后面没有右括号，则修复
    # 这个更精确的模式用于处理"（3g，"这种情况
    text = re.sub(r"（(\d+[a-zA-Z]+)([，；])(?=\s|$|[^）])", r"（\1）", text)

    # 统计并修复不匹配的括号
    left_count = text.count('（')
    right_count = text.count('）')
    if left_count > right_count:
        # 从右到左查找未匹配的左括号
        bracket_stack = []
        for i, char in enumerate(text):
            if char == '（':
                bracket_stack.append(i)
            elif char == '）':
                if bracket_stack:
                    bracket_stack.pop()

        # 对于未匹配的左括号，在其后合理位置添加右括号
        for left_idx in reversed(bracket_stack):
            # 在左括号后查找数字+单位或纯数字的模式
            match = re.search(r"（([^）]*?)(\d+[a-zA-Z]*|[a-zA-Z]+\d*)([，；。]?\s*)", text[left_idx:])
            if match:
                insert_pos = left_idx + match.end()
                if insert_pos < len(text) and text[insert_pos] != '）':
                    text = text[:insert_pos] + '）' + text[insert_pos:]
                elif insert_pos >= len(text):
                    text = text + '）'

    return text

def clean_cell_smart(cell, field_context=None):
    """智能清洗单元格（支持单字值、粘连水印处理）"""
    if not cell:
        return ""

    # 保留小数点，支持小数和整数后跟点的情况（如0.5和1.）
    cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】《》！？·\-—\d\.\s]", "", cell)
    cleaned = cleaned.replace("\n", "").strip()
    if len(cleaned) < 1:
        return ""

    # 保护数字格式：确保小数点和数字的合理组合不被破坏
    # 处理多个连续小数点的情况，只保留合理的小数点
    cleaned = re.sub(r"\.{2,}", ".", cleaned)  # 多个连续小数点变为单个
    # 保护数字格式：
    # - 保留小数格式（如0.5, 1.5等）
    # - 保留整数后跟点的情况（如1.）
    # - 删除前面没有数字的小数点
    cleaned = re.sub(r"(?<!\d)\.(?!\d)", "", cleaned)  # 删除前后都没有数字的孤立小数点
    # 但保留数字后跟点的情况（如"1."），即使后面没有数字

    # 对于配料字段，使用更保守的水印过滤策略
    if field_context == "配料":
        # 配料字段：不过度处理，只做基本的字符清理
        # 不调用split_stuck_content，避免破坏词语完整性
        # 只删除明显不是有效字符的内容（已经在前面通过正则表达式处理了）
        pass  # 配料字段保持原样，后续通过字符级别的处理来保护词语
    else:
        cleaned = split_stuck_content(cleaned)

    if len(cleaned) < 1:
        return ""

    if field_context and field_context in ["烹饪方式", "味型"] and len(cleaned) == 1:
        return cleaned

    # 对于配料字段，完全跳过jieba分词和词语过滤，直接进入字符级别处理
    # 这样可以避免jieba分词破坏"娃娃菜"、"老鸡汤"等完整词语
    if field_context == "配料":
        # 配料字段：不进行分词，直接保留所有字符
        valid_words = []  # 不需要valid_words，因为我们会保留所有字符
    else:
        raw_words = jieba.lcut(cleaned)
        valid_words = [word for word in raw_words if not all(c in WATERMARK_CHARS for c in word)]

    cleaned_chars = list(cleaned)
    final_chars = []
    n = len(cleaned_chars)

    for i in range(n):
        char = cleaned_chars[i]
        if char not in WATERMARK_CHARS:
            final_chars.append(char)
            continue

        # 对于配料字段，完全跳过水印字符的删除
        # 因为"鸡"、"老"、"菜"等字符在食材名称中很常见，不应该被删除
        if field_context == "配料":
            # 对于配料字段，保留所有字符，不删除任何水印字符
            final_chars.append(char)
            continue

        # 改进：保护数字周围的字符，避免误删数字相关的内容
        # 如果水印字符在数字附近，要更谨慎处理
        prev_is_digit_or_dot = i > 0 and (cleaned_chars[i-1].isdigit() or cleaned_chars[i-1] == '.')
        next_is_digit_or_dot = i < n-1 and (cleaned_chars[i+1].isdigit() or cleaned_chars[i+1] == '.')

        # 如果水印字符在数字和小数点之间，很可能是误识别，保留它
        if prev_is_digit_or_dot or next_is_digit_or_dot:
            # 检查是否是数字格式的一部分（如"0.5"中的水印）
            # 如果前后都是数字或小数点，可能是数字的一部分，保留
            if (prev_is_digit_or_dot and next_is_digit_or_dot) or \
               (i > 0 and i < n-1 and cleaned_chars[i-1].isdigit() and cleaned_chars[i+1] == '.'):
                final_chars.append(char)
                continue

        phrases_to_check = []
        if i > 0:
            phrases_to_check.append(cleaned_chars[i-1] + char)
        if i < n-1:
            phrases_to_check.append(char + cleaned_chars[i+1])
        if i > 0 and i < n-1:
            phrases_to_check.append(cleaned_chars[i-1] + char + cleaned_chars[i+1])
        if any(is_valid_word(phrase) for phrase in phrases_to_check):
            final_chars.append(char)
            continue

        in_valid_word = False
        for word in valid_words:
            if char in word and len(word) > 1:
                char_idx_in_word = word.find(char)
                if char_idx_in_word >= 0:
                    if char_idx_in_word > 0 and i > 0 and cleaned_chars[i-1] == word[char_idx_in_word-1]:
                        in_valid_word = True
                        break
                    if char_idx_in_word < len(word)-1 and i < n-1 and cleaned_chars[i+1] == word[char_idx_in_word+1]:
                        in_valid_word = True
                        break
        if in_valid_word:
            final_chars.append(char)
            continue

        if len(cleaned) == 1 and char in SINGLE_CHAR_WHITELIST:
            final_chars.append(char)
            continue

        # 改进：保护数字格式，包括小数点
        prev_valid = i > 0 and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】\d\.]", cleaned_chars[i-1])
        next_valid = i < n-1 and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】\d\.]", cleaned_chars[i+1])
        # 对于配料字段，更保守：只要前后有中文字符，就保留
        if field_context == "配料":
            if prev_valid or next_valid:
                final_chars.append(char)
                continue
        elif not prev_valid and not next_valid:
            continue

        final_chars.append(char)

    result = "".join(final_chars).strip()
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"^[,，、;；:：]+|[,，、;；:：]+$", "", result)

    # 修复括号匹配问题
    result = fix_brackets(result)

    # 最终清理：确保数字格式正确，不添加多余的小数点
    # 对于配料字段，跳过这些清理，避免删除有效字符
    if field_context != "配料":
        # 保护有效的小数格式（如0.5, 1.5等）
        # 清理数字中间的多余标点，但保留合理的小数点
        result = re.sub(r"(\d)\.+(\d)", r"\1.\2", result)  # 多个小数点变为单个
        # 清理数字中间的水印字符（如果误插入）
        result = re.sub(r"(\d)[" + "".join(WATERMARK_CHARS) + r"]+(\d)", r"\1\2", result)
        result = re.sub(r"(\d)[" + "".join(WATERMARK_CHARS) + r"]+(\.\d)", r"\1\2", result)
        result = re.sub(r"(\d\.)[" + "".join(WATERMARK_CHARS) + r"]+(\d)", r"\1\2", result)
        # 保留"1."这种格式（整数后跟点），不删除

    if len(result) > 0:
        if len(result) == 1 and result in SINGLE_CHAR_WHITELIST:
            return result
        # 对于配料字段，跳过valid_content_ratio检查，因为我们已经保留了所有字符
        if field_context == "配料":
            return result
        # 对于烹饪方式字段，清理开头和结尾的水印字符
        if field_context == "烹饪方式":
            result = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", result)
            result = re.sub(r"[" + "".join(WATERMARK_CHARS) + r"]+$", "", result)
            result = result.strip()
        valid_content_ratio = len("".join(valid_words)) / len(result) if len(result) > 0 else 0
        if valid_content_ratio < 0.3 and not any(field in result for field in COMMON_FIELDS):
            return ""

    return result

def parse_table(cleaned_table):
    """解析表格，只提取“基本信息”和“餐厅操作工艺”核心内容"""
    basic_info = defaultdict(str)  # 基本信息（品名、味型等）
    kitchen_process = defaultdict(str)  # 餐厅操作工艺（烹饪方式、制作工艺）
    current_dish = ""

    for row in cleaned_table:
        if not any(row):
            continue
        non_empty_cells = [cell for cell in row if cell]
        if not non_empty_cells:
            continue

        # 1. 提取品名（基本信息核心）
        if "基本信息" in non_empty_cells[0]:
            for cell in non_empty_cells[1:]:
                if cell and not any(field in cell for field in COMMON_FIELDS):
                    current_dish = cell
                    basic_info["品名"] = current_dish
                    break

        # 2. 提取基本信息子字段（味型、最佳风味期等）
        for idx, cell in enumerate(non_empty_cells):
            if cell in ["味型", "最佳风味期", "加工等级"]:
                if idx + 1 < len(non_empty_cells):
                    basic_info[cell] = clean_cell_smart(non_empty_cells[idx + 1], field_context=cell)
            elif cell == "烹饪方式":
                # 改进：单独提取烹饪方式字段
                if idx + 1 < len(non_empty_cells):
                    cooking_method = clean_cell_smart(non_empty_cells[idx + 1], field_context="烹饪方式")
                    if cooking_method:
                        # 清理开头的水印字符（如"品现调"应该变成"现调"）
                        cooking_method = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", cooking_method)
                        if cooking_method:
                            kitchen_process["烹饪方式"] = cooking_method
                # 如果右侧单元格为空，尝试从当前单元格提取（格式：烹饪方式：xxx）
                elif "烹饪方式" in cell:
                    cooking_match = re.search(r"烹饪方式[:：]\s*(\S+)", cell)
                    if cooking_match:
                        cooking_value = clean_cell_smart(cooking_match.group(1), field_context="烹饪方式")
                        # 清理开头的水印字符
                        cooking_value = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", cooking_value)
                        if cooking_value:
                            kitchen_process["烹饪方式"] = cooking_value
            elif cell == "配料":
                if idx + 1 < len(non_empty_cells):
                    # 改进配料拆分逻辑，处理括号匹配
                    # 注意：这里直接使用原始单元格内容，不再调用clean_cell_smart
                    # 因为clean_cell_smart可能在提取阶段就已经删除了字符
                    ingredients_str = str(non_empty_cells[idx + 1]) if non_empty_cells[idx + 1] else ""

                    # 对于配料字段，使用最保守的策略：只做最基本的字符清理
                    # 只删除明显不是中文、数字、标点的字符，不删除任何可能是有效字符的内容
                    ingredients_str = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】《》！？·\s]", "", ingredients_str)
                    ingredients_str = ingredients_str.replace("\n", "").strip()

                    # 修复括号匹配问题
                    ingredients_str = fix_brackets(ingredients_str)

                    # 注意：对于配料字段，不进行任何水印字符的删除
                    # 因为"鸡"、"老"、"菜"等字符在食材名称中很常见，不应该被删除

                    ingredients = []
                    start = 0
                    bracket_count = 0  # 括号计数器，用于处理成对括号

                    for i, c in enumerate(ingredients_str):
                        if c == '（':
                            bracket_count += 1
                        elif c == '）':
                            bracket_count -= 1
                            if bracket_count < 0:  # 处理不匹配的右括号
                                bracket_count = 0
                        # 只在括号平衡且遇到分隔符时拆分
                        elif bracket_count == 0 and c in ['、', '，']:
                            ingredient = ingredients_str[start:i].strip()
                            if ingredient:
                                # 对于配料字段，只做最基本的清理，不删除任何字符
                                # 只去除首尾空白和特殊控制字符
                                cleaned_ingredient = ingredient.strip()
                                # 只删除明显的无效字符（非中文、非数字、非标点）
                                cleaned_ingredient = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】《》！？·\s]", "", cleaned_ingredient)
                                if cleaned_ingredient:
                                    ingredients.append(cleaned_ingredient)
                            start = i + 1

                    # 添加最后一个配料
                    last_ingredient = ingredients_str[start:].strip()
                    if last_ingredient:
                        # 对于配料字段，只做最基本的清理，不删除任何字符
                        cleaned_last = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】《》！？·\s]", "", last_ingredient)
                        if cleaned_last:
                            ingredients.append(cleaned_last)

                    basic_info[cell] = ingredients

        # 3. 提取餐厅操作工艺（兼容跨页步骤合并）
        if "餐厅操作工艺" in non_empty_cells[0] or any("制作工艺" in cell for cell in non_empty_cells):
            process_content = []
            for cell in non_empty_cells:
                if cell and (any(field in cell for field in ["制作工艺", "烹饪方式"]) or re.match(r"\d+", cell.strip())):
                    cleaned_cell = clean_cell_smart(cell, field_context="制作工艺")
                    if cleaned_cell:
                        process_content.append(cleaned_cell)
                elif cell and len(cell) > 10:  # 长文本视为工艺步骤
                    cleaned_cell = clean_cell_smart(cell, field_context="制作工艺")
                    if cleaned_cell:
                        process_content.append(cleaned_cell)

            # 解析烹饪方式（改进：更全面的提取逻辑）
            if not kitchen_process["烹饪方式"]:
                # 方法1：从process_content中查找"烹饪方式"字段
                for content in process_content:
                    if "烹饪方式" in content:
                        # 尝试多种格式：烹饪方式：xxx 或 烹饪方式xxx
                        cooking_match = re.search(r"烹饪方式[:：]?\s*([^\s，。；：]+)", content)
                        if cooking_match:
                            cooking_value = clean_cell_smart(cooking_match.group(1), field_context="烹饪方式")
                            # 清理开头的水印字符
                            cooking_value = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", cooking_value)
                            if cooking_value:
                                kitchen_process["烹饪方式"] = cooking_value
                                break
                # 方法2：从所有单元格中查找"烹饪方式"（如果还没找到）
                if not kitchen_process["烹饪方式"]:
                    for row in cleaned_table:
                        non_empty_row_cells = [c for c in row if c]
                        for idx, cell in enumerate(non_empty_row_cells):
                            if "烹饪方式" in str(cell):
                                # 尝试从当前单元格提取
                                cooking_match = re.search(r"烹饪方式[:：]?\s*([^\s，。；：]+)", str(cell))
                                if cooking_match:
                                    cooking_value = clean_cell_smart(cooking_match.group(1), field_context="烹饪方式")
                                    # 清理开头的水印字符
                                    cooking_value = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", cooking_value)
                                    if cooking_value:
                                        kitchen_process["烹饪方式"] = cooking_value
                                        break
                                # 或者从下一个单元格提取
                                elif idx + 1 < len(non_empty_row_cells):
                                    cooking_value = clean_cell_smart(non_empty_row_cells[idx + 1], field_context="烹饪方式")
                                    # 清理开头的水印字符
                                    cooking_value = re.sub(r"^[" + "".join(WATERMARK_CHARS) + r"]+", "", cooking_value)
                                    if cooking_value and cooking_value not in COMMON_FIELDS:
                                        kitchen_process["烹饪方式"] = cooking_value
                                        break
                            if kitchen_process["烹饪方式"]:
                                break
                        if kitchen_process["烹饪方式"]:
                            break
                # 方法3：兜底：从步骤中匹配单字烹饪方式
                if not kitchen_process["烹饪方式"]:
                    for word in jieba.lcut(" ".join(process_content)):
                        if word in SINGLE_CHAR_WHITELIST:
                            kitchen_process["烹饪方式"] = word
                            break

            # 解析制作工艺（合并跨页步骤）
            process_steps = ""
            for content in process_content:
                if "制作工艺" in content:
                    steps = re.sub(r"制作工艺.*?[:：]?", "", content).strip()
                    process_steps += steps + " "
                elif "烹饪方式" not in content:  # 排除烹饪方式内容，避免重复
                    process_steps += content + " "
            if process_steps:
                # 修复制作工艺中的括号匹配问题
                process_steps = fix_brackets(process_steps.strip())
                kitchen_process["制作工艺"] = kitchen_process["制作工艺"] + process_steps

    # 确保字段结构完整（避免缺失）
    return {
        "基本信息": dict(basic_info) or {},
        "餐厅操作工艺": dict(kitchen_process) or {}
    }

# ---------------------- 跨页表格合并（记录表格对应的页码）----------------------
def merge_cross_page_tables_with_page_num(pdf, start_page, end_page):
    """合并跨页表格，并记录每个表格的“起始页码”（用于确定类别和图片路径）"""
    merged_tables = []  # 元素格式：(合并后的表格, 表格起始页码)
    current_table = []
    current_table_start_page = None  # 当前表格的起始页码
    total_pages = len(pdf.pages)
    start_idx = start_page - 1
    end_idx = end_page - 1 if end_page and end_page <= total_pages else total_pages - 1

    for page_idx in range(start_idx, end_idx + 1):
        current_page_num = page_idx + 1  # 实际页码（从1开始）
        page = pdf.pages[page_idx]
        table = page.extract_table()

        if not table:
            # 保存当前未完成的表格
            if current_table:
                merged_tables.append((current_table, current_table_start_page))
                current_table = []
                current_table_start_page = None
            continue

        # 清洗当前页表格行
        # 注意：对于配料字段，需要保留所有字符，所以在提取阶段使用更保守的策略
        cleaned_rows = []
        for row in table:
            # 先检查这一行是否包含"配料"字段
            row_str = " ".join(str(cell) if cell else "" for cell in row)
            has_ingredient_field = "配料" in row_str

            cleaned_row = []
            for cell in row:
                if cell:
                    cell_str = str(cell) if cell else ""
                    # 检查是否是配料相关的单元格
                    is_ingredient_cell = False

                    # 方法1：检查是否包含"配料"字段名
                    if "配料" in cell_str:
                        is_ingredient_cell = True
                    # 方法2：如果这一行包含"配料"字段，检查当前单元格是否是配料内容
                    elif has_ingredient_field:
                        # 配料内容通常在"配料"字段的右侧
                        if "配料" not in cell_str:
                            # 不是"配料"字段本身，可能是配料内容
                            # 如果包含分隔符或括号，很可能是配料内容
                            if any(c in cell_str for c in ['、', '，', '（', '）']) or len(cell_str) > 3:
                                is_ingredient_cell = True

                    # 方法3：检查是否包含常见食材字符（如"菜"、"鸡"、"汤"等）
                    # 这些字符在水印列表中，但在食材名称中很常见
                    common_ingredient_chars = {"菜", "鸡", "汤", "油", "肉", "盐"}
                    if not is_ingredient_cell and any(char in cell_str for char in common_ingredient_chars):
                        # 如果单元格包含常见食材字符，且不是字段名，很可能是食材相关内容
                        if not any(field in cell_str for field in COMMON_FIELDS):
                            is_ingredient_cell = True

                    # 方法4：检查是否是品名（通常在"基本信息"行的右侧）
                    if "基本信息" in row_str and not is_ingredient_cell:
                        # 如果这一行包含"基本信息"，且当前单元格不是字段名，可能是品名
                        if "基本信息" not in cell_str and not any(field in cell_str for field in COMMON_FIELDS):
                            is_ingredient_cell = True

                    if is_ingredient_cell:
                        # 对于配料/品名单元格，使用配料上下文，保护所有字符
                        cleaned_cell = clean_cell_smart(cell, field_context="配料")
                    else:
                        # 对于其他单元格，正常处理
                        cleaned_cell = clean_cell_smart(cell)
                    cleaned_row.append(cleaned_cell)
                else:
                    cleaned_row.append("")
            if any(cleaned_row):
                cleaned_rows.append(cleaned_row)

        # 改进跨页判断：更准确地检测表格延续
        # 判断是否为跨页延续：
        # 1. 当前表格不为空
        # 2. 新页首行不包含核心字段（基本信息、餐厅操作工艺等）
        # 3. 新页首行与上一页最后一行在结构上连续（列数相同或相似）
        is_continue = False
        if len(current_table) > 0 and len(cleaned_rows) > 0:
            first_row_str = "".join(str(cell) for cell in cleaned_rows[0])
            has_core_field = any(field in first_row_str for field in COMMON_FIELDS)

            # 如果首行没有核心字段，且列数匹配，则视为延续
            if not has_core_field:
                last_row_cols = len([c for c in current_table[-1] if c])
                first_row_cols = len([c for c in cleaned_rows[0] if c])
                # 列数相同或相差不超过1，视为延续
                if abs(last_row_cols - first_row_cols) <= 1:
                    is_continue = True

        if is_continue:
            # 延续上一表格，不修改起始页码
            current_table.extend(cleaned_rows)
        else:
            # 保存上一表格，开始新表格（记录新表格的起始页码）
            if current_table:
                merged_tables.append((current_table, current_table_start_page))
            current_table = cleaned_rows
            current_table_start_page = current_page_num  # 新表格的起始页码为当前页

    # 保存最后一个表格
    if current_table and current_table_start_page:
        merged_tables.append((current_table, current_table_start_page))

    return merged_tables

# ---------------------- 主逻辑（按页码分类别+格式化图片路径）----------------------
def extract_dish_info_final(pdf_path, start_page, end_page=None):
    all_dishes = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # 页码合法性校验
        if start_page < 1:
            start_page = 1
            print(f"起始页码不合法，自动调整为1")
        if end_page is None or end_page > total_pages:
            end_page = total_pages
            print(f"结束页码不合法，自动调整为总页数{total_pages}")
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        print(f"正在提取页码范围：{start_page} - {end_page}")

        # 合并跨页表格（带起始页码）
        merged_tables = merge_cross_page_tables_with_page_num(pdf, start_page, end_page)
        print(f"合并后表格数量：{len(merged_tables)}")

        # 解析每个表格并组装指定字段
        for table_idx, (table, table_start_page) in enumerate(merged_tables):
            parsed_data = parse_table(table)
            dish_name = parsed_data["基本信息"].get("品名", f"未命名菜品_{table_idx+1}")

            # 1. 根据表格起始页码获取类别
            dish_category,dish_category_eng = get_category_by_page(table_start_page)

            # 2. 格式化图片路径：类别_page_页码_img.png
            # img_path = f"{dish_category}_page_{table_start_page}_img.png"
            # （可选）如果需要图片路径带目录，比如 output/images/xxx.png，可改为：
            img_path = f"./images/{dish_category_eng}_page_{table_start_page}_img.png"

            # 3. 组装最终输出字段（严格保留4个指定字段）
            final_dish = {
                "基本信息": parsed_data["基本信息"],
                "餐厅操作工艺": parsed_data["餐厅操作工艺"],
                "图片": img_path,
                "类别": dish_category
            }

            # 过滤无品名的无效数据
            if parsed_data["基本信息"].get("品名"):
                all_dishes.append(final_dish)
                print(f"表格{table_idx+1}：{dish_name} → 类别：{dish_category} → 图片：{img_path}")
            else:
                print(f"表格{table_idx+1}未识别到品名，跳过")

    return all_dishes

# ---------------------- 执行提取 ----------------------
if __name__ == "__main__":
    # 安装依赖提示（首次运行需执行）
    # print("请确保已安装依赖：pip install pdfplumber jieba")

    dishes = extract_dish_info_final(PDF_PATH, START_PAGE, END_PAGE)

    # 写入JSON文件（严格保留指定4个字段）
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dishes, f, ensure_ascii=False, indent=2)

    # 输出结果统计
    print(f"\n提取完成！共成功提取{len(dishes)}道菜品信息")
    print(f"输出文件路径：{OUTPUT_JSON}")

    # 预览第一条数据（验证字段结构）
    if dishes:
        print("\n字段结构预览（仅展示第一条）：")
        print(json.dumps(dishes[0], ensure_ascii=False, indent=2))