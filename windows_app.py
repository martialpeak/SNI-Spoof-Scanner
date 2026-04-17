import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import threading
import concurrent.futures
import winsound
import ipaddress
import urllib.request
import urllib.error

# پورت‌های استاندارد CDN
PORTS = [443, 2053, 2083, 2087, 2096, 8443]

# دیتابیس آفلاین رنج آی‌پی‌ها (برای سرعت لحظه‌ای)
RAW_PROVIDERS = {
    '☁️ Cloudflare': ['173.245.0.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22', '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20', '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13', '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22'],
    '⚡ Fastly': ['151.101.0.0/16', '199.232.0.0/16', '146.75.0.0/16', '199.27.72.0/21'],
    '☁️ ArvanCloud': ['185.143.232.0/22', '185.228.228.0/22', '2.146.0.0/21', '94.182.160.0/21', '178.220.208.0/21'],
    '🌐 Google': ['34.0.0.0/10', '35.192.0.0/12', '35.224.0.0/12', '104.154.0.0/15'],
    '📦 Amazon/AWS': ['13.32.0.0/15', '13.224.0.0/14', '18.64.0.0/14', '52.46.0.0/18'],
    '🔥 G-Core': ['92.38.128.0/18', '185.156.116.0/22']
}
OFFLINE_PROVIDERS = {name: [ipaddress.ip_network(cidr, strict=False) for cidr in cidrs] for name, cidrs in RAW_PROVIDERS.items()}

class SNI_Scanner_vFinal:
    def __init__(self, root):
        self.root = root
        self.root.title("💎 SNI Scanner Pro Ultimate - Windows Edition")
        self.root.geometry("950x800")
        self.root.configure(bg="#0F0F10")
        
        self.colors = {
            "bg": "#0F0F10", "card": "#1C1C1E", "accent": "#0A84FF",
            "success": "#30D158", "fail": "#FF453A", "text": "#FFFFFF"
        }
        
        self.ok_data = [] 
        self.isp_cache = {} # حافظه کش برای سرعت فضایی
        
        self.setup_ui()
        self.setup_shortcuts()

    def setup_shortcuts(self):
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
        header = tk.Frame(self.root, bg=self.colors["accent"], height=55)
        header.pack(fill="x")
        tk.Label(header, text="SNI SCANNER ULTIMATE - WINDOWS", bg=self.colors["accent"], 
                 fg="white", font=("Segoe UI", 14, "bold")).pack(pady=12)

        container = tk.Frame(self.root, bg=self.colors["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=10)

        self.status = tk.Label(container, text="Ready 🟢", bg="#1C1C1E", fg="#8E8E93", anchor="w", padx=15, pady=5)
        self.status.pack(side="bottom", fill="x")

        export_frame = tk.Frame(container, bg=self.colors["bg"])
        export_frame.pack(side="bottom", fill="x", pady=10)

        self.btn_copy = tk.Button(export_frame, text="📋 کپی کامل آی‌پی‌های تمیز", command=self.copy_results,
                                 bg="#2C2C2E", fg=self.colors["success"], font=("Tahoma", 9, "bold"),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_copy.pack(side="right", padx=5)

        self.btn_save = tk.Button(export_frame, text="💾 ذخیره در فایل", command=self.save_results,
                                 bg="#2C2C2E", fg="white", font=("Tahoma", 9),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_save.pack(side="left", padx=5)

        input_header = tk.Frame(container, bg=self.colors["bg"])
        input_header.pack(side="top", fill="x", pady=5)
        
        tk.Label(input_header, text="📥 ورودی آی‌پی یا دامنه (هر خط یکی):", bg=self.colors["bg"], fg="white", font=("Tahoma", 10)).pack(side="right")
        
        self.btn_load = tk.Button(input_header, text="📁 بارگذاری فایل", command=self.load_file,
                                bg="#3A3A3C", fg="white", font=("Tahoma", 8),
                                relief="flat", padx=10, pady=2, cursor="hand2")
        self.btn_load.pack(side="left", padx=5)
        
        self.btn_test_ips = tk.Button(input_header, text="☁️ آی‌پی تست", command=self.load_default_cdns,
                                bg="#3A3A3C", fg="white", font=("Tahoma", 8),
                                relief="flat", padx=10, pady=2, cursor="hand2")
        self.btn_test_ips.pack(side="left")

        self.txt_input = scrolledtext.ScrolledText(container, height=6, bg=self.colors["card"], 
                                                 fg="white", font=("Segoe UI", 11), borderwidth=0, padx=5, pady=5)
        self.txt_input.pack(side="top", fill="x", pady=5)

        self.btn_scan = tk.Button(container, text="🚀 شروع اسکن هوشمند", command=self.start_scan,
                                bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                                relief="flat", pady=10, cursor="hand2")
        self.
