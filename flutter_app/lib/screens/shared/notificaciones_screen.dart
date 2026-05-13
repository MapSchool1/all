import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';

class NotificacionesScreen extends StatefulWidget {
  const NotificacionesScreen({super.key});
  @override
  State<NotificacionesScreen> createState() => _NotificacionesScreenState();
}

class _NotificacionesScreenState extends State<NotificacionesScreen> {
  List<dynamic> _items = [];
  bool _loading = true;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/notificaciones?per_page=30');
      if (mounted) {
        setState(() {
        _items = r['data'] as List; _loading = false;
      });
      }
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _markAll() async {
    try {
      await ApiService.post('/api/v1/notificaciones/leer-todas');
      _load();
    } catch (_) {}
  }

  IconData _icon(String? tipo) {
    switch (tipo) {
      case 'horario': return Icons.calendar_today_outlined;
      case 'calificacion': return Icons.bar_chart_outlined;
      case 'tramite': return Icons.description_outlined;
      case 'anuncio': return Icons.campaign_outlined;
      case 'conflicto': return Icons.warning_amber_outlined;
      default: return Icons.notifications_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notificaciones'),
        actions: [
          TextButton(onPressed: _markAll,
            child: Text('Marcar todas',
              style: MapText.b14.copyWith(color: MapColors.surface0))),
        ],
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _items.isEmpty
          ? Center(child: Text('Sin notificaciones',
                              style: MapText.b14.copyWith(color: MapColors.ink600)))
          : ListView.separated(
              itemCount: _items.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (_, i) {
                final n = _items[i] as Map<String, dynamic>;
                return ListTile(
                  leading: Icon(_icon(n['tipo']),
                                color: MapColors.navy600),
                  title: Text(n['titulo'] as String,
                    style: MapText.b14.copyWith(
                      fontWeight: n['leida'] == false
                        ? FontWeight.w700 : FontWeight.w400)),
                  subtitle: Text(n['cuerpo'] as String? ?? '',
                                 maxLines: 2, overflow: TextOverflow.ellipsis),
                  trailing: n['leida'] == false
                    ? Container(width: 8, height: 8,
                        decoration: const BoxDecoration(
                          color: MapColors.danger, shape: BoxShape.circle))
                    : null,
                );
              },
            ),
    );
  }
}
