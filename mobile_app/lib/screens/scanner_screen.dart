import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  // Flag to ensure we only process the first successful scan
  bool _hasScanned = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Deposit QR'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: MobileScanner(
        onDetect: (BarcodeCapture capture) {
          if (_hasScanned) return;

          final List<Barcode> barcodes = capture.barcodes;
          if (barcodes.isNotEmpty) {
            final String? rawValue = barcodes.first.rawValue;

            if (rawValue != null) {
              setState(() {
                _hasScanned = true;
              });

              // Return the decoded JSON string back to the VerificationScreen
              Navigator.pop(context, rawValue);
            }
          }
        },
      ),
    );
  }
}
