import Foundation

/// Shared backend host — keep in sync with `web/.env.production` (`VITE_API_BASE_URL`).
enum BackendConfiguration {
    static let productionBaseURL = "https://warmth-api-30164818817.us-central1.run.app"
    static let localDevelopmentBaseURL = "http://127.0.0.1:8010"

    /// Default for device builds: hosted Cloud Run API (same data as the web dashboard).
    static let defaultBaseURL = productionBaseURL

    /// Upgrade persisted localhost URLs so physical devices don't point at themselves.
    static func normalizedBaseURLString(_ raw: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return defaultBaseURL }
        let lower = trimmed.lowercased()
        if lower.contains("127.0.0.1") || lower.contains("localhost") {
            return defaultBaseURL
        }
        return trimmed
    }
}

extension AuthProviding {
    func applyAuthorization(to request: inout URLRequest) async {
        let token = await idToken()
        guard !token.isEmpty else { return }
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    }
}
