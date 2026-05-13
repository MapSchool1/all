import 'package:flutter/material.dart';
import '../models/bloque.dart';
import '../theme/colors.dart';
import '../theme/text_styles.dart';

/// Widget de grilla horaria 6 días × 14 horas, scrollable.
class ScheduleGrid extends StatelessWidget {
  final List<Bloque> bloques;
  final void Function(Bloque)? onTap;
  final int horaMin;
  final int horaMax;

  const ScheduleGrid({
    super.key,
    required this.bloques,
    this.onTap,
    this.horaMin = 7,
    this.horaMax = 20,
  });

  static const dias = ['lun', 'mar', 'mie', 'jue', 'vie', 'sab'];
  static const labels = {
    'lun': 'Lun', 'mar': 'Mar', 'mie': 'Mié',
    'jue': 'Jue', 'vie': 'Vie', 'sab': 'Sáb',
  };
  static const cellH = 64.0;
  static const colW = 96.0;
  static const timeColW = 56.0;

  @override
  Widget build(BuildContext context) {
    final horas = List.generate(horaMax - horaMin + 1, (i) => horaMin + i);
    return SingleChildScrollView(
      scrollDirection: Axis.vertical,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Container(
          decoration: BoxDecoration(
            color: MapColors.surface0,
            border: Border.all(color: MapColors.line200),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            children: [
              // Header
              Row(
                children: [
                  _headerCell('Hora', timeColW),
                  ...dias.map((d) => _headerCell(labels[d]!, colW)),
                ],
              ),
              ...horas.map((h) => Row(
                children: [
                  Container(
                    width: timeColW, height: cellH,
                    alignment: Alignment.topRight,
                    padding: const EdgeInsets.all(6),
                    decoration: const BoxDecoration(
                      color: MapColors.surface100,
                      border: Border(
                        right: BorderSide(color: MapColors.line200),
                        top: BorderSide(color: MapColors.line200),
                      ),
                    ),
                    child: Text('${h.toString().padLeft(2, '0')}:00',
                        style: MapText.mono(10, color: MapColors.ink600)),
                  ),
                  ...dias.map((d) => _scheduleCell(d, h)),
                ],
              )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _headerCell(String text, double w) {
    return Container(
      width: w, height: 36, alignment: Alignment.center,
      decoration: const BoxDecoration(color: MapColors.navy800),
      child: Text(text.toUpperCase(),
          style: MapText.mono(11, w: FontWeight.w700, color: MapColors.surface0)),
    );
  }

  Widget _scheduleCell(String dia, int hora) {
    final bloque = bloques.cast<Bloque?>().firstWhere(
      (b) => b!.dia == dia && b.horaInicioH == hora,
      orElse: () => null);
    return Container(
      width: colW, height: cellH,
      decoration: const BoxDecoration(
        border: Border(
          right: BorderSide(color: MapColors.line200),
          top: BorderSide(color: MapColors.line200),
        ),
      ),
      child: bloque == null ? null : _bloqueWidget(bloque),
    );
  }

  Widget _bloqueWidget(Bloque b) {
    final color = b.conflicto
      ? MapColors.bloqueConflicto
      : MapColors.bloqueColor(b.tipoMateria);
    final textColor = (b.conflicto || b.tipoMateria == 'idiomas')
      ? MapColors.ink900 : MapColors.surface0;
    return GestureDetector(
      onTap: onTap == null ? null : () => onTap!(b),
      child: Container(
        margin: const EdgeInsets.all(2),
        height: cellH * b.duracionH - 4,
        padding: const EdgeInsets.all(6),
        clipBehavior: Clip.hardEdge,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(4),
          border: b.conflicto
              ? Border.all(color: MapColors.danger, width: 2)
              : null,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Flexible(
              child: Text(b.materiaNombre,
                maxLines: 2, overflow: TextOverflow.ellipsis,
                style: MapText.body(11, w: FontWeight.w700, color: textColor)),
            ),
            Text(b.salonCodigo,
              maxLines: 1, overflow: TextOverflow.ellipsis,
              style: MapText.mono(9, color: textColor.withValues(alpha: 0.85))),
            if (b.conflicto)
              Text('⚠ CONFLICTO',
                maxLines: 1, overflow: TextOverflow.ellipsis,
                style: MapText.mono(8, w: FontWeight.w700, color: MapColors.ink900)),
          ],
        ),
      ),
    );
  }
}
