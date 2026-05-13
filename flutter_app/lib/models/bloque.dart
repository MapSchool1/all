class Bloque {
  final int id;
  final String dia;
  final String horaInicio;
  final String horaFin;
  final bool conflicto;
  final Map<String, dynamic>? materia;
  final Map<String, dynamic>? salon;
  final Map<String, dynamic>? profesor;

  Bloque({
    required this.id,
    required this.dia,
    required this.horaInicio,
    required this.horaFin,
    required this.conflicto,
    this.materia, this.salon, this.profesor,
  });

  String get materiaNombre =>
    (materia?['nombre_corto'] as String?) ??
    (materia?['nombre'] as String?) ?? '—';

  String get salonCodigo => (salon?['codigo'] as String?) ?? '—';

  String? get tipoMateria => materia?['tipo'] as String?;

  int get horaInicioH => int.parse(horaInicio.split(':')[0]);
  int get horaFinH => int.parse(horaFin.split(':')[0]);
  int get duracionH => horaFinH - horaInicioH;

  factory Bloque.fromJson(Map<String, dynamic> j) => Bloque(
    id: j['id'] as int,
    dia: j['dia'] as String,
    horaInicio: j['hora_inicio'] as String,
    horaFin: j['hora_fin'] as String,
    conflicto: j['conflicto'] as bool? ?? false,
    materia: j['materia'] as Map<String, dynamic>?,
    salon: j['salon'] as Map<String, dynamic>?,
    profesor: j['profesor'] as Map<String, dynamic>?,
  );
}
