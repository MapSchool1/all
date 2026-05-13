import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/text_styles.dart';

class StatusBadge extends StatelessWidget {
  final String label;
  final Color color;
  const StatusBadge(this.label, {super.key, required this.color});

  factory StatusBadge.fromEstado(String estado) {
    return StatusBadge(estado.replaceAll('_', ' '),
      color: MapColors.statusColor(estado));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(label.toUpperCase(),
        style: MapText.mono(10, w: FontWeight.w700, color: color)),
    );
  }
}
