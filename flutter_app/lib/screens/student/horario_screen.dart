import 'package:flutter/material.dart';
import '../../models/bloque.dart';
import '../../models/horario.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/schedule_grid.dart';
import '../../widgets/status_badge.dart';

class HorarioScreen extends StatefulWidget {
  const HorarioScreen({super.key});
  @override
  State<HorarioScreen> createState() => _HorarioScreenState();
}

class _HorarioScreenState extends State<HorarioScreen> {
  Horario? _horario;
  bool _loading = true;
  String? _error;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await ApiService.get('/api/v1/horarios');
      final horarios = list['data'] as List;
      if (horarios.isEmpty) {
        if (mounted) setState(() => _loading = false);
        return;
      }
      final id = horarios.first['id'];
      final detail = await ApiService.get('/api/v1/horarios/$id');
      if (mounted) {
        setState(() {
        _horario = Horario.fromResponse(detail);
        _loading = false;
      });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
        _error = e.toString(); _loading = false;
      });
      }
    }
  }

  void _showBloqueDetail(Bloque b) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(b.materiaNombre, style: MapText.d20),
            const SizedBox(height: 12),
            _row(Icons.access_time, '${b.horaInicio} – ${b.horaFin}'),
            _row(Icons.location_on_outlined, b.salonCodigo),
            if (b.profesor != null)
              _row(Icons.person_outline, b.profesor!['nombre_completo']),
            if (b.conflicto) ...[
              const SizedBox(height: 12),
              Row(children: [
                const Icon(Icons.warning_amber, color: MapColors.warning),
                const SizedBox(width: 8),
                Text('Conflicto · revisa tu agenda',
                  style: MapText.b14.copyWith(color: MapColors.danger,
                                              fontWeight: FontWeight.w700)),
              ]),
            ],
          ],
        ),
      ),
    );
  }

  Widget _row(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 16, color: MapColors.ink600),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: MapText.b14)),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Text('Error: $_error',
        style: MapText.b14.copyWith(color: MapColors.danger)));
    }
    if (_horario == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.calendar_today_outlined,
                       size: 48, color: MapColors.ink400),
            const SizedBox(height: 12),
            Text('Sin horario activo', style: MapText.d20),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Row(
            children: [
              Expanded(child: Text(_horario!.nombre, style: MapText.d20)),
              StatusBadge.fromEstado(_horario!.estado),
            ],
          ),
          const SizedBox(height: 12),
          ScheduleGrid(bloques: _horario!.bloques, onTap: _showBloqueDetail),
          const SizedBox(height: 12),
          _legend(),
        ],
      ),
    );
  }

  Widget _legend() {
    Widget chip(Color c, String label) => Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Container(width: 12, height: 12,
          decoration: BoxDecoration(color: c, borderRadius: BorderRadius.circular(3))),
        const SizedBox(width: 4),
        Text(label, style: MapText.b12),
      ]),
    );
    return Wrap(children: [
      chip(MapColors.bloqueTroncoComun, 'Tronco común'),
      chip(MapColors.bloqueAreaProfesional, 'Área profesional'),
      chip(MapColors.bloqueLaboratorio, 'Laboratorio'),
      chip(MapColors.bloqueIdiomas, 'Idiomas'),
      chip(MapColors.bloqueConflicto, 'Conflicto'),
    ]);
  }
}
