import 'package:flutter/material.dart';
import '../../models/salon.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../salones/salon_detail_screen.dart';

class AdminSalonesScreen extends StatefulWidget {
  const AdminSalonesScreen({super.key});
  @override
  State<AdminSalonesScreen> createState() => _AdminSalonesScreenState();
}

class _AdminSalonesScreenState extends State<AdminSalonesScreen> {
  List<Salon> _salones = [];
  bool _loading = true;
  String _query = '';
  String? _tipo;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/salones', requiresAuth: false);
      if (mounted) {
        setState(() {
        _salones = (r['data'] as List)
          .map((j) => Salon.fromJson(j as Map<String, dynamic>)).toList();
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _salones.where((s) {
      final matchQ = _query.isEmpty ||
        s.codigo.toLowerCase().contains(_query.toLowerCase()) ||
        (s.nombre ?? '').toLowerCase().contains(_query.toLowerCase());
      final matchT = _tipo == null || _tipo!.isEmpty || s.tipo == _tipo;
      return matchQ && matchT;
    }).toList();
    final groups = <String, List<Salon>>{};
    for (final s in filtered) {
      groups.putIfAbsent(s.edificioClave, () => []).add(s);
    }
    final keys = groups.keys.toList()..sort();

    return Scaffold(
      appBar: AppBar(title: const Text('Salones')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                TextField(
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Buscar código…',
                  ),
                  onChanged: (v) => setState(() => _query = v),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: _tipo,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Tipo',
                    contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                  items: const [
                    DropdownMenuItem(value: '', child: Text('Todos')),
                    DropdownMenuItem(value: 'aula', child: Text('Aula')),
                    DropdownMenuItem(value: 'laboratorio', child: Text('Laboratorio')),
                    DropdownMenuItem(value: 'auditorio', child: Text('Auditorio')),
                    DropdownMenuItem(value: 'sala_computo', child: Text('Sala de cómputo')),
                    DropdownMenuItem(value: 'sala_idiomas', child: Text('Sala de idiomas')),
                  ],
                  onChanged: (v) => setState(() => _tipo = v),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator())
              : filtered.isEmpty
                ? Center(child: Text('Sin resultados',
                    style: MapText.b14.copyWith(color: MapColors.ink600)))
                : ListView(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    children: [
                      for (final k in keys) ...[
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Text('Edificio $k (${groups[k]!.length})',
                            style: MapText.d20),
                        ),
                        ...groups[k]!.map((s) => Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: ListTile(
                            title: Text(s.codigo,
                              style: MapText.body(15, w: FontWeight.w700)),
                            subtitle: Text(
                              '${s.nombre ?? ''} · ${s.tipo?.replaceAll('_', ' ') ?? ''} · '
                              '${s.capacidad} cupos · piso ${s.piso}',
                              style: MapText.b12.copyWith(color: MapColors.ink600)),
                            trailing: Container(
                              width: 10, height: 10,
                              decoration: BoxDecoration(
                                color: s.disponibleAhora
                                  ? MapColors.success : MapColors.warning,
                                shape: BoxShape.circle,
                              ),
                            ),
                            onTap: () => Navigator.push(context,
                              MaterialPageRoute(builder: (_) =>
                                SalonDetailScreen(salonId: s.id, codigo: s.codigo))),
                          ),
                        )),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}
