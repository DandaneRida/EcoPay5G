class DepositModel {
  final String wasteClass;
  final int weightGrams;
  final double points;

  DepositModel({
    required this.wasteClass,
    required this.weightGrams,
    required this.points,
  });

  factory DepositModel.fromJson(Map<String, dynamic> json) {
    return DepositModel(
      wasteClass: json['waste_class'] ?? 'UNKNOWN',
      weightGrams: json['weight_g'] ?? 0,
      points: (json['points'] ?? 0).toDouble(),
    );
  }
}
