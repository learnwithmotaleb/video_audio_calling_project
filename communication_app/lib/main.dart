import 'package:flutter/material.dart';

import 'api/backend_client.dart';
import 'app_config.dart';
import 'screens/join_screen.dart';

void main() {
  runApp(CommunicationApp(client: BackendClient(baseUrl: resolveApiBaseUrl())));
}

class CommunicationApp extends StatelessWidget {
  const CommunicationApp({super.key, required this.client});

  final BackendClient client;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Communication',
      theme: ThemeData(colorSchemeSeed: Colors.indigo),
      home: JoinScreen(client: client),
    );
  }
}
