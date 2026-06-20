import Foundation

/// Posts detected signals to the Warmth backend (`POST /api/signals`), which
/// forwards qualified leads into Zero CRM and kicks off the follow-up sequence.
final class SignalAPIClient {
    static let shared = SignalAPIClient()

    /// Override via the `WARMTH_API_BASE_URL` Info.plist key or build setting.
    private let baseURL: URL

    init() {
        let configured = Bundle.main.object(forInfoDictionaryKey: "WARMTH_API_BASE_URL") as? String
        self.baseURL = URL(string: configured ?? "http://localhost:8000")!
    }

    @discardableResult
    func send(_ signal: Signal) async -> Bool {
        let endpoint = baseURL.appendingPathComponent("api/signals")
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.keyEncodingStrategy = .convertToSnakeCase

        do {
            request.httpBody = try encoder.encode(signal)
            let (_, response) = try await URLSession.shared.data(for: request)
            let code = (response as? HTTPURLResponse)?.statusCode ?? 0
            let ok = (200..<300).contains(code)
            if !ok { print("SignalAPIClient: backend returned \(code)") }
            return ok
        } catch {
            print("SignalAPIClient: failed to send signal: \(error)")
            return false
        }
    }
}
