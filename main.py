import flet as ft
import socket
import concurrent.futures
import re
import threading
import traceback

# پورت‌های استاندارد اسکن
PORTS = [443, 2053, 2083, 2087, 2096, 8443]

def check_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5) # تایم‌اوت برای اینترنت موبایل
            result = s.connect_ex((ip, port))
            return (port, result == 0)
    except:
        return (port, False)

def main(page: ft.Page):
    # تنظیمات مخصوص موبایل
    page.title = "SNI Scanner Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "adaptive"

    # هدر برنامه
    title = ft.Text("📱 SNI Scanner Android", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
    
    # باکس ورودی
    txt_input = ft.TextField(
        multiline=True,
        min_lines=4,
        max_lines=5,
        hint_text="دامنه‌ها یا آی‌پی‌ها را وارد کنید...",
        border_color=ft.colors.BLUE_200,
        text_align=ft.TextAlign.LEFT
    )
    
    lbl_status = ft.Text("وضعیت: آماده به کار 🟢", color=ft.colors.GREY_400)
    lv_results = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    # تعریف دکمه (عملکرد آن در پایین‌تر مشخص می‌شود)
    btn_scan = ft.ElevatedButton(
        text="🚀 شروع اسکن در گوشی", 
        bgcolor=ft.colors.BLUE_700, 
        color=ft.colors.WHITE,
        height=50
    )

    def log_message(msg, text_color=ft.colors.WHITE):
        lv_results.controls.append(ft.Text(msg, color=text_color, selectable=True))
        page.update()

    def run_scan(targets):
        try:
            ok_count = 0
            
            for target in targets:
                ips = []
                # بررسی اینکه ورودی آی‌پی است یا دامنه
                if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", target):
                    ips = [target]
                else:
                    try:
                        # جلوگیری از قفل شدن برنامه روی دامنه‌های فیلتر شده یا نامعتبر
                        socket.setdefaulttimeout(3.0) 
                        ips = socket.gethostbyname_ex(target)[2]
                    except Exception:
                        log_message(f"❌ {target} -> کشف نشد یا فیلتر است", ft.colors.RED_400)
                        continue

                for ip in ips:
                    results = []
                    # استفاده اصولی از ThreadPool برای بررسی سریع پورت‌ها
                    with concurrent.futures.ThreadPoolExecutor(max_workers=len(PORTS)) as ex:
                        futures = {ex.submit(check_port, ip, p): p for p in PORTS}
                        for f in concurrent.futures.as_completed(futures):
                            results.append(f.result())
                    
                    results.sort(key=lambda x: x[0])
                    res_str = " ".join([f"{p}{'✔️' if o else '❌'}" for p, o in results])
                    
                    line = f"🌐 {target}\n↳ {ip} | {res_str}"
                    if any(o for p, o in results):
                        log_message(line, ft.colors.GREEN_400)
                        ok_count += 1
                    else:
                        log_message(line, ft.colors.RED_400)

            lbl_status.value = f"✅ اسکن تمام شد. ({ok_count} آی‌پی تمیز)"
            lbl_status.color = ft.colors.GREEN_400
            btn_scan.disabled = False
            page.update()

        except Exception as e:
            log_message(f"SYSTEM ERROR:\n{str(e)}\n{traceback.format_exc()}", ft.colors.RED_ACCENT)
            lbl_status.value = "❌ خطا در اجرای اسکن"
            btn_scan.disabled = False
            page.update()

    def start_click(e):
        raw_lines = txt_input.value.splitlines()
        targets = list(dict.fromkeys([t.strip() for t in raw_lines if t.strip()]))
        
        if not targets:
            page.snack_bar = ft.SnackBar(ft.Text("لیست خالی است! لطفا تارگت وارد کنید."))
            page.snack_bar.open = True
            page.update()
            return

        # غیرفعال کردن دکمه هنگام اسکن
        btn_scan.disabled = True
        lv_results.controls.clear()
        lbl_status.value = "🔍 در حال اسکن شبکه (کمی صبر کنید)..."
        lbl_status.color = ft.colors.ORANGE_400
        page.update()

        # اجرای اسکن در پس‌زمینه برای هنگ نکردن رابط کاربری
        threading.Thread(target=run_scan, args=(targets,), daemon=True).start()

    # اتصال رویداد کلیک به دکمه
    btn_scan.on_click = start_click

    # اضافه کردن المان‌ها به صفحه
    page.add(title, txt_input, btn_scan, lbl_status, ft.Divider(), lv_results)

# اجرای برنامه
try:
    ft.app(target=main)
except Exception as main_e:
    print(f"CRITICAL BOOT ERROR: {main_e}")
