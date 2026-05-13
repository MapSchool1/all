import 'api_service.dart';
import 'storage_service.dart';

class AuthService {
  static Future<Map<String, dynamic>> login(String email, String password) async {
    final r = await ApiService.post('/auth/login',
        body: {'email': email, 'password': password},
        requiresAuth: false);
    await StorageService.saveTokens(
      r['access_token'] as String, r['refresh_token'] as String);
    await StorageService.saveUser(r['user'] as Map<String, dynamic>);
    return r['user'] as Map<String, dynamic>;
  }

  static Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final r = await ApiService.post('/auth/register',
        body: data, requiresAuth: false);
    await StorageService.saveTokens(
      r['access_token'] as String, r['refresh_token'] as String);
    await StorageService.saveUser(r['user'] as Map<String, dynamic>);
    return r['user'] as Map<String, dynamic>;
  }

  static Future<void> logout() async {
    final refresh = await StorageService.getRefresh();
    if (refresh != null) {
      try {
        await ApiService.post('/auth/logout',
          body: {'refresh_token': refresh});
      } catch (_) {}
    }
    await StorageService.clear();
  }

  static Future<Map<String, dynamic>?> currentUser() => StorageService.getUser();
}
