import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'colors.dart';

/// MapSchool typography — Lexend display, DM Sans body, DM Mono mono.
/// Nunca uses TextStyle inline; usa estos helpers o las escalas predefinidas.
class MapText {
  static TextStyle display(double size,
      {FontWeight w = FontWeight.w700, Color? color}) {
    return GoogleFonts.lexend(
      fontSize: size, fontWeight: w,
      color: color ?? MapColors.ink900,
      letterSpacing: -0.01,
    );
  }

  static TextStyle body(double size,
      {FontWeight w = FontWeight.w400, Color? color}) {
    return GoogleFonts.dmSans(
      fontSize: size, fontWeight: w,
      color: color ?? MapColors.ink900, height: 1.45,
    );
  }

  static TextStyle mono(double size,
      {FontWeight w = FontWeight.w500, Color? color}) {
    return GoogleFonts.dmMono(
      fontSize: size, fontWeight: w,
      color: color ?? MapColors.ink700,
      letterSpacing: 0.06,
    );
  }

  // Escalas predefinidas
  static TextStyle get d48 => display(48, w: FontWeight.w700);
  static TextStyle get d32 => display(32, w: FontWeight.w700);
  static TextStyle get d24 => display(24, w: FontWeight.w700);
  static TextStyle get d20 => display(20, w: FontWeight.w600);
  static TextStyle get b16 => body(16);
  static TextStyle get b14 => body(14);
  static TextStyle get b12 => body(12);
  static TextStyle get monoBadge => mono(10, w: FontWeight.w700,
                                         color: MapColors.ink600).copyWith(
    letterSpacing: 1.0,
  );
}
