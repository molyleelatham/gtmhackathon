import Foundation

/// Wire model POSTed to `{baseURL}/api/signals`. Field names use snake_case to
/// match the backend contract exactly (see `CodingKeys`).
struct CapturedSignal: Codable, Sendable, Identifiable {
    struct User: Codable, Sendable {
        let uid: String
        let idToken: String

        enum CodingKeys: String, CodingKey {
            case uid
            case idToken = "id_token"
        }
    }

    struct Person: Codable, Sendable {
        let name: String
        let org: String?
        let role: String?
    }

    struct Relation: Codable, Sendable, Hashable {
        let subject: String
        let predicate: String
        let object: String
    }

    struct Device: Codable, Sendable {
        let model: String
        let os: String
    }

    /// Stable client id (not sent on the wire; used for the retry queue + lists).
    var id: UUID = UUID()

    let user: User
    let sessionId: String
    let capturedAt: Date
    let person: Person
    let relations: [Relation]
    let interests: [String]
    let icpKeywordScore: Int
    let transcriptExcerpt: String
    let device: Device

    enum CodingKeys: String, CodingKey {
        case user
        case sessionId = "session_id"
        case capturedAt = "captured_at"
        case person
        case relations
        case interests
        case icpKeywordScore = "icp_keyword_score"
        case transcriptExcerpt = "transcript_excerpt"
        case device
    }

    /// Shared encoder/decoder producing the ISO8601 timestamps the schema requires.
    static func makeEncoder() -> JSONEncoder {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return encoder
    }
}

extension CapturedSignal.Device {
    /// Current device descriptor for the payload.
    static var current: CapturedSignal.Device {
        CapturedSignal.Device(model: "iPhone", os: "iOS 26.5")
    }
}
