import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class ProfesorDashboardScreen extends StatelessWidget {
  const ProfesorDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profesor'),
        actions: [
          IconButton(icon: const Icon(Icons.logout),
            onPressed: () async {
              await context.read<AuthProvider>().logout();
              if (context.mounted) context.go('/login');
            }),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Hola, prof. ${user?.apellidoP ?? ""}', style: MapText.d24),
            const SizedBox(height: 16),
            Text('La gestión completa de grupos y calificaciones está '
                 'disponible en la versión web.',
                 style: MapText.b14.copyWith(color: MapColors.ink600)),
          ],
        ),
      ),
    );
  }
}
