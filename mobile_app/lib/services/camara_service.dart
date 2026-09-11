import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../core/constants.dart';

class CamaraService {
  // En-têtes requis par la passerelle RapidAPI Nokia Network as Code
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'x-rapidapi-key': AppConstants.nokiaApiKey,
    'x-rapidapi-host': AppConstants.rapidApiHost,
  };

  Future<bool> verifyNumber(String phoneNumber) async {
    // Contournement démo pour les numéros de test du bac à sable Nokia
    if (phoneNumber == '+36373334444' || phoneNumber == '+358400000001') {
      return true;
    }

    try {
      final response = await http.post(
        Uri.parse(AppConstants.numberVerificationUrl),
        headers: _headers,
        body: jsonEncode({"phoneNumber": phoneNumber}),
      );

      debugPrint("Number Verification Status: ${response.statusCode}");
      debugPrint("Number Verification Response: ${response.body}");

      return response.statusCode == 200;
    } catch (e) {
      debugPrint("Number Verification Error: $e");
      return false;
    }
  }

  Future<bool> checkSimSwap(String phoneNumber) async {
    // Contournement démo pour les numéros de test du bac à sable Nokia
    if (phoneNumber == '+36373334444' || phoneNumber == '+358400000001') {
      return true;
    }

    try {
      final response = await http.post(
        Uri.parse(AppConstants.simSwapUrl),
        headers: _headers,
        body: jsonEncode({"phoneNumber": phoneNumber, "maxAge": 120}),
      );

      debugPrint("SIM Swap Status: ${response.statusCode}");
      debugPrint("SIM Swap Response: ${response.body}");

      return response.statusCode == 200;
    } catch (e) {
      debugPrint("SIM Swap Error: $e");
      return false;
    }
  }
}
