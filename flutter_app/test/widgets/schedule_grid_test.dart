import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/models/bloque.dart';
import 'package:matute_guide/widgets/schedule_grid.dart';

Bloque _bloque({
  required int id, required String dia,
  required String hi, required String hf,
  bool conflicto = false,
  String tipo = 'tronco_comun',
  String materia = 'Cálculo I',
}) => Bloque(
  id: id, dia: dia, horaInicio: hi, horaFin: hf, conflicto: conflicto,
  materia: {'nombre': materia, 'nombre_corto': materia, 'tipo': tipo},
  salon: {'codigo': 'A-203'},
);

Widget _wrap(Widget child) => MaterialApp(
  home: Scaffold(
    body: SizedBox(width: 800, height: 600, child: child),
  ),
);

void main() {
  group('ScheduleGrid', () {
    testWidgets('renderiza headers de días', (tester) async {
      await tester.pumpWidget(_wrap(const ScheduleGrid(bloques: [])));
      for (final lbl in ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB']) {
        expect(find.text(lbl), findsOneWidget);
      }
      expect(find.text('HORA'), findsOneWidget);
    });

    testWidgets('renderiza la columna horaria 07:00 a 20:00', (tester) async {
      await tester.pumpWidget(_wrap(const ScheduleGrid(bloques: [])));
      // 07:00 está visible al cargar
      expect(find.text('07:00'), findsOneWidget);
      // Confirmar que hay columna horaria con varias entradas
      expect(find.text('10:00'), findsOneWidget);
    });

    testWidgets('renderiza un bloque con su materia', (tester) async {
      await tester.pumpWidget(_wrap(ScheduleGrid(
        bloques: [_bloque(id: 1, dia: 'lun', hi: '07:00', hf: '09:00')],
      )));
      expect(find.text('Cálculo I'), findsOneWidget);
      expect(find.text('A-203'), findsOneWidget);
    });

    testWidgets('bloque en conflicto muestra label CONFLICTO', (tester) async {
      await tester.pumpWidget(_wrap(ScheduleGrid(
        bloques: [_bloque(id: 7, dia: 'mie', hi: '11:00', hf: '13:00',
                          conflicto: true, materia: 'Programación Web')],
      )));
      expect(find.text('Programación Web'), findsOneWidget);
      expect(find.text('⚠ CONFLICTO'), findsOneWidget);
    });

    testWidgets('tap en bloque dispara onTap con el bloque correcto',
        (tester) async {
      Bloque? tapped;
      final b = _bloque(id: 7, dia: 'mie', hi: '11:00', hf: '13:00',
                        conflicto: true);
      await tester.pumpWidget(_wrap(ScheduleGrid(
        bloques: [b], onTap: (x) => tapped = x,
      )));
      await tester.tap(find.text('Cálculo I'));
      await tester.pump();
      expect(tapped, isNotNull);
      expect(tapped!.id, 7);
      expect(tapped!.conflicto, isTrue);
    });

    testWidgets('múltiples bloques se renderizan', (tester) async {
      await tester.pumpWidget(_wrap(ScheduleGrid(
        bloques: [
          _bloque(id: 1, dia: 'lun', hi: '07:00', hf: '09:00',
                  materia: 'Cálculo I'),
          _bloque(id: 2, dia: 'mar', hi: '09:00', hf: '11:00',
                  materia: 'Bases de Datos'),
        ],
      )));
      expect(find.text('Cálculo I'), findsOneWidget);
      expect(find.text('Bases de Datos'), findsOneWidget);
    });
  });
}
