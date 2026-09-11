import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/deposit_model.dart';

class ResultScreen extends StatelessWidget {
  final String qrData;

  const ResultScreen({super.key, required this.qrData});

  @override
  Widget build(BuildContext context) {
    DepositModel? deposit;
    bool isError = false;

    try {
      final data = jsonDecode(qrData);
      deposit = DepositModel.fromJson(data);

      // MOCK DATABASE SAVE: Log statement represents the backend saving step
      debugPrint(
        "MOCK DB: Saving ${deposit.points} points for user to backend...",
      );
    } catch (e) {
      isError = true;
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Deposit Verified')),
      body: Center(
        child: isError || deposit == null
            ? const Text(
                'Error: Invalid QR payload',
                style: TextStyle(color: Colors.red),
              )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.cloud_done, color: Colors.green, size: 100),
                  const SizedBox(height: 20),
                  const Text(
                    'Database Save Mocked',
                    style: TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    'Material: ${deposit.wasteClass} (${deposit.weightGrams}g)',
                    style: const TextStyle(fontSize: 18),
                  ),
                  const SizedBox(height: 30),
                  Text(
                    '+${deposit.points} PTS',
                    style: const TextStyle(
                      fontSize: 48,
                      color: Colors.green,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 50),
                  ElevatedButton(
                    onPressed: () => Navigator.of(
                      context,
                    ).popUntil((route) => route.isFirst),
                    child: const Text('Return to Home'),
                  ),
                ],
              ),
      ),
    );
  }
}
