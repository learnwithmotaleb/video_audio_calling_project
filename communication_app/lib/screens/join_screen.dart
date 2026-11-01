import 'package:flutter/material.dart';

import '../api/backend_client.dart';
import 'call_screen.dart';
import 'status_screen.dart';

final _idPattern = RegExp(r'^[A-Za-z0-9_-]{1,64}$');

class JoinScreen extends StatefulWidget {
  const JoinScreen({super.key, required this.client});

  final BackendClient client;

  @override
  State<JoinScreen> createState() => _JoinScreenState();
}

class _JoinScreenState extends State<JoinScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _room = TextEditingController(text: 'demo');
  bool _joining = false;

  @override
  void dispose() {
    _name.dispose();
    _room.dispose();
    super.dispose();
  }

  String? _validateId(String? value) => _idPattern.hasMatch(value ?? '')
      ? null
      : 'Use letters, numbers, - or _ with no spaces';

  Future<void> _join({required bool withVideo}) async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _joining = true;
    });
    try {
      final credentials = await widget.client.fetchCallCredentials(
        userId: _name.text,
        roomId: _room.text,
      );
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => CallScreen(
            credentials: credentials,
            roomName: _room.text,
            startWithVideo: withVideo,
          ),
        ),
      );
    } on BackendRejected catch (error) {
      _showError(error.message);
    } on BackendUnreachable {
      _showError('Cannot reach the backend at ${widget.client.baseUrl}');
    } finally {
      if (mounted) {
        setState(() {
          _joining = false;
        });
      }
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Communication'),
        actions: [
          IconButton(
            icon: const Icon(Icons.dns_outlined),
            tooltip: 'Backend status',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => StatusScreen(client: widget.client),
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              TextFormField(
                controller: _name,
                autocorrect: false,
                decoration: const InputDecoration(labelText: 'Your name'),
                validator: _validateId,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _room,
                autocorrect: false,
                decoration: const InputDecoration(labelText: 'Room'),
                validator: _validateId,
              ),
              const SizedBox(height: 32),
              FilledButton.icon(
                onPressed: _joining ? null : () => _join(withVideo: false),
                icon: const Icon(Icons.call),
                label: const Text('Audio call'),
              ),
              const SizedBox(height: 12),
              FilledButton.tonalIcon(
                onPressed: _joining ? null : () => _join(withVideo: true),
                icon: const Icon(Icons.videocam),
                label: const Text('Video call'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
