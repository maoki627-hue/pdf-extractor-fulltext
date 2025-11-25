# extractor.py
from PyPDF2 import PdfReader
import re
import os

TARGET_SECTIONS = ["abstract", "introduction", "discussion"]

def extract_sections(pdf_path):
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]

    text = "\n".join(pages)

    sections = {}

    # --- 通常のセクション抽出 ---
    lower = text.lower()
    for sec in TARGET_SECTIONS:
        if sec in lower:
            pattern = rf"{sec}(.+?)(?=(abstract|introduction|discussion|references|$))"
            found = re.findall(pattern, lower, flags=re.DOTALL)
            if found:
                sections[sec.capitalize()] = found[0][0].strip()

    # --- ★ Fallback: セクション抽出ゼロなら FullText を返す ---
    if len(sections) == 0:
        full_text = text.strip()

        # ----- タイトル抽出 A-3 -----
        first_page = pages[0].split("\n")

        # 一行目〜三行目を候補
        candidates = [
            line.strip()
            for line in first_page[:6]
            if len(line.strip()) > 6
        ]

        # 条件に合う候補を抽出
        if candidates:
            title = candidates[0]
        else:
            # PDF タイトル抽出不可 → ファイル名
            title = os.path.splitext(os.path.basename(pdf_path))[0]

        sections = {
            "Title": title,
            "FullText": full_text
        }

    return sections
