import 'package:flutter/material.dart';
import '../theme/colors.dart';
import '../theme/text_styles.dart';

class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final String? meta;
  const StatCard({super.key, required this.label, required this.value, this.meta});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: MapColors.surface0,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: MapColors.line200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(),
              style: MapText.mono(10, w: FontWeight.w700,
                                  color: MapColors.ink600)),
          const SizedBox(height: 8),
          Text(value, style: MapText.display(28, w: FontWeight.w700)),
          if (meta != null) ...[
            const SizedBox(height: 8),
            Text(meta!, style: MapText.b12.copyWith(color: MapColors.ink600)),
          ],
        ],
      ),
    );
  }
}
