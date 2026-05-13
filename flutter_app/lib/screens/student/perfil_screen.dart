import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/avatar_widget.dart';
import '../../widgets/status_badge.dart';

class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    if (user == null) return const SizedBox();
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Center(child: AppAvatar(iniciales: user.iniciales,
                                colorHex: user.avatarColor, size: 96)),
        const SizedBox(height: 16),
        Center(child: Text(user.nombreCompleto, style: MapText.d24)),
        const SizedBox(height: 4),
        Center(child: Text(user.email,
                           style: MapText.b14.copyWith(color: MapColors.ink600))),
        const SizedBox(height: 12),
        Center(child: StatusBadge.fromEstado(user.estado)),
        const SizedBox(height: 32),
        Card(child: ListTile(
          leading: const Icon(Icons.badge_outlined),
          title: const Text('Expediente'),
          subtitle: Text(user.expediente ?? '—'),
        )),
        Card(child: ListTile(
          leading: const Icon(Icons.school_outlined),
          title: const Text('Carrera'),
          subtitle: Text(user.carreraNombre ?? '—'),
        )),
        Card(child: ListTile(
          leading: const Icon(Icons.format_list_numbered),
          title: const Text('Semestre'),
          subtitle: Text(user.semestreActual?.toString() ?? '—'),
        )),
        const SizedBox(height: 24),
        OutlinedButton.icon(
          icon: const Icon(Icons.logout),
          label: const Text('Cerrar sesión'),
          style: OutlinedButton.styleFrom(
            foregroundColor: MapColors.danger,
            side: const BorderSide(color: MapColors.danger),
          ),
          onPressed: () async {
            await context.read<AuthProvider>().logout();
            if (context.mounted) context.go('/login');
          },
        ),
      ],
    );
  }
}
