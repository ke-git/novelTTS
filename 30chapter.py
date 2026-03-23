import re
import os

def split_novel_by_30_chapters(file_path, output_folder='split_results'):
 # 1. 创建输出文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    #2. --- 增强版读取逻辑 ---
    content = ""
    for enc in ['utf-8', 'gb18030', 'utf-16']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            print(f"成功使用 {enc} 编码读取文件")
            break
        except UnicodeDecodeError:
            continue
    
    if not content:
        print("错误：无法识别文件编码，请手动将小说另存为 UTF-8 格式")
        return

    # 3. 正则匹配：匹配“第”开头，中间是数字或中文数字，结尾是“章/回/节”的行
    # 这个正则能涵盖绝大多数网文格式
    chapter_pattern = re.compile(r'\n?\s*(第[一二三四五六七八九十百千万零\d]+[章节回节])')
    
    # 找到所有章节标题的起始位置
    matches = list(chapter_pattern.finditer(content))
    total_chapters = len(matches)
    print(f"检测到总章节数: {total_chapters}")

    if total_chapters == 0:
        print("未检测到章节标识，请检查正则匹配规则。")
        return

    # 4. 每30章切割一次
    step = 30
    for i in range(0, total_chapters, step):
        start_pos = matches[i].start()
        
        # 如果是最后一份，截取到全文末尾；否则截取到第 i+30 章的开头
        if i + step < total_chapters:
            end_pos = matches[i + step].start()
        else:
            end_pos = len(content)
        
        # 提取这30章的内容
        chunk = content[start_pos:end_pos]
        
        # 生成文件名（例如：第1-30章.txt）
        start_ch = i + 1
        end_ch = min(i + step, total_chapters)
        file_name = f"Chapters_{start_ch:04d}-{end_ch:04d}.txt"
        
        # 写入文件
        save_path = os.path.join(output_folder, file_name)
        with open(save_path, 'w', encoding='gb18030') as f_out:
            f_out.write(chunk)
        
        print(f"已生成: {file_name}")

if __name__ == "__main__":
    # 在这里修改你的文件名，并将小说文件与python脚本放在同一文件夹，运行python 30chapter.py
    split_novel_by_30_chapters('novel.txt')
