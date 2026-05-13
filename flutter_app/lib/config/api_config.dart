/// Configuración del backend. Para emuladores Android usa 10.0.2.2 (host loopback).
class ApiConfig {
  // Para emulador Android, 10.0.2.2 mapea al host del Mac.
  // Cambia a la IP local del Mac (e.g. 192.168.1.10) para dispositivo físico.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://10.0.2.2:5001',
  );
  static const Duration timeout = Duration(seconds: 15);
}
