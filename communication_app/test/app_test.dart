import 'package:communication_app/api/backend_client.dart';
import 'package:communication_app/main.dart';
import 'package:communication_app/screens/status_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const _ready = '{"status":"ok","checks":{"database":"ok","redis":"ok"}}';
const _degraded =
    '{"status":"unavailable","checks":{"database":"ok","redis":"unavailable"}}';

BackendClient _clientReturning(String body, int status) => BackendClient(
      baseUrl: 'http://backend.test',
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/health/ready');
        return http.Response(body, status);
      }),
    );

BackendClient _clientForToken(String body, int status) => BackendClient(
      baseUrl: 'http://backend.test',
      httpClient: MockClient((_) async => http.Response(body, status)),
    );

void main() {
  test('503 is parsed as a degraded backend, not an error', () async {
    final status = await _clientReturning(_degraded, 503).fetchStatus();
    expect(status.isReady, isFalse);
    expect(status.checks['redis'], 'unavailable');
  });

  test('unexpected responses are reported as unreachable', () async {
    await expectLater(
      _clientReturning('nope', 500).fetchStatus(),
      throwsA(isA<BackendUnreachable>()),
    );
    await expectLater(
      _clientReturning('not json', 200).fetchStatus(),
      throwsA(isA<BackendUnreachable>()),
    );
  });

  testWidgets('shows each dependency when the backend is ready', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: StatusScreen(client: _clientReturning(_ready, 200))),
    );
    await tester.pumpAndSettle();
    expect(find.text('Backend ready'), findsOneWidget);
    expect(find.text('database'), findsOneWidget);
    expect(find.text('redis'), findsOneWidget);
  });

  testWidgets('shows a failed dependency', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: StatusScreen(client: _clientReturning(_degraded, 503))),
    );
    await tester.pumpAndSettle();
    expect(find.text('Backend degraded'), findsOneWidget);
    expect(find.byIcon(Icons.error), findsOneWidget);
  });

  testWidgets('refresh recovers after the backend comes back', (tester) async {
    var online = false;
    final client = BackendClient(
      baseUrl: 'http://backend.test',
      httpClient: MockClient((_) async {
        if (!online) throw http.ClientException('connection refused');
        return http.Response(_ready, 200);
      }),
    );

    await tester.pumpWidget(MaterialApp(home: StatusScreen(client: client)));
    await tester.pumpAndSettle();
    expect(find.textContaining('Cannot reach the backend'), findsOneWidget);

    online = true;
    await tester.tap(find.byIcon(Icons.refresh));
    await tester.pumpAndSettle();
    expect(find.text('Backend ready'), findsOneWidget);
  });

  test('call credentials send the identity and room to the backend', () async {
    final client = BackendClient(
      baseUrl: 'http://backend.test',
      httpClient: MockClient((request) async {
        expect(request.url.path, '/api/v1/calls/token');
        expect(request.headers['X-Dev-User-Id'], 'alice');
        expect(request.body, '{"room_id":"demo"}');
        return http.Response('{"url":"ws://lk.test","token":"jwt"}', 200);
      }),
    );
    final credentials = await client.fetchCallCredentials(
      userId: 'alice',
      roomId: 'demo',
    );
    expect(credentials.url, 'ws://lk.test');
    expect(credentials.token, 'jwt');
  });

  test('a backend refusal keeps its message', () async {
    final client = _clientForToken(
      '{"error":{"code":"livekit_unavailable","message":"The media server is unavailable"}}',
      502,
    );
    await expectLater(
      client.fetchCallCredentials(userId: 'alice', roomId: 'demo'),
      throwsA(
        isA<BackendRejected>().having(
          (error) => error.message,
          'message',
          'The media server is unavailable',
        ),
      ),
    );
  });

  testWidgets('join screen requires a valid name before calling', (
    tester,
  ) async {
    var requests = 0;
    final client = BackendClient(
      baseUrl: 'http://backend.test',
      httpClient: MockClient((_) async {
        requests++;
        return http.Response('{}', 500);
      }),
    );
    await tester.pumpWidget(CommunicationApp(client: client));

    await tester.tap(find.text('Audio call'));
    await tester.pump();
    expect(find.textContaining('no spaces'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'bad name');
    await tester.tap(find.text('Video call'));
    await tester.pump();
    expect(find.textContaining('no spaces'), findsOneWidget);
    expect(requests, 0);
  });
}
