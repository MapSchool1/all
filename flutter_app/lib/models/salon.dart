class Salon {
  final int id;
  final String codigo;
  final String? nombre;
  final String? tipo;
  final int capacidad;
  final int piso;
  final bool activo;
  final bool disponibleAhora;
  final String edificioClave;
  final int edificioId;

  Salon({
    required this.id,
    required this.codigo,
    this.nombre,
    this.tipo,
    required this.capacidad,
    required this.piso,
    required this.activo,
    required this.disponibleAhora,
    required this.edificioClave,
    required this.edificioId,
  });

  factory Salon.fromJson(Map<String, dynamic> j) => Salon(
    id: j['id'] as int,
    codigo: j['codigo'] as String,
    nombre: j['nombre'] as String?,
    tipo: j['tipo'] as String?,
    capacidad: j['capacidad'] as int? ?? 0,
    piso: j['piso'] as int? ?? 1,
    activo: j['activo'] as bool? ?? true,
    disponibleAhora: j['disponible_ahora'] as bool? ?? true,
    edificioClave: (j['edificio'] is Map) ? j['edificio']['clave'] as String : '?',
    edificioId: j['edificio_id'] as int? ?? 0,
  );
}
