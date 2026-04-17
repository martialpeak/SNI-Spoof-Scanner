import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import socket
import threading
import concurrent.futures
import re

PORTS = [443, 2053, 2083, 2087, 2096, 8443]

def is_ipv4(address): return re.match(r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$", address) is not None

def resolve_domain(domain):
    try: return socket.gethostbyname_ex(domain)[2]
    except socket.error: return []

def check_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return (port, s.connect_ex((ip, port)) == 0)
    except: return (port, False)

def scan_target_ports(ip):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as executor:
        futures = {executor.submit(check_port, ip, port): port for port in PORTS}
        for future in concurrent.futures.as_completed(futures):
            port, is_open = future.result()
            results[port] = is_open
    return results

class SNIScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SNI Scanner - Windows Edition")
        self.root.geometry("750x600")
        self.root.configure(padx=10, pady=10)

        input_frame = ttk.LabelFrame(self.root, text=" Targets (IPs or Domains) ")
        input_frame.pack(fill="x", pady=5)
        self.txt_input = scrolledtext.ScrolledText(input_frame, height=7, width=80)
        self.txt_input.pack(padx=5, pady=5)
        
        btn_frame = tk.Frame(input_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        self.btn_load = ttk.Button(btn_frame, text="Load targets.txt", command=self.load_file)
        self.btn_load.pack(side="left", padx=5)
        self.btn_scan = ttk.Button(btn_frame, text="▶ Start Fast Scan", command=self.start_scan)
        self.btn_scan.pack(side="right", padx=5)

        output_frame = ttk.LabelFrame(self.root, text=" Scan Results ")
        output_frame.pack(fill="both", expand=True, pady=5)
        self.txt_output = scrolledtext.ScrolledText(output_frame, height=15, width=80)
        self.txt_output.pack(padx=5, pady=5, fill="both", expand=True)
        self.lbl_status = ttk.Label(self.root, text="Status: Ready", foreground="blue")
        self.lbl_status.pack(anchor="w")

    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                self.txt_input.delete("1.0", tk.END)
                self.txt_input.insert(tk.END, f.read())

    def start_scan(self):
        targets = [t.strip() for t in self.txt_input.get("1.0", tk.END).splitlines() if t.strip()]
        if not targets:
            messagebox.showwarning("Warning", "Please enter at least one target!")
            return
        
        self.btn_scan.config(state="disabled")
        self.txt_output.delete("1.0", tk.END)
        self.lbl_status.config(text="Status: Scanning concurrently... Fasten your seatbelt!", foreground="red")
        threading.Thread(target=self.run_concurrent_scan, args=(targets,), daemon=True).start()

    def run_concurrent_scan(self, targets):
        ok_list, fail_list, resolve_fail_list = [], [], []

        for target in targets:
            ips = [target] if is_ipv4(target) else resolve_domain(target)
            if not ips:
                resolve_fail_list.append(target)
                continue

            for ip in ips:
                port_results = scan_target_ports(ip)
                result_str = ""
                open_found = False
                for port in sorted(port_results.keys()):
                    if port_results[port]:
                        result_str += f" {port}✔"
                        open_found = True
                    else:
                        result_str += f" {port}✖"
                
                output_line = f"{target} -> {ip} ->{result_str}"
                if open_found: ok_list.append(output_line)
                else: fail_list.append(output_line)

        self.root.after(0, self.display_results, ok_list, fail_list, resolve_fail_list)

    def display_results(self, ok_list, fail_list, resolve_fail_list):
        def append_text(text): self.txt_output.insert(tk.END, text + "\n")
        append_text("=== OK (at least one open port) ===")
        for item in ok_list: append_text(item)
        append_text("\n=== FAIL (all ports closed) ===")
        for item in fail_list: append_text(item)
        append_text("\n=== RESOLVE FAILED ===")
        for item in resolve_fail_list: append_text(item)
        self.lbl_status.config(text="Status: Fast Scan Completed!", foreground="green")
        self.btn_scan.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SNIScannerApp(root)
    root.mainloop()
