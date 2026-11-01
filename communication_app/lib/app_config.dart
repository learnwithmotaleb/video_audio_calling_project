import 'package:flutter/foundation.dart';

/// Backend address. Override with `--dart-define=API_BASE_URL=http://host:8000`.
String resolveApiBaseUrl() {
  const configured = String.fromEnvironment('API_BASE_URL');
  if (configured.isNotEmpty) return configured;

  // The Android emulator reaches the host machine through 10.0.2.2.
  return defaultTargetPlatform == TargetPlatform.android
      ? 'http://10.0.2.2:8000'
      : 'http://localhost:8000';
}
