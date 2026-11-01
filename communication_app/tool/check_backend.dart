import 'dart:io';

import 'package:communication_app/api/backend_client.dart';

/// Runs the app's real client against a live backend, without a device.
Future<void> main(List<String> args) async {
  final client = BackendClient(
    baseUrl: args.isEmpty ? 'http://localhost:8000' : args.first,
  );
  try {
    final status = await client.fetchStatus();
    stdout.writeln('ready=${status.isReady} checks=${status.checks}');
    exitCode = status.isReady ? 0 : 1;
  } on BackendUnreachable catch (error) {
    stderr.writeln(error);
    exitCode = 2;
  } finally {
    client.close();
  }
}
