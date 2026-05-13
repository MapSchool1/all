import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController(text: 'alvaro.diaz@alumnos.udg.mx');
  final _pwd = TextEditingController(text: 'Estudiante1!');
  bool _obscure = true;
  bool _busy = false;
  String? _error;

  Future<void> _submit() async {
    if (_email.text.trim().isEmpty || _pwd.text.isEmpty) {
      setState(() => _error = 'Correo y contraseña son obligatorios');
      return;
    }
    setState(() { _busy = true; _error = null; });
    try {
      await context.read<AuthProvider>()
        .login(_email.text.trim().toLowerCase(), _pwd.text);
      if (!mounted) return;
      _redirect();
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'No pudimos conectar con el servidor');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _redirect() {
    final user = context.read<AuthProvider>().user;
    if (user == null) return;
    final dest = const {
      'admin': '/admin', 'director': '/admin', 'coordinador': '/admin',
      'rector': '/admin', 'profesor': '/profesor', 'estudiante': '/dashboard',
      'invitado': '/dashboard', 'aspirante': '/dashboard',
    }[user.rol] ?? '/dashboard';
    context.go(dest);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: MapColors.surface0,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Matute Guide',
                style: MapText.display(20, w: FontWeight.w700,
                                       color: MapColors.navy800)),
              const SizedBox(height: 32),
              Text('Inicia sesión', style: MapText.d24),
              const SizedBox(height: 24),
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: MapColors.dangerBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: MapColors.danger),
                  ),
                  child: Text(_error!,
                    style: MapText.b14.copyWith(color: MapColors.danger)),
                ),
                const SizedBox(height: 16),
              ],
              TextField(
                controller: _email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'Correo institucional',
                  hintText: 'usuario@alumnos.udg.mx',
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _pwd,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: 'Contraseña',
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => _obscure = !_obscure),
                    icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _busy ? null : _submit,
                  child: _busy
                    ? const SizedBox(width: 20, height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2, color: MapColors.surface0))
                    : const Text('Iniciar sesión'),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: TextButton(
                  onPressed: () => context.go('/register'),
                  child: const Text('Crear una cuenta'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
