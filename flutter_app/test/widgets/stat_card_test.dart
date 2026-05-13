import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/widgets/stat_card.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

void main() {
  group('StatCard', () {
    testWidgets('renderiza label en mayúsculas y valor', (tester) async {
      await tester.pumpWidget(_wrap(
        const StatCard(label: 'Estudiantes', value: '14,218'),
      ));
      expect(find.text('ESTUDIANTES'), findsOneWidget);
      expect(find.text('14,218'), findsOneWidget);
    });

    testWidgets('renderiza meta cuando se pasa', (tester) async {
      await tester.pumpWidget(_wrap(
        const StatCard(
          label: 'Conflictos', value: '12', meta: 'Desde el lunes',
        ),
      ));
      expect(find.text('CONFLICTOS'), findsOneWidget);
      expect(find.text('12'), findsOneWidget);
      expect(find.text('Desde el lunes'), findsOneWidget);
    });

    testWidgets('NO renderiza meta cuando es null', (tester) async {
      await tester.pumpWidget(_wrap(
        const StatCard(label: 'Materias', value: '6'),
      ));
      expect(find.text('MATERIAS'), findsOneWidget);
      expect(find.text('6'), findsOneWidget);
      expect(find.byType(Text), findsNWidgets(2));
    });
  });
}
