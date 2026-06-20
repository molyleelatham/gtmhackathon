import Foundation

/// A connection row from `GET /api/v1/connections` — mirrors the backend
/// `PreMeetConnection` schema used by the web dashboard.
struct CRMConnection: Identifiable, Hashable, Sendable, Codable {
    let id: String
    let eventId: String
    let name: String
    let title: String?
    let companyName: String?
    let interests: [String]
    let icpScore: Int
    let predictedWarmth: Int
    let draftSubject: String?
    let draftBody: String?
    let status: String?
    let source: String?

    enum CodingKeys: String, CodingKey {
        case id
        case eventId = "event_id"
        case name
        case title
        case companyName = "company_name"
        case interests
        case icpScore = "icp_score"
        case predictedWarmth = "predicted_warmth"
        case draftSubject = "draft_subject"
        case draftBody = "draft_body"
        case status
        case source
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        eventId = try container.decodeIfPresent(String.self, forKey: .eventId) ?? ""
        name = try container.decodeIfPresent(String.self, forKey: .name) ?? "Unknown"
        title = try container.decodeIfPresent(String.self, forKey: .title)
        companyName = try container.decodeIfPresent(String.self, forKey: .companyName)
        interests = try container.decodeIfPresent([String].self, forKey: .interests) ?? []
        icpScore = Self.decodeInt(container, forKey: .icpScore)
        predictedWarmth = Self.decodeInt(container, forKey: .predictedWarmth, fallback: icpScore)
        draftSubject = try container.decodeIfPresent(String.self, forKey: .draftSubject)
        draftBody = try container.decodeIfPresent(String.self, forKey: .draftBody)
        status = try container.decodeIfPresent(String.self, forKey: .status)
        source = try container.decodeIfPresent(String.self, forKey: .source)
    }

    init(
        id: String,
        eventId: String = "",
        name: String,
        title: String? = nil,
        companyName: String? = nil,
        interests: [String] = [],
        icpScore: Int = 0,
        predictedWarmth: Int = 0,
        draftSubject: String? = nil,
        draftBody: String? = nil,
        status: String? = nil,
        source: String? = nil
    ) {
        self.id = id
        self.eventId = eventId
        self.name = name
        self.title = title
        self.companyName = companyName
        self.interests = interests
        self.icpScore = icpScore
        self.predictedWarmth = predictedWarmth
        self.draftSubject = draftSubject
        self.draftBody = draftBody
        self.status = status
        self.source = source
    }

    var org: String? { companyName }
    var role: String? { title }
    var band: WarmthBand { WarmthBand(score: predictedWarmth) }

    var initials: String {
        let parts = name.split(separator: " ").prefix(2)
        return parts.compactMap { $0.first.map(String.init) }.joined().uppercased()
    }

    private static func decodeInt(
        _ container: KeyedDecodingContainer<CodingKeys>,
        forKey key: CodingKeys,
        fallback: Int = 0
    ) -> Int {
        if let value = try? container.decode(Int.self, forKey: key) { return value }
        if let value = try? container.decode(Double.self, forKey: key) { return Int(value.rounded()) }
        return fallback
    }
}

/// Detail payload from `GET /api/v1/connections/:id`.
struct CRMConnectionDetail: Sendable {
    let connection: CRMConnection
    let warmth: CRMWarmthScore?
    let gmailDraft: [String: String]?

    init(connection: CRMConnection, warmth: CRMWarmthScore?, gmailDraft: [String: String]?) {
        self.connection = connection
        self.warmth = warmth
        self.gmailDraft = gmailDraft
    }
}

struct CRMWarmthScore: Sendable, Codable {
    let icpScore: Int
    let warmthScore: Double
    let predictedScore: Double?
    let actualScore: Double?
    let band: String?

    enum CodingKeys: String, CodingKey {
        case icpScore = "icp_score"
        case warmthScore = "warmth_score"
        case predictedScore = "predicted_score"
        case actualScore = "actual_score"
        case band
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        if let value = try? container.decode(Int.self, forKey: .icpScore) {
            icpScore = value
        } else if let value = try? container.decode(Double.self, forKey: .icpScore) {
            icpScore = Int(value.rounded())
        } else {
            icpScore = 0
        }
        warmthScore = (try? container.decode(Double.self, forKey: .warmthScore)) ?? 0
        predictedScore = try container.decodeIfPresent(Double.self, forKey: .predictedScore)
        actualScore = try container.decodeIfPresent(Double.self, forKey: .actualScore)
        band = try container.decodeIfPresent(String.self, forKey: .band)
    }
}

extension CRMConnection {
    static let preview = CRMConnection(
        id: "premeet_preview",
        name: "Maya Chen",
        title: "VP RevOps",
        companyName: "NorthWind Labs",
        interests: ["RevOps", "pipeline"],
        icpScore: 88,
        predictedWarmth: 81
    )

    static let previewList: [CRMConnection] = [
        preview,
        CRMConnection(
            id: "premeet_preview_2",
            name: "Diego Alvarez",
            title: "Founder",
            companyName: "Loophole",
            interests: ["growth"],
            icpScore: 64,
            predictedWarmth: 58
        ),
    ]
}
