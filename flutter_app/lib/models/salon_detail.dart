import 'salon.dart';

class SalonDisponibilidad {
  final String horaInicio;
  final String horaFin;
  final String? materia;
  final String? profesor;
  SalonDisponibilidad({required this.horaInicio, required this.horaFin,
                       this.materia, this.profesor});
  factory SalonDisponibilidad.fromJson(Map<String, dynamic> j) =>
    SalonDisponibilidad(
      horaInicio: j['hora_inicio'] as String,
      horaFin: j['hora_fin'] as String,
      materia: j['materia'] as String?,
      profesor: j['profesor'] as String?,
    );
  int get horaH => int.parse(horaInicio.split(':')[0]);
  int get duracionH => int.parse(horaFin.split(':')[0]) - horaH;
}

class SalonDetail {
  final Salon salon;
  final bool disponibleAhora;
  final Map<String, List<SalonDisponibilidad>> disponibilidad;
  final List<String> equipamiento;
  final String? descripcion;

  SalonDetail({
    required this.salon,
    required this.disponibleAhora,
    required this.disponibilidad,
    required this.equipamiento,
    this.descripcion,
  });

  factory SalonDetail.fromResponse(Map<String, dynamic> r) {
    final s = r['salon'] as Map<String, dynamic>;
    final disp = (r['disponibilidad_semana'] as Map<String, dynamic>?) ?? {};
    final byDia = <String, List<SalonDisponibilidad>>{};
    disp.forEach((dia, list) {
      byDia[dia] = (list as List).map((j) =>
        SalonDisponibilidad.fromJson(j as Map<String, dynamic>)).toList();
    });
    return SalonDetail(
      salon: Salon.fromJson(s),
      disponibleAhora: r['disponible_ahora'] as bool? ?? true,
      disponibilidad: byDia,
      equipamiento: ((s['equipamiento'] as List?) ?? [])
        .cast<String>(),
      descripcion: s['descripcion'] as String?,
    );
  }
}
