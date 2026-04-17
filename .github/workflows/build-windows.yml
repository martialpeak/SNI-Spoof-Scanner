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

class SNI_Pro_Final_V4:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SNI Scanner Pro v4.0 - Stable Edition")
        self.root.geometry("900x800")
        self.root.configure(bg="#0F0F10")
        
        self.colors = {
            "bg": "#0F0F10", "card": "#1C1C1E", "accent": "#0A84FF",
            "success": "#30D158", "fail": "#FF453A", "text": "#FFFFFF"
        }
        
        self.clean_ips = [] # لیست نتایج موفق برای کپی
        self.setup_ui()
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """فعال‌سازی کپی/پیست سیستمی"""
        for widget in [self.txt_input, self.txt_output]:
            widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))
            widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))
            widget.bind("<Control-a>", lambda e: widget.event_generate("<<SelectAll>>"))

    def setup_ui(self):
        # هدر برنامه
        header = tk.Frame(self.root, bg=self.colors["accent"], height=55)
        header.pack(fill="x")
        tk.Label(header, text="💎 SNI SCANNER PRO - v4.0", bg=self.colors["accent"], 
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)

        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # ورودی
        tk.Label(container, text="📥 ورودی آی‌پی یا دامنه:", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e")
        self.txt_input = scrolledtext.ScrolledText(container, height=7, bg=self.colors["card"], 
                                                 fg="white", font=("Segoe UI", 11), borderwidth=0, padx=10, pady=10)
        self.txt_input.pack(fill="x", pady=5)

        # دکمه شروع
        self.btn_scan = tk.Button(container, text="⚡ شروع اسکن پرسرعت", command=self.start_scan,
                                bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", pady=8, cursor="hand2")
        self.btn_scan.pack(fill="x", pady=10)

        # لاگ خروجی
        tk.Label(container, text="📊 گزارش اسکن:", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e")
        self.txt_output = scrolledtext.ScrolledText(container, bg="#000000", font=("Consolas", 10), borderwidth=0, padx=10, pady=10)
        self.txt_output.pack(fill="both", expand=True, pady=5)

        # پنل دکمه‌های ابزار (فریم جدید)
        tools_frame = tk.Frame(container, bg=self.colors["bg"])
        tools_frame.pack(fill="x", pady=10)

        self.btn_copy = tk.Button(tools_frame, text="📋 کپی آی‌پی‌های تمیز", command=self.copy_ok_results,
                                 bg="#2C2C2E", fg=self.colors["success"], font=("Tahoma", 9, "bold"),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_copy.pack(side="right", padx=5)

        self.btn_save = tk.Button(tools_frame, text="💾 ذخیره در فایل", command=self.save_to_file,
                                 bg="#2C2C2E", fg="white", font=("Tahoma", 9),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=5)

        self.status = tk.Label(self.root, text="Ready 🟢", bg="#1C1C1E", fg="#8E8E93", anchor="w", padx=15, pady=5)
        self.status.pack(fill="x")

    def play_sound(self, mode="end"):
        try:
            if mode == "end":
                winsound.Beep(500, 150); winsound.Beep(700, 200)
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
                res_ports = self.scan_ports(ip)
                line = f"🌐 {target.ljust(22)} | {ip.ljust(15)} | {' '.join(res_ports)}"
                if "✔️" in "".join(res_ports):
                    self.clean_ips.append(f"{target} | {ip}")
                    self.root.after(0, lambda l=line: self.log_to_ui(l, "green"))
                else:
                    self.root.after(0, lambda l=line: self.log_to_ui(l, "red"))
        self.root.after(0, self.on_finish)

    def resolve(self, domain):
        try: return socket.gethostbyname_ex(domain)[2]
        except: return []

    def scan_ports(self, ip):
        def check(p):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.2); return (p, s.connect_ex((ip, p)) == 0)
            except: return (p, False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as ex:
            results = list(ex.map(check, PORTS))
        return [f"{p}{'✔️' if o else '❌'}" for p, o in sorted(results)]

    def log_to_ui(self, text, color_tag):
        color = self.colors["success"] if color_tag == "green" else self.colors["fail"]
        self.txt_output.tag_config(color_tag, foreground=color)
        self.txt_output.insert(tk.END, text + "\n", color_tag)
        self.txt_output.see(tk.END)

    def on_finish(self):
        self.btn_scan.config(state="normal", text="⚡ شروع اسکن پرسرعت")
        self.status.config(text=f"✅ اسکن تمام شد. {len(self.clean_ips)} مورد تمیز پیدا شد.")
        self.play_sound()

    def copy_ok_results(self):
        if not self.clean_ips: return
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(self.clean_ips))
        messagebox.showinfo("موفق", "لیست آی‌پی‌های تمیز کپی شد.")

    def save_to_file(self):
        if not self.clean_ips: return
        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="Clean_IPs.txt")
        if f:
            with open(f, "w", encoding="utf-8") as file:
                file.write("=== SNI SCANNER CLEAN IPs ===\n" + "\n".join(self.clean_ips))
            messagebox.showinfo("ذخیره", "نتایج با موفقیت ذخیره شد.")

if __name__ == "__main__":
    root = tk.Tk(); app = SNI_Pro_Final_V4(root); root.mainloop()
