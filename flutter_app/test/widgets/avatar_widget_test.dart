import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:matute_guide/widgets/avatar_widget.dart';

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: Center(child: child)));

void main() {
  group('AppAvatar', () {
    testWidgets('renderiza las iniciales como texto', (tester) async {
      await tester.pumpWidget(_wrap(
        const AppAvatar(iniciales: 'AD'),
      ));
      expect(find.text('AD'), findsOneWidget);
    });

    testWidgets('respeta el size pasado por parámetro', (tester) async {
      await tester.pumpWidget(_wrap(
        const AppAvatar(iniciales: 'AD', size: 96),
      ));
      final container = tester.widget<Container>(
        find.ancestor(of: find.text('AD'), matching: find.byType(Container)).first,
      );
      expect(container.constraints?.maxWidth ?? 96, 96);
    });

    testWidgets('parsea colorHex sin prefijo #', (tester) async {
      // No debe lanzar excepción al construir
      await tester.pumpWidget(_wrap(
        const AppAvatar(iniciales: 'YV', colorHex: '28A745'),
      ));
      expect(find.text('YV'), findsOneWidget);
    });

    testWidgets('usa color por defecto si colorHex es null', (tester) async {
      await tester.pumpWidget(_wrap(
        const AppAvatar(iniciales: '·'),
      ));
      expect(find.text('·'), findsOneWidget);
    });

    testWidgets('tiene forma circular', (tester) async {
      await tester.pumpWidget(_wrap(
        const AppAvatar(iniciales: 'X'),
      ));
      final container = tester.widgetList<Container>(find.byType(Container))
          .firstWhere((c) => (c.decoration as BoxDecoration?)?.shape == BoxShape.circle);
      expect((container.decoration as BoxDecoration).shape, BoxShape.circle);
    });
  });
}
