import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/stat_card.dart';
import '../shared/notificaciones_screen.dart';
import 'admin_usuarios_screen.dart';
import 'admin_horarios_screen.dart';
import 'admin_salones_screen.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({super.key});
  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  Map<String, dynamic>? _kpi;
  bool _loading = true;

  Widget _drawerItem(IconData icon, String label, VoidCallback onTap) =>
    ListTile(
      leading: Icon(icon, color: MapColors.navy200),
      title: Text(label,
        style: MapText.b14.copyWith(color: MapColors.surface0)),
      onTap: onTap,
    );

  Widget _drawerSection(String label) => Padding(
    padding: const EdgeInsets.fromLTRB(20, 16, 20, 4),
    child: Text(label.toUpperCase(),
      style: MapText.mono(10, w: FontWeight.w700, color: MapColors.navy300)),
  );

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/stats/dashboard');
      if (mounted) setState(() { _kpi = r; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Panel administrativo'),
        actions: [
          IconButton(icon: const Icon(Icons.logout),
            onPressed: () async {
              await context.read<AuthProvider>().logout();
              if (context.mounted) context.go('/login');
            }),
        ],
      ),
      drawer: Drawer(
        backgroundColor: MapColors.navy800,
        child: SafeArea(
          child: ListView(
            padding: EdgeInsets.zero,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Matute Guide',
                      style: MapText.display(20, w: FontWeight.w700,
                                             color: MapColors.surface0)),
                    const SizedBox(height: 4),
                    Text('Panel administrativo',
                      style: MapText.b12.copyWith(color: MapColors.navy200)),
                  ],
                ),
              ),
              const Divider(color: MapColors.navy700, height: 1),
              _drawerItem(Icons.home, 'Inicio', () => Navigator.pop(context)),
              _drawerSection('Académico'),
              _drawerItem(Icons.calendar_today, 'Horarios', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) => const AdminHorariosScreen()));
              }),
              _drawerSection('Campus'),
              _drawerItem(Icons.meeting_room, 'Salones', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) => const AdminSalonesScreen()));
              }),
              _drawerSection('Comunidad'),
              _drawerItem(Icons.people, 'Usuarios', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) => const AdminUsuariosScreen()));
              }),
              _drawerItem(Icons.school, 'Estudiantes', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) =>
                    const AdminUsuariosScreen(rolFiltro: 'estudiante')));
              }),
              _drawerItem(Icons.cast_for_education, 'Profesores', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) =>
                    const AdminUsuariosScreen(rolFiltro: 'profesor')));
              }),
              _drawerItem(Icons.notifications, 'Notificaciones', () {
                Navigator.pop(context);
                Navigator.push(context, MaterialPageRoute(
                  builder: (_) => const NotificacionesScreen()));
              }),
            ],
          ),
        ),
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : RefreshIndicator(
            onRefresh: _load,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text('Bienvenido, ${user?.nombre ?? ""}', style: MapText.d24),
                const SizedBox(height: 8),
                Text('Resumen del plantel',
                  style: MapText.b14.copyWith(color: MapColors.ink600)),
                const SizedBox(height: 24),
                if (_kpi != null) ...[
                  GridView.count(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisCount: 2,
                    childAspectRatio: 1.6,
                    mainAxisSpacing: 12,
                    crossAxisSpacing: 12,
                    children: [
                      StatCard(label: 'Estudiantes',
                        value: _kpi!['estudiantes_activos']['total'].toString(),
                        meta: _kpi!['estudiantes_activos']['periodo']),
                      StatCard(label: 'Horarios pub.',
                        value: '${_kpi!['horarios_publicados']['total']}/${_kpi!['horarios_publicados']['meta']}',
                        meta: _kpi!['horarios_publicados']['periodo']),
                      StatCard(label: 'Conflictos',
                        value: _kpi!['conflictos_abiertos']['total'].toString(),
                        meta: _kpi!['conflictos_abiertos']['periodo']),
                      StatCard(label: 'Asistencia',
                        value: '${_kpi!['asistencia_promedio']['valor']}%',
                        meta: _kpi!['asistencia_promedio']['periodo']),
                      StatCard(label: 'Trámites pend.',
                        value: _kpi!['tramites_pendientes']['total'].toString()),
                      StatCard(label: 'Nuevos hoy',
                        value: (_kpi!['nuevos_hoy']['usuarios'] +
                                _kpi!['nuevos_hoy']['tramites']).toString(),
                        meta: '${_kpi!['nuevos_hoy']['usuarios']} usuarios'),
                    ],
                  ),
                ],
              ],
            ),
          ),
    );
  }
}
