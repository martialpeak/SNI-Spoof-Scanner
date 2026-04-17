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

class SNI_Pro_Stable_V4:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SNI Scanner Pro v4.0 - Stable Edition")
        self.root.geometry("900x820")
        self.root.configure(bg="#0F0F10")
        
        self.colors = {
            "bg": "#0F0F10", "card": "#1C1C1E", "accent": "#0A84FF",
            "success": "#30D158", "fail": "#FF453A", "text": "#FFFFFF"
        }
        
        self.clean_ips = [] 
        self.setup_ui()
        self.setup_keyboard_fix()

    def setup_keyboard_fix(self):
        """حل مشکل کپی و پیست برای تمام ورودی‌ها"""
        for w in [self.txt_input, self.txt_output]:
            w.bind("<Control-v>", lambda e: e.widget.event_generate("<<Paste>>"))
            w.bind("<Control-c>", lambda e: e.widget.event_generate("<<Copy>>"))
            w.bind("<Control-a>", lambda e: e.widget.event_generate("<<SelectAll>>"))

    def setup_ui(self):
        # هدر اصلی
        header = tk.Frame(self.root, bg=self.colors["accent"], height=60)
        header.pack(fill="x")
        tk.Label(header, text="💎 SNI SCANNER PRO - v4.0 FINAL", bg=self.colors["accent"], 
                 fg="white", font=("Segoe UI", 15, "bold")).pack(pady=12)

        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=25, pady=10)

        # ورودی (تارگت‌ها)
        tk.Label(container, text="📥 ورودی آی‌پی یا دامنه (هر خط یکی):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e")
        self.txt_input = scrolledtext.ScrolledText(container, height=7, bg=self.colors["card"], 
                                                 fg="white", font=("Segoe UI", 11), borderwidth=0, padx=10, pady=10)
        self.txt_input.pack(fill="x", pady=5)

        # دکمه اسکن
        self.btn_scan = tk.Button(container, text="⚡ شروع اسکن پرسرعت", command=self.start_scan,
                                bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", pady=10, cursor="hand2")
        self.btn_scan.pack(fill="x", pady=10)

        # لاگ خروجی
        tk.Label(container, text="📊 گزارش لحظه‌ای اسکن:", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e")
        self.txt_output = scrolledtext.ScrolledText(container, bg="#000000", font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.txt_output.pack(fill="both", expand=True, pady=5)

        # پنل دکمه‌های خروجی (Export Panel)
        export_frame = tk.Frame(container, bg=self.colors["bg"])
        export_frame.pack(fill="x", pady=10)

        self.btn_copy = tk.Button(export_frame, text="📋 کپی آی‌پی‌های تمیز", command=self.copy_results,
                                 bg="#2C2C2E", fg=self.colors["success"], font=("Tahoma", 9, "bold"),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_copy.pack(side="right", padx=5)

        self.btn_save = tk.Button(export_frame, text="💾 ذخیره در فایل متنی", command=self.save_results,
                                 bg="#2C2C2E", fg="white", font=("Tahoma", 9),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=5)

        self.status = tk.Label(self.root, text="Ready 🟢", bg="#1C1C1E", fg="#8E8E93", anchor="w", padx=15, pady=5)
        self.status.pack(fill="x")

    def play_sound(self):
        try: winsound.Beep(500, 150); winsound.Beep(750, 200)
        except: pass

    def start_scan(self):
        targets = [t.strip() for t in self.txt_input.get("1.0", tk.END).splitlines() if t.strip()]
        if not targets: return
        self.clean_ips = []
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
                    self.clean_ips.append(f"{target} | {ip}")
                    self.root.after(0, lambda l=line: self.print_log(l, "green"))
                else:
                    self.root.after(0, lambda l=line: self.print_log(l, "red"))
        self.root.after(0, self.on_finish)

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

    def on_finish(self):
        self.btn_scan.config(state="normal", text="⚡ شروع اسکن پرسرعت")
        self.status.config(text=f"✅ اسکن پایان یافت. {len(self.clean_ips)} مورد موفق پیدا شد.")
        self.play_sound()

    def copy_results(self):
        if not self.clean_ips: return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.clean_ips))
        messagebox.showinfo("کپی شد", "لیست آی‌پی‌های تمیز در کلیبورد ذخیره شد.")

    def save_results(self):
        if not self.clean_ips: return
        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="Clean_IPs.txt")
        if f:
            with open(f, "w", encoding="utf-8") as file:
                file.write("=== SNI SCANNER RESULTS ===\n" + "\n".join(self.clean_ips))
            messagebox.showinfo("ذخیره شد", "فایل با موفقیت ذخیره شد.")

if __name__ == "__main__":
    root = tk.Tk(); app = SNI_Pro_Stable_V4(root); root.mainloop()
