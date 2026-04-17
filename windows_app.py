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

class SNI_Scanner_Ultimate:
    def __init__(self, root):
        self.root = root
        self.root.title("💎 SNI Ultra Scanner v5.0 - Professional")
        self.root.geometry("900x850")
        self.root.configure(bg="#0F0F10")
        
        # پالت رنگی دقیق نسخه ۳ که زیبا بود
        self.colors = {
            "bg": "#0F0F10",
            "card": "#1C1C1E",
            "accent": "#0A84FF",
            "success": "#30D158",
            "fail": "#FF453A",
            "text": "#FFFFFF",
            "secondary": "#8E8E93"
        }
        
        self.ok_results = [] 
        self.setup_ui()
        self.enable_persian_clipboard()

    def enable_persian_clipboard(self):
        """حل قطعی مشکل کپی/پیست در کیبوردهای فارسی با منوی راست‌کلیک"""
        def make_menu(w):
            menu = tk.Menu(w, tearoff=0, bg="#2C2C2E", fg="white", font=("Tahoma", 9))
            menu.add_command(label="✂️ برش (Cut)", command=lambda: w.event_generate("<<Cut>>"))
            menu.add_command(label="📋 کپی (Copy)", command=lambda: w.event_generate("<<Copy>>"))
            menu.add_command(label="📝 چسباندن (Paste)", command=lambda: w.event_generate("<<Paste>>"))
            menu.add_separator()
            menu.add_command(label="انتخاب همه", command=lambda: w.event_generate("<<SelectAll>>"))
            w.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

        for widget in [self.txt_input, self.txt_output]:
            make_menu(widget)
            widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))
            widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))
            widget.bind("<Control-a>", lambda e: widget.event_generate("<<SelectAll>>"))

    def setup_ui(self):
        # هدر بالایی (دقیقاً مثل نسخه 3)
        header = tk.Frame(self.root, bg=self.colors["accent"], height=55)
        header.pack(fill="x")
        tk.Label(header, text="💎 SNI SCANNER PRO - ULTRA EDITION", bg=self.colors["accent"], 
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # فریم اصلی با حاشیه مناسب تا کادرها به لبه‌ها نچسبند
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill="both", expand=True, padx=25, pady=10)

        # راهنمای فارسی
        guide_label = tk.Label(main_container, text="📌 راهنما: دامنه‌ها را وارد کنید و اسکن را بزنید. موارد موفق سبز می‌شوند.", 
                              bg=self.colors["bg"], fg=self.colors["secondary"], font=("Tahoma", 9))
        guide_label.pack(anchor="e", pady=(0, 10))

        # بخش ورودی
        tk.Label(main_container, text="📥 ورودی اهداف (IP/Domain):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10, "bold")).pack(anchor="e")
        self.txt_input = scrolledtext.ScrolledText(main_container, height=7, bg=self.colors["card"], 
                                                 fg="white", font=("Segoe UI", 11), borderwidth=0, 
                                                 padx=10, pady=10, insertbackground="white")
        self.txt_input.pack(fill="x", pady=5)

        # پنل دکمه‌های عملیاتی (بازگشت دکمه انتخاب فایل)
        action_frame = tk.Frame(main_container, bg=self.colors["bg"])
        action_frame.pack(fill="x", pady=15)

        self.btn_scan = tk.Button(action_frame, text="⚡ شروع اسکن پرسرعت", command=self.start_scan,
                                bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", padx=30, pady=8, cursor="hand2")
        self.btn_scan.pack(side="right")

        self.btn_load = tk.Button(action_frame, text="📁 انتخاب فایل", command=self.load_file,
                                bg="#3A3A3C", fg="white", font=("Segoe UI", 10),
                                relief="flat", padx=15, pady=8, cursor="hand2")
        self.btn_load.pack(side="left")

        # بخش خروجی (Log)
        tk.Label(main_container, text="📊 گزارش لحظه‌ای (Logs):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10, "bold")).pack(anchor="e")
        self.txt_output = scrolledtext.ScrolledText(main_container, bg="black", font=("Consolas", 10), 
                                                  borderwidth=0, padx=10, pady=10)
        self.txt_output.pack(fill="both", expand=True, pady=5)

        # پنل ابزارهای کاربردی (Export Tools)
        export_frame = tk.Frame(main_container, bg=self.colors["bg"])
        export_frame.pack(fill="x", pady=10)

        self.btn_copy_ok = tk.Button(export_frame, text="📋 کپی موارد موفق", command=self.copy_to_clipboard,
                                   bg="#2C2C2E", fg=self.colors["success"], font=("Tahoma", 9, "bold"),
                                   relief="flat", padx=15, pady=8, cursor="hand2")
        self.btn_copy_ok.pack(side="right", padx=5)

        self.btn_save = tk.Button(export_frame, text="💾 ذخیره در فایل", command=self.save_to_file,
                                bg="#2C2C2E", fg="white", font=("Tahoma", 9),
                                relief="flat", padx=15, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=5)

        # استاتوس بار پایین
        self.status_bar = tk.Label(self.root, text="آماده به کار 🟢", bg="#1C1C1E", fg=self.colors["secondary"], anchor="w", padx=15, pady=5)
        self.status_bar.pack(fill="x")

    def play_sound(self, mode):
        try:
            if mode == "start": winsound.Beep(440, 100)
            elif mode == "end": 
                winsound.Beep(523, 150)
                winsound.Beep(659, 150)
        except: pass

    def load_file(self):
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file:
            with open(file, "r", encoding="utf-8") as f:
                self.txt_input.delete("1.0", tk.END)
                self.txt_input.insert(tk.END, f.read())

    def start_scan(self):
        raw_input = self.txt_input.get("1.0", tk.END).splitlines()
        targets = list(set([t.strip() for t in raw_input if t.strip()])) # حذف تکراری‌ها
        if not targets:
            messagebox.showwarning("ورودی خالی", "لطفاً ابتدا لیست آی‌پی‌ها یا دامنه‌ها را وارد کنید.")
            return
        
        self.ok_results = []
        self.play_sound("start")
        self.btn_scan.config(state="disabled", text="⌛ در حال پردازش...")
        self.txt_output.delete("1.0", tk.END)
        self.status_bar.config(text="🔍 اسکن در حال انجام است...", fg=self.colors["accent"])
        threading.Thread(target=self.run_logic, args=(targets,), daemon=True).start()

    def run_logic(self, targets):
        for target in targets:
            ips = [target] if re.match(r"^[0-9.]+$", target) else self.resolve(target)
            if not ips:
                self.root.after(0, lambda t=target: self.print_log(f"❌ {t} -> (کشف نشد/Resolve Failed)", "red"))
                continue
            
            for ip in ips:
                ports_res = self.scan_ports(ip)
                result_line = f"🌐 {target.ljust(22)} | {ip.ljust(15)} | {' '.join(ports_res)}"
                if any("✔️" in s for s in ports_res):
                    self.ok_results.append(f"{target} | {ip}")
                    self.root.after(0, lambda l=result_line: self.print_log(l, "green"))
                else:
                    self.root.after(0, lambda l=result_line: self.print_log(l, "red"))
        
        self.root.after(0, self.finish_scan)

    def resolve(self, domain):
        try: return socket.gethostbyname_ex(domain)[2]
        except: return []

    def scan_ports(self, ip):
        def check_port(port):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.5)
                    return (port, s.connect_ex((ip, port)) == 0)
            except: return (port, False)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as ex:
            results = list(ex.map(check_port, PORTS))
        return [f"{p}{'✔️' if o else '❌'}" for p, o in sorted(results)]

    def print_log(self, text, color_type):
        # این تابع از قاطی شدن رنگ سبز و قرمز جلوگیری می‌کند
        color = self.colors["success"] if color_type == "green" else self.colors["fail"]
        self.txt_output.tag_config(color_type, foreground=color)
        self.txt_output.insert(tk.END, text + "\n", color_type)
        self.txt_output.see(tk.END)

    def finish_scan(self):
        self.status_bar.config(text=f"✅ اسکن پایان یافت. {len(self.ok_results)} مورد تمیز یافت شد.", fg=self.colors["success"])
        self.btn_scan.config(state="normal", text="⚡ شروع اسکن پرسرعت")
        self.play_sound("end")

    def copy_to_clipboard(self):
        if not self.ok_results:
            messagebox.showinfo("خالی", "مورد موفقی برای کپی وجود ندارد.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.ok_results))
        messagebox.showinfo("کپی شد", "لیست آی‌پی‌های تمیز در کلیبورد ذخیره شد.")

    def save_to_file(self):
        if not self.ok_results:
            messagebox.showinfo("خالی", "دیتایی برای ذخیره وجود ندارد.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="Clean_IPs.txt", filetypes=[("Text Files", "*.txt")])
        if file:
            with open(file, "w", encoding="utf-8") as f:
                f.write("=== CLEAN IP RESULTS ===\n")
                f.write("\n".join(self.ok_results))
            messagebox.showinfo("ذخیره شد", f"فایل با موفقیت ذخیره شد.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SNI_Scanner_Ultimate(root)
    root.mainloop()
