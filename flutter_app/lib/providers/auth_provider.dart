import 'package:flutter/foundation.dart';
import '../models/user.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

class AuthProvider extends ChangeNotifier {
  AppUser? _user;
  bool _loading = true;

  AppUser? get user => _user;
  bool get loading => _loading;
  bool get isAuthenticated => _user != null;

  Future<void> bootstrap() async {
    final stored = await StorageService.getUser();
    if (stored != null) _user = AppUser.fromJson(stored);
    _loading = false;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    final j = await AuthService.login(email, password);
    _user = AppUser.fromJson(j);
    notifyListeners();
  }

  Future<void> register(Map<String, dynamic> data) async {
    final j = await AuthService.register(data);
    _user = AppUser.fromJson(j);
    notifyListeners();
  }

  Future<void> logout() async {
    await AuthService.logout();
    _user = null;
    notifyListeners();
  }
}
