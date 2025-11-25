import tkinter as tk
from tkinter import filedialog, messagebox
from extractor import extract_sections
from formatter import format_text
from word_export import export_to_word
import os

class PDFExtractorGUI:
    def __init__(self, master):
        self.master = master
        master.title("PDF抽出ツール v2（FullText対応）")
        master.geometry("720x520")
        
        self.pdf_path = None          # 選択されたPDFパス
        self.sections = {}            # セクション内容
        self.title = None             # PDFタイトル
        
        # --- Step 1: PDF選択 ---
        frame1 = tk.LabelFrame(master, text="Step 1: PDF を選択してください")
        frame1.pack(fill="x", padx=10, pady=5)

        tk.Button(frame1, text="PDF を選択", command=self.select_pdf).pack(pady=6)
        self.pdf_label = tk.Label(frame1, text="（未選択）")
        self.pdf_label.pack()

        # --- Step 2: セクション選択 ---
        frame2 = tk.LabelFrame(master, text="Step 2: 出力するセクションを選択")
        frame2.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_sections = frame2
        self.check_vars = {}

        # --- Step 3: 整形 ---
        frame3 = tk.LabelFrame(master, text="Step 3: Speechify向け整形を実行")
        frame3.pack(fill="x", padx=10, pady=5)

        tk.Button(frame3, text="整形を実行", command=self.run_format).pack(pady=6)

        # --- Step 4: Word 出力 ---
        frame4 = tk.LabelFrame(master, text="Step 4: Word ファイルとして保存")
        frame4.pack(fill="x", padx=10, pady=5)

        tk.Button(frame4, text="Word に保存", command=self.save_word).pack(pady=6)

    # ★ PDF を選択してセクションを抽出
    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        
        self.pdf_path = path
        self.pdf_label.config(text=os.path.basename(path))

        # セクション抽出
        data = extract_sections(path)

        # タイトル
        self.title = data.get("_title")

        # セクション本体のみ
        self.sections = {k: v for k, v in data.items() if not k.startswith("_")}

        if not self.sections:
            messagebox.showwarning("抽出できません", "PDFからテキストを抽出できませんでした。")
            return

        self._refresh_section_checkboxes()
        messagebox.showinfo("抽出完了", "PDF からセクションを抽出しました。")

    # ★ チェックボックス描画更新
    def _refresh_section_checkboxes(self):
        for w in self.frame_sections.winfo_children():
            w.destroy()

        self.check_vars = {}
        for sec in self.sections.keys():
            var = tk.IntVar(value=1)
            tk.Checkbutton(self.frame_sections, text=sec, variable=var).pack(anchor="w")
            self.check_vars[sec] = var

    # ★ 整形実行
    def run_format(self):
        if not self.sections:
            messagebox.showwarning("未抽出", "PDFを先に選択してください。")
            return
        
        for sec in self.sections:
            self.sections[sec] = format_text(self.sections[sec])
        
        messagebox.showinfo("整形完了", "Speechify向けの整形が完了しました。")

    # ★ Word 保存
    def save_word(self):
        if not self.sections:
            messagebox.showwarning("未抽出", "PDFを先に選択してください。")
            return
        
        selected = {sec: self.sections[sec] for sec, var in self.check_vars.items() if var.get() == 1}

        if not selected:
            messagebox.showwarning("未選択", "少なくとも1つのセクションを選択してください。")
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word files", "*.docx")]
        )
        if not path:
            return
        
        export_to_word(selected, path, self.title)
        messagebox.showinfo("保存完了", f"{os.path.basename(path)} を保存しました。")

# --- 実行 ---
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFExtractorGUI(root)
    root.mainloop()
