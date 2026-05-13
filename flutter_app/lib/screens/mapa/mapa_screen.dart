import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../salones/salon_detail_screen.dart';

class MapaScreen extends StatefulWidget {
  const MapaScreen({super.key});
  @override
  State<MapaScreen> createState() => _MapaScreenState();
}

class _MapaScreenState extends State<MapaScreen> {
  List<dynamic> _edificios = [];
  List<dynamic> _puntos = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/mapa', requiresAuth: false);
      if (mounted) {
        setState(() {
        _edificios = (r['edificios'] as List?) ?? [];
        _puntos = (r['puntos_interes'] as List?) ?? [];
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Color _poiColor(String tipo) => switch (tipo) {
    'cafeteria' => MapColors.success,
    'biblioteca' => MapColors.info,
    'enfermeria' => MapColors.danger,
    'estacionamiento' => MapColors.warning,
    _ => MapColors.ink600,
  };

  IconData _poiIcon(String tipo) => switch (tipo) {
    'cafeteria' => Icons.coffee,
    'biblioteca' => Icons.menu_book,
    'enfermeria' => Icons.local_hospital,
    'estacionamiento' => Icons.local_parking,
    'canchas' => Icons.sports_soccer,
    'bano' => Icons.wc,
    _ => Icons.place,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mapa del campus')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : InteractiveViewer(
            minScale: 0.5, maxScale: 3.5,
            boundaryMargin: const EdgeInsets.all(64),
            child: SizedBox(
              width: 1200, height: 800,
              child: Stack(
                children: [
                  // Fondo
                  Positioned.fill(child: Container(color: MapColors.surface100)),
                  // Edificios
                  for (final e in _edificios)
                    Positioned(
                      left: (e['coordenadas_x'] as num).toDouble(),
                      top: (e['coordenadas_y'] as num).toDouble(),
                      width: (e['ancho'] as num).toDouble(),
                      height: (e['alto'] as num).toDouble(),
                      child: _BuildingTile(
                        clave: e['clave'] as String,
                        nombre: e['nombre'] as String,
                        color: _parseHex(e['color'] as String? ?? '#172846'),
                        edificioId: e['id'] as int,
                      ),
                    ),
                  // Puntos de interés
                  for (final p in _puntos)
                    Positioned(
                      left: ((p['coord_x'] as num).toDouble()) - 16,
                      top: ((p['coord_y'] as num).toDouble()) - 16,
                      child: Tooltip(
                        message: p['nombre'] as String,
                        child: Container(
                          width: 32, height: 32,
                          decoration: BoxDecoration(
                            color: _poiColor(p['tipo'] as String? ?? ''),
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: MapColors.surface0, width: 2),
                          ),
                          child: Icon(
                            _poiIcon(p['tipo'] as String? ?? ''),
                            color: MapColors.surface0, size: 16),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
    );
  }

  Color _parseHex(String hex) {
    final s = hex.replaceFirst('#', '');
    return Color(int.parse('FF$s', radix: 16));
  }
}

class _BuildingTile extends StatelessWidget {
  final String clave;
  final String nombre;
  final Color color;
  final int edificioId;
  const _BuildingTile({required this.clave, required this.nombre,
                       required this.color, required this.edificioId});

  Future<void> _onTap(BuildContext context) async {
    try {
      final r = await ApiService.get('/api/v1/edificios/$edificioId',
                                     requiresAuth: false);
      if (!context.mounted) return;
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        builder: (_) => _EdificioSheet(
          edificio: r['edificio'] as Map<String, dynamic>,
          salones: (r['salones'] as List).cast<Map<String, dynamic>>(),
        ),
      );
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: color,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _onTap(context),
        child: Center(
          child: Text(clave,
            style: MapText.display(36, w: FontWeight.w800,
                                   color: MapColors.surface0)),
        ),
      ),
    );
  }
}

class _EdificioSheet extends StatelessWidget {
  final Map<String, dynamic> edificio;
  final List<Map<String, dynamic>> salones;
  const _EdificioSheet({required this.edificio, required this.salones});

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.6, maxChildSize: 0.9,
      expand: false,
      builder: (_, ctrl) => Container(
        decoration: const BoxDecoration(
          color: MapColors.surface0,
          borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
        ),
        child: ListView(
          controller: ctrl,
          padding: const EdgeInsets.all(20),
          children: [
            Center(child: Container(
              width: 40, height: 4,
              decoration: BoxDecoration(
                color: MapColors.ink300,
                borderRadius: BorderRadius.circular(2),
              ),
            )),
            const SizedBox(height: 16),
            Text(edificio['nombre'] as String, style: MapText.d24),
            if (edificio['descripcion'] != null) ...[
              const SizedBox(height: 8),
              Text(edificio['descripcion'] as String,
                style: MapText.b14.copyWith(color: MapColors.ink600)),
            ],
            const SizedBox(height: 16),
            Text('Salones (${salones.length})', style: MapText.d20),
            const SizedBox(height: 8),
            for (final s in salones)
              Card(
                child: ListTile(
                  title: Text(s['codigo'] as String,
                    style: MapText.body(16, w: FontWeight.w700)),
                  subtitle: Text(
                    '${s['nombre'] ?? ''} · ${(s['tipo'] as String? ?? '').replaceAll('_', ' ')} · ${s['capacidad']} cupos'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    Navigator.pop(context);
                    Navigator.push(context, MaterialPageRoute(
                      builder: (_) => SalonDetailScreen(
                        salonId: s['id'] as int,
                        codigo: s['codigo'] as String,
                      ),
                    ));
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}
