import 'package:flutter/material.dart';
import 'dart:io';
import 'dart:async';

void main() {
  runApp(const SNIScannerApp());
}

class SNIScannerApp extends StatelessWidget {
  const SNIScannerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SNI Scanner Mobile',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF121212),
        primaryColor: Colors.blueAccent,
      ),
      home: const ScannerHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class ScannerHomePage extends StatefulWidget {
  const ScannerHomePage({super.key});

  @override
  State<ScannerHomePage> createState() => _ScannerHomePageState();
}

class _ScannerHomePageState extends State<ScannerHomePage> {
  final TextEditingController _inputController = TextEditingController();
  final List<Widget> _results = [];
  bool _isScanning = false;
  String _statusText = "وضعیت: آماده به کار 🟢";
  Color _statusColor = Colors.grey;

  final List<int> _ports = [443, 2053, 2083, 2087, 2096, 8443];

  void _logMessage(String message, Color color) {
    setState(() {
      _results.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 8.0),
          child: SelectableText(
            message,
            style: TextStyle(color: color, fontSize: 14, fontFamily: 'monospace'),
          ),
        ),
      );
    });
  }

  // تابع بررسی باز بودن پورت به صورت Asynchronous
  Future<MapEntry<int, bool>> _checkPort(String ip, int port) async {
    try {
      final socket = await Socket.connect(ip, port, timeout: const Duration(milliseconds: 1500));
      socket.destroy(); // بستن بلافاصله سوکت بعد از اتصال موفق
      return MapEntry(port, true);
    } catch (e) {
      return MapEntry(port, false);
    }
  }

  Future<void> _startScan() async {
    final rawInput = _inputController.text;
    final targets = rawInput.split('\n').map((e) => e.trim()).where((e) => e.isNotEmpty).toSet().toList();

    if (targets.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("لیست خالی است! لطفا تارگت وارد کنید.")),
      );
      return;
    }

    setState(() {
      _isScanning = true;
      _results.clear();
      _statusText = "🔍 در حال اسکن شبکه (کمی صبر کنید)...";
      _statusColor = Colors.orangeAccent;
    });

    int okCount = 0;
    final ipRegex = RegExp(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$");

    for (var target in targets) {
      List<String> ips = [];

      if (ipRegex.hasMatch(target)) {
        ips.add(target);
      } else {
        // DNS Lookup با پشتیبانی از Timeout برای جلوگیری از قفل شدن
        try {
          final addresses = await InternetAddress.lookup(target).timeout(const Duration(seconds: 3));
          ips = addresses.map((a) => a.address).toList();
        } catch (e) {
          _logMessage("❌ $target -> کشف نشد", Colors.redAccent);
          continue;
        }
      }

      for (var ip in ips) {
        // اجرای همزمان تمامی درخواست‌های پورت برای یک آی‌پی
        final futures = _ports.map((port) => _checkPort(ip, port)).toList();
        final results = await Future.wait(futures);

        // مرتب‌سازی نتایج بر اساس پورت
        results.sort((a, b) => a.key.compareTo(b.key));

        String resStr = results.map((e) => "${e.key}${e.value ? '✔️' : '❌'}").join(" ");
        String line = "🌐 $target\n↳ $ip | $resStr";

        bool isAnyOpen = results.any((element) => element.value);
        if (isAnyOpen) {
          _logMessage(line, Colors.greenAccent);
          okCount++;
        } else {
          _logMessage(line, Colors.redAccent);
        }
      }
    }

    setState(() {
      _statusText = "✅ اسکن تمام شد. ($okCount آی‌پی تمیز)";
      _statusColor = Colors.greenAccent;
      _isScanning = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                "📱 SNI Scanner Android",
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blueAccent),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _inputController,
                maxLines: 5,
                minLines: 4,
                textDirection: TextDirection.ltr,
                decoration: InputDecoration(
                  hintText: "دامنه‌ها یا آی‌پی‌ها را وارد کنید...",
                  border: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.blue.shade200),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.blue.shade200),
                  ),
                ),
              ),
              const SizedBox(height: 15),
              ElevatedButton(
                onPressed: _isScanning ? null : _startScan,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue.shade700,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(double.infinity, 50),
                ),
                child: _isScanning 
                    ? const SizedBox(
                        height: 20, width: 20, 
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)
                      )
                    : const Text("🚀 شروع اسکن در گوشی", style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 15),
              Text(
                _statusText,
                style: TextStyle(color: _statusColor, fontWeight: FontWeight.bold),
              ),
              const Divider(height: 30, color: Colors.white24),
              Expanded(
                child: ListView.builder(
                  itemCount: _results.length,
                  itemBuilder: (context, index) {
                    return _results[index];
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
