import 'package:flutter/material.dart';
import '../services/camara_service.dart';
import 'scanner_screen.dart';
import 'result_screen.dart';

class VerificationScreen extends StatefulWidget {
  const VerificationScreen({super.key});

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  final TextEditingController _phoneController = TextEditingController(
    text: '+358400000001',
  );
  final CamaraService _camaraService = CamaraService();

  bool _isLoading = false;
  String _statusMessage = '';

  Future<void> _processVerification() async {
    final phone = _phoneController.text;
    if (phone.isEmpty) return;

    setState(() {
      _isLoading = true;
      _statusMessage = 'Calling CAMARA Number Verification...';
    });

    bool isNumberValid = await _camaraService.verifyNumber(phone);

    setState(() {
      _statusMessage = 'Calling CAMARA SIM Swap Check...';
    });

    bool isSimSafe = await _camaraService.checkSimSwap(phone);

    setState(() {
      _isLoading = false;
    });

    debugPrint(
      'Security Check - Number Valid: $isNumberValid | SIM Safe: $isSimSafe',
    );

    if (!mounted) return;

    // Strict validation: Stop processing if security checks fail
    if (!isNumberValid || !isSimSafe) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Security verification failed. Invalid number or SIM swapped.',
          ),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Proceed to QR scanner only if verification passes
    final qrResult = await Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const ScannerScreen()),
    );

    if (qrResult != null && mounted) {
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultScreen(qrData: qrResult as String),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('EcoPay 5G - Security')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Icon(Icons.shield, size: 80, color: Colors.green),
            const SizedBox(height: 20),
            TextField(
              controller: _phoneController,
              decoration: const InputDecoration(
                labelText: 'Phone Number (E.164)',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.phone),
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 20),
            if (_isLoading) ...[
              const Center(child: CircularProgressIndicator()),
              const SizedBox(height: 10),
              Text(_statusMessage, textAlign: TextAlign.center),
            ] else
              ElevatedButton.icon(
                onPressed: _processVerification,
                icon: const Icon(Icons.qr_code_scanner),
                label: const Text('Verify Identity & Scan'),
              ),
          ],
        ),
      ),
    );
  }
}
