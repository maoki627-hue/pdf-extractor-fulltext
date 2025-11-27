# extractor.py — Stable Final (Abstract + FullText, Abstract removal from FullText)

import fitz  # PyMuPDF
import os
import re

# -----------------------
# Utility functions
# -----------------------

def sanitize_title(title: str) -> str:
    """Remove invisible characters and illegal chars for Word heading."""
    if not title:
        return ""
    title = re.sub(r'[\u200B-\u200F\u202A-\u202E]', '', title)
    title = title.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")
    title = title.replace("\n", " ").replace("\r", " ")
    title = re.sub(r'[\\/:*?"<>|]', " ", title)
    return " ".join(title.split()).strip()


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_title_from_doc(doc: fitz.Document) -> str:
    """タイトル抽出：1ページ目の上から2-3行をタイトルとみなす"""
    if len(doc) == 0:
        return ""
    page0 = doc[0]
    text = page0.get_text()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""
    candidates = []
    for ln in lines[:15]:
        low = ln.lower()
        if low.startswith(("abstract", "introduction", "background")):
            break
        if " md" in low or " phd" in low or low.count(",") >= 2:
            continue
        if len(ln.split()) < 3:
            continue
        candidates.append(ln)
        if len(candidates) >= 2:
            break
    if not candidates:
        return ""
    return sanitize_title(" ".join(candidates))


# -----------------------
# Abstract extraction
# -----------------------

def extract_abstract(full_lines, full_lines_lower):
    """Return abstract_text or 'Abstract Unretrievable.'"""
    abstract_text = ""
    start_idx = None

    # 1) "abstract" 行を探す
    for i, low in enumerate(full_lines_lower[:200]):
        if low == "abstract" or low.startswith("abstract "):
            start_idx = i + 1
            break

    # 2) 見つからなければ background を Abstract とみなす
    if start_idx is None:
        for i, low in enumerate(full_lines_lower[:200]):
            if low.startswith("background"):
                start_idx = i
                break

    # 見つからなかった場合
    if start_idx is None:
        return "Abstract Unretrievable.", None, None

    # Abstract 終了位置推定
    end_idx = len(full_lines)
    STOP = ("introduction", "methods", "patients", "materials", "results")

    for j in range(start_idx + 1, min(len(full_lines_lower), start_idx + 400)):
        low = full_lines_lower[j]
        if any(low.startswith(k) for k in STOP):
            end_idx = j
            break

    text = "\n".join(full_lines[start_idx:end_idx]).strip()
    text = clean_text(text)

    # 判定
    if len(text) < 80:  # 短すぎる場合は失敗扱い
        return "Abstract Unretrievable.", None, None

    return text, start_idx, end_idx


# -----------------------
# Main function
# -----------------------

def extract_sections(pdf_path: str) -> dict:
    doc = fitz.open(pdf_path)

    # FullText 抽出
    pages = [page.get_text() or "" for page in doc]
    full_text_raw = "\n".join(pages)
    full_text = clean_text(full_text_raw)

    full_lines = full_text.split("\n")
    full_lines_lower = [ln.lower().strip() for ln in full_lines]

    # 1) Abstract 抽出
    abs_text, abs_start, abs_end = extract_abstract(full_lines, full_lines_lower)

    # 2) FullText から Abstract を除去
    if abs_start is not None and abs_end is not None:
        filtered_lines = full_lines[:abs_start - 1] + full_lines[abs_end:]
        filtered_fulltext = clean_text("\n".join(filtered_lines))
    else:
        filtered_fulltext = full_text

    # 3) タイトル
    title = extract_title_from_doc(doc)
    if not title:
        title = sanitize_title(os.path.splitext(os.path.basename(pdf_path))[0])

    return {
        "__TITLE__": title,
        "Abstract": abs_text,
        "FullText": filtered_fulltext,
    }
