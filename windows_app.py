import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import threading
import concurrent.futures
import re
import winsound  # مخصوص پخش صدا در ویندوز

# پورت‌های هدف
PORTS = [443, 2053, 2083, 2087, 2096, 8443]

class UltraScannerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SNI Ultra Scanner v2.0 - Special Edition")
        self.root.geometry("850x750")
        self.root.configure(bg="#1A1A1B")
        
        # رنگ‌بندی حرفه‌ای
        self.colors = {
            "bg": "#1A1A1B",
            "card": "#272729",
            "accent": "#00D1FF",
            "success": "#00FF66",
            "fail": "#FF4D4D",
            "text": "#FFFFFF"
        }
        
        self.setup_ui()

    def setup_ui(self):
        # هدر برنامه با ایموجی
        header_frame = tk.Frame(self.root, bg=self.colors["accent"], height=60)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="⚡ SNI ULTRA SCANNER PRO ⚡", bg=self.colors["accent"], 
                 fg="black", font=("Segoe UI", 16, "bold")).pack(pady=10)

        # بخش راهنما (Help)
        guide_frame = tk.LabelFrame(self.root, text=" 📖 راهنمای سریع / Guide ", bg=self.colors["bg"], 
                                   fg=self.colors["accent"], font=("Tahoma", 10, "bold"))
        guide_frame.pack(fill="x", padx=20, pady=10)
        
        guide_text = (
            "🔸 لیست آی‌پی‌ها یا دامنه‌ها را در باکس زیر وارد کنید (هر خط یکی)\n"
            "🔸 دکمه اسکن را بزنید تا وضعیت پورت‌های CDN بررسی شود\n"
            "🔸 علامت ✔️ به معنی باز بودن پورت (IP تمیز) و ❌ به معنی بسته بودن است"
        )
        tk.Label(guide_frame, text=guide_text, bg=self.colors["bg"], fg="#BBBBBB", 
                 justify="right", font=("Tahoma", 9), padx=10, pady=10).pack(anchor="e")

        # باکس ورودی
        input_label = tk.Label(self.root, text="📥 ورودی دامنه‌ها یا آی‌پی‌ها:", bg=self.colors["bg"], fg="white", font=("Tahoma", 10))
        input_label.pack(anchor="e", padx=20)
        
        self.txt_input = scrolledtext.ScrolledText(self.root, height=8, bg=self.colors["card"], 
                                                 fg="white", font=("Consolas", 11), borderwidth=0)
        self.txt_input.pack(fill="x", padx=20, pady=5)
        self.txt_input.insert(tk.END, "104.19.229.21\nexample.com")

        # دکمه‌ها
        btn_frame = tk.Frame(self.root, bg=self.colors["bg"])
        btn_frame.pack(fill="x", padx=20, pady=15)

        self.btn_scan = tk.Button(btn_frame, text="🚀 شروع اسکن سریع (Start Scan)", command=self.start_scan,
                                bg=self.colors["accent"], fg="black", font=("Segoe UI", 11, "bold"),
                                relief="flat", padx=40, pady=8, cursor="hand2")
        self.btn_scan.pack(side="right")

        self.btn_load = tk.Button(btn_frame, text="📁 انتخاب فایل", command=self.load_file,
                                bg="#444", fg="white", font=("Segoe UI", 10),
                                relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_load.pack(side="left")

        # خروجی نهایی
        output_label = tk.Label(self.root, text="📊 نتایج اسکن (Results):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10))
        output_label.pack(anchor="e", padx=20)
        
        self.txt_output = scrolledtext.ScrolledText(self.root, bg="#000000", fg=self.colors["success"], 
                                                  font=("Consolas", 10), borderwidth=0)
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=10)

        self.status_bar = tk.Label(self.root, text="آماده به کار 🟢", bg="#222", fg="white", anchor="w", padx=10)
        self.status_bar.pack(fill="x")

    def play_sound(self, type):
        try:
            if type == "start":
                winsound.Beep(600, 150)
            elif type == "end":
                winsound.Beep(800, 200)
                winsound.Beep(1000, 300)
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
            messagebox.showwarning("خطا", "لطفاً ابتدا لیست اهداف را وارد کنید!")
            return
        
        self.play_sound("start")
        self.btn_scan.config(state="disabled", text="⌛ در حال اسکن...")
        self.txt_output.delete("1.0", tk.END)
        self.status_bar.config(text="🔍 در حال اسکن... لطفاً صبور باشید", fg=self.colors["accent"])
        
        threading.Thread(target=self.run_logic, args=(targets,), daemon=True).start()

    def run_logic(self, targets):
        # منطق اسکن با سرعت بالا
        ok_res, fail_res = [], []
        for target in targets:
            ips = [target] if re.match(r"^[0-9.]+$", target) else self.resolve(target)
            for ip in (ips or []):
                ports_res = self.scan_all_ports(ip)
                line = f"🌐 {target} ({ip}) -> {' '.join(ports_res)}"
                if any("✔️" in s for s in ports_res): ok_res.append(line)
                else: fail_res.append(line)
        
        self.root.after(0, self.finish_ui, ok_res, fail_res)

    def resolve(self, domain):
        try: return socket.gethostbyname_ex(domain)[2]
        except: return []

    def scan_all_ports(self, ip):
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
        self.txt_output.insert(tk.END, "✅ موارد موفق (آی‌پی‌های تمیز):\n", "green")
        for line in ok: self.txt_output.insert(tk.END, line + "\n")
        
        self.txt_output.insert(tk.END, "\n❌ موارد ناموفق:\n", "red")
        for line in fail: self.txt_output.insert(tk.END, line + "\n")
        
        self.txt_output.tag_config("green", foreground=self.colors["success"])
        self.txt_output.tag_config("red", foreground=self.colors["fail"])
        
        self.status_bar.config(text="✅ اسکن با موفقیت به پایان رسید", fg=self.colors["success"])
        self.btn_scan.config(state="normal", text="🚀 شروع اسکن سریع (Start Scan)")
        self.play_sound("end")

if __name__ == "__main__":
    root = tk.Tk()
    app = UltraScannerPro(root)
    root.mainloop()
