import 'dart:convert';

import 'package:http/http.dart' as http;

/// Readiness reported by the backend's `/api/v1/health/ready` endpoint.
class BackendStatus {
  const BackendStatus({required this.isReady, required this.checks});

  final bool isReady;
  final Map<String, String> checks;
}

/// What the app needs to join a LiveKit room.
class CallCredentials {
  const CallCredentials({required this.url, required this.token});

  final String url;
  final String token;
}

class BackendUnreachable implements Exception {
  const BackendUnreachable(this.cause);

  final Object cause;

  @override
  String toString() => 'BackendUnreachable: $cause';
}

/// The backend answered, and refused the request.
class BackendRejected implements Exception {
  const BackendRejected(this.message);

  final String message;

  @override
  String toString() => message;
}

class BackendClient {
  BackendClient({required this.baseUrl, http.Client? httpClient})
      : _http = httpClient ?? http.Client();

  static const _timeout = Duration(seconds: 5);
  static const _callTokenTimeout = Duration(seconds: 10);

  final String baseUrl;
  final http.Client _http;

  /// A 503 is a valid answer: the backend is up but a dependency is down.
  Future<BackendStatus> fetchStatus() async {
    try {
      final uri = Uri.parse('$baseUrl/api/v1/health/ready');
      final response = await _http.get(uri).timeout(_timeout);
      if (response.statusCode != 200 && response.statusCode != 503) {
        throw BackendUnreachable('HTTP ${response.statusCode}');
      }

      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final checks = (body['checks'] as Map<String, dynamic>)
          .map((name, status) => MapEntry(name, status as String));
      return BackendStatus(isReady: body['status'] == 'ok', checks: checks);
    } on BackendUnreachable {
      rethrow;
    } catch (error) {
      throw BackendUnreachable(error);
    }
  }

  /// [userId] is the temporary development identity. The authentication
  /// service will replace this header.
  Future<CallCredentials> fetchCallCredentials({
    required String userId,
    required String roomId,
  }) async {
    final http.Response response;
    try {
      response = await _http
          .post(
            Uri.parse('$baseUrl/api/v1/calls/token'),
            headers: {
              'Content-Type': 'application/json',
              'X-Dev-User-Id': userId,
            },
            body: jsonEncode({'room_id': roomId}),
          )
          .timeout(_callTokenTimeout);
    } catch (error) {
      throw BackendUnreachable(error);
    }

    final Map<String, dynamic> body;
    try {
      body = jsonDecode(response.body) as Map<String, dynamic>;
    } on FormatException catch (error) {
      throw BackendUnreachable(error);
    }

    if (response.statusCode != 200) {
      final error = body['error'] as Map<String, dynamic>?;
      throw BackendRejected(error?['message'] as String? ?? 'Request failed');
    }
    return CallCredentials(
      url: body['url'] as String,
      token: body['token'] as String,
    );
  }

  void close() => _http.close();
}
