import 'package:flutter/material.dart';
import '../../models/bloque.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/schedule_grid.dart';

class AdminHorariosScreen extends StatefulWidget {
  const AdminHorariosScreen({super.key});
  @override
  State<AdminHorariosScreen> createState() => _AdminHorariosScreenState();
}

class _AdminHorariosScreenState extends State<AdminHorariosScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabs;
  List<dynamic> _carreras = [];
  List<dynamic> _profesores = [];
  List<dynamic> _salones = [];
  int? _carreraId;
  int _semestre = 1;
  int? _profesorId;
  int? _salonId;
  List<Bloque> _bloques = [];
  bool _loading = false;
  int _conflictosGlobales = 0;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _loadFiltros();
  }

  Future<void> _loadFiltros() async {
    try {
      final c = await ApiService.get('/api/v1/carreras', requiresAuth: false);
      final s = await ApiService.get('/api/v1/salones', requiresAuth: false);
      final p = await ApiService.get('/api/v1/users?rol=profesor&per_page=50');
      if (mounted) {
        setState(() {
        _carreras = c['data'] as List;
        _salones = s['data'] as List;
        _profesores = p['data'] as List;
        if (_carreras.isNotEmpty) _carreraId = _carreras.first['id'] as int;
        if (_salones.isNotEmpty) _salonId = _salones.first['id'] as int;
        if (_profesores.isNotEmpty) _profesorId = _profesores.first['id'] as int;
      });
      }
    } catch (_) {}
  }

  Future<void> _cargarVistaCarrera() async {
    if (_carreraId == null) return;
    setState(() { _loading = true; _bloques = []; });
    try {
      final r = await ApiService.get(
        '/api/v1/horarios/admin/vista-carrera'
        '?carrera_id=$_carreraId&semestre=$_semestre');
      if (mounted) {
        setState(() {
        _bloques = ((r['bloques_consolidados'] as List?) ?? [])
          .map((j) => Bloque.fromJson(j as Map<String, dynamic>)).toList();
        _conflictosGlobales = r['conflictos_globales'] as int? ?? 0;
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _cargarVistaSalon() async {
    if (_salonId == null) return;
    setState(() { _loading = true; _bloques = []; });
    try {
      final r = await ApiService.get(
        '/api/v1/horarios/admin/vista-salon?salon_id=$_salonId');
      // Convertir disponibilidad_semana a Bloques
      final disp = r['disponibilidad_semana'] as Map<String, dynamic>? ?? {};
      final bloques = <Bloque>[];
      disp.forEach((dia, list) {
        for (final b in (list as List)) {
          final m = b as Map<String, dynamic>;
          bloques.add(Bloque(
            id: bloques.length, dia: dia,
            horaInicio: m['hora_inicio'] as String,
            horaFin: m['hora_fin'] as String,
            conflicto: false,
            materia: {'nombre': m['materia'] ?? 'Ocupado',
                      'nombre_corto': m['materia'] ?? 'Ocupado',
                      'tipo': 'tronco_comun'},
            profesor: m['profesor'] != null
              ? {'nombre_completo': m['profesor']} : null,
          ));
        }
      });
      if (mounted) setState(() { _bloques = bloques; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _cargarVistaProfesor() async {
    if (_profesorId == null) return;
    setState(() { _loading = true; _bloques = []; });
    try {
      final r = await ApiService.get(
        '/api/v1/horarios/admin/vista-profesor?profesor_id=$_profesorId');
      if (mounted) {
        setState(() {
        _bloques = ((r['bloques'] as List?) ?? [])
          .map((j) => Bloque.fromJson(j as Map<String, dynamic>)).toList();
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Horarios'),
        bottom: TabBar(
          controller: _tabs,
          labelColor: MapColors.surface0,
          indicatorColor: MapColors.surface0,
          tabs: const [
            Tab(text: 'Por carrera'),
            Tab(text: 'Por salón'),
            Tab(text: 'Por profesor'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          _vistaCarrera(),
          _vistaSalon(),
          _vistaProfesor(),
        ],
      ),
    );
  }

  Widget _vistaCarrera() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: DropdownButtonFormField<int>(
                initialValue: _carreraId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Carrera',
                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                items: [for (final c in _carreras)
                  DropdownMenuItem(value: c['id'] as int,
                    child: Text(c['nombre_corto'] as String? ??
                                 c['nombre'] as String,
                      overflow: TextOverflow.ellipsis))],
                onChanged: (v) => setState(() => _carreraId = v),
              )),
              const SizedBox(width: 8),
              SizedBox(width: 100, child: DropdownButtonFormField<int>(
                initialValue: _semestre,
                decoration: const InputDecoration(labelText: 'Sem',
                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                items: [for (var i = 1; i <= 8; i++)
                  DropdownMenuItem(value: i, child: Text('$i'))],
                onChanged: (v) => setState(() => _semestre = v ?? 1),
              )),
            ],
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text('Cargar'),
            onPressed: _loading ? null : _cargarVistaCarrera,
          ),
          const SizedBox(height: 8),
          if (_conflictosGlobales > 0)
            Text('⚠ $_conflictosGlobales conflictos globales',
              style: MapText.b14.copyWith(color: MapColors.warning,
                                          fontWeight: FontWeight.w700)),
          Expanded(child: _gridOrEmpty()),
        ],
      ),
    );
  }

  Widget _vistaSalon() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DropdownButtonFormField<int>(
            initialValue: _salonId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Salón',
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
            items: [for (final s in _salones)
              DropdownMenuItem(value: s['id'] as int,
                child: Text('${s['codigo']} · ${s['nombre'] ?? ''}',
                  overflow: TextOverflow.ellipsis))],
            onChanged: (v) => setState(() => _salonId = v),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text('Cargar'),
            onPressed: _loading ? null : _cargarVistaSalon,
          ),
          Expanded(child: _gridOrEmpty()),
        ],
      ),
    );
  }

  Widget _vistaProfesor() {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DropdownButtonFormField<int>(
            initialValue: _profesorId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Profesor',
              contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
            items: [for (final p in _profesores)
              DropdownMenuItem(value: p['id'] as int,
                child: Text(p['nombre_completo'] as String,
                  overflow: TextOverflow.ellipsis))],
            onChanged: (v) => setState(() => _profesorId = v),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            icon: const Icon(Icons.refresh),
            label: const Text('Cargar'),
            onPressed: _loading ? null : _cargarVistaProfesor,
          ),
          Expanded(child: _gridOrEmpty()),
        ],
      ),
    );
  }

  Widget _gridOrEmpty() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_bloques.isEmpty) {
      return Center(child: Text('Carga datos para ver el horario',
        style: MapText.b14.copyWith(color: MapColors.ink600)));
    }
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: ScheduleGrid(bloques: _bloques),
    );
  }

  @override
  void dispose() { _tabs.dispose(); super.dispose(); }
}
