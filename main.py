import flet as ft
import socket
import concurrent.futures
import re
import threading
import traceback

PORTS = [443, 2053, 2083, 2087, 2096, 8443]

def check_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            return (port, s.connect_ex((ip, port)) == 0)
    except:
        return (port, False)

def main(page: ft.Page):
    try:
        # تنظیمات پایه‌ای صفحه
        page.title = "SNI Scanner Mobile"
        page.theme_mode = ft.ThemeMode.DARK
        page.padding = 10
        
        # المان‌های رابط کاربری
        title = ft.Text("📱 SNI Scanner Android", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_400)
        
        txt_input = ft.TextField(
            multiline=True,
            min_lines=3,
            max_lines=4,
            hint_text="دامنه‌ها یا آی‌پی‌ها را وارد کنید...",
            border_color=ft.colors.BLUE_200
        )
        
        lbl_status = ft.Text("وضعیت: آماده به کار 🟢", color=ft.colors.GREY_400)
        
        # لیست نتایج داخل یک کانتینر امن
        lv_results = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        
        btn_scan = ft.ElevatedButton(
            text="🚀 شروع اسکن در گوشی", 
            bgcolor=ft.colors.BLUE_700, 
            color=ft.colors.WHITE,
            height=50,
            width=page.window_width # دکمه به عرض صفحه
        )

        def log_message(msg, text_color=ft.colors.WHITE):
            lv_results.controls.append(ft.Text(msg, color=text_color, selectable=True))
            page.update()

        def run_scan(targets):
            try:
                ok_count = 0
                for target in targets:
                    ips = []
                    if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", target):
                        ips = [target]
                    else:
                        try:
                            socket.setdefaulttimeout(3.0) 
                            ips = socket.gethostbyname_ex(target)[2]
                        except Exception:
                            log_message(f"❌ {target} -> کشف نشد", ft.colors.RED_400)
                            continue

                    for ip in ips:
                        results = []
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
                log_message(f"ERROR: {str(e)}", ft.colors.RED_ACCENT)
                lbl_status.value = "❌ خطا در اسکن"
                btn_scan.disabled = False
                page.update()

        def start_click(e):
            raw_lines = txt_input.value.splitlines() if txt_input.value else []
            targets = list(dict.fromkeys([t.strip() for t in raw_lines if t.strip()]))
            
            if not targets:
                # پیام ساده به جای اسنک‌بار که گاهی باگ دارد
                lbl_status.value = "⚠️ لیست خالی است!"
                lbl_status.color = ft.colors.ORANGE_400
                page.update()
                return

            btn_scan.disabled = True
            lv_results.controls.clear()
            lbl_status.value = "🔍 در حال اسکن شبکه..."
            lbl_status.color = ft.colors.ORANGE_400
            page.update()

            threading.Thread(target=run_scan, args=(targets,), daemon=True).start()

        btn_scan.on_click = start_click

        # ساختار امن برای اندروید (جلوگیری از صفحه سیاه)
        # استفاده از SafeArea و Column برای مدیریت درست ابعاد گرافیکی
        main_layout = ft.SafeArea(
            ft.Column(
                controls=[
                    title,
                    txt_input,
                    btn_scan,
                    lbl_status,
                    ft.Divider(color=ft.colors.WHITE24),
                    lv_results # چون Column خاصیت expand دارد، ListView اینجا گیر نمی‌کند
                ],
                expand=True # این خط کلیدی برای حل مشکل صفحه سیاه است
            )
        )

        page.add(main_layout)
        page.update() # آپدیت اجباری در زمان بوت شدن برنامه

    except Exception as boot_error:
        # اگر هر خطایی در گرافیک پیش بیاید، به جای صفحه سیاه این متن چاپ می‌شود
        page.add(ft.Text(f"CRITICAL BOOT ERROR:\n{str(boot_error)}", color=ft.colors.RED_500))
        page.update()

# اجرای برنامه
ft.app(target=main)
