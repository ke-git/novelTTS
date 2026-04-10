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
    处理要求2：删除指定的特殊符号，包括全角和半角变体。
    针对 @#￥%&*+= 及其对应的全角字符进行正则替换删除。
    
    【修复】避免使用复杂的正则表达式构造，改用简单的列表遍历删除
    """
    if not content:
        return ""
    
    # 需要删除的半角字符集合
    half_chars_to_remove = '@#￥%&*+=/'
    
    # 对应的全角/特殊 Unicode 字符映射（根据要求覆盖全角/半角）
    full_chars_map = {
        '@': '＠', '#': '＃', '$': '＄', '%': '％', '&': '＆', 
        '*': '＊', '+': '＋', '/': '／', '=': '＝'
    }
    
    # 构建所有需要删除的字符集合（包括半角和全角）
    all_chars_to_remove = set()
    
    for char in half_chars_to_remove:
        full_match = full_chars_map.get(char, "")
        if full_match:
            all_chars_to_remove.add(char)
            all_chars_to_remove.add(full_match)
        else:
            all_chars_to_remove.add(char)
    
    # 简单的遍历删除（避免复杂的正则表达式）
    cleaned = ""
    for char in content:
        if char not in all_chars_to_remove:
            cleaned += char
    
    return cleaned


def split_into_lines(content, max_length=42):
    """智能断行函数：按中英文混合文本，每行最多 max_length 字符。（保持原有逻辑）"""
    if not content:
        return []

    # 【修复】使用字符直接定义，避免 \~ 转义警告。
    # 包含全角/半角标点及换行符
    punctuation_set = {
        '。', '！', '？', '…', '，', '.', '?', '|', '/', '\\', '~', ')', '\n'
    }
    
    lines = []
    current_line = ""

    for char in content:
        # 遇到换行符时，如果当前行已满且无断点，强制截断；否则视为普通字符处理
        if char == '\n':
            pass 
        
        current_line += char

        # 2. 长度控制：超过 max_length (42) 时尝试断行
        if len(current_line) > max_length:
            found_break = False
            
            # 从后往前查找最近的合法断点
            for i in range(len(current_line), -1, -1):
                if current_line[i-1] in punctuation_set:
                    line_part = current_line[:i]
                    remaining = current_line[i:]
                    
                    lines.append(line_part)
                    current_line = remaining
                    found_break = True
                    break
            
            # 3. 若未找到合法断点（如超长单词），强制截断以满足长度限制 (Req 2)
            if not found_break:
                split_idx = max_length
                line_part = current_line[:split_idx]
                remaining = current_line[split_idx:]
                
                lines.append(line_part)
                current_line = remaining

    # 处理剩余内容
    if current_line.strip():
        lines.append(current_line)

    # 4. 后处理：合并纯标点行 (Req 4) & 首行顶格 (Req 5)
    final_lines = []
    
    for i, line in enumerate(lines):
        # 【修复】强制去除首尾空格，确保统一顶格显示
        stripped_line = line.strip()
        
        if not stripped_line:
            continue
            
        # 检查是否为纯标点/符号行（无中英文字符）
        is_pure_punctuation = True
        has_text_char = False
        
        for char in stripped_line:
            # 判断是否包含中文或英文字母数字
            if '\u4e00' <= char <= '\u9fff' or char.isalpha() or char.isdigit():
                has_text_char = True
                is_pure_punctuation = False
                break
        
        # 如果当前行是纯标点，且不是第一行（有上一行），则合并到上一行
        if i > 0 and is_pure_punctuation:
            final_lines[-1] += ' ' + stripped_line
        else:
            final_lines.append(stripped_line)

    return [line for line in final_lines if line.strip()]


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
        mode='clean'  
    )
