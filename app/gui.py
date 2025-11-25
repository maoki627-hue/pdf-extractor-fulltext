# gui.py — Stable Ver 1.3 Final
import tkinter as tk
from tkinter import filedialog, messagebox
from extractor import extract_sections
from formatter import format_text
from word_export import export_to_word
import os

class PDFExtractorGUI:
    def __init__(self, master):
        self.master = master
        self.master.geometry("700x500")
        self.master.title("PDF Extractor for Speechify (FullText Version)")
        self.pdf_path = None
        self.sections = {}

        # Step1: PDF選択
        self.step1_frame = tk.LabelFrame(master, text="Step1: PDFを選択")
        self.step1_frame.pack(fill="x", padx=10, pady=5)

        self.select_btn = tk.Button(self.step1_frame, text="PDFを選択", command=self.select_pdf)
        self.select_btn.pack(pady=10)

        self.pdf_label = tk.Label(self.step1_frame, text="PDFが選択されていません")
        self.pdf_label.pack()

        # Step2: セクション選択
        self.step2_frame = tk.LabelFrame(master, text="Step2: 出力するセクションを選択（FullTextは自動使用）")
        self.step2_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.check_vars = {}
        for sec in ["Abstract", "Introduction", "Discussion"]:
            var = tk.IntVar(value=1)
            cb = tk.Checkbutton(self.step2_frame, text=sec, variable=var)
            cb.pack(anchor="w")
            self.check_vars[sec] = var

        # Step3: 整形
        self.step3_frame = tk.LabelFrame(master, text="Step3: Speechify向け整形")
        self.step3_frame.pack(fill="x", padx=10, pady=5)

        self.format_btn = tk.Button(self.step3_frame, text="整形実行", command=self.format_sections)
        self.format_btn.pack(pady=10)

        # Step4: Word出力
        self.step4_frame = tk.LabelFrame(master, text="Step4: Wordに出力")
        self.step4_frame.pack(fill="x", padx=10, pady=5)

        self.export_btn = tk.Button(self.step4_frame, text="Wordに出力", command=self.export_word)
        self.export_btn.pack(pady=10)

    def select_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.pdf_path = path
            self.pdf_label.config(text=os.path.basename(path))
            self.sections = extract_sections(path)
            messagebox.showinfo("抽出完了", "PDFからセクションを抽出しました")

    def format_sections(self):
        if not self.sections:
            messagebox.showwarning("未抽出", "先にPDFを選択してください")
            return
        for sec in self.sections:
            if sec != "__TITLE__":
                self.sections[sec] = format_text(self.sections[sec])
        messagebox.showinfo("整形完了", "Speechify向け整形が完了しました")

    def export_word(self):
        if not self.sections:
            messagebox.showwarning("未抽出", "先にPDFを選択してください")
            return

        # __TITLE__ は常に含める
        selected_sections = {"__TITLE__": self.sections["__TITLE__"]}

        # チェックされたセクションを追加
        for sec, var in self.check_vars.items():
            if var.get() == 1 and sec in self.sections:
                selected_sections[sec] = self.sections[sec]

        # セクションが何も無い場合 → FullText fallback
        if len(selected_sections) == 1:  # タイトルだけ
            if "FullText" in self.sections:
                selected_sections["FullText"] = self.sections["FullText"]
            else:
                messagebox.showwarning("データなし", "抽出された本文がありません。")
                return

        # 保存処理
        save_path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word files", "*.docx")]
        )
        if save_path:
            export_to_word(selected_sections, save_path)
            messagebox.showinfo("出力完了", f"{os.path.basename(save_path)} に出力しました")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFExtractorGUI(root)
    root.mainloop()
