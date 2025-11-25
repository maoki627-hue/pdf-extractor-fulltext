# extractor.py — Stable Ver 1.3 (Title extraction + FullText fallback + invisible space fix)

from PyPDF2 import PdfReader
import os
import re

# セクション識別
TARGET_SECTIONS = ["abstract", "introduction", "discussion"]


def sanitize_title(title: str) -> str:
    """Word heading が silent-fail しないように論文タイトルを完全無害化"""
    if not title:
        return ""

    # Zero-width / Unicode 制御文字削除
    title = re.sub(r'[\u200B-\u200F\u202A-\u202E]', '', title)

    # ★ 不可視スペース（NBSP, thin-space, narrow no-break space）を通常スペースへ変換
    title = title.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")

    # 改行は heading に入れられないため削除
    title = title.replace("\n", " ").replace("\r", " ")

    # 記号類（Windows filename/Word heading 禁止文字）を無害化
    title = re.sub(r'[\\/:*?"<>|]', ' ', title)

    # 余分なスペースの整理
    title = ' '.join(title.split())

    return title.strip()


def extract_title_from_first_page(first_page_text: str) -> str:
    """論文タイトルを1ページ目から抽出（A-3 ルールに基づく）"""
    if not first_page_text:
        return ""

    # 1行ずつに分解
    lines = [ln.strip() for ln in first_page_text.split("\n") if ln.strip()]
    candidates = []

    for ln in lines[:12]:  # 先頭12行ほどに限定（タイトル周囲）
        low = ln.lower()

        # 1) ジャーナル種別は除外
        if low in (
            "original research",
            "review",
            "case report",
            "editorial",
            "short communication",
            "pediatric cardiology",
        ):
            continue

        # 2) セクション名は除外
        if low in ("abstract", "introduction", "discussion", "background"):
            continue

        # 3) 著者行（MD, PhD, , が多い）は除外
        if " md" in low or " phd" in low or low.count(",") >= 2:
            continue

        # 4) 単語数5以上の “文” だけを候補とする
        if len(ln.split()) >= 5:
            candidates.append(ln)

    # 最も上にある候補を採用
    if candidates:
        return sanitize_title(candidates[0])

    return ""


def extract_sections(pdf_path: str) -> dict:
    """Abstract / Introduction / Discussion 抽出 + タイトル付与 + FullText fallback"""
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]

    full_text = "\n".join(pages)
    lines = full_text.split("\n")
    lines_lower = [ln.strip().lower() for ln in lines]

    sections = {}

    # --------------------
    # 1) セクション抽出
    # --------------------
    for sec in TARGET_SECTIONS:
        sec_lower = sec.lower()
        for i, ln in enumerate(lines_lower):
            if ln == sec_lower:  # 行頭単独一致
                start = i + 1
                end = len(lines)
                for j in range(start, len(lines_lower)):
                    if lines_lower[j] in TARGET_SECTIONS:
                        end = j
                        break
                body = "\n".join(lines[start:end]).strip()
                if len(body) > 30:
                    sections[sec.capitalize()] = body
                break

    # --------------------
    # 2) タイトル抽出
    # --------------------
    title = extract_title_from_first_page(pages[0]) if pages else ""

    # タイトル抽出できなければファイル名fallback
    if not title:
        title = sanitize_title(os.path.splitext(os.path.basename(pdf_path))[0])

    # 最終的に必ずタイトルを先頭に入れる
    final_sections = {"__TITLE__": title}

    # --------------------
    # 3) セクションが1つ以上ある場合
    # --------------------
    if len(sections) > 0:
        final_sections.update(sections)
        return final_sections

    # --------------------
    # 4) セクションゼロ → FullText fallback
    # --------------------
    final_sections["FullText"] = full_text.strip()
    return final_sections
