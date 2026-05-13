import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class CalificacionesScreen extends StatefulWidget {
  const CalificacionesScreen({super.key});
  @override
  State<CalificacionesScreen> createState() => _CalificacionesScreenState();
}

class _CalificacionesScreenState extends State<CalificacionesScreen> {
  List<dynamic> _inscripciones = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    final user = context.read<AuthProvider>().user;
    if (user == null) { setState(() => _loading = false); return; }
    try {
      final r = await ApiService.get(
        '/api/v1/users/${user.id}/calificaciones');
      if (mounted) {
        setState(() {
        _inscripciones = (r['inscripciones'] as List?) ?? [];
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  static const _tipos = ['parcial_1', 'parcial_2', 'parcial_3', 'final'];
  static const _tipoLbl = {
    'parcial_1': 'P1', 'parcial_2': 'P2', 'parcial_3': 'P3', 'final': 'F',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Calificaciones')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _inscripciones.isEmpty
          ? Center(child: Text('Sin inscripciones',
              style: MapText.b14.copyWith(color: MapColors.ink600)))
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _inscripciones.length,
                itemBuilder: (_, i) {
                  final ins = _inscripciones[i] as Map<String, dynamic>;
                  return _buildRow(ins);
                },
              ),
            ),
    );
  }

  Widget _buildRow(Map<String, dynamic> ins) {
    final materia = ins['materia'] as Map<String, dynamic>?;
    final califs = (ins['calificaciones'] as List? ?? [])
      .cast<Map<String, dynamic>>()
      .where((c) => c['publicado'] == true).toList();
    final byTipo = {for (final c in califs) c['tipo'] as String: c};
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(materia?['nombre'] ?? '—',
              style: MapText.body(15, w: FontWeight.w700)),
            Text(materia?['clave'] ?? '',
              style: MapText.mono(11, color: MapColors.ink600)),
            const SizedBox(height: 12),
            Row(
              children: _tipos.map((t) {
                final c = byTipo[t];
                final v = c == null ? null : (c['valor'] as num?)?.toDouble();
                return Expanded(child: Column(
                  children: [
                    Text(_tipoLbl[t] ?? t,
                      style: MapText.mono(10, w: FontWeight.w700,
                                          color: MapColors.ink500)),
                    const SizedBox(height: 4),
                    Text(v == null ? '—' : v.toStringAsFixed(1),
                      style: MapText.display(20, w: FontWeight.w700,
                        color: v == null
                          ? MapColors.ink400
                          : (v < 6 ? MapColors.danger : MapColors.ink900))),
                  ],
                ));
              }).toList(),
            ),
            if (ins['asistencia_pct'] != null) ...[
              const SizedBox(height: 8),
              Text('Asistencia: ${ins['asistencia_pct']}%',
                style: MapText.b12.copyWith(color: MapColors.ink600)),
            ],
          ],
        ),
      ),
    );
  }
}
