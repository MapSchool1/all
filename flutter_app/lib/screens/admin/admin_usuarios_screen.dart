import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/avatar_widget.dart';
import '../../widgets/status_badge.dart';

class AdminUsuariosScreen extends StatefulWidget {
  final String? rolFiltro;
  const AdminUsuariosScreen({super.key, this.rolFiltro});
  @override
  State<AdminUsuariosScreen> createState() => _AdminUsuariosScreenState();
}

class _AdminUsuariosScreenState extends State<AdminUsuariosScreen> {
  List<dynamic> _users = [];
  bool _loading = true;
  int _page = 1, _pages = 1;
  String _search = '';
  String? _rol;
  String? _estado;

  @override
  void initState() {
    super.initState();
    _rol = widget.rolFiltro;
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final params = <String, String>{
      'per_page': '25', 'page': _page.toString(),
    };
    if (_search.isNotEmpty) params['search'] = _search;
    if (_rol != null && _rol!.isNotEmpty) params['rol'] = _rol!;
    if (_estado != null && _estado!.isNotEmpty) params['estado'] = _estado!;
    final qs = params.entries.map((e) => '${e.key}=${e.value}').join('&');
    try {
      final r = await ApiService.get('/api/v1/users?$qs');
      if (mounted) {
        setState(() {
        _users = r['data'] as List;
        _pages = r['pages'] as int? ?? 1;
        _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _accion(int uid, String accion) async {
    String? path;
    if (accion == 'suspender') {
      path = '/api/v1/users/$uid/suspender';
    } else if (accion == 'restablecer') {
      path = '/api/v1/users/$uid/restablecer';
    } else if (accion == 'eliminar') {
      final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
          title: const Text('Eliminar usuario'),
          content: const Text('Esta acción es soft-delete. ¿Continuar?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancelar')),
            TextButton(
              style: TextButton.styleFrom(foregroundColor: MapColors.danger),
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Eliminar')),
          ],
        ),
      );
      if (ok != true) return;
    }
    try {
      if (accion == 'eliminar') {
        await ApiService.delete('/api/v1/users/$uid');
      } else if (path != null) {
        await ApiService.post(path,
          body: accion == 'suspender' ? {'motivo': 'Vía panel'} : null);
      }
      _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Acción "$accion" completada'),
          backgroundColor: MapColors.success,
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: ${e.toString()}'),
          backgroundColor: MapColors.danger,
        ));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(
        widget.rolFiltro == 'estudiante' ? 'Estudiantes'
        : widget.rolFiltro == 'profesor' ? 'Profesores'
        : 'Usuarios')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                TextField(
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    hintText: 'Buscar nombre, email, expediente…',
                  ),
                  onChanged: (v) {
                    _search = v;
                    Future.delayed(const Duration(milliseconds: 250), () {
                      if (_search == v) { _page = 1; _load(); }
                    });
                  },
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Expanded(child: DropdownButtonFormField<String>(
                      initialValue: _rol,
                      isExpanded: true,
                      decoration: const InputDecoration(labelText: 'Rol',
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                      items: const [
                        DropdownMenuItem(value: '', child: Text('Todos')),
                        DropdownMenuItem(value: 'estudiante', child: Text('Estudiante')),
                        DropdownMenuItem(value: 'profesor', child: Text('Profesor')),
                        DropdownMenuItem(value: 'admin', child: Text('Admin')),
                        DropdownMenuItem(value: 'coordinador', child: Text('Coordinador')),
                        DropdownMenuItem(value: 'director', child: Text('Director')),
                      ],
                      onChanged: (v) { _rol = v; _page = 1; _load(); },
                    )),
                    const SizedBox(width: 8),
                    Expanded(child: DropdownButtonFormField<String>(
                      initialValue: _estado,
                      isExpanded: true,
                      decoration: const InputDecoration(labelText: 'Estado',
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
                      items: const [
                        DropdownMenuItem(value: '', child: Text('Todos')),
                        DropdownMenuItem(value: 'activo', child: Text('Activo')),
                        DropdownMenuItem(value: 'suspendido', child: Text('Suspendido')),
                      ],
                      onChanged: (v) { _estado = v; _page = 1; _load(); },
                    )),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _users.isEmpty
                ? Center(child: Text('Sin resultados',
                    style: MapText.b14.copyWith(color: MapColors.ink600)))
                : ListView.separated(
                    itemCount: _users.length,
                    separatorBuilder: (_, _) => const Divider(height: 1),
                    itemBuilder: (_, i) {
                      final u = _users[i] as Map<String, dynamic>;
                      return ListTile(
                        leading: AppAvatar(
                          iniciales: (u['iniciales'] as String?) ?? '·',
                          colorHex: u['avatar_color'] as String?,
                          size: 36),
                        title: Text(u['nombre_completo'] as String? ?? '—',
                          style: MapText.body(14, w: FontWeight.w600)),
                        subtitle: Text(
                          '${u['email']}${u['expediente'] != null ? " · ${u['expediente']}" : ""}',
                          style: MapText.b12.copyWith(color: MapColors.ink600)),
                        trailing: PopupMenuButton<String>(
                          onSelected: (v) => _accion(u['id'] as int, v),
                          itemBuilder: (_) => const [
                            PopupMenuItem(value: 'suspender',
                              child: Text('Suspender')),
                            PopupMenuItem(value: 'restablecer',
                              child: Text('Restablecer')),
                            PopupMenuDivider(),
                            PopupMenuItem(value: 'eliminar',
                              child: Text('Eliminar',
                                style: TextStyle(color: MapColors.danger))),
                          ],
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              StatusBadge.fromEstado(u['estado'] as String),
                              const Icon(Icons.more_vert, size: 18),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
          if (_pages > 1)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    icon: const Icon(Icons.chevron_left),
                    onPressed: _page > 1
                      ? () { _page--; _load(); } : null),
                  Text('Página $_page de $_pages',
                    style: MapText.b14),
                  IconButton(
                    icon: const Icon(Icons.chevron_right),
                    onPressed: _page < _pages
                      ? () { _page++; _load(); } : null),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
