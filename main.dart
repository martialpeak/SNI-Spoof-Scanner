import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
      title: 'SNI Scanner Offline',
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
  
  final List<String> _cleanIps = []; 
  
  bool _isScanning = false;
  String _statusMessage = "وضعیت: آماده به کار 🟢";
  Color _statusColor = Colors.grey;

  // ---------------------------------------------------------
  // دیتابیس آفلاین رنج آی‌پی‌های (CIDR) معروف
  // ---------------------------------------------------------
  final Map<String, List<String>> _offlineProviders = {
    '☁️ Cloudflare': [
      '173.245.0.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22', 
      '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20', 
      '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13', 
      '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22'
    ],
    '⚡ Fastly': [
      '151.101.0.0/16', '199.232.0.0/16', '146.75.0.0/16', '199.27.72.0/21'
    ],
    '☁️ ArvanCloud': [
      '185.143.232.0/22', '185.228.228.0/22', '2.146.0.0/21', '94.182.160.0/21', '178.220.208.0/21'
    ],
    '🌐 Google': [
      '34.0.0.0/10', '35.192.0.0/12', '35.224.0.0/12', '104.154.0.0/15'
    ],
    '📦 Amazon/AWS': [
      '13.32.0.0/15', '13.224.0.0/14', '18.64.0.0/14', '52.46.0.0/18'
    ],
    '🔥 G-Core': [
      '92.38.128.0/18', '185.156.116.0/22'
    ]
  };

  // تبدیل IP به عدد برای محاسبه ریاضی آفلاین
  int ipToInt(String ip) {
    try {
      List<String> parts = ip.split('.');
      if (parts.length != 4) return 0;
      return (int.parse(parts[0]) * 16777216) +
             (int.parse(parts[1]) * 65536) +
             (int.parse(parts[2]) * 256) +
             int.parse(parts[3]);
    } catch (e) {
      return 0;
    }
  }

  // بررسی اینکه آیا یک آی‌پی در یک رنج خاص (مثل 104.16.0.0/12) قرار دارد یا خیر
  bool inCidr(int ip, String cidr) {
    try {
      List<String> parts = cidr.split('/');
      int network = ipToInt(parts[0]);
      int prefix = int.parse(parts[1]);
      int wildcard = (pow(2, 32 - prefix).toInt()) - 1;
      int broadcast = network + wildcard;
      return ip >= network && ip <= broadcast;
    } catch (e) {
      return false;
    }
  }

  // موتور جستجوی آفلاین آی‌پی
  String getOfflineProvider(String ip) {
    int targetIp = ipToInt(ip);
    for (var provider in _offlineProviders.entries) {
      for (var cidr in provider.value) {
        if (inCidr(targetIp, cidr)) {
          return provider.key;
        }
      }
    }
    return '❓ نامشخص';
  }

  Future<MapEntry<int, bool>> checkPort(String ip, int port) async {
    try {
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
      
      if (results.any((e) => e.value)) {
        // شناسایی آنی و ۱۰۰٪ آفلاین
        String provider = getOfflineProvider(ip);
        
        String line = "🌐 $target\n↳ $ip | $provider | $resStr";
        _logMessage(line, Colors.greenAccent);
        
        _cleanIps.add("$ip\t# $provider"); 
      } else {
        String line = "🌐 $target\n↳ $ip | $resStr";
        _logMessage(line, Colors.redAccent);
      }
    }
  }

  Future<void> runScan(List<String> targets) async {
    _cleanIps.clear();
    const int chunkSize = 10;
    
    for (int i = 0; i < targets.length; i += chunkSize) {
      if (!mounted || !_isScanning) break; 
      
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
              const Text("📱 SNI Scanner Offline Pro", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue), textAlign: TextAlign.center),
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
                  : const Text("🚀 شروع اسکن هوشمند (آفلاین)", style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 5),
              OutlinedButton.icon(
                onPressed: _isScanning ? null : _copyCleanIps,
                icon: const Icon(Icons.copy, color: Colors.greenAccent),
                label: const Text("کپی آی‌پی‌های تمیز + نام شرکت", style: TextStyle(color: Colors.greenAccent)),
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
                      child: SelectableText(log.message, style: TextStyle(color: log.color, fontFamily: 'monospace', fontSize: 13)),
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
