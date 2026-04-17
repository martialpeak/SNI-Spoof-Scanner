import flet as ft
import socket
import concurrent.futures
import re
import threading

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

def main(page: ft.Page):
    page.title = "SNI Scanner"
    page.theme_mode = ft.ThemeMode.DARK # تم تاریک
    page.padding = 15

    title = ft.Text("SNI Scanner", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    
    txt_input = ft.TextField(
        multiline=True, 
        min_lines=6, 
        max_lines=6, 
        hint_text="Enter IPs or Domains (one per line)...\nExample:\n104.19.229.21\nexample.com",
        border_color=ft.colors.BLUE_400
    )
    
    lbl_status = ft.Text("Status: Ready", color=ft.colors.CYAN_200)
    
    lv_results = ft.ListView(expand=True, spacing=5, auto_scroll=True)

    def append_result(text, text_color=ft.colors.WHITE):
        lv_results.controls.append(ft.Text(text, color=text_color, selectable=True))
        page.update()

    def run_scan_logic(targets):
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

        lv_results.controls.clear()
        
        append_result("=== OK (at least one open port) ===", ft.colors.GREEN_400)
        for item in ok_list: append_result(item)
        
        append_result("\n=== FAIL (all ports closed) ===", ft.colors.RED_400)
        for item in fail_list: append_result(item)
        
        append_result("\n=== RESOLVE FAILED ===", ft.colors.ORANGE_400)
        for item in resolve_fail_list: append_result(item)

        lbl_status.value = "Status: Scan Completed!"
        lbl_status.color = ft.colors.GREEN_400
        btn_scan.disabled = False
        page.update()

    def on_start_scan(e):
        targets = [t.strip() for t in txt_input.value.splitlines() if t.strip()]
        if not targets:
            page.snack_bar = ft.SnackBar(ft.Text("Please enter at least one target!"), bgcolor=ft.colors.RED_900)
            page.snack_bar.open = True
            page.update()
            return

        btn_scan.disabled = True
        lv_results.controls.clear()
        lbl_status.value = "Status: Scanning concurrently..."
        lbl_status.color = ft.colors.RED_400
        page.update()

        threading.Thread(target=run_scan_logic, args=(targets,), daemon=True).start()

    btn_scan = ft.ElevatedButton(
        text="▶ Start Fast Scan", 
        on_click=on_start_scan, 
        bgcolor=ft.colors.BLUE_700, 
        color=ft.colors.WHITE,
        height=50
    )

    page.add(
        title,
        txt_input,
        btn_scan,
        lbl_status,
        ft.Divider(),
        lv_results
    )

ft.app(target=main)
