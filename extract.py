import pdfplumber
import json
import re
from collections import defaultdict
import jieba

# ---------------------- 配置参数（重点修改这里！）----------------------
PDF_PATH = "老乡鸡.pdf"  # 你的PDF文件路径
OUTPUT_JSON = "dish_info_category_page_img_35.json"  # 输出JSON路径
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
    (14, 138, "正餐菜品"),    # 1-50页 → 主食类
    (139, 150, "炸品"),  # 51-150页 → 热菜类
    (151, 186, "主食"), # 151-200页 → 凉菜类
    (187, 207, "早餐"), # 201-250页 → 汤羹类
    (208, 210, "饮品")
]
DEFAULT_CATEGORY = "其他"  # 未匹配到页码范围时的默认类别
# -------------------------------------------------------------------

def get_category_by_page(page_num):
    """根据当前页码获取对应类别（核心函数）"""
    for start, end, category in PAGE_TO_CATEGORY:
        if start <= page_num <= end:
            return category
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
    merged = re.sub(r"[" + "".join(WATERMARK_CHARS) + r"](\d+)", r"\1", merged)
    merged = re.sub(r"(\d+)[" + "".join(WATERMARK_CHARS) + r"]", r"\1", merged)

    field_name = ""
    for field in COMMON_FIELDS:
        if field in merged:
            field_name = field
            break
    if field_name:
        content_after_field = re.sub(r"^.*?" + re.escape(field_name), "", merged)
        if content_after_field and content_after_field[0].isdigit():
            num_unit = re.match(r"(\d+[^\u4e00-\u9fa5]*?)", content_after_field).group(1) if re.match(r"\d+", content_after_field) else ""
            rest_content = re.sub(r"^\d+[^\u4e00-\u9fa5]*?", "", content_after_field)
            merged = f"{field_name}（{num_unit}）{rest_content}"
        else:
            merged = f"{field_name}{content_after_field}"

    return merged.strip()

def clean_cell_smart(cell, field_context=None):
    """智能清洗单元格（支持单字值、粘连水印处理）"""
    if not cell:
        return ""

    cleaned = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】《》！？·\-—\d\s]", "", cell)
    cleaned = cleaned.replace("\n", "").strip()
    if len(cleaned) < 1:
        return ""

    cleaned = split_stuck_content(cleaned)
    if len(cleaned) < 1:
        return ""

    if field_context and field_context in ["烹饪方式", "味型"] and len(cleaned) == 1:
        return cleaned

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

        prev_valid = i > 0 and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】\d]", cleaned_chars[i-1])
        next_valid = i < n-1 and re.match(r"[\u4e00-\u9fa5a-zA-Z0-9，。、；：（）【】\d]", cleaned_chars[i+1])
        if not prev_valid and not next_valid:
            continue

        final_chars.append(char)

    result = "".join(final_chars).strip()
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"^[,，、;；:：]+|[,，、;；:：]+$", "", result)

    if len(result) > 0:
        if len(result) == 1 and result in SINGLE_CHAR_WHITELIST:
            return result
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
            elif cell == "配料":
                if idx + 1 < len(non_empty_cells):
                    # 改进配料拆分逻辑，处理括号匹配
                    ingredients_str = non_empty_cells[idx + 1]
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
                                ingredients.append(clean_cell_smart(ingredient))
                            start = i + 1

                    # 添加最后一个配料
                    last_ingredient = ingredients_str[start:].strip()
                    if last_ingredient:
                        ingredients.append(clean_cell_smart(last_ingredient))

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

            # 解析烹饪方式
            if not kitchen_process["烹饪方式"]:
                for content in process_content:
                    if "烹饪方式" in content:
                        cooking_match = re.search(r"烹饪方式[:：](\S+)", content)
                        if cooking_match:
                            kitchen_process["烹饪方式"] = cooking_match.group(1)
                            break
                # 兜底：从步骤中匹配单字烹饪方式
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
                else:
                    process_steps += content + " "
            if process_steps:
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
        cleaned_rows = []
        for row in table:
            cleaned_row = [clean_cell_smart(cell) for cell in row]
            if any(cleaned_row):
                cleaned_rows.append(cleaned_row)

        # 判断是否为跨页延续（首行无核心字段则视为延续）
        is_continue = len(current_table) > 0 and not any(field in str(cleaned_rows[0]) for field in COMMON_FIELDS)

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
            dish_category = get_category_by_page(table_start_page)

            # 2. 格式化图片路径：类别_page_页码_img.png
            # img_path = f"{dish_category}_page_{table_start_page}_img.png"
            # （可选）如果需要图片路径带目录，比如 output/images/xxx.png，可改为：
            img_path = f"/images/{dish_category}_page_{table_start_page}_img.png"

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