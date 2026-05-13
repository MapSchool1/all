import 'package:flutter/material.dart';
import '../../models/salon.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class SalonesListScreen extends StatefulWidget {
  const SalonesListScreen({super.key});
  @override
  State<SalonesListScreen> createState() => _SalonesListScreenState();
}

class _SalonesListScreenState extends State<SalonesListScreen> {
  List<Salon> _salones = [];
  bool _loading = true;
  String _query = '';

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/salones');
      final list = (r['data'] as List).map((j) => Salon.fromJson(j)).toList();
      if (mounted) setState(() { _salones = list; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final filtered = _salones.where((s) =>
      s.codigo.toLowerCase().contains(_query.toLowerCase()) ||
      (s.nombre ?? '').toLowerCase().contains(_query.toLowerCase())).toList();
    final groups = <String, List<Salon>>{};
    for (final s in filtered) {
      groups.putIfAbsent(s.edificioClave, () => []).add(s);
    }
    final sortedKeys = groups.keys.toList()..sort();

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: TextField(
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Buscar salón…',
            ),
            onChanged: (v) => setState(() => _query = v),
          ),
        ),
        Expanded(
          child: filtered.isEmpty
            ? Center(child: Text('Sin salones', style: MapText.b14))
            : ListView(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  for (final k in sortedKeys) ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      child: Text('Edificio $k (${groups[k]!.length})',
                                  style: MapText.d20),
                    ),
                    ...groups[k]!.map((s) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        title: Text(s.codigo,
                          style: MapText.display(18, w: FontWeight.w700)),
                        subtitle: Text(
                          '${s.nombre ?? ''} · ${s.tipo?.replaceAll('_', ' ')} · ${s.capacidad} cupos',
                          style: MapText.b12),
                        trailing: Container(
                          width: 10, height: 10,
                          decoration: BoxDecoration(
                            color: s.disponibleAhora
                              ? MapColors.success : MapColors.warning,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                    )),
                  ],
                ],
              ),
        ),
      ],
    );
  }
}
