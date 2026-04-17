import re
import os
import glob


def clean_text(content, chapter_matches=None, mode='full'):
    """精确清洗文本，支持可选规则执行。（保持原有逻辑）"""
    if not content:
        return ""

    # Step 1: 获取章节标题位置（如果未传入则扫描一次）
    if not chapter_matches or len(chapter_matches) == 0:
        # 使用正则匹配章节标题，减少误判
        chapter_pattern = re.compile(
            r'(?:\n\s*)?' 
            r'([第][一二三四五六七八九十百千万零\d]+[章节回节卷]|' 
            r'\d+[章节回节卷])', 
            re.IGNORECASE | re.UNICODE
        )
        matches = list(chapter_pattern.finditer(content))
        if not matches:
            return content.strip()
    else:
        matches = chapter_matches

    parts = []
    
    for i, match in enumerate(matches):
        start_idx = match.start()
        
        # 获取当前章节正文范围 (不含标题) -> 注意：这里是包含标题的完整内容切片
        prev_end = 0 if i == 0 else matches[i-1].end()
        next_chapter_start = matches[i+1].start() if i + 1 < len(matches) else len(content)
        
        full_chapter_content = content[start_idx:next_chapter_start] # 包含标题
        
        # 规则基础：确认是否存在"作者有话"部分
        author_pattern = re.compile(r'(?:\n\s*|\A)[（(【/]?作者有话', re.IGNORECASE)
        
        auth_match = author_pattern.search(full_chapter_content)
        
        if not auth_match:
            # 若未找到"作者有话"，跳过清洗规则（保持原样）
            parts.append(full_chapter_content)
            continue

        auth_start_idx = auth_match.start()
        
        # 根据 mode 执行不同逻辑
        
        if mode == 'none':
            # none模式：不执行清洗
            parts.append(full_chapter_content)
            continue
            
        elif mode == 'clean':
            # clean模式：直接删除从"作者有话"起至本章末（保留标题和正文）
            parts.append(full_chapter_content[:auth_start_idx])
            continue

        else:
            # mode == 'part': 细化规则逻辑，智能删除
            
            trigger_words = ['感谢', '预收']
            
            # 获取"作者有话"行结束位置（含该行换行符）
            auth_line_end = full_chapter_content.find('\n', auth_start_idx)
            if auth_line_end == -1:
                auth_line_end = len(full_chapter_content) + 1 # 无换行，视为最后一行结束
            
            # 检查下一行是否包含触发词 (Req part logic: immediate next line)
            remaining_after_auth = full_chapter_content[auth_line_end:]
            
            if remaining_after_auth:
                # 查找下一行的第一个字符位置（相对于 full_chapter_content）
                next_line_start = auth_line_end
                next_line_content = remaining_after_auth.split('\n')[0] + ('\n' if len(remaining_after_auth) > auth_line_end else '')
                
                # 检查下一行（auth后的第一行）是否有触发词
                found_trigger_in_next_line = False
                for word in trigger_words:
                    if re.search(re.escape(word), next_line_content, re.IGNORECASE):
                        found_trigger_in_next_line = True
                        break
                
                # 如果下一行是触发词 -> 执行 clean 逻辑 (删除从"作者有话"起)
                if found_trigger_in_next_line:
                    parts.append(full_chapter_content[:auth_start_idx])
                    continue
                
            # 3. 否则 -> 保留作者内容（包括 header），查找后续是否有触发词
            remaining_text = full_chapter_content[auth_start_idx:] # From the start of Author Notes
            
            found_trigger_later = False
            last_safe_pos = auth_start_idx
            
            for word in trigger_words:
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                match_after_auth = pattern.search(remaining_text)
                
                if match_after_auth:
                    offset = auth_start_idx + match_after_auth.start() # Absolute index relative to full_chapter_content
                    
                    # 查找触发词所在行的结束位置（包含换行符）
                    line_end_char = remaining_text.find('\n', offset)
                    
                    if line_end_char == -1:
                        end_pos = len(full_chapter_content)
                    else:
                        end_pos = auth_start_idx + (offset + (line_end_char - offset) + 1) # +1 for \n
                    
                    new_content = full_chapter_content[:auth_start_idx] + remaining_text[offset:]
                    parts.append(new_content)
                    found_trigger_later = True
                    break
            
            if not found_trigger_later:
                # 未找到触发词，保留全文（包括作者内容）
                parts.append(full_chapter_content)

    # 【关键修复】返回拼接后的文本
    return '\n'.join(parts)


def remove_special_chars(content):
    """
    清洗文本：仅保留中文、英文、数字以及指定的标点符号和换行符。
    
    参数:
        content (str): 需要清洗的原始文本
    
    返回:
        str: 清洗后的文本
    """
    # 定义允许的字符集合（基于你提供的示例）
    punctuation_set = {
        '，', '。', '！', '？', '；', '：', '_',
        '"', '"', '“', '”', "（", "）","《", "》", "[", "]", "{", "}", '-', '—', '…', 
        ',', '.', '?', '!', ';', ':', "'", "'", 
        '(' , ')', '\n'  # 注意：这里包含了换行符
    }
    
    # 构建正则表达式模式
    # \u4e00-\u9fff: 匹配所有常用汉字 (CJK Unified Ideographs)
    # a-zA-Z: 匹配英文字母
    # 0-9: 匹配数字
    # [] 内部列出所有允许的标点符号
    
    pattern = r'[\u4e00-\u9fffa-zA-Z0-9' + ''.join(re.escape(p) for p in punctuation_set) + ']'
    
    # 使用 re.findall 提取所有匹配的字符，然后重新拼接
    cleaned_chars = re.findall(pattern, content)
    
    return ''.join(cleaned_chars)

def split_into_lines(content, max_length=42):
    """
    智能断行函数 v2.0 (基于语义单元)
    
    策略：
    1. 定义“非断行字符”为：汉字、英文字母、数字。
    2. 定义“断行候选符”为：除换行符外的所有其他符号（标点、空格等）。
    3. 遇到长度超限，优先在最近的“断行候选符”后断开。
    4. 若整行无非断行字符（纯标点/空白），则丢弃该行。
    
    :param content: 输入文本字符串
    :param max_length: 每行最大长度 (默认 42)
    :return: 处理后的列表
    """
    if not content:
        return []

    lines = []
    current_line = ""

    # 预定义非断行字符集合 (用于快速判断)
    # 包含：中文、英文大小写、数字
    non_break_chars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # 辅助函数：判断是否为“非断行字符”
    def is_text_char(char):
        return char in non_break_chars or (char.isalpha() and not char.isascii()) or (char.isdigit() and not char.isascii())

    for char in content:
        if char == '\n':
            # 处理换行符：保存当前行（如果是有效内容），然后重置
            if current_line.strip():
                stripped = current_line.strip()
                
                # 【需求 1】检查是否为“纯标点/空白行”
                # 如果去除空格后，没有任何一个字符是“非断行字符”，则视为无效行丢弃
                has_text = any(is_text_char(c) for c in stripped)
                
                if has_text:
                    lines.append(current_line)
            current_line = ""
        else:
            current_line += char

        # 长度控制：超过 max_length 时尝试断行
        if len(current_line) > max_length:
            found_break = False
            
            # 从后往前遍历，寻找最近的“断行候选符”
            # i 代表断点后的起始索引 (即切掉前 i 个字符)
            for i in range(len(current_line), 1, -1): 
                # 检查位置 i-1 (当前行的最后一个字符) 是否是“断行候选符”
                last_char = current_line[i-1]
                
                # 逻辑：如果不是非断行字符，则它是断行候选符（标点、空格等）
                if not is_text_char(last_char):
                    # 【关键】找到合法断点！
                    # 因为 last_char 是标点/空格，切断后：
                    # 1. 上一行以标点/空格结尾 (符合需求)
                    # 2. 下一行以剩余内容开头 (不会以标点开头，除非剩余内容也是标点，但那是下一行的事了)
                    
                    line_part = current_line[:i]
                    remaining = current_line[i:]
                    
                    lines.append(line_part)
                    current_line = remaining
                    found_break = True
                    break
            
            # 【兜底策略】如果整行全是文字（没有标点或空格），找不到断点，强制截断
            if not found_break:
                split_idx = max_length
                line_part = current_line[:split_idx]
                remaining = current_line[split_idx:]
                
                lines.append(line_part)
                current_line = remaining

    # 处理剩余内容
    if current_line.strip():
        stripped = current_line.strip()
        has_text = any(is_text_char(c) for c in stripped)
        
        if has_text:
            lines.append(current_line)

    return lines

def split_novel_by_30_chapters(
    input_folder='.',
    output_folder='2', # 修改：输出文件夹名称改为"2"
    mode='clean', # 默认修改为 clean，但也支持 none, part
    max_length=42,
    skip_trigger_rule=False  
):
    """主函数：按每 30 章切分小说，清理内容，并对每一章内文本进行断行处理（≤max_length 字符/行）"""
    
    # 处理兼容参数：如果传入 skip_trigger_rule=True，强制覆盖 mode
    if skip_trigger_rule:
        mode = 'part' # 兼容旧逻辑，对应 part 模式的特定行为

    # 创建输出目录
    os.makedirs(output_folder, exist_ok=True)

    txt_files = glob.glob(os.path.join(input_folder, "*.txt"))
    
    if not txt_files:
        print("No TXT files found in current directory.")
        return

    print(f"Found {len(txt_files)} text file(s) to process. Mode: {mode}")

    for file_path in txt_files:
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        
        # 文件名清洗：移除特殊字符，防止路径错误
        safe_base_name = re.sub(r'[^\w\s]', '_', base_name)
        print(f"Processing: {filename}")

        content = ""
        encodings = ['utf-8-sig', 'gb18030','gbk', 'utf-16'] 
        
        found_encoding = False
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                print(f"  [+] Read using {enc}")
                found_encoding = True
                break
            except UnicodeDecodeError:
                continue

        if not content:
            print(f"  [-] Failed to decode: {filename}. Skipping.")
            continue

        # Step 1: 匹配章节标题 (统一正则，修复"未找到章节"问题)
        chapter_pattern = re.compile(
            r'(?:\n\s*)?' 
            r'([第][一二三四五六七八九十百千万零\d]+[章节回节卷]|' 
            r'\d+[章节回节卷])', 
            re.IGNORECASE | re.UNICODE
        )
        
        matches = list(chapter_pattern.finditer(content))

        if not matches:
            print(f"  [-] No chapters found in {filename}. Skipping.")
            continue

        # Step 2: 清洗文本 (传入匹配对象，避免重复扫描)
        cleaned_content = clean_text(content, chapter_matches=matches, mode=mode)

        # 【安全检查】确保 cleaned_content 不为 None
        if cleaned_content is None:
            print(f"  [-] Warning: cleaned_content is None for {filename}. Using original content.")
            cleaned_content = content

        # 【新增】处理要求2：先删除特殊符号，防止断行过程中保留无用字符
        processed_content = remove_special_chars(cleaned_content)

        # Step 3: 分批处理（每 30 章）
        step = 30
        total_chapters = len(matches)
        
        # 【关键修复】在清洗后的内容上重新匹配章节，确保索引对齐
        cleaned_matches = list(chapter_pattern.finditer(processed_content))
        
        if not cleaned_matches:
            print(f"  [-] Warning: No chapters found in cleaned content for {filename}. Skipping.")
            continue

        # 更新总章节数（以防清洗后某些章节标题丢失，虽然通常不会）
        total_chapters = len(cleaned_matches)

        for i in range(0, total_chapters, step):
            start_idx = cleaned_matches[i].start()
            if i + step < total_chapters:
                end_idx = cleaned_matches[i + step].start()
            else:
                end_idx = len(processed_content)

            chunk = processed_content[start_idx:end_idx]

            # Step 4: 第一次断行 (满足要求1：再次断行前的准备)
            lines_first_pass = split_into_lines(chunk, max_length=max_length)
            
            # 合并为字符串再进入第二次（双重断行）
            text_after_first_break = '\n'.join(lines_first_pass)

            # Step 5: 第二次断行（校验长度，确保无遗漏）
            lines_final = split_into_lines(text_after_first_break, max_length=max_length)
            
            # Step 6: 合并最终文本
            final_text = '\n'.join(lines_final)

            # Step 7: 写入输出文件
            start_ch = i + 1
            end_ch = min(i + step, total_chapters)
            
            file_name = f"{safe_base_name}_Chapters_{start_ch:04d}-{end_ch:04d}.txt"
            save_path = os.path.join(output_folder, file_name)

            try:
                with open(save_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(final_text)
                print(f"  [+] Saved: {file_name}")
            except Exception as e:
                print(f"  [-] Failed to save {save_path}: {e}")

    print("All files processed.")


if __name__ == "__main__":
    split_novel_by_30_chapters(
        input_folder='.',
        output_folder='2', # 显式指定输出文件夹为"2"
        mode='part'  
    )
