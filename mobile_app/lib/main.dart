import 'package:flutter/material.dart';
import 'screens/verification_screen.dart';

void main() {
  runApp(const EcoPayApp());
}

class EcoPayApp extends StatelessWidget {
  const EcoPayApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EcoPay 5G',
      theme: ThemeData(primarySwatch: Colors.green, useMaterial3: true),
      home: const VerificationScreen(),
    );
  }
}
