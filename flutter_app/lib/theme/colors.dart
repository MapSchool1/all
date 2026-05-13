import 'package:flutter/material.dart';

/// MapSchool tokens — espejo exacto de tokens.css.
/// Nunca uses Color(0xFF...) inline en widgets.
class MapColors {
  static const navy950   = Color(0xFF0B1423);
  static const navy900   = Color(0xFF031633);
  static const navy800   = Color(0xFF172846); // primary
  static const navy700   = Color(0xFF233C5B);
  static const navy600   = Color(0xFF304B7A);
  static const navy500   = Color(0xFF3C61A5);
  static const navy400   = Color(0xFF6DB4D2);
  static const navy300   = Color(0xFF9FCDE3);
  static const navy200   = Color(0xFFCFE2FF);
  static const navy100   = Color(0xFFE8F1FF);

  static const surface0   = Color(0xFFFFFFFF);
  static const surface50  = Color(0xFFFCFCFD);
  static const surface100 = Color(0xFFF8F9FA);
  static const surface150 = Color(0xFFF1F3F5);
  static const surface200 = Color(0xFFE9ECEF);

  static const ink900 = Color(0xFF212529);
  static const ink800 = Color(0xFF343A40);
  static const ink700 = Color(0xFF495057);
  static const ink600 = Color(0xFF6C757D);
  static const ink500 = Color(0xFF9899A8);
  static const ink400 = Color(0xFFADB5BD);
  static const ink300 = Color(0xFFCED4DA);

  static const line200 = Color(0xFFE9ECEF);
  static const line300 = Color(0xFFDEE2E6);

  static const success = Color(0xFF28A745);
  static const danger  = Color(0xFFDC3545);
  static const warning = Color(0xFFF2B705);
  static const info    = Color(0xFF0D6EFD);

  static const successBg = Color(0xFFE6F4EA);
  static const dangerBg  = Color(0xFFFBE9EB);
  static const warningBg = Color(0xFFFEF7E0);
  static const infoBg    = Color(0xFFE7F0FF);

  // Schedule blocks
  static const bloqueTroncoComun     = navy800;
  static const bloqueAreaProfesional = navy500;
  static const bloqueLaboratorio     = success;
  static const bloqueIdiomas         = navy400;
  static const bloqueConflicto       = warning;

  static Color statusColor(String estado) {
    switch (estado) {
      case 'activo':
      case 'publicado':
      case 'listo':
        return success;
      case 'suspendido':
      case 'pendiente_pago':
      case 'borrador':
        return warning;
      case 'inactivo':
      case 'archivado':
      case 'entregado':
        return ink400;
      case 'eliminado':
      case 'rechazado':
        return danger;
      default:
        return ink400;
    }
  }

  static Color bloqueColor(String? tipo) {
    switch (tipo) {
      case 'tronco_comun': return bloqueTroncoComun;
      case 'area_profesional': return bloqueAreaProfesional;
      case 'laboratorio': return bloqueLaboratorio;
      case 'idiomas': return bloqueIdiomas;
      default: return navy600;
    }
  }
}
