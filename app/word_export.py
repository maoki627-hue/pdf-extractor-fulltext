from docx import Document

def export_to_word(sections: dict, save_path: str):
    doc = Document()

    # dict をコピーして内部用に
    data = dict(sections)

    # 特別なタイトルキーを取り出す
    title = data.pop("__TITLE__", None)
    if title:
        # 論文タイトルをドキュメント先頭の大見出しに
        doc.add_heading(title, level=0)

    # 残りのキーをセクションとして出力
    for sec, content in data.items():
        doc.add_heading(sec, level=1)
        doc.add_paragraph(content)

    doc.save(save_path)
