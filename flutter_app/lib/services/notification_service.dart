import 'dart:async';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'api_service.dart';

/// Polling-based push usando flutter_local_notifications.
/// Cada 30s consulta el endpoint de no leídas y muestra las nuevas.
class NotificationService {
  static final FlutterLocalNotificationsPlugin _plugin =
    FlutterLocalNotificationsPlugin();
  static Timer? _timer;
  static int _lastSeenId = 0;
  static bool _initialized = false;

  static Future<void> init() async {
    if (_initialized) return;
    _initialized = true;
    const init = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
    );
    await _plugin.initialize(init);
    // Pide permisos en Android 13+
    final android = _plugin.resolvePlatformSpecificImplementation<
      AndroidFlutterLocalNotificationsPlugin>();
    await android?.requestNotificationsPermission();
  }

  static void startPolling() {
    stopPolling();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _poll());
    _poll();
  }

  static void stopPolling() {
    _timer?.cancel(); _timer = null;
  }

  static Future<void> _poll() async {
    try {
      final r = await ApiService.get(
        '/api/v1/notificaciones?leida=false&per_page=10');
      final list = (r['data'] as List).cast<Map<String, dynamic>>();
      // Procesar de más antiguas a más nuevas
      final nuevas = list.where((n) => (n['id'] as int) > _lastSeenId).toList()
        ..sort((a, b) => (a['id'] as int).compareTo(b['id'] as int));
      for (final n in nuevas) {
        await _show(n);
        _lastSeenId = n['id'] as int;
      }
    } catch (_) { /* silencioso */ }
  }

  static Future<void> _show(Map<String, dynamic> n) async {
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'matute_general', 'Notificaciones',
        channelDescription: 'Avisos de Matute Guide',
        importance: Importance.high, priority: Priority.high,
      ),
    );
    await _plugin.show(
      n['id'] as int,
      n['titulo'] as String,
      n['cuerpo'] as String? ?? '',
      details,
    );
  }
}
