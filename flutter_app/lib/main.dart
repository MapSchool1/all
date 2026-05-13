import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'screens/admin/admin_dashboard_screen.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/register_screen.dart';
import 'screens/profesor/profesor_dashboard_screen.dart';
import 'screens/student/dashboard_screen.dart';
import 'services/notification_service.dart';
import 'theme/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await NotificationService.init();
  runApp(const MatuteGuideApp());
}

class MatuteGuideApp extends StatelessWidget {
  const MatuteGuideApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider()..bootstrap(),
      child: Builder(builder: (ctx) {
        final auth = ctx.watch<AuthProvider>();
        if (auth.loading) {
          return const MaterialApp(
            home: Scaffold(body: Center(child: CircularProgressIndicator())));
        }
        // Arranca/detiene polling de notificaciones según sesión
        if (auth.isAuthenticated) {
          NotificationService.startPolling();
        } else {
          NotificationService.stopPolling();
        }
        return MaterialApp.router(
          title: 'Matute Guide',
          debugShowCheckedModeBanner: false,
          theme: buildTheme(),
          routerConfig: _router(auth),
        );
      }),
    );
  }

  GoRouter _router(AuthProvider auth) {
    return GoRouter(
      initialLocation: auth.isAuthenticated ? _destFor(auth) : '/login',
      refreshListenable: auth,
      redirect: (context, state) {
        final loggedIn = auth.isAuthenticated;
        final goingToAuth = state.matchedLocation == '/login' ||
                            state.matchedLocation == '/register';
        if (!loggedIn && !goingToAuth) return '/login';
        if (loggedIn && goingToAuth) return _destFor(auth);
        return null;
      },
      routes: [
        GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
        GoRoute(path: '/register', builder: (_, _) => const RegisterScreen()),
        GoRoute(path: '/dashboard', builder: (_, _) => const DashboardScreen()),
        GoRoute(path: '/admin', builder: (_, _) => const AdminDashboardScreen()),
        GoRoute(path: '/profesor',
                builder: (_, _) => const ProfesorDashboardScreen()),
      ],
    );
  }

  String _destFor(AuthProvider auth) {
    final rol = auth.user?.rol;
    if (rol == 'admin' || rol == 'director' || rol == 'coordinador' ||
        rol == 'rector') {
      return '/admin';
    }
    if (rol == 'profesor') return '/profesor';
    return '/dashboard';
  }
}
