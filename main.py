package main

import (
	"fmt"
	"net"
	"strings"
	"sync"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/widget"
)

var ports = []int{443, 2053, 2083, 2087, 2096, 8443}
var timeout = 1500 * time.Millisecond

func main() {
	// ساخت اپلیکیشن و پنجره
	myApp := app.New()
	myWindow := myApp.NewWindow("SNI Scanner Mobile")

	// المان‌های رابط کاربری
	title := widget.NewLabelWithStyle("📱 SNI Scanner (Golang Edition)", fyne.TextAlignCenter, fyne.TextStyle{Bold: true})
	
	input := widget.NewMultiLineEntry()
	input.SetPlaceHolder("دامنه‌ها یا آی‌پی‌ها را وارد کنید (هر خط یکی)...")
	input.Wrapping = fyne.TextWrapWord

	status := widget.NewLabel("وضعیت: آماده به کار 🟢")
	
	resultsLabel := widget.NewLabel("")
	resultsLabel.Wrapping = fyne.TextWrapWord
	scrollArea := container.NewVScroll(resultsLabel) // قابل اسکرول کردن نتایج

	var isScanning bool

	// دکمه اسکن
	scanBtn := widget.NewButton("🚀 شروع اسکن پرسرعت", func() {
		if isScanning {
			return
		}

		// دریافت و تمیز کردن تارگت‌ها
		rawText := input.Text
		lines := strings.Split(rawText, "\n")
		var targets []string
		for _, line := range lines {
			t := strings.TrimSpace(line)
			if t != "" {
				targets = append(targets, t)
			}
		}

		if len(targets) == 0 {
			status.SetText("❌ لیست خالی است!")
			return
		}

		isScanning = true
		status.SetText("🔍 در حال اسکن با نهایت سرعت...")
		resultsLabel.SetText("") // پاک کردن نتایج قبلی

		// اجرای اسکن در بک‌گراند تا گرافیک قفل نشود
		go runScan(targets, status, resultsLabel, &isScanning)
	})

	// چیدمان عناصر روی صفحه
	topBox := container.NewVBox(title, input, scanBtn, status)
	content := container.NewBorder(topBox, nil, nil, nil, scrollArea)

	myWindow.SetContent(content)
	myWindow.Resize(fyne.NewSize(350, 600)) // اندازه پیش‌فرض موبایل
	myWindow.ShowAndRun()
}

// تابع اصلی اسکن همزمان
func runScan(targets []string, status *widget.Label, resultsLabel *widget.Label, isScanning *bool) {
	var wg sync.WaitGroup
	var mu sync.Mutex
	cleanCount := 0
	var outputBuilder strings.Builder

	// تابع کمکی برای آپدیت امن رابط کاربری
	updateUI := func(msg string) {
		mu.Lock()
		outputBuilder.WriteString(msg + "\n")
		currentText := outputBuilder.String()
		mu.Unlock()
		resultsLabel.SetText(currentText)
	}

	for _, target := range targets {
		wg.Add(1)
		go func(t string) {
			defer wg.Done()

			var ips []string
			if net.ParseIP(t) != nil {
				ips = []string{t}
			} else {
				resolved, err := net.LookupHost(t)
				if err != nil {
					updateUI(fmt.Sprintf("❌ %s -> کشف نشد", t))
					return
				}
				ips = resolved
			}

			for _, ip := range ips {
				res := scanPorts(ip)
				statusStr := ""
				isClean := false
				for _, p := range ports {
					if res[p] {
						statusStr += fmt.Sprintf("%d✔️ ", p)
						isClean = true
					} else {
						statusStr += fmt.Sprintf("%d❌ ", p)
					}
				}

				line := fmt.Sprintf("🌐 %s\n↳ %s | %s\n", t, ip, statusStr)
				updateUI(line)
				
				if isClean {
					mu.Lock()
					cleanCount++
					mu.Unlock()
				}
			}
		}(target)
	}

	wg.Wait()
	status.SetText(fmt.Sprintf("✅ پایان! %d آی‌پی تمیز پیدا شد.", cleanCount))
	*isScanning = false
}

// بررسی پورت‌ها
func scanPorts(ip string) map[int]bool {
	results := make(map[int]bool)
	var portWg sync.WaitGroup
	var mu sync.Mutex

	for _, port := range ports {
		portWg.Add(1)
		go func(p int) {
			defer portWg.Done()
			address := fmt.Sprintf("%s:%d", ip, p)
			conn, err := net.DialTimeout("tcp", address, timeout)

			mu.Lock()
			if err != nil {
				results[p] = false
			} else {
				results[p] = true
				conn.Close()
			}
			mu.Unlock()
		}(port)
	}
	portWg.Wait()
	return results
}
