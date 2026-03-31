import os
import re
SOURCE_FOLDER = "中文原始101-120"
TARGET_FOLDER = "中文101-120"

def read_file_safe(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip("\ufeff")  # 去除BOM头，避免乱码
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="gbk") as f:
            return f.read().strip("\ufeff")

def write_file_safe(file_path: str, content: str) -> None:
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)

def main():
    if not os.path.isdir(SOURCE_FOLDER):
        print(f"❌ 错误：原始文件夹【{SOURCE_FOLDER}】不存在，请检查路径和文件夹名称")
        return
    if not os.path.isdir(TARGET_FOLDER):
        print(f"❌ 错误：目标文件夹【{TARGET_FOLDER}】不存在，请检查路径和文件夹名称")
        return

    source_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(".txt")]
    target_files = [f for f in os.listdir(TARGET_FOLDER) if f.lower().endswith(".txt")]
    matched_files = list(set(source_files) & set(target_files))
    if not matched_files:
        print("❌ 错误：两个文件夹内没有找到同名的txt文件，请确认两个文件夹内的文件名完全一致")
        return
    success_count = 0
    skip_count = 0

    for filename in matched_files:
        print(f"\n---------------- 正在处理文件：{filename} ----------------")
        source_path = os.path.join(SOURCE_FOLDER, filename)
        target_path = os.path.join(TARGET_FOLDER, filename)
        try:
            source_full = read_file_safe(source_path)
        except Exception as e:
            print(f"⚠️  读取原始文件失败，跳过 | 错误信息：{str(e)}")
            skip_count += 1
            continue

        source_full = source_full.replace("\r\n", "\n").replace("\r", "\n")
        source_all_lines = source_full.split("\n")
        source_valid_lines = [line.strip() for line in source_all_lines if line.strip()]
        if len(source_valid_lines) < 3:
            print(f"⚠️  原始文件有效行数不足3行，不符合【标题/日期/作者】的格式要求，跳过")
            skip_count += 1
            continue
        source_title, source_date, source_author = source_valid_lines[0], source_valid_lines[1], source_valid_lines[2]
        source_body_raw = "\n".join(source_all_lines[3:]).strip()
        raw_paragraphs = re.split(r"\n\s*\n", source_body_raw)
        source_paragraphs = []
        para_sentence_count = []
        for para in raw_paragraphs:
            para_stripped = para.strip()
            sent_count = para_stripped.count("。") + para_stripped.count("！") + para_stripped.count("？")
            if para_stripped and sent_count > 0:
                source_paragraphs.append(para_stripped)
                para_sentence_count.append(sent_count)

        if not source_paragraphs:
            print(f"⚠️  原始文件无有效正文段落，跳过")
            skip_count += 1
            continue

        print(f"✅ 原始文件解析完成 | 标题：{source_title} | 有效段落数：{len(source_paragraphs)}")
        for idx, count in enumerate(para_sentence_count, 1):
            print(f"  第{idx}段 | 句子数：{count}")
        try:
            target_full = read_file_safe(target_path)
        except Exception as e:
            print(f"⚠️  读取目标文件失败，跳过 | 错误信息：{str(e)}")
            skip_count += 1
            continue
        target_full = re.sub(r"</?p\s*>", "", target_full)
        target_full = target_full.replace("。/wj", "。").replace("！/wt", "！").replace("？/ww", "？")
        target_full = target_full.replace("\r\n", "\n").replace("\r", "\n")
        target_valid_lines = [line for line in target_full.split("\n") if line.strip()]

        if len(target_valid_lines) < 3:
            print(f"⚠️  目标文件有效行数不足3行，不符合格式要求，跳过")
            skip_count += 1
            continue

        target_title, target_date, target_author = target_valid_lines[0], target_valid_lines[1], target_valid_lines[2]
        target_sentence_lines = target_valid_lines[3:]
        total_source_sent = sum(para_sentence_count)
        total_target_sent = len(target_sentence_lines)
        print(f"✅ 目标文件解析完成 | 正文句子总行数：{total_target_sent} | 原始文件总句子数：{total_source_sent}")
        if total_target_sent < total_source_sent:
            print(f"⚠️  警告：目标文件句子数少于原始文件，剩余内容会追加到最后一段")
        formatted_head = [
            f"<head>{target_title}</head>",
            "",  # head标签后单独空一行
            f"<date>{target_date}</date>",
            "",  # date标签后单独空一行
            f"<author>{target_author}</author>",
            "",  # author标签后单独空一行
        ]
        formatted_body = []
        current_sent_index = 0

        for para_idx, sent_count in enumerate(para_sentence_count, 1):
            if current_sent_index >= total_target_sent:
                break
            end_index = current_sent_index + sent_count
            current_sentences = target_sentence_lines[current_sent_index:end_index]

            formatted_body.append("<p>")
            formatted_body.extend(current_sentences)
            formatted_body.append("</p>")
            current_sent_index = end_index
            print(f"✅ 第{para_idx}段格式化完成 | 已处理句子数：{len(current_sentences)}")
        if current_sent_index < total_target_sent:
            remaining_sents = target_sentence_lines[current_sent_index:]
            if formatted_body:
                formatted_body[-1:-1] = remaining_sents
                print(f"✅ 剩余{len(remaining_sents)}行句子已追加到最后一段")
            else:
                formatted_body.append("<p>")
                formatted_body.extend(remaining_sents)
                formatted_body.append("</p>")
        full_content = "\n".join(formatted_head + formatted_body)
        # 1. 替换句号
        full_content = full_content.replace("。", "。/wj")
        # 2. 替换感叹号
        full_content = full_content.replace("！", "！/wt")
        # 3. 替换问号
        full_content = full_content.replace("？", "？/ww")
        # 4. 修正标签结尾的错误替换
        full_content = full_content.replace(">/wj", ">")
        full_content = full_content.replace(">/ww", ">")
        full_content = full_content.replace(">/wt", ">")
        try:
            write_file_safe(target_path, full_content)
            print(f"✅ 文件全部处理完成，已成功保存")
            success_count += 1
        except Exception as e:
            print(f"⚠️  写入文件失败，跳过 | 错误信息：{str(e)}")
            skip_count += 1
            continue

    print(f"\n==================== 全部处理完成 ====================")
    print(f"📊 总匹配到的同名文件：{len(matched_files)} 个")
    print(f"✅ 成功处理：{success_count} 个")
    print(f"⚠️  跳过处理：{skip_count} 个")
    print("=======================================================")

if __name__ == "__main__":
    main()