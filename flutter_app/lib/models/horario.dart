import 'bloque.dart';

class Horario {
  final int id;
  final String nombre;
  final String estado;
  final int totalCreditos;
  final int totalHoras;
  final bool tieneConflictos;
  final List<Bloque> bloques;

  Horario({
    required this.id,
    required this.nombre,
    required this.estado,
    required this.totalCreditos,
    required this.totalHoras,
    required this.tieneConflictos,
    required this.bloques,
  });

  factory Horario.fromResponse(Map<String, dynamic> r) {
    final h = r['horario'] as Map<String, dynamic>;
    final blqsList = (r['bloques'] as List?) ?? [];
    return Horario(
      id: h['id'] as int,
      nombre: h['nombre'] as String? ?? 'Mi horario',
      estado: h['estado'] as String,
      totalCreditos: h['total_creditos'] as int? ?? 0,
      totalHoras: h['total_horas'] as int? ?? 0,
      tieneConflictos: h['tiene_conflictos'] as bool? ?? false,
      bloques: blqsList.map((b) => Bloque.fromJson(b as Map<String, dynamic>)).toList(),
    );
  }
}
