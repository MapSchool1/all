import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/status_badge.dart';

class TramitesScreen extends StatefulWidget {
  const TramitesScreen({super.key});
  @override
  State<TramitesScreen> createState() => _TramitesScreenState();
}

class _TramitesScreenState extends State<TramitesScreen> {
  List<dynamic> _tramites = [];
  List<dynamic> _tipos = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final results = await Future.wait([
        ApiService.get('/api/v1/tramites?per_page=50'),
        ApiService.get('/api/v1/tramites/tipos', requiresAuth: false),
      ]);
      if (mounted) {
        setState(() {
        _tramites = results[0]['data'] as List;
        _tipos = results[1]['data'] as List;
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _showCreate() async {
    final tipoCtrl = ValueNotifier<int?>(
      _tipos.isNotEmpty ? _tipos.first['id'] as int : null);
    final descCtrl = TextEditingController();
    bool busy = false;

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setBs) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom,
            left: 20, right: 20, top: 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(
                  color: MapColors.ink300,
                  borderRadius: BorderRadius.circular(2),
                ),
              )),
              const SizedBox(height: 16),
              Text('Nuevo trámite', style: MapText.d24),
              const SizedBox(height: 16),
              ValueListenableBuilder<int?>(
                valueListenable: tipoCtrl,
                builder: (_, value, _) => DropdownButtonFormField<int>(
                  initialValue: value,
                  isExpanded: true,
                  items: [
                    for (final t in _tipos)
                      DropdownMenuItem(
                        value: t['id'] as int,
                        child: Text(
                          '${t['nombre']} · ~${t['tiempo_estimado_dias']}d',
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: (v) => tipoCtrl.value = v,
                  decoration: const InputDecoration(
                    labelText: 'Tipo de trámite'),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descCtrl,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Descripción / motivo',
                  hintText: '¿Para qué necesitas este trámite?',
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: busy ? null : () async {
                    if (tipoCtrl.value == null) return;
                    setBs(() => busy = true);
                    // Capturar messenger ANTES del await para evitar
                    // el lint use_build_context_synchronously.
                    final messenger = ScaffoldMessenger.of(context);
                    try {
                      final r = await ApiService.post('/api/v1/tramites',
                        body: {
                          'tipo_tramite_id': tipoCtrl.value,
                          'descripcion': descCtrl.text,
                        });
                      if (ctx.mounted) Navigator.pop(ctx);
                      messenger.showSnackBar(SnackBar(
                        content: Text(
                          'Trámite enviado · folio ${r['tramite']['folio']}'),
                        backgroundColor: MapColors.success,
                      ));
                      _load();
                    } catch (e) {
                      setBs(() => busy = false);
                      messenger.showSnackBar(SnackBar(
                        content: Text('Error: ${e.toString()}'),
                        backgroundColor: MapColors.danger,
                      ));
                    }
                  },
                  child: busy
                    ? const CircularProgressIndicator(color: MapColors.surface0)
                    : const Text('Solicitar'),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Trámites')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showCreate,
        icon: const Icon(Icons.add),
        label: const Text('Nuevo'),
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _tramites.isEmpty
          ? Center(child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.description_outlined,
                  size: 48, color: MapColors.ink400),
                const SizedBox(height: 12),
                Text('Sin trámites', style: MapText.d20),
                const SizedBox(height: 4),
                Text('Solicita uno con el botón de abajo.',
                  style: MapText.b14.copyWith(color: MapColors.ink600)),
              ],
            ))
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _tramites.length,
                itemBuilder: (_, i) {
                  final t = _tramites[i] as Map<String, dynamic>;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      title: Text(t['folio'] as String,
                        style: MapText.body(14, w: FontWeight.w700)),
                      subtitle: Text(
                        '${t['tipo']?['nombre'] ?? '—'}\n${t['descripcion'] ?? ''}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      isThreeLine: true,
                      trailing: StatusBadge.fromEstado(t['estado'] as String),
                    ),
                  );
                },
              ),
            ),
    );
  }
}
