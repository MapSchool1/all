import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'storage_service.dart';

/// Cliente HTTP central. Inyecta JWT, intenta refresh en 401 y reintenta
/// una vez antes de propagar el error.
class ApiException implements Exception {
  final int status;
  final String message;
  final String? code;
  final Map<String, dynamic>? body;
  ApiException(this.status, this.message, {this.code, this.body});
  @override
  String toString() => 'ApiException($status, $message)';
}

class ApiService {
  static Future<Map<String, dynamic>> _request(
    String method, String path, {
    Object? body,
    bool retry = true,
    bool requiresAuth = true,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}$path');
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (requiresAuth) {
      final token = await StorageService.getAccess();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    final encoded = body == null ? null : json.encode(body);
    final res = await _send(method, uri, headers, encoded);

    if (res.statusCode == 401 && retry && requiresAuth) {
      final ok = await _refresh();
      if (ok) {
        return _request(method, path, body: body, retry: false,
                        requiresAuth: requiresAuth);
      } else {
        await StorageService.clear();
      }
    }

    Map<String, dynamic> parsed = {};
    if (res.body.isNotEmpty) {
      try { parsed = json.decode(res.body) as Map<String, dynamic>; }
      catch (_) { parsed = {'raw': res.body}; }
    }
    if (res.statusCode >= 200 && res.statusCode < 300) return parsed;
    throw ApiException(
      res.statusCode,
      parsed['error']?.toString() ?? 'Error ${res.statusCode}',
      code: parsed['code']?.toString(),
      body: parsed,
    );
  }

  static Future<http.Response> _send(String method, Uri uri,
      Map<String, String> headers, String? body) {
    final client = http.Client();
    switch (method) {
      case 'GET': return client.get(uri, headers: headers).timeout(ApiConfig.timeout);
      case 'POST': return client.post(uri, headers: headers, body: body).timeout(ApiConfig.timeout);
      case 'PUT': return client.put(uri, headers: headers, body: body).timeout(ApiConfig.timeout);
      case 'DELETE': return client.delete(uri, headers: headers, body: body).timeout(ApiConfig.timeout);
      default: throw ArgumentError('Método no soportado: $method');
    }
  }

  static Future<bool> _refresh() async {
    final refresh = await StorageService.getRefresh();
    if (refresh == null) return false;
    try {
      final res = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/refresh'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $refresh',
        },
      ).timeout(ApiConfig.timeout);
      if (res.statusCode != 200) return false;
      final data = json.decode(res.body) as Map<String, dynamic>;
      await StorageService.saveTokens(
        data['access_token'] as String,
        (data['refresh_token'] as String?) ?? refresh,
      );
      return true;
    } catch (_) { return false; }
  }

  // === API pública ===
  static Future<Map<String, dynamic>> get(String path,
      {bool requiresAuth = true}) =>
      _request('GET', path, requiresAuth: requiresAuth);

  static Future<Map<String, dynamic>> post(String path, {Object? body,
      bool requiresAuth = true}) =>
      _request('POST', path, body: body, requiresAuth: requiresAuth);

  static Future<Map<String, dynamic>> put(String path, {Object? body}) =>
      _request('PUT', path, body: body);

  static Future<Map<String, dynamic>> delete(String path, {Object? body}) =>
      _request('DELETE', path, body: body);
}
