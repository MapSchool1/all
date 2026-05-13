import 'package:flutter/material.dart';
import '../../models/salon_detail.dart';
import '../../services/api_service.dart';
import '../../theme/colors.dart';
import '../../theme/text_styles.dart';
import '../../widgets/status_badge.dart';

class SalonDetailScreen extends StatefulWidget {
  final int salonId;
  final String? codigo;
  const SalonDetailScreen({super.key, required this.salonId, this.codigo});

  @override
  State<SalonDetailScreen> createState() => _SalonDetailScreenState();
}

class _SalonDetailScreenState extends State<SalonDetailScreen> {
  SalonDetail? _detail;
  bool _loading = true;
  String? _error;

  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final r = await ApiService.get('/api/v1/salones/${widget.salonId}');
      if (mounted) {
        setState(() {
        _detail = SalonDetail.fromResponse(r); _loading = false;
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

  static const _dias = ['lun', 'mar', 'mie', 'jue', 'vie', 'sab'];
  static const _diasLbl = {'lun':'Lun','mar':'Mar','mie':'Mié',
                           'jue':'Jue','vie':'Vie','sab':'Sáb'};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.codigo ?? 'Salón')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _error != null
          ? Center(child: Text(_error!,
              style: MapText.b14.copyWith(color: MapColors.danger)))
          : _build(),
    );
  }

  Widget _build() {
    final d = _detail!;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Text(d.salon.codigo,
              style: MapText.display(32, w: FontWeight.w700)),
            const SizedBox(width: 12),
            StatusBadge(
              d.disponibleAhora ? 'Libre ahora' : 'Ocupado ahora',
              color: d.disponibleAhora ? MapColors.success : MapColors.warning,
            ),
          ],
        ),
        if (d.salon.nombre != null) ...[
          const SizedBox(height: 4),
          Text(d.salon.nombre!,
            style: MapText.b14.copyWith(color: MapColors.ink600)),
        ],
        const SizedBox(height: 16),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: [
            _chip('${d.salon.capacidad} cupos'),
            _chip('Piso ${d.salon.piso}'),
            _chip((d.salon.tipo ?? '').replaceAll('_', ' ')),
            _chip('Edif. ${d.salon.edificioClave}'),
          ],
        ),
        if (d.descripcion != null && d.descripcion!.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(d.descripcion!, style: MapText.b14),
        ],
        const SizedBox(height: 24),
        Text('Disponibilidad semanal', style: MapText.d20),
        const SizedBox(height: 8),
        _availabilityGrid(d),
        const SizedBox(height: 24),
        Text('Equipamiento', style: MapText.d20),
        const SizedBox(height: 8),
        if (d.equipamiento.isEmpty)
          Text('Sin equipamiento registrado.',
            style: MapText.b14.copyWith(color: MapColors.ink600))
        else
          Wrap(
            spacing: 8, runSpacing: 8,
            children: d.equipamiento.map((e) => Chip(
              avatar: const Icon(Icons.check, size: 16,
                                 color: MapColors.success),
              label: Text(e.replaceAll('_', ' ')),
              backgroundColor: MapColors.successBg,
              side: const BorderSide(color: MapColors.success),
            )).toList(),
          ),
      ],
    );
  }

  Widget _chip(String label) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    decoration: BoxDecoration(
      color: MapColors.surface150,
      borderRadius: BorderRadius.circular(999),
    ),
    child: Text(label,
      style: MapText.b12.copyWith(color: MapColors.ink800,
                                  fontWeight: FontWeight.w500)),
  );

  Widget _availabilityGrid(SalonDetail d) {
    final horas = List.generate(14, (i) => i + 7); // 07..20
    const cellH = 28.0;
    return Container(
      decoration: BoxDecoration(
        color: MapColors.surface0,
        border: Border.all(color: MapColors.line200),
        borderRadius: BorderRadius.circular(8),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Column(
          children: [
            Row(
              children: [
                _headerCell('Hora', 50),
                for (final dia in _dias) _headerCell(_diasLbl[dia]!, 80),
              ],
            ),
            for (final h in horas)
              Row(
                children: [
                  Container(
                    width: 50, height: cellH * 2 + 4,
                    alignment: Alignment.topRight,
                    padding: const EdgeInsets.all(4),
                    color: MapColors.surface100,
                    child: Text('${h.toString().padLeft(2, '0')}:00',
                      style: MapText.mono(10, color: MapColors.ink600)),
                  ),
                  for (final dia in _dias) _cell(d, dia, h, cellH),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _headerCell(String text, double w) => Container(
    width: w, height: 28, alignment: Alignment.center,
    color: MapColors.navy800,
    child: Text(text.toUpperCase(),
      style: MapText.mono(10, w: FontWeight.w700, color: MapColors.surface0)),
  );

  Widget _cell(SalonDetail d, String dia, int h, double cellH) {
    final ocup = d.disponibilidad[dia]?.firstWhere(
      (b) => b.horaH == h,
      orElse: () => SalonDisponibilidad(horaInicio: '', horaFin: ''),
    );
    final hasOcup = ocup != null && ocup.horaInicio.isNotEmpty;
    return Container(
      width: 80, height: cellH * 2 + 4,
      padding: const EdgeInsets.all(2),
      decoration: const BoxDecoration(
        border: Border(
          left: BorderSide(color: MapColors.line200),
          top: BorderSide(color: MapColors.line200),
        ),
      ),
      child: hasOcup
        ? Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: MapColors.navy800,
              borderRadius: BorderRadius.circular(3),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(ocup.materia ?? 'Ocupado',
                  style: MapText.body(9, w: FontWeight.w700,
                                      color: MapColors.surface0),
                  maxLines: 2, overflow: TextOverflow.ellipsis),
                Text('${ocup.horaInicio}–${ocup.horaFin}',
                  style: MapText.mono(8,
                    color: MapColors.surface0.withValues(alpha: 0.8))),
              ],
            ),
          )
        : Container(color: MapColors.surface150),
    );
  }
}
