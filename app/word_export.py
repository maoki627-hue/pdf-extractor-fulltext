from docx import Document

def export_to_word(sections, save_path, title=None):
    """
    sections: dict（_title を含まない、本文セクション）
    save_path: 保存先の .docx パス
    title: 論文タイトル（extractor.py で _title として抽出）
    """

    doc = Document()

    # ---- 先頭に大見出しとしてタイトルを表示 ----
    if title:
        doc.add_heading(title, level=0)
        doc.add_paragraph("")  # 空行を追加

    # ---- セクションごとに出力 ----
    for sec, text in sections.items():
        if sec.startswith("_"):
            continue
        if not text:
            continue

        # セクション見出し（Full Text 含む）
        doc.add_heading(sec, level=1)

        # 本文
        doc.add_paragraph(text)
        doc.add_paragraph("")  # 1 行あける

    # ---- 保存 ----
    doc.save(save_path)
