import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Wrapper sobre SharedPreferences para tokens y datos de usuario.
class StorageService {
  static const _kAccess = 'mg_access';
  static const _kRefresh = 'mg_refresh';
  static const _kUser = 'mg_user';

  static Future<SharedPreferences> _prefs() => SharedPreferences.getInstance();

  static Future<String?> getAccess() async => (await _prefs()).getString(_kAccess);
  static Future<String?> getRefresh() async => (await _prefs()).getString(_kRefresh);

  static Future<void> saveTokens(String access, String refresh) async {
    final p = await _prefs();
    await p.setString(_kAccess, access);
    await p.setString(_kRefresh, refresh);
  }

  static Future<void> saveUser(Map<String, dynamic> user) async {
    final p = await _prefs();
    await p.setString(_kUser, json.encode(user));
  }

  static Future<Map<String, dynamic>?> getUser() async {
    final raw = (await _prefs()).getString(_kUser);
    if (raw == null) return null;
    try { return json.decode(raw) as Map<String, dynamic>; } catch (_) { return null; }
  }

  static Future<void> clear() async {
    final p = await _prefs();
    await p.remove(_kAccess);
    await p.remove(_kRefresh);
    await p.remove(_kUser);
  }
}
