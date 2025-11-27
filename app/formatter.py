import re

def format_text(text):
    """
    Speechify 最適化整形：
      - URL/DOI の削除
      - References 以降の削除
      - 文献番号 [1], (1), ^1 など除去
      - ページ番号/フッタ除去
      - ハイフネーション解除
      - 改行整理
    """

    if not text:
        return ""

    # ---- URL / DOI を削除 ----
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"www\.\S+", "", text)
    text = re.sub(r"doi:\s*\S+", "", text, flags=re.IGNORECASE)

    # ---- References / Bibliography 以降を削除 ----
    for key in ["references", "bibliography"]:
        idx = text.lower().find(key)
        if idx != -1:
            text = text[:idx]

    # ================================
    # ★ 文献番号の削除（本文内）
    # ================================
    # ① 角括弧付き [12], [3–5]
    text = re.sub(r"\[\s*\d+(\s*[-–]\s*\d+)?\s*\]", " ", text)

    # ② 丸括弧付き (1), (23)
    text = re.sub(r"\(\s*\d+\s*\)", " ", text)

    # ③ 上付き数字の簡易表現 ^12
    text = re.sub(r"\^\s*\d+", " ", text)

    # ④ 文末の引用スタイル …12.
    text = re.sub(r"(?<=\w)\s*\d+(?=[\.\,\;])", " ", text)

    # ---- ページ番号/フッタ除去 ----
    # “Page 2 of 10”
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", " ", text, flags=re.IGNORECASE)

    # 単独のページ番号（行頭行末にある 1桁〜3桁）
    text = re.sub(r"^\s*\d{1,3}\s*$", " ", text, flags=re.MULTILINE)

    # ---- ハイフネーション解除 ----
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    # ---- 改行整理 ----
    lines = text.splitlines()
    merged = []

    for line in lines:
        s = line.strip()
        if not s:
            merged.append("\n")
        else:
            merged.append(s + " ")

    joined = "".join(merged)

    joined = re.sub(r"\n\s*", "\n", joined)
    joined = re.sub(r"(\n\s*){3,}", "\n\n", joined)

    return joined.strip()
