import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class AsistenciaScreen extends StatefulWidget {
  const AsistenciaScreen({super.key});
  @override
  State<AsistenciaScreen> createState() => _AsistenciaScreenState();
}

class _AsistenciaScreenState extends State<AsistenciaScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final user = context.read<AuthProvider>().user;
    if (user == null) { setState(() => _loading = false); return; }
    try {
      // Usa el mismo endpoint de calificaciones que ya trae asistencia_pct
      final r = await ApiService.get(
        '/api/v1/users/${user.id}/calificaciones');
      final list = (r['inscripciones'] as List? ?? [])
        .cast<Map<String, dynamic>>();
      // Carga detalle de asistencia por inscripción (paralelo limitado)
      for (final ins in list) {
        try {
          final det = await ApiService.get(
            '/api/v1/inscripciones/${ins['id']}/asistencia');
          ins['_detail'] = det;
        } catch (_) {}
      }
      if (mounted) setState(() { _items = list; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Asistencia')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _items.isEmpty
          ? Center(child: Text('Sin registros',
              style: MapText.b14.copyWith(color: MapColors.ink600)))
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _items.length,
                itemBuilder: (_, i) => _row(_items[i]),
              ),
            ),
    );
  }

  Widget _row(Map<String, dynamic> ins) {
    final materia = ins['materia'] as Map<String, dynamic>?;
    final det = ins['_detail'] as Map<String, dynamic>?;
    final pct = (det?['porcentaje'] as num?)?.toDouble() ?? 0;
    final faltas = det?['faltas'] as int? ?? 0;
    final just = det?['justificadas'] as int? ?? 0;
    final total = det?['total'] as int? ?? 0;
    final color = pct < 80 ? MapColors.warning : MapColors.success;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(materia?['nombre'] ?? '—',
                  style: MapText.body(15, w: FontWeight.w700))),
                Text('${pct.toStringAsFixed(1)}%',
                  style: MapText.display(18, w: FontWeight.w700, color: color)),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(999),
              child: LinearProgressIndicator(
                value: pct / 100,
                backgroundColor: MapColors.surface150,
                valueColor: AlwaysStoppedAnimation(color),
                minHeight: 8,
              ),
            ),
            const SizedBox(height: 8),
            Text('$total sesiones · ${total - faltas - just} presentes · '
                 '$just justificadas · $faltas ausencias',
              style: MapText.b12.copyWith(color: MapColors.ink600)),
            if (pct < 80 && total > 0) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: MapColors.warningBg,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Row(children: [
                  const Icon(Icons.warning_amber,
                             size: 16, color: MapColors.warning),
                  const SizedBox(width: 6),
                  Expanded(child: Text(
                    'Asistencia debajo del 80%. Recupera lo antes posible.',
                    style: MapText.b12.copyWith(color: MapColors.ink800))),
                ]),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
