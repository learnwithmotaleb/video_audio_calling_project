# Communication App

Flutter client for the self-hosted communication backend.

**Current status:** audio and video calls between devices in the same room, with mute, camera on/off, camera switching and a backend status screen. There are no accounts yet: the name you type is a temporary development identity.

## Run

Start the backend first, then open an iOS simulator or Android emulator:

```bash
flutter run
```

To use another backend address:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

A physical phone needs the Mac's LAN address, must be on the same network, and the backend needs `API_BIND_IP=0.0.0.0` and `LIVEKIT_NODE_IP` set to that address.

## Make a call

Run the app on two devices. Enter a different name on each and the same room, then tap **Audio call** or **Video call**. The iOS simulator has no camera, so test video on a real device or an Android emulator.

## Test

```bash
flutter test
flutter analyze
dart run tool/check_backend.dart
```

The last command uses the app's real client against the running backend and needs no device.
