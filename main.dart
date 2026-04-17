import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';

void main() {
  runApp(const SNIScannerApp());
}

// یک کلاس ساده برای نگهداری داده‌های لاگ (به جای ذخیره ویجت)
class ScanLog {
  final String message;
  final Color color;
  ScanLog(this.message, this.color);
}

class SNIScannerApp extends StatelessWidget {
  const SNIScannerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SNI Scanner Mobile',
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF121212),
      ),
      home: const ScannerHomePage(),
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
  final List<ScanLog> _results = []; // ذخیره داده به جای ویجت
  final List<int> ports = [443, 2053, 2083, 2087, 2096, 8443];
  
  bool _isScanning = false;
  String _statusMessage = "وضعیت: آماده به کار 🟢";
  Color _statusColor = Colors.grey;
  int _okCount = 0; // شمارنده سراسری

  Future<MapEntry<int, bool>> checkPort(String ip, int port) async {
    try {
      final socket = await Socket.connect(ip, port, timeout: const Duration(milliseconds: 1500));
      socket.destroy();
      return MapEntry(port, true);
    } catch (e) {
      return MapEntry(port, false);
    }
  }

  void _logMessage(String msg, Color color) {
    if (!mounted) return;
    setState(() {
      _results.add(ScanLog(msg, color));
    });
  }

  // تابع پردازش یک هدف به صورت مستقل
  Future<void> processTarget(String target) async {
    List<String> ips = [];
    
    // اعتبارسنجی قطعی آی‌پی بدون نیاز به Regex
    if (InternetAddress.tryParse(target) != null) {
      ips = [target];
    } else {
      try {
        final lookup = await InternetAddress.lookup(target).timeout(const Duration(seconds: 3));
        ips = lookup.map((e) => e.address).toList();
      } catch (e) {
        _logMessage("❌ $target -> کشف نشد", Colors.redAccent);
        return;
      }
    }

    for (var ip in ips) {
      List<Future<MapEntry<int, bool>>> futures = ports.map((p) => checkPort(ip, p)).toList();
      List<MapEntry<int, bool>> results = await Future.wait(futures);
      
      results.sort((a, b) => a.key.compareTo(b.key));
      
      String resStr = results.map((e) => "${e.key}${e.value ? '✔️' : '❌'}").join(" ");
      String line = "🌐 $target\n↳ $ip | $resStr";

      if (results.any((e) => e.value)) {
        _logMessage(line, Colors.greenAccent);
        _okCount++;
      } else {
        _logMessage(line, Colors.redAccent);
      }
    }
  }

  Future<void> runScan(List<String> targets) async {
    _okCount = 0;

    // اجرای همزمان (Concurrent) تمامی اهداف برای افزایش چشمگیر سرعت
    List<Future<void>> allTasks = targets.map((t) => processTarget(t)).toList();
    await Future.wait(allTasks);

    if (!mounted) return;
    setState(() {
      _statusMessage = "✅ اسکن تمام شد. ($_okCount آی‌پی تمیز)";
      _statusColor = Colors.green;
      _isScanning = false;
    });
  }

  void _startClick() {
    FocusScope.of(context).unfocus();
    final rawText = _inputController.text;
    final targets = rawText.split('\n').map((e) => e.trim()).where((e) => e.isNotEmpty).toSet().toList();

    if (targets.isEmpty) {
      setState(() {
        _statusMessage = "⚠️ لیست خالی است!";
        _statusColor = Colors.orange;
      });
      return;
    }

    setState(() {
      _isScanning = true;
      _results.clear();
      _statusMessage = "🔍 در حال اسکن شبکه (پرسرعت)...";
      _statusColor = Colors.orange;
    });

    runScan(targets);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text("📱 SNI Scanner Android", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue), textAlign: TextAlign.center),
              const SizedBox(height: 15),
              TextField(
                controller: _inputController,
                maxLines: 4, minLines: 3,
                decoration: InputDecoration(
                  hintText: "دامنه‌ها یا آی‌پی‌ها را وارد کنید...",
                  border: const OutlineInputBorder(),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.blue)),
                ),
              ),
              const SizedBox(height: 10),
              ElevatedButton(
                onPressed: _isScanning ? null : _startClick,
                style: ElevatedButton.styleFrom(backgroundColor: Colors.blue.shade700, foregroundColor: Colors.white, minimumSize: const Size(double.infinity, 50)),
                child: _isScanning 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("🚀 شروع اسکن در گوشی", style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 10),
              Text(_statusMessage, style: TextStyle(color: _statusColor, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              const Divider(color: Colors.white24, height: 20),
              Expanded(
                child: ListView.builder(
                  itemCount: _results.length,
                  itemBuilder: (context, index) {
                    // ویجت‌ها اینجا ساخته می‌شوند که بسیار بهینه‌تر است
                    final log = _results[index];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: SelectableText(log.message, style: TextStyle(color: log.color, fontFamily: 'monospace')),
                    );
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
