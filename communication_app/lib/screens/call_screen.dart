import 'package:flutter/material.dart';
import 'package:livekit_client/livekit_client.dart';

import '../api/backend_client.dart';

class CallScreen extends StatefulWidget {
  const CallScreen({
    super.key,
    required this.credentials,
    required this.roomName,
    required this.startWithVideo,
  });

  final CallCredentials credentials;
  final String roomName;
  final bool startWithVideo;

  @override
  State<CallScreen> createState() => _CallScreenState();
}

class _CallScreenState extends State<CallScreen> {
  final _room = Room(
    roomOptions: const RoomOptions(adaptiveStream: true, dynacast: true),
  );
  late final EventsListener<RoomEvent> _events = _room.createListener();

  String? _error;
  bool _connected = false;
  bool _micEnabled = true;
  late bool _cameraEnabled = widget.startWithVideo;
  CameraPosition _cameraPosition = CameraPosition.front;

  @override
  void initState() {
    super.initState();
    _room.addListener(_onRoomChanged);
    _events.on<RoomDisconnectedEvent>((_) => _onRemoteDisconnect());
    _connect();
  }

  @override
  void dispose() {
    _room.removeListener(_onRoomChanged);
    _events.dispose();
    _room.disconnect().whenComplete(_room.dispose);
    super.dispose();
  }

  void _onRoomChanged() {
    if (mounted) setState(() {});
  }

  void _onRemoteDisconnect() {
    if (mounted && _connected) Navigator.of(context).pop();
  }

  Future<void> _connect() async {
    try {
      await _room.connect(widget.credentials.url, widget.credentials.token);
      final local = _room.localParticipant!;
      await local.setMicrophoneEnabled(true);
      if (mounted) {
        setState(() {
          _connected = true;
        });
      }
      if (widget.startWithVideo) await _startCamera(local);
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = 'Could not join the call: $error';
        });
      }
    }
  }

  /// A missing or refused camera must not end the call: audio keeps working.
  Future<void> _startCamera(LocalParticipant local) async {
    try {
      await local.setCameraEnabled(true);
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _cameraEnabled = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Camera is unavailable')),
      );
    }
  }

  Future<void> _toggleMic() async {
    final enabled = !_micEnabled;
    await _room.localParticipant?.setMicrophoneEnabled(enabled);
    setState(() {
      _micEnabled = enabled;
    });
  }

  Future<void> _toggleCamera() async {
    final local = _room.localParticipant;
    if (local == null) return;

    if (_cameraEnabled) {
      await local.setCameraEnabled(false);
      setState(() {
        _cameraEnabled = false;
      });
    } else {
      setState(() {
        _cameraEnabled = true;
      });
      await _startCamera(local);
    }
  }

  Future<void> _flipCamera() async {
    final track = _room.localParticipant?.videoTrackPublications
        .where((publication) => !publication.isScreenShare)
        .firstOrNull
        ?.track;
    if (track == null) return;

    final position = _cameraPosition.switched();
    await track.setCameraPosition(position);
    setState(() {
      _cameraPosition = position;
    });
  }

  void _hangUp() => Navigator.of(context).pop();

  @override
  Widget build(BuildContext context) {
    final local = _room.localParticipant;
    final participants = <Participant>[
      ?local,
      ..._room.remoteParticipants.values,
    ];

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        automaticallyImplyLeading: false,
        title: Text(widget.roomName),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(child: Text('${participants.length} in call')),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(child: _buildStage(participants)),
            _Controls(
              enabled: _connected,
              micEnabled: _micEnabled,
              cameraEnabled: _cameraEnabled,
              onToggleMic: _toggleMic,
              onToggleCamera: _toggleCamera,
              onFlipCamera: _flipCamera,
              onHangUp: _hangUp,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStage(List<Participant> participants) {
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            _error!,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.white),
          ),
        ),
      );
    }
    if (!_connected) {
      return const Center(child: CircularProgressIndicator());
    }
    return GridView.count(
      crossAxisCount: participants.length > 2 ? 2 : 1,
      childAspectRatio: participants.length > 2 ? 0.8 : 1.1,
      padding: const EdgeInsets.all(8),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      children: [
        for (final participant in participants)
          _ParticipantTile(
            key: ValueKey(participant.sid),
            participant: participant,
          ),
      ],
    );
  }
}

class _ParticipantTile extends StatelessWidget {
  const _ParticipantTile({super.key, required this.participant});

  final Participant participant;

  VideoTrack? _activeVideoTrack() {
    for (final publication in participant.videoTrackPublications) {
      final track = publication.track;
      if (track is VideoTrack && !publication.muted) return track;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: participant,
      builder: (context, _) {
        final track = _activeVideoTrack();
        final name = participant.name.isEmpty
            ? participant.identity
            : participant.name;
        return ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: DecoratedBox(
            decoration: BoxDecoration(
              color: Colors.grey.shade900,
              border: Border.all(
                color: participant.isSpeaking
                    ? Colors.greenAccent
                    : Colors.transparent,
                width: 2,
              ),
            ),
            child: Stack(
              fit: StackFit.expand,
              children: [
                if (track != null)
                  VideoTrackRenderer(track)
                else
                  const Center(
                    child: Icon(Icons.person, size: 64, color: Colors.white54),
                  ),
                Positioned(
                  left: 8,
                  bottom: 8,
                  child: Row(
                    children: [
                      if (participant.isMuted)
                        const Icon(
                          Icons.mic_off,
                          size: 16,
                          color: Colors.redAccent,
                        ),
                      const SizedBox(width: 4),
                      Text(name, style: const TextStyle(color: Colors.white)),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Controls extends StatelessWidget {
  const _Controls({
    required this.enabled,
    required this.micEnabled,
    required this.cameraEnabled,
    required this.onToggleMic,
    required this.onToggleCamera,
    required this.onFlipCamera,
    required this.onHangUp,
  });

  final bool enabled;
  final bool micEnabled;
  final bool cameraEnabled;
  final VoidCallback onToggleMic;
  final VoidCallback onToggleCamera;
  final VoidCallback onFlipCamera;
  final VoidCallback onHangUp;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          IconButton.filledTonal(
            tooltip: micEnabled ? 'Mute' : 'Unmute',
            onPressed: enabled ? onToggleMic : null,
            icon: Icon(micEnabled ? Icons.mic : Icons.mic_off),
          ),
          IconButton.filledTonal(
            tooltip: cameraEnabled ? 'Turn camera off' : 'Turn camera on',
            onPressed: enabled ? onToggleCamera : null,
            icon: Icon(cameraEnabled ? Icons.videocam : Icons.videocam_off),
          ),
          IconButton.filledTonal(
            tooltip: 'Switch camera',
            onPressed: enabled && cameraEnabled ? onFlipCamera : null,
            icon: const Icon(Icons.cameraswitch),
          ),
          IconButton.filled(
            tooltip: 'Leave call',
            style: IconButton.styleFrom(backgroundColor: Colors.red),
            onPressed: onHangUp,
            icon: const Icon(Icons.call_end, color: Colors.white),
          ),
        ],
      ),
    );
  }
}
