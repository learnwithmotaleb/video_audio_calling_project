import 'package:flutter/material.dart';

import '../api/backend_client.dart';

class StatusScreen extends StatefulWidget {
  const StatusScreen({super.key, required this.client});

  final BackendClient client;

  @override
  State<StatusScreen> createState() => _StatusScreenState();
}

class _StatusScreenState extends State<StatusScreen> {
  late Future<BackendStatus> _status = widget.client.fetchStatus();

  void _refresh() {
    setState(() {
      _status = widget.client.fetchStatus();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Communication')),
      body: FutureBuilder<BackendStatus>(
        future: _status,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _Unreachable(baseUrl: widget.client.baseUrl);
          }
          return _StatusList(status: snapshot.requireData);
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _refresh,
        tooltip: 'Refresh',
        child: const Icon(Icons.refresh),
      ),
    );
  }
}

class _Unreachable extends StatelessWidget {
  const _Unreachable({required this.baseUrl});

  final String baseUrl;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          'Cannot reach the backend at $baseUrl',
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

class _StatusList extends StatelessWidget {
  const _StatusList({required this.status});

  final BackendStatus status;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        ListTile(
          title: Text(status.isReady ? 'Backend ready' : 'Backend degraded'),
        ),
        const Divider(),
        for (final check in status.checks.entries)
          ListTile(
            leading: Icon(
              check.value == 'ok' ? Icons.check_circle : Icons.error,
              color: check.value == 'ok' ? Colors.green : Colors.red,
            ),
            title: Text(check.key),
            trailing: Text(check.value),
          ),
      ],
    );
  }
}
