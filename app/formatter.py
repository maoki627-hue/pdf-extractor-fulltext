import re

def format_text(text):
    """
    Speechify で聞きやすくするための整形処理：
      - URL/DOI の削除
      - References 以降の削除
      - ハイフネーション解除（word-break対策）
      - 不要な改行の整理
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

    # ---- ハイフネーション解除（行末の hyphen + 改行）----
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)

    # ---- 改行を整える ----
    lines = text.splitlines()
    merged = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            merged.append("\n")  # 空行はそのまま
        else:
            merged.append(stripped + " ")  # 文の途中にはスペースを追加

    joined = "".join(merged)

    # ---- 改行の最適化 ----
    joined = re.sub(r"\n\s*", "\n", joined)
    joined = re.sub(r"(\n\s*){3,}", "\n\n", joined)

    return joined.strip()
