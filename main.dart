import 'dart:async';
import 'dart:io';
import 'dart:math';
import 'dart:convert'; // اضافه شده برای API آنلاین
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:file_picker/file_picker.dart';
import 'package:share_plus/share_plus.dart';

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
      title: 'SNI Scanner Hybrid Pro',
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF121212),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.blue.shade700,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        ),
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

  // دیتابیس آفلاین آی‌پی‌ها برای سرعت لحظه‌ای
  final Map<String, List<String>> _offlineProviders = {
    '☁️ Cloudflare': ['173.245.0.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22', '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20', '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13', '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22'],
    '⚡ Fastly': ['151.101.0.0/16', '199.232.0.0/16', '146.75.0.0/16', '199.27.72.0/21'],
    '☁️ ArvanCloud': ['185.143.232.0/22', '185.228.228.0/22', '2.146.0.0/21', '94.182.160.0/21', '178.220.208.0/21'],
    '🌐 Google': ['34.0.0.0/10', '35.192.0.0/12', '35.224.0.0/12', '104.154.0.0/15'],
    '📦 Amazon/AWS': ['13.32.0.0/15', '13.224.0.0/14', '18.64.0.0/14', '52.46.0.0/18'],
    '🔥 G-Core': ['92.38.128.0/18', '185.156.116.0/22']
  };

  int ipToInt(String ip) {
    try {
      List<String> parts = ip.split('.');
      if (parts.length != 4) return 0;
      return (int.parse(parts[0]) * 16777216) + (int.parse(parts[1]) * 65536) + (int.parse(parts[2]) * 256) + int.parse(parts[3]);
    } catch (e) { return 0; }
  }

  bool inCidr(int ip, String cidr) {
    try {
      List<String> parts = cidr.split('/');
      int network = ipToInt(parts[0]);
      int prefix = int.parse(parts[1]);
      int wildcard = (pow(2, 32 - prefix).toInt()) - 1;
      return ip >= network && ip <= (network + wildcard);
    } catch (e) { return false; }
  }

  // موتور ترکیبی (Hybrid) برای تشخیص قطعی نام شرکت
  Future<String> getProviderHybrid(String ip) async {
    // مرحله اول: استعلام آفلاین (بدون قطعی و پرسرعت)
    int targetIp = ipToInt(ip);
    for (var provider in _offlineProviders.entries) {
      for (var cidr in provider.value) {
        if (inCidr(targetIp, cidr)) return provider.key;
      }
    }

    // مرحله دوم: استعلام آنلاین به عنوان پشتیبان
    try {
      final request = await HttpClient().getUrl(Uri.parse('https://api.iplocation.net/?ip=$ip'));
      final response = await request.close().timeout(const Duration(seconds: 2));
      
      if (response.statusCode == 200) {
        final responseBody = await response.transform(utf8.decoder).join();
        final data = jsonDecode(responseBody);
        String isp = data['isp']?.toString().trim() ?? '';
        
        if (isp.isEmpty) return '❓ نامشخص';
        
        String ispLower = isp.toLowerCase();
        if (ispLower.contains('cloudflare')) return '☁️ Cloudflare';
        if (ispLower.contains('amazon') || ispLower.contains('cloudfront')) return '📦 Amazon/AWS';
        if (ispLower.contains('fastly')) return '⚡ Fastly';
        if (ispLower.contains('arvan')) return '☁️ ArvanCloud';
        if (ispLower.contains('google')) return '🌐 Google';
        if (ispLower.contains('digitalocean')) return '💧 DigitalOcean';
        if (ispLower.contains('microsoft') || ispLower.contains('azure')) return '🪟 Azure';
        if (ispLower.contains('hetzner')) return '🔴 Hetzner';
        if (ispLower.contains('ovh')) return '🟣 OVH';
        
        return '🏢 ${isp.length > 15 ? isp.substring(0, 15) : isp}';
      }
    } catch (e) {
      // در صورت فیلتر بودن یا قطعی اینترنت
    }
    return '❓ نامشخص';
  }

  void _playSuccessAlert() {
    SystemSound.play(SystemSoundType.click);
    HapticFeedback.heavyImpact();
    Future.delayed(const Duration(milliseconds: 300), () {
      SystemSound.play(SystemSoundType.click);
      HapticFeedback.heavyImpact();
    });
  }

  Future<void> _loadFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['txt', 'csv']);
      if (result != null && result.files.single.path != null) {
        File file = File(result.files.single.path!);
        String contents = await file.readAsString();
        setState(() { _inputController.text = contents; });
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("✅ فایل با موفقیت بارگذاری شد"), backgroundColor: Colors.green));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("❌ خطا در خواندن فایل: $e"), backgroundColor: Colors.red));
    }
  }

  Future<void> _saveToFile() async {
    if (_cleanIps.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("آی‌پی تمیزی برای ذخیره وجود ندارد!")));
      return;
    }
    try {
      final String fileText = "=== SNI Clean IPs ===\n\n" + _cleanIps.join('\n');
      final directory = Directory.systemTemp;
      final file = File('${directory.path}/Clean_IPs.txt');
      await file.writeAsString(fileText);
      await Share.shareXFiles([XFile(file.path)], text: 'لیست آی‌پی‌های تمیز');
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("خطا در ذخیره فایل")));
    }
  }

  void _loadDefaultCDNs() {
    const String sampleData = "104.16.1.1\n151.101.1.1\n13.32.1.1\n185.143.232.1\n8.8.8.8";
    setState(() { _inputController.text = sampleData; });
  }

  Future<MapEntry<int, bool>> checkPort(String ip, int port) async {
    try {
      final socket = await Socket.connect(ip, port, timeout: const Duration(milliseconds: 2000));
      socket.destroy();
      return MapEntry(port, true);
    } catch (e) { return MapEntry(port, false); }
  }

  void _logMessage(String msg, Color color) {
    if (!mounted) return;
    setState(() { _results.add(ScanLog(msg, color)); });
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
        // گرفتن نام شرکت به صورت هیبریدی (دقیق)
        String provider = await getProviderHybrid(ip);
        _logMessage("🌐 $target\n↳ $ip | $provider | $resStr", Colors.greenAccent);
        
        // فرمت شیک برای کپی همراه با دامنه
        if (target == ip) {
          _cleanIps.add("$ip\t# $provider");
        } else {
          _cleanIps.add("$ip\t# $provider  [🌐 $target]");
        }
      } else {
        _logMessage("🌐 $target\n↳ $ip | ❓ مسدود | $resStr", Colors.redAccent);
      }
    }
  }

  Future<void> runScan(List<String> targets) async {
    _cleanIps.clear();
    // کاهش فشار روی شبکه اندروید با تنظیم 8 آی‌پی همزمان
    const int chunkSize = 8; 
    
    for (int i = 0; i < targets.length; i += chunkSize) {
      if (!mounted || !_isScanning) break; 
      final end = (i + chunkSize < targets.length) ? i + chunkSize : targets.length;
      await Future.wait(targets.sublist(i, end).map((t) => processTarget(t)));
    }

    if (!mounted) return;
    setState(() {
      _statusMessage = "✅ اسکن تمام شد. (${_cleanIps.length} آی‌پی تمیز)";
      _statusColor = Colors.green;
      _isScanning = false;
    });
    
    _playSuccessAlert();
  }

  void _startClick() {
    FocusScope.of(context).unfocus();
    final targets = _inputController.text.split('\n').map((e) => e.trim()).where((e) => e.isNotEmpty).toSet().toList();
    if (targets.isEmpty) {
      setState(() { _statusMessage = "⚠️ لیست خالی است!"; _statusColor = Colors.orange; });
      return;
    }
    setState(() {
      _isScanning = true; _results.clear(); _cleanIps.clear();
      _statusMessage = "🔍 در حال اسکن دقیق شبکه..."; _statusColor = Colors.orange;
    });
    runScan(targets);
  }

  void _copyCleanIps() {
    if (_cleanIps.isEmpty) return;
    Clipboard.setData(ClipboardData(text: _cleanIps.join('\n')));
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("${_cleanIps.length} نتیجه (همراه با دامنه) کپی شد ✅"), backgroundColor: Colors.green.shade700));
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
              const Text("📱 SNI Scanner Hybrid Pro", style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.blue), textAlign: TextAlign.center),
              const SizedBox(height: 15),
              
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isScanning ? null : _loadFile,
                      icon: const Icon(Icons.folder_open, size: 18),
                      label: const Text("فایل TXT"),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.grey.shade800),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isScanning ? null : _loadDefaultCDNs,
                      icon: const Icon(Icons.cloud_download, size: 18),
                      label: const Text("آی‌پی تست"),
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.grey.shade800),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              TextField(
                controller: _inputController,
                maxLines: 4, minLines: 3,
                decoration: const InputDecoration(
                  hintText: "دامنه‌ها یا آی‌پی‌ها را وارد کنید...",
                  border: OutlineInputBorder(),
                  focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: Colors.blue)),
                ),
              ),
              const SizedBox(height: 10),
              
              ElevatedButton(
                onPressed: _isScanning ? null : _startClick,
                style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                child: _isScanning 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text("🚀 شروع اسکن هوشمند (ترکیبی)", style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 8),
              
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isScanning ? null : _copyCleanIps,
                      icon: const Icon(Icons.copy, color: Colors.greenAccent, size: 18),
                      label: const Text("کپی کامل (با دامنه)", style: TextStyle(color: Colors.greenAccent)),
                      style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.greenAccent)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _isScanning ? null : _saveToFile,
                      icon: const Icon(Icons.save_alt, color: Colors.blueAccent, size: 18),
                      label: const Text("ذخیره در گوشی", style: TextStyle(color: Colors.blueAccent)),
                      style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.blueAccent)),
                    ),
                  ),
                ],
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
