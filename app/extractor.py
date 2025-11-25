from PyPDF2 import PdfReader
import re
import os

def extract_sections(pdf_path):
    reader = PdfReader(pdf_path)

    # ---- 全ページテキスト抽出 ----
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"

    # ---- タイトル取得（メタデータ） ----
    title = ""
    try:
        meta = reader.metadata
        if meta and getattr(meta, "title", None):
            title = str(meta.title).strip()
    except:
        pass

    # メタデータが無ければ PDF ファイル名をタイトルとして採用
    if not title:
        title = os.path.splitext(os.path.basename(pdf_path))[0]

    # ---- References 以降を削除 ----
    lower_all = text.lower()
    for key in ["references", "bibliography"]:
        idx = lower_all.find(key)
        if idx != -1:
            text = text[:idx]
            lower_all = text.lower()

    # ---- 複数スペース削除 ----
    text = re.sub(r" {2,}", " ", text)

    # ---- セクション候補 ----
    section_candidates = {
        "Abstract": [r"\babstract\b", r"\bsummary\b"],
        "Introduction": [r"\bintroduction\b", r"\bbackground\b"],
        "Discussion": [
            r"\bdiscussion\b",
            r"\bcomment\b",
            r"\bcomments\b",
            r"\bconclusion\b",
            r"\bconclusions\b",
        ],
    }

    lower = text.lower()
    indices = {}

    # ---- 各セクションの開始位置を取得 ----
    for sec, patterns in section_candidates.items():
        best_idx = None
        for pat in patterns:
            m = re.search(pat, lower, flags=re.IGNORECASE)
            if m:
                if best_idx is None or m.start() < best_idx:
                    best_idx = m.start()
        indices[sec] = best_idx

    # ---- 開始位置があるものだけ並べ替え ----
    order = [(k, v) for k, v in indices.items() if v is not None]
    order.sort(key=lambda x: x[1])

    sections = {}

    # ---- セクション抽出 ----
    if order:
        for i, (sec, start) in enumerate(order):
            end = order[i + 1][1] if i + 1 < len(order) else len(text)
            raw = text[start:end].strip()
            sections[sec] = raw
    else:
        # ---- セクションが何も見つからなければ Full Text として登録 ----
        sections["Full Text"] = text.strip()

    # ---- タイトルは別処理で利用 ----
    sections["_title"] = title
    return sections
