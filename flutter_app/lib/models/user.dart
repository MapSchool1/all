class AppUser {
  final int id;
  final String nombre;
  final String apellidoP;
  final String? apellidoM;
  final String email;
  final String rol;
  final String estado;
  final String? expediente;
  final String avatarColor;
  final String? carreraNombre;
  final int? semestreActual;

  AppUser({
    required this.id,
    required this.nombre,
    required this.apellidoP,
    this.apellidoM,
    required this.email,
    required this.rol,
    required this.estado,
    this.expediente,
    this.avatarColor = '#172846',
    this.carreraNombre,
    this.semestreActual,
  });

  String get nombreCompleto =>
      [nombre, apellidoP, apellidoM].where((s) => s != null && s.isNotEmpty).join(' ');

  String get iniciales {
    final a = nombre.isNotEmpty ? nombre[0].toUpperCase() : '';
    final b = apellidoP.isNotEmpty ? apellidoP[0].toUpperCase() : '';
    return '$a$b';
  }

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
    id: j['id'] as int,
    nombre: j['nombre'] as String,
    apellidoP: j['apellido_p'] as String,
    apellidoM: j['apellido_m'] as String?,
    email: j['email'] as String,
    rol: j['rol'] as String,
    estado: j['estado'] as String,
    expediente: j['expediente'] as String?,
    avatarColor: j['avatar_color'] as String? ?? '#172846',
    carreraNombre: (j['carrera'] is Map) ? j['carrera']['nombre'] as String? : null,
    semestreActual: j['semestre_actual'] as int?,
  );
}
