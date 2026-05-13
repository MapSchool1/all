// Test E2E: arrancar app → login con cuenta del seed → verificar dashboard
// con el conflicto Mié 11:00 visible.
//
// REQUISITOS para correr:
//  1. Backend Flask corriendo (`python run.py` desde el repo root) en :5001.
//  2. seed.py ejecutado al menos una vez para tener al estudiante Álvaro
//     con su horario que contiene el conflicto Mié 11:00.
//  3. Emulador Android disponible o dispositivo físico en la misma red.
//
// Cómo correrlo:
//   # Emulador (10.0.2.2 → host)
//   flutter test integration_test/login_flow_test.dart \
//     --dart-define=API_BASE=http://10.0.2.2:5001
//
//   # Dispositivo físico (cambia por tu IP local)
//   flutter test integration_test/login_flow_test.dart \
//     --dart-define=API_BASE=http://192.168.1.10:5001
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:matute_guide/main.dart';
import 'package:matute_guide/services/storage_service.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Flujo de login del estudiante', () {
    setUp(() async {
      // Garantiza que arrancamos sin sesión previa
      await StorageService.clear();
    });

    testWidgets('Álvaro inicia sesión y ve el conflicto Mié 11:00',
        (tester) async {
      await tester.pumpWidget(const MatuteGuideApp());
      await tester.pumpAndSettle(const Duration(seconds: 2));

      // === Pantalla de login visible ===
      expect(find.text('Inicia sesión'), findsOneWidget);
      expect(find.text('Iniciar sesión'), findsWidgets);

      // === Llenar credenciales del seed ===
      await tester.enterText(
        find.widgetWithText(TextField, 'Correo institucional'),
        'alvaro.diaz@alumnos.udg.mx',
      );
      await tester.enterText(
        find.widgetWithText(TextField, 'Contraseña'),
        'Estudiante1!',
      );
      await tester.pumpAndSettle();

      // === Tap en "Iniciar sesión" ===
      await tester.tap(find.widgetWithText(ElevatedButton, 'Iniciar sesión'));
      // Esperar a la respuesta de la API + navegación
      await tester.pumpAndSettle(const Duration(seconds: 5));

      // === Dashboard cargado: saludo personalizado ===
      expect(find.textContaining('¡Hola, Álvaro'), findsOneWidget);

      // === Verificar que la card "Conflictos" muestra al menos 1 ===
      expect(find.text('CONFLICTOS'), findsOneWidget);

      // === Banner amarillo de conflicto visible ===
      expect(
        find.textContaining('conflicto sin resolver'),
        findsOneWidget,
        reason: 'El dashboard debe mostrar el banner de conflicto.',
      );

      // === Navegar al tab Horario ===
      await tester.tap(find.text('Horario').first);
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // === En el horario debe aparecer el label "⚠ CONFLICTO" ===
      // (puede haber 2: uno por cada bloque solapado en mié 11:00)
      final conflictoFinder = find.textContaining('CONFLICTO');
      expect(conflictoFinder, findsWidgets,
          reason: 'El bloque de Mié 11:00 debe mostrarse marcado como conflicto.');
    }, timeout: const Timeout(Duration(minutes: 2)));
  });
}
