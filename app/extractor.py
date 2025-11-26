# extractor.py — PyMuPDF版 + Abstractフェイルセーフ対応

import fitz  # PyMuPDF
import os
import re

TARGET_SECTIONS = ["abstract", "introduction", "discussion"]


def sanitize_title(title: str) -> str:
    """Word heading が壊れないようにタイトルを無害化"""
    if not title:
        return ""

    # Zero-width / Unicode 制御文字削除
    title = re.sub(r'[\u200B-\u200F\u202A-\u202E]', '', title)

    # 不可視スペース → 通常スペース
    title = title.replace("\u00A0", " ").replace("\u2009", " ").replace("\u202F", " ")

    # 改行削除
    title = title.replace("\n", " ").replace("\r", " ")

    # ファイル名禁止文字
    title = re.sub(r'[\\/:*?"<>|]', " ", title)

    # 余分なスペース整理
    title = " ".join(title.split())

    return title.strip()


def clean_text(text: str) -> str:
    """制御文字除去・改行整理などの共通クレンジング"""
    if not text:
        return ""

    # CR→LF
    text = text.replace("\r", "\n")

    # 制御文字除去（TABは残す）
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", text)

    # 連続改行を少し抑える
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_title_from_doc(doc: fitz.Document) -> str:
    """1ページ目からタイトル候補を抽出（2行タイトル対応）"""
    if len(doc) == 0:
        return ""

    page0 = doc[0]
    text = page0.get_text()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return ""

    title_lines = []
    for ln in lines[:15]:  # 上から15行程度までを見る
        low = ln.lower()

        # セクションヘッダに到達したら終了
        if low.startswith(("abstract", "background", "introduction")):
            break

        # 著者行らしきものはスキップ
        if " md" in low or " phd" in low or low.count(",") >= 2:
            continue

        # 短すぎる行はタイトル候補としては弱い
        if len(ln.split()) < 3:
            continue

        title_lines.append(ln)

        # 2〜3行程度あれば十分
        if len(title_lines) >= 2:
            # 次が明らかなセクションならそこで切る
            continue

    if not title_lines:
        return ""

    raw_title = " ".join(title_lines)
    return sanitize_title(raw_title)


def extract_sections(pdf_path: str) -> dict:
    """
    Abstract / Introduction / Discussion 抽出 + タイトル付与 + FullText fallback
    PyMuPDFで全文を取りつつ、Abstractはフェイルセーフ付き。
    """
    doc = fitz.open(pdf_path)

    # --- FullText 作成 ---
    page_texts = [page.get_text() or "" for page in doc]
    full_text_raw = "\n".join(page_texts)
    full_text = clean_text(full_text_raw)

    lines = full_text.split("\n")
    lines_lower = [ln.strip().lower() for ln in lines]

    sections: dict[str, str] = {}

    # -------------------------
    # 1) Abstract 抽出（特別扱い）
    # -------------------------
    abstract_text = ""
    start_idx = None

    # ① "abstract" 行を探す
    for i, low in enumerate(lines_lower[:200]):  # 論文冒頭〜200行程度を対象
        if low == "abstract" or low.startswith("abstract "):
            start_idx = i + 1
            break

    # ② 見つからない場合、"background" を Abstract 先頭とみなすケース
    if start_idx is None:
        for i, low in enumerate(lines_lower[:200]):
            if low.startswith("background"):
                start_idx = i
                break

    if start_idx is not None:
        # 終了位置を探す（Introduction / Methods / Patients などの前まで）
        end_idx = len(lines)
        STOP_KEYS = (
            "introduction",
            "methods",
            "patients and methods",
            "materials and methods",
            "results",
        )
        for j in range(start_idx + 1, min(len(lines_lower), start_idx + 400)):
            low = lines_lower[j]
            if any(low.startswith(k) for k in STOP_KEYS):
                end_idx = j
                break

        candidate = "\n".join(lines[start_idx:end_idx]).strip()
        candidate = clean_text(candidate)
        abstract_text = candidate

    # 抽出結果を評価し、短すぎ/壊れていそうならフェイルセーフ
    if abstract_text and len(abstract_text) >= 100:
        sections["Abstract"] = abstract_text
    else:
        sections["Abstract"] = "Abstract Unretrievable."

    # -------------------------
    # 2) Introduction / Discussion 抽出
    # -------------------------
    def extract_section_by_header(header: str) -> str:
        header_low = header.lower()
        start = None
        end = len(lines)

        for i, low in enumerate(lines_lower):
            if low == header_low or low.startswith(header_low + " "):
                start = i + 1
                break

        if start is None:
            return ""

        STOP_KEYS = [k for k in TARGET_SECTIONS if k != header_low]
        for j in range(start + 1, len(lines_lower)):
            if lines_lower[j] in STOP_KEYS:
                end = j
                break

        body = "\n".join(lines[start:end]).strip()
        return clean_text(body)

    intro = extract_section_by_header("introduction")
    if intro:
        sections["Introduction"] = intro

    disc = extract_section_by_header("discussion")
    if disc:
        sections["Discussion"] = disc

    # -------------------------
    # 3) タイトル抽出
    # -------------------------
    title = extract_title_from_doc(doc)
    if not title:
        # 取れなければファイル名
        title = sanitize_title(os.path.splitext(os.path.basename(pdf_path))[0])

    final_sections = {"__TITLE__": title}

    # -------------------------
    # 4) セクションが1つもまともに取れていない場合 → FullText fallback
    # -------------------------
    has_valid_body = any(
        k in sections and sections[k] and sections[k] != "Abstract Unretrievable."
        for k in ("Abstract", "Introduction", "Discussion")
    )

    if not has_valid_body:
        # FullTextのみ
        final_sections["FullText"] = full_text
        return final_sections

    # -------------------------
    # 5) 通常ケース：抽出できたセクションをマージ
    # -------------------------
    final_sections.update(sections)
    return final_sections
