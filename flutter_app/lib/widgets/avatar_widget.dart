import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/text_styles.dart';

class AppAvatar extends StatelessWidget {
  final String iniciales;
  final String? colorHex;
  final double size;
  const AppAvatar({super.key, required this.iniciales, this.colorHex,
                   this.size = 40});

  Color _parse(String hex) {
    final s = hex.replaceFirst('#', '');
    return Color(int.parse('FF$s', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size, height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: _parse(colorHex ?? '#172846'),
        shape: BoxShape.circle,
      ),
      child: Text(iniciales,
        style: MapText.display(size * 0.36,
          w: FontWeight.w600, color: MapColors.surface0)),
    );
  }
}
