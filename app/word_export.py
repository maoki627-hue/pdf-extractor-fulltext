from docx import Document

def export_to_word(sections: dict, save_path: str):

    def add_large_text(doc, text):
        """
        python-docx の silent-fail を防ぐため、
        巨大テキストを安全に段落分割して追加する
        """
        # 不要な制御文字を削除
        text = text.replace("\x0c", " ").replace("\x0b", " ")

        # 行ごとに段落として追加（最も安全）
        lines = text.split("\n")
        for ln in lines:
            ln = ln.strip()
            if ln:
                doc.add_paragraph(ln)
            else:
                doc.add_paragraph("")  # 空行も保持

    doc = Document()

    # dict をコピーして内部用に
    data = dict(sections)

    # タイトル
    title = data.pop("__TITLE__", None)
    if title:
        doc.add_heading(title, level=0)

    # セクションごとに出力
    for sec, content in data.items():
        doc.add_heading(sec, level=1)
        add_large_text(doc, content)

    doc.save(save_path)
