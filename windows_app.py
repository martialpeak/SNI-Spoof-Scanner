import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import threading
import concurrent.futures
import re
import winsound
import os

# پورت‌های استاندارد CDN
PORTS = [443, 2053, 2083, 2087, 2096, 8443]

class SNI_Scanner_v4_3:
    def __init__(self, root):
        self.root = root
        self.root.title("💎 SNI Scanner Pro v4.3 - Perfect Edition")
        self.root.geometry("850x800")
        self.root.configure(bg="#0F0F10")
        
        self.colors = {
            "bg": "#0F0F10", "card": "#1C1C1E", "accent": "#0A84FF",
            "success": "#30D158", "fail": "#FF453A", "text": "#FFFFFF"
        }
        
        self.ok_data = [] 
        self.setup_ui()
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """اضافه کردن منوی راست‌کلیک و حل مشکل کپی/پیست"""
        def make_menu(w):
            m = tk.Menu(self.root, tearoff=0, bg="#2C2C2E", fg="white", font=("Tahoma", 9))
            m.add_command(label="📋 کپی (Copy)", command=lambda: w.event_generate("<<Copy>>"))
            m.add_command(label="📝 چسباندن (Paste)", command=lambda: w.event_generate("<<Paste>>"))
            m.add_separator()
            m.add_command(label="انتخاب همه", command=lambda: w.event_generate("<<SelectAll>>"))
            w.bind("<Button-3>", lambda e: m.post(e.x_root, e.y_root))

        for w in [self.txt_input, self.txt_output]:
            make_menu(w)
            w.bind("<Control-v>", lambda e: w.event_generate("<<Paste>>"))
            w.bind("<Control-c>", lambda e: w.event_generate("<<Copy>>"))
            w.bind("<Control-a>", lambda e: w.event_generate("<<SelectAll>>"))

    def setup_ui(self):
        # هدر اصلی
        header = tk.Frame(self.root, bg=self.colors["accent"], height=55)
        header.pack(fill="x")
        tk.Label(header, text="SNI SCANNER PRO - v4.3 EXTREME", bg=self.colors["accent"], 
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=12)

        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # ---------------------------------------------------------
        # المان‌های پایینی (وضعیت و دکمه‌های خروجی)
        # ---------------------------------------------------------
        self.status = tk.Label(container, text="Ready 🟢", bg="#1C1C1E", fg="#8E8E93", anchor="w", padx=15, pady=5)
        self.status.pack(side="bottom", fill="x")

        export_frame = tk.Frame(container, bg=self.colors["bg"])
        export_frame.pack(side="bottom", fill="x", pady=10)

        self.btn_copy = tk.Button(export_frame, text="📋 کپی آی‌پی‌های تمیز", command=self.copy_results,
                                 bg="#2C2C2E", fg=self.colors["success"], font=("Tahoma", 9, "bold"),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_copy.pack(side="right", padx=5)

        self.btn_save = tk.Button(export_frame, text="💾 ذخیره در فایل", command=self.save_results,
                                 bg="#2C2C2E", fg="white", font=("Tahoma", 9),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=5)

        # ---------------------------------------------------------
        # المان‌های بالایی (ورودی، دکمه بارگذاری، اسکن و لاگ)
        # ---------------------------------------------------------
        input_header = tk.Frame(container, bg=self.colors["bg"])
        input_header.pack(side="top", fill="x")
        
        tk.Label(input_header, text="📥 ورودی آی‌پی یا دامنه (هر خط یکی):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(side="right")
        
        # بازگشت دکمه انتخاب فایل
        self.btn_load = tk.Button(input_header, text="📁 بارگذاری فایل (TXT)", command=self.load_file,
                                bg="#3A3A3C", fg="white", font=("Tahoma", 8),
                                relief="flat", padx=10, pady=2, cursor="hand2")
        self.btn_load.pack(side="left")

        self.txt_input = scrolledtext.ScrolledText(container, height=6, bg=self.colors["card"], 
                                                 fg="white", font=("Segoe UI", 11), borderwidth=0, padx=5, pady=5)
        self.txt_input.pack(side="top", fill="x", pady=5)

        self.btn_scan = tk.Button(container, text="🚀 شروع اسکن پرسرعت", command=self.start_scan,
                                bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", pady=10, cursor="hand2")
        self.btn_scan.pack(side="top", fill="x", pady=5)

        tk.Label(container, text="📊 گزارش اسکن:", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(side="top", anchor="e")
        
        self.txt_output = scrolledtext.ScrolledText(container, bg="black", font=("Consolas", 10), borderwidth=0, padx=5, pady=5)
        self.txt_output.pack(side="top", fill="both", expand=True, pady=5)

    def play_sound(self):
        try: winsound.Beep(500, 200); winsound.Beep(800, 250)
        except: pass

    def load_file(self):
        """تابع بارگذاری فایل تکست"""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.txt_input.delete("1.0", tk.END)
                self.txt_input.insert(tk.END, f.read())

    def start_scan(self):
        raw_lines = self.txt_input.get("1.0", tk.END).splitlines()
        
        # حذف فاصله‌های اضافی و خطوط خالی
        cleaned_lines = [t.strip() for t in raw_lines if t.strip()]
        
        # حذف خطوط تکراری با حفظ ترتیب ورود
        targets = list(dict.fromkeys(cleaned_lines))

        if not targets: return
        
        self.ok_data = []
        self.btn_scan.config(state="disabled", text="⌛ در حال اسکن...")
        self.txt_output.delete("1.0", tk.END)
        threading.Thread(target=self.run_logic, args=(targets,), daemon=True).start()

    def run_logic(self, targets):
        for target in targets:
            ips = [target] if re.match(r"^[0-9.]+$", target) else self.resolve(target)
            for ip in (ips or []):
                res = self.scan(ip)
                line = f"🌐 {target.ljust(22)} | {ip.ljust(15)} | {' '.join(res)}"
                if "✔️" in "".join(res):
                    self.ok_data.append(f"{target} | {ip}")
                    self.root.after(0, lambda l=line: self.print_log(l, "green"))
                else:
                    self.root.after(0, lambda l=line: self.print_log(l, "red"))
        self.root.after(0, self.finish)

    def resolve(self, d):
        try: return socket.gethostbyname_ex(d)[2]
        except: return []

    def scan(self, ip):
        def check(p):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.2); return (p, s.connect_ex((ip, p)) == 0)
            except: return (p, False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as ex:
            results = list(ex.map(check, PORTS))
        return [f"{p}{'✔️' if o else '❌'}" for p, o in sorted(results)]

    def print_log(self, text, tag):
        color = self.colors["success"] if tag == "green" else self.colors["fail"]
        self.txt_output.tag_config(tag, foreground=color)
        self.txt_output.insert(tk.END, text + "\n", tag)
        self.txt_output.see(tk.END)

    def finish(self):
        self.btn_scan.config(state="normal", text="🚀 شروع اسکن پرسرعت")
        self.status.config(text=f"✅ اسکن پایان یافت. {len(self.ok_data)} مورد موفق.")
        self.play_sound()

    def copy_results(self):
        if not self.ok_data:
            messagebox.showinfo("خالی", "مورد موفقی برای کپی وجود ندارد.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.ok_data))
        messagebox.showinfo("کپی شد", "لیست موارد موفق در کلیبورد ذخیره شد.")

    def save_results(self):
        if not self.ok_data:
            messagebox.showinfo("خالی", "مورد موفقی برای ذخیره وجود ندارد.")
            return
        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="Clean_IPs.txt")
        if f:
            with open(f, "w", encoding="utf-8") as file:
                file.write("=== SNI SCANNER RESULTS ===\n" + "\n".join(self.ok_data))
            messagebox.showinfo("ذخیره شد", "فایل با موفقیت ذخیره شد.")

if __name__ == "__main__":
    root = tk.Tk(); app = SNI_Scanner_v4_3(root); root.mainloop()
