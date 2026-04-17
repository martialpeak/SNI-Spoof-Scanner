import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import threading
import concurrent.futures
import re
import winsound

PORTS = [443, 2053, 2083, 2087, 2096, 8443]

class UltraScannerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SNI Ultra Scanner v2.5 - Professional Edition")
        self.root.geometry("850x780")
        self.root.configure(bg="#1A1A1B")
        
        # رنگ‌بندی اصلاح شده
        self.colors = {"bg": "#1A1A1B", "card": "#272729", "accent": "#00D1FF", 
                       "success": "#00FF66", "fail": "#FF4D4D", "text": "#FFFFFF"}
        
        self.setup_ui()
        self.fix_shortcuts() # حل مشکل کپی/پیست

    def fix_shortcuts(self):
        # فعال کردن کپی، پیست و انتخاب همه برای ویندوز
        self.txt_input.bind("<Control-v>", lambda e: self.txt_input.event_generate("<<Paste>>"))
        self.txt_input.bind("<Control-c>", lambda e: self.txt_input.event_generate("<<Copy>>"))
        self.txt_input.bind("<Control-a>", lambda e: self.txt_input.event_generate("<<SelectAll>>"))

    def setup_ui(self):
        # هدر
        header = tk.Frame(self.root, bg=self.colors["accent"], height=60)
        header.pack(fill="x")
        tk.Label(header, text="⚡ SNI ULTRA SCANNER PRO ⚡", bg=self.colors["accent"], 
                 fg="black", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # بخش راهنمای فارسی (راست‌چین شده)
        guide_frame = tk.LabelFrame(self.root, text=" 📖 راهنمای کاربری ", bg=self.colors["bg"], 
                                   fg=self.colors["accent"], font=("Tahoma", 10, "bold"), labelanchor="ne")
        guide_frame.pack(fill="x", padx=20, pady=10)
        
        guide_text = (
            "• آی‌پی‌ها یا دامنه‌ها را در باکس زیر وارد کنید (هر خط یک مورد) 📝\n"
            "• دکمه اسکن را بزنید تا وضعیت پورت‌های CDN بررسی شود 🔍\n"
            "• علامت ✔️ یعنی پورت باز (آی‌پی تمیز) و ❌ یعنی پورت بسته است 🛡️"
        )
        tk.Label(guide_frame, text=guide_text, bg=self.colors["bg"], fg="#BBBBBB", 
                 justify="right", font=("Tahoma", 9), padx=10, pady=10).pack(anchor="e")

        # ورودی
        tk.Label(self.root, text="📥 لیست اهداف (Targets):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e", padx=20)
        self.txt_input = scrolledtext.ScrolledText(self.root, height=8, bg=self.colors["card"], 
                                                 fg="white", font=("Consolas", 11), borderwidth=0, undo=True)
        self.txt_input.pack(fill="x", padx=20, pady=5)

        # دکمه‌ها
        btn_frame = tk.Frame(self.root, bg=self.colors["bg"])
        btn_frame.pack(fill="x", padx=20, pady=15)

        self.btn_scan = tk.Button(btn_frame, text="🚀 شروع اسکن سریع", command=self.start_scan,
                                bg=self.colors["accent"], fg="black", font=("Segoe UI", 11, "bold"),
                                relief="flat", padx=40, pady=8, cursor="hand2")
        self.btn_scan.pack(side="right")

        self.btn_load = tk.Button(btn_frame, text="📁 انتخاب فایل", command=self.load_file,
                                bg="#444", fg="white", font=("Segoe UI", 10),
                                relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_load.pack(side="left")

        # خروجی
        tk.Label(self.root, text="📊 نتایج نهایی (Results):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(anchor="e", padx=20)
        self.txt_output = scrolledtext.ScrolledText(self.root, bg="#000000", font=("Consolas", 10), borderwidth=0)
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=10)

        self.status_bar = tk.Label(self.root, text="آماده به کار 🟢", bg="#222", fg="white", anchor="w", padx=10)
        self.status_bar.pack(fill="x")

    def play_sound(self, sound_type):
        try:
            if sound_type == "start": winsound.Beep(600, 150)
            elif sound_type == "end": 
                winsound.Beep(800, 150)
                winsound.Beep(1100, 200)
        except: pass

    def load_file(self):
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file:
            with open(file, "r", encoding="utf-8") as f:
                self.txt_input.delete("1.0", tk.END)
                self.txt_input.insert(tk.END, f.read())

    def start_scan(self):
        targets = [t.strip() for t in self.txt_input.get("1.0", tk.END).splitlines() if t.strip()]
        if not targets:
            messagebox.showwarning("خطا", "لطفاً ابتدا لیست را پر کنید!")
            return
        
        self.play_sound("start")
        self.btn_scan.config(state="disabled", text="⌛ در حال بررسی...")
        self.txt_output.delete("1.0", tk.END)
        self.status_bar.config(text="🔍 در حال اسکن پورت‌ها...", fg=self.colors["accent"])
        threading.Thread(target=self.run_logic, args=(targets,), daemon=True).start()

    def run_logic(self, targets):
        ok_res, fail_res = [], []
        for target in targets:
            ips = [target] if re.match(r"^[0-9.]+$", target) else self.resolve(target)
            for ip in (ips or []):
                ports_res = self.scan_ports(ip)
                line = f"🌐 {target.ljust(20)} -> {ip.ljust(15)} | {' '.join(ports_res)}"
                if any("✔️" in s for s in ports_res): ok_res.append(line)
                else: fail_res.append(line)
        self.root.after(0, self.finish_ui, ok_res, fail_res)

    def resolve(self, domain):
        try: return socket.gethostbyname_ex(domain)[2]
        except: return []

    def scan_ports(self, ip):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as ex:
            futures = {ex.submit(self.check_port, ip, p): p for p in PORTS}
            for f in concurrent.futures.as_completed(futures):
                p, is_open = f.result()
                results.append(f"{p}{'✔️' if is_open else '❌'}")
        return sorted(results)

    def check_port(self, ip, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.2)
                return (port, s.connect_ex((ip, port)) == 0)
        except: return (port, False)

    def finish_ui(self, ok, fail):
        # تنظیم رنگ‌بندی دقیق
        self.txt_output.tag_config("green_tag", foreground=self.colors["success"])
        self.txt_output.tag_config("red_tag", foreground=self.colors["fail"])
        self.txt_output.tag_config("white_tag", foreground="white")

        self.txt_output.insert(tk.END, "✅ موارد موفق (IP CLEAN):\n", "green_tag")
        for line in ok: self.txt_output.insert(tk.END, line + "\n", "white_tag")
        
        self.txt_output.insert(tk.END, "\n❌ موارد ناموفق (CLOSED):\n", "red_tag")
        for line in fail: self.txt_output.insert(tk.END, line + "\n", "white_tag")
        
        self.status_bar.config(text="✅ پایان اسکن", fg=self.colors["success"])
        self.btn_scan.config(state="normal", text="🚀 شروع اسکن سریع")
        self.play_sound("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = UltraScannerPro(root)
    root.mainloop()
