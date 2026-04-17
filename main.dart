import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart'; // اضافه شدن برای قابلیت کپی

void main() {
  runApp(const SNIScannerApp());
}

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
  final List<ScanLog> _results = [];
  final List<int> ports = [443, 2053, 2083, 2087, 2096, 8443];
  
  // لیست اختصاصی برای ذخیره آی‌پی‌های تمیز جهت کپی
  final List<String> _cleanIps = []; 
  
  bool _isScanning = false;
  String _statusMessage = "وضعیت: آماده به کار 🟢";
  Color _statusColor = Colors.grey;

  Future<MapEntry<int, bool>> checkPort(String ip, int port) async {
    try {
      // افزایش تایم‌اوت به ۲ ثانیه برای پایداری بیشتر در اینترنت موبایل
      final socket = await Socket.connect(ip, port, timeout: const Duration(milliseconds: 2000));
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

  Future<void> processTarget(String target) async {
    List<String> ips = [];
    
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
        // اگر حتی یک پورت باز بود، آی‌پی به لیست تمیزها اضافه می‌شود
        _cleanIps.add(ip); 
      } else {
        _logMessage(line, Colors.redAccent);
      }
    }
  }

  Future<void> runScan(List<String> targets) async {
    _cleanIps.clear();
    
    // منطق اسکن دسته‌ای (Chunking) برای جلوگیری از خفگی شبکه گوشی
    // هر بار ۱۰ آی‌پی را با هم بررسی می‌کند
    const int chunkSize = 10;
    
    for (int i = 0; i < targets.length; i += chunkSize) {
      if (!mounted || !_isScanning) break; // امکان توقف وجود داشته باشد
      
      final end = (i + chunkSize < targets.length) ? i + chunkSize : targets.length;
      final chunk = targets.sublist(i, end);
      
      await Future.wait(chunk.map((t) => processTarget(t)));
    }

    if (!mounted) return;
    setState(() {
      _statusMessage = "✅ اسکن تمام شد. (${_cleanIps.length} آی‌پی تمیز)";
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
      _cleanIps.clear();
      _statusMessage = "🔍 در حال اسکن شبکه...";
      _statusColor = Colors.orange;
    });

    runScan(targets);
  }

  void _copyCleanIps() {
    if (_cleanIps.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("آی‌پی تمیزی برای کپی وجود ندارد!")),
      );
      return;
    }
    
    // کپی کردن آی‌پی‌ها در حافظه موقت گوشی (کلیپ‌بورد)
    Clipboard.setData(ClipboardData(text: _cleanIps.join('\n')));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text("${_cleanIps.length} آی‌پی تمیز با موفقیت کپی شد ✅"),
        backgroundColor: Colors.green.shade700,
      ),
    );
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
                  focusedBorder: const OutlineInputBorder(borderSide: BorderSide(color: Colors.blue)),
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
              const SizedBox(height: 5),
              
              // اضافه شدن دکمه کپی
              OutlinedButton.icon(
                onPressed: _isScanning ? null : _copyCleanIps,
                icon: const Icon(Icons.copy, color: Colors.greenAccent),
                label: const Text("کپی آی‌پی‌های تمیز", style: TextStyle(color: Colors.greenAccent)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.greenAccent),
                  minimumSize: const Size(double.infinity, 45)
                ),
              ),
              
              const SizedBox(height: 10),
              Text(_statusMessage, style: TextStyle(color: _statusColor, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              const Divider(color: Colors.white24, height: 20),
              Expanded(
                child: ListView.builder(
                  itemCount: _results.length,
                  itemBuilder: (context, index) {
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
