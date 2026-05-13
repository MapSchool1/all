import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/avatar_widget.dart';
import '../../widgets/stat_card.dart';
import '../../widgets/status_badge.dart';
import '../../models/horario.dart';
import 'horario_screen.dart';
import 'salones_list_screen.dart';
import 'perfil_screen.dart';
import 'calificaciones_screen.dart';
import 'asistencia_screen.dart';
import 'tramites_screen.dart';
import '../mapa/mapa_screen.dart';
import '../shared/notificaciones_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = [
      const _HomeTab(),
      const HorarioScreen(),
      const SalonesListScreen(),
      const MapaScreen(),
      const PerfilScreen(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: Image.asset('assets/images/logo-white.png',
            height: 32, fit: BoxFit.contain),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => const NotificacionesScreen(),
            )),
          ),
        ],
      ),
      body: pages[_index],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined),
                                  activeIcon: Icon(Icons.home), label: 'Inicio'),
          BottomNavigationBarItem(icon: Icon(Icons.calendar_today_outlined),
                                  activeIcon: Icon(Icons.calendar_today), label: 'Horario'),
          BottomNavigationBarItem(icon: Icon(Icons.meeting_room_outlined),
                                  activeIcon: Icon(Icons.meeting_room), label: 'Salones'),
          BottomNavigationBarItem(icon: Icon(Icons.map_outlined),
                                  activeIcon: Icon(Icons.map), label: 'Mapa'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline),
                                  activeIcon: Icon(Icons.person), label: 'Perfil'),
        ],
      ),
    );
  }
}

class _HomeTab extends StatefulWidget {
  const _HomeTab();
  @override
  State<_HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<_HomeTab> {
  Horario? _horario;
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final list = await ApiService.get('/api/v1/horarios');
      final horarios = list['data'] as List;
      if (horarios.isNotEmpty) {
        final id = horarios.first['id'];
        final detail = await ApiService.get('/api/v1/horarios/$id');
        if (mounted) setState(() { _horario = Horario.fromResponse(detail); _loading = false; });
      } else {
        if (mounted) setState(() { _loading = false; });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    if (user == null) return const SizedBox();
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              AppAvatar(iniciales: user.iniciales, colorHex: user.avatarColor, size: 56),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('¡Hola, ${user.nombre}!', style: MapText.d24),
                    if (user.expediente != null)
                      Text('Expediente ${user.expediente}',
                        style: MapText.b14.copyWith(color: MapColors.ink600)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          if (_loading)
            const Center(child: Padding(
              padding: EdgeInsets.all(32),
              child: CircularProgressIndicator(),
            ))
          else if (_horario == null)
            _emptyState()
          else ...[
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              childAspectRatio: 2.0,
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              children: [
                StatCard(label: 'Materias',
                  value: _horario!.bloques.map((b) => b.materia?['id']).toSet().length.toString()),
                StatCard(label: 'Horas semana',
                  value: _horario!.totalHoras.toString()),
                StatCard(label: 'Créditos',
                  value: _horario!.totalCreditos.toString()),
                StatCard(label: 'Conflictos',
                  value: _horario!.bloques.where((b) => b.conflicto).length.toString(),
                  meta: _horario!.tieneConflictos ? '⚠ Revísalo' : 'Todo en orden'),
              ],
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Text(_horario!.nombre, style: MapText.d20),
                const SizedBox(width: 8),
                StatusBadge.fromEstado(_horario!.estado),
              ],
            ),
            const SizedBox(height: 8),
            if (_horario!.tieneConflictos)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: MapColors.warningBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: MapColors.warning),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber, color: MapColors.warning),
                    const SizedBox(width: 8),
                    Expanded(child: Text(
                      'Tu horario tiene un conflicto sin resolver. '
                      'Revísalo en la pestaña Horario.',
                      style: MapText.b14)),
                  ],
                ),
              ),
            ..._proximosBloques(),
            const SizedBox(height: 16),
            _quickActions(context),
          ],
        ],
      ),
    );
  }

  Widget _quickActions(BuildContext ctx) {
    Widget tile(IconData ic, String label, Widget Function() builder) =>
      Expanded(
        child: Card(
          child: InkWell(
            onTap: () => Navigator.of(ctx).push(
              MaterialPageRoute(builder: (_) => builder())),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  Icon(ic, color: MapColors.navy700, size: 28),
                  const SizedBox(height: 6),
                  Text(label, textAlign: TextAlign.center,
                    style: MapText.b12.copyWith(fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
        ),
      );
    return Row(
      children: [
        tile(Icons.bar_chart, 'Calificaciones',
             () => const CalificacionesScreen()),
        const SizedBox(width: 8),
        tile(Icons.check_circle_outline, 'Asistencia',
             () => const AsistenciaScreen()),
        const SizedBox(width: 8),
        tile(Icons.description_outlined, 'Trámites',
             () => const TramitesScreen()),
      ],
    );
  }

  Widget _emptyState() {
    return Container(
      padding: const EdgeInsets.all(32),
      alignment: Alignment.center,
      child: Column(
        children: [
          const Icon(Icons.calendar_today_outlined,
                     size: 48, color: MapColors.ink400),
          const SizedBox(height: 12),
          Text('Sin horario en este periodo', style: MapText.d20),
          const SizedBox(height: 8),
          Text('Crea tu horario desde la pestaña Horario.',
               style: MapText.b14.copyWith(color: MapColors.ink600)),
        ],
      ),
    );
  }

  List<Widget> _proximosBloques() {
    final today = DateTime.now().weekday;
    const map = {1:'lun', 2:'mar', 3:'mie', 4:'jue', 5:'vie', 6:'sab'};
    final hoyKey = map[today];
    final hoy = _horario!.bloques.where((b) => b.dia == hoyKey).toList()
      ..sort((a, b) => a.horaInicio.compareTo(b.horaInicio));
    if (hoy.isEmpty) {
      return [
      const SizedBox(height: 16),
      Text('Hoy', style: MapText.d20),
      const SizedBox(height: 8),
      Text('Sin clases programadas para hoy.',
           style: MapText.b14.copyWith(color: MapColors.ink600)),
    ];
    }
    return [
      const SizedBox(height: 16),
      Text('Hoy (${_diaLabel(hoyKey!)})', style: MapText.d20),
      const SizedBox(height: 8),
      ...hoy.map((b) => Card(
        child: ListTile(
          title: Text(b.materiaNombre),
          subtitle: Text('${b.horaInicio} – ${b.horaFin}  ·  ${b.salonCodigo}'),
          trailing: b.conflicto
            ? StatusBadge.fromEstado('conflicto')
            : null,
        ),
      )),
    ];
  }

  String _diaLabel(String d) => const {
    'lun': 'lunes', 'mar': 'martes', 'mie': 'miércoles',
    'jue': 'jueves', 'vie': 'viernes', 'sab': 'sábado',
  }[d] ?? d;
}
