# Build de release Android

El APK de `flutter build apk --release` por defecto se firma con la clave de
debug (incluida en el SDK). Esto sirve para pruebas locales pero **no se puede
publicar en Play Store** ni se puede actualizar una app firmada con otra clave.

## 1. Generar el keystore (una sola vez, guárdalo seguro)

```bash
keytool -genkey -v \
  -keystore ~/matute-release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias matute
```

Te pedirá:
- Contraseña del keystore (≥6 caracteres)
- Nombre, organización, ciudad, país (CN, OU, O, L, ST, C)
- Contraseña del alias (puede ser la misma que el keystore)

Guarda el `.jks` en un lugar seguro **fuera del repo** (idealmente respaldado en un
gestor de contraseñas o vault). Si lo pierdes, no podrás actualizar la app.

## 2. Configurar `key.properties`

```bash
cp android/key.properties.example android/key.properties
$EDITOR android/key.properties
```

Llena los valores con tu keystore real. **No commitear** este archivo (`.gitignore`
ya lo excluye).

## 3. Construir APK / App Bundle

```bash
# APK (instalación directa)
flutter build apk --release --target-platform android-arm64
# → build/app/outputs/flutter-apk/app-release.apk

# AAB (Play Store)
flutter build appbundle --release
# → build/app/outputs/bundle/release/app-release.aab
```

El `build.gradle.kts` detecta automáticamente si existe `key.properties` y firma
con la clave release. Si no existe, vuelve a la firma de debug (útil en CI o
desarrollo local sin las claves).

## 4. Verificar firma

```bash
jarsigner -verify -verbose -certs build/app/outputs/flutter-apk/app-release.apk
```

Debe decir `jar verified.` y mostrar el alias `matute`.

## 5. Subir a Play Store

1. Crea la ficha en [Play Console](https://play.google.com/console).
2. Sube el `.aab` en *Producción → Crear nueva versión*.
3. Habilita Play App Signing (Google guarda una copia de tu clave de subida).

## CI/CD

Para builds automáticos, guarda el contenido del `.jks` como secreto base64
y `key.properties` como secretos individuales. Decodifica antes del build.
