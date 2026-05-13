import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'colors.dart';

ThemeData buildTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: MapColors.navy800,
    primary: MapColors.navy800,
    secondary: MapColors.navy500,
    error: MapColors.danger,
    surface: MapColors.surface0,
    onPrimary: MapColors.surface0,
    onSurface: MapColors.ink900,
    brightness: Brightness.light,
  );

  final base = ThemeData.from(colorScheme: scheme, useMaterial3: true);

  return base.copyWith(
    scaffoldBackgroundColor: MapColors.surface100,
    textTheme: GoogleFonts.dmSansTextTheme(base.textTheme).apply(
      bodyColor: MapColors.ink900,
      displayColor: MapColors.ink900,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: MapColors.navy800,
      foregroundColor: MapColors.surface0,
      elevation: 0,
      centerTitle: false,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: MapColors.navy800,
        foregroundColor: MapColors.surface0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(6),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        minimumSize: const Size(0, 40),
        textStyle: GoogleFonts.dmSans(fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: MapColors.navy800,
        side: const BorderSide(color: MapColors.navy800),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(6),
        ),
        minimumSize: const Size(0, 40),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: MapColors.navy800,
        textStyle: GoogleFonts.dmSans(fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: MapColors.surface0,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: MapColors.line300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: MapColors.line300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(6),
        borderSide: const BorderSide(color: MapColors.navy700, width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
    ),
    cardTheme: CardThemeData(
      color: MapColors.surface0,
      surfaceTintColor: Colors.transparent,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: MapColors.line200),
      ),
    ),
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: MapColors.surface0,
      selectedItemColor: MapColors.navy800,
      unselectedItemColor: MapColors.ink500,
      type: BottomNavigationBarType.fixed,
      showUnselectedLabels: true,
    ),
    progressIndicatorTheme: const ProgressIndicatorThemeData(
      color: MapColors.navy800,
    ),
    dividerColor: MapColors.line200,
  );
}
