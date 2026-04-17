import flet as ft
import traceback
# انتقال تمام ایمپورت‌ها به بالای صفحه برای شناسایی توسط پکیجر اندروید
import socket
import threading
import concurrent.futures
import re

def main(page: ft.Page):
    # تنظیمات مخصوص موبایل
    page.title = "SNI Scanner Mobile"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    # ❌ خط page.scroll = "adaptive" حذف شد تا با ListView تداخل نکند

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
    
    # اینجا expand=True به درستی کار می‌کند چون صفحه دیگر بی‌نهایت نیست
    lv_results = ft.ListView(expand=True, spacing=10, auto_scroll=True)

    def log_message(msg, text_color=ft.colors.WHITE):
        lv_results.controls.append(ft.Text(msg, color=text_color, selectable=True))
        page.update()

    def run_scan(targets):
        try:
            PORTS = [443, 2053, 2083, 2087, 2096, 8443]

            def check_port(ip, port):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1.5) # تایم‌اوت کمی بیشتر برای اینترنت موبایل
                        return (port, s.connect_ex((ip, port)) == 0)
                except:
                    return (port, False)

            ok_count = 0
            for target in targets:
                ips = [target] if re.match(r"^[0-9.]+$", target) else []
                if not ips:
                    try:
                        ips = socket.gethostbyname_ex(target)[2]
                    except:
                        log_message(f"❌ {target} -> کشف نشد", ft.colors.RED_400)
                        continue

                for ip in ips:
                    # استفاده از ThreadPool سبک‌تر برای فشار نیامدن به پردازنده گوشی
                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                        futures = {ex.submit(check_port, ip, p): p for p in PORTS}
                        results = []
                        for f in concurrent.futures.as_completed(futures):
                            p, is_open = f.result()
                            results.append((p, is_open))
                    
                    # مرتب‌سازی پورت‌ها و ساخت متن خروجی
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
        # حذف تکراری‌ها و فاصله‌ها
        raw_lines = txt_input.value.splitlines()
        targets = list(dict.fromkeys([t.strip() for t in raw_lines if t.strip()]))
        
        if not targets:
            page.snack_bar = ft.SnackBar(ft.Text("لیست خالی است! لطفا تارگت وارد کنید."))
            page.snack_bar.open = True
            page.update()
            return

        btn_scan.disabled = True
        lv_results.controls.clear()
        lbl_status.value = "🔍 در حال اسکن شبکه (کمی صبر کنید)..."
        lbl_status.color = ft.colors.ORANGE_400
        page.update()

        # اجرای اسکن در Thread جداگانه برای جلوگیری از فریز شدن صفحه
        threading.Thread(target=run_scan, args=(targets,), daemon=True).start()

    btn_scan = ft.ElevatedButton(
        text="🚀 شروع اسکن در گوشی", 
        on_click=start_click, 
        bgcolor=ft.colors.BLUE_700, 
        color=ft.colors.WHITE,
        height=50
    )

    # چیدمان عناصر روی صفحه موبایل
    page.add(title, txt_input, btn_scan, lbl_status, ft.Divider(), lv_results)

# اجرای امن برنامه
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except Exception as main_e:
        print(f"CRITICAL BOOT ERROR: {main_e}")
