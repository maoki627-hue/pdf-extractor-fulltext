# extractor.py — Stable Ver 1.2 (Title extraction + FullText fallback)

from PyPDF2 import PdfReader
import os
import re

# セクション識別
TARGET_SECTIONS = ["abstract", "introduction", "discussion"]


def sanitize_title(title: str) -> str:
    """Word heading でクラッシュしないようにタイトルを無害化"""
    if not title:
        return ""

    # Zero-width / Unicode 制御文字削除
    title = re.sub(r'[\u200B-\u200F\u202A-\u202E]', '', title)

    # 改行は入れない（python-docx がクラッシュするため）
    title = title.replace("\n", " ").replace("\r", " ")

    # 記号類を削除 or スペース置換
    title = re.sub(r'[\\/:*?"<>|]', ' ', title)

    # 余分なスペースをまとめる
    title = ' '.join(title.split())

    return title.strip()


def extract_title_from_first_page(first_page_text: str) -> str:
    """1ページ目から論文タイトルらしい1行を抽出（A-3 仕様）"""
    if not first_page_text:
        return ""

    lines = [ln.strip() for ln in first_page_text.split("\n") if ln.strip()]
    candidates = []

    for ln in lines[:12]:  # 先頭12行くらいを候補に
        low = ln.lower()

        # ジャーナル種別・カテゴリ名は除外
        if low in (
            "original research",
            "pediatric cardiology",
            "review",
            "editorial",
            "case report",
            "short communication"
        ):
            continue

        # セクション名は除外
        if low in ("abstract", "introduction", "discussion"):
            continue

        # 著者行っぽいもの（カンマ大量、MD/PhDなど）は除外
        if " md" in low or " phd" in low or low.count(",") >= 2:
            continue

        # 単語数がある程度ある行のみ（＝タイトルらしい）
        if len(ln.split()) >= 5:
            candidates.append(ln)

    if candidates:
        return sanitize_title(candidates[0])

    return ""


def extract_sections(pdf_path: str) -> dict:
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]

    full_text = "\n".join(pages)

    # 行単位に分割（セクション検出用）
    lines = full_text.split("\n")
    lines_lower = [ln.strip().lower() for ln in lines]

    sections = {}

    # --------------------
    # 1) セクション抽出
    # --------------------
    for sec in TARGET_SECTIONS:
        sec_lower = sec.lower()
        for i, ln in enumerate(lines_lower):
            if ln == sec_lower:  # 行頭単独一致のみ
                start = i + 1
                end = len(lines)
                for j in range(start, len(lines_lower)):
                    if lines_lower[j] in TARGET_SECTIONS:
                        end = j
                        break
                body = "\n".join(lines[start:end]).strip()
                if len(body) > 30:  # 最低文字数
                    sections[sec.capitalize()] = body
                break

    # --------------------
    # 2) タイトル抽出（A-3）
    # --------------------
    title = extract_title_from_first_page(pages[0]) if pages else ""

    # タイトルが抽出できなければ → PDF ファイル名
    if not title:
        title = sanitize_title(os.path.splitext(os.path.basename(pdf_path))[0])

    # Word heading に必ず使う
    final_sections = {"__TITLE__": title}

    # --------------------
    # 3) セクションが1つでもあれば → Title + セクション
    # --------------------
    if len(sections) > 0:
        final_sections.update(sections)
        return final_sections

    # --------------------
    # 4) セクションがゼロ → FullText fallback（確実に出力される）
    # --------------------
    final_sections["FullText"] = full_text.strip()
    return final_sections
