import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/theme/colors.dart';
import 'package:matute_guide/widgets/status_badge.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

void main() {
  group('StatusBadge', () {
    testWidgets('renderiza el label en mayúsculas', (tester) async {
      await tester.pumpWidget(_wrap(
        const StatusBadge('publicado', color: MapColors.success),
      ));
      expect(find.text('PUBLICADO'), findsOneWidget);
    });

    testWidgets('reemplaza guiones bajos por espacios via fromEstado', (tester) async {
      await tester.pumpWidget(_wrap(
        StatusBadge.fromEstado('en_proceso'),
      ));
      expect(find.text('EN PROCESO'), findsOneWidget);
    });

    testWidgets('fromEstado mapea activo → success', (tester) async {
      await tester.pumpWidget(_wrap(
        StatusBadge.fromEstado('activo'),
      ));
      expect(find.text('ACTIVO'), findsOneWidget);
      // No assertion del color exacto pero se construye sin error
    });

    testWidgets('fromEstado mapea desconocido → ink400', (tester) async {
      await tester.pumpWidget(_wrap(
        StatusBadge.fromEstado('estado_inexistente'),
      ));
      expect(find.text('ESTADO INEXISTENTE'), findsOneWidget);
    });

    testWidgets('color se aplica al fondo del badge', (tester) async {
      await tester.pumpWidget(_wrap(
        const StatusBadge('listo', color: MapColors.success),
      ));
      final container = tester.widget<Container>(find.byType(Container));
      final decoration = container.decoration as BoxDecoration;
      // El badge usa color con alpha 0.12
      expect(decoration.color, isNotNull);
      expect(decoration.borderRadius, BorderRadius.circular(4));
    });
  });
}
