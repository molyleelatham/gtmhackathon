import Foundation

/// A person discovered during a conversation, accumulated across capture windows
/// into a lightweight on-device social graph.
struct PersonNode: Identifiable, Codable, Hashable {
    var id: String { name.lowercased() }
    var name: String
    var company: String?
    var title: String?
    /// Other people this person was mentioned alongside.
    var relatedNames: Set<String> = []
    /// ICP keywords heard in proximity to this person.
    var icpKeywordsHit: Set<String> = []
    var firstSeen: Date = Date()
    var lastSeen: Date = Date()
    var mentionCount: Int = 1
}

/// A detected relationship between two entities ("works with", "reports to", etc.).
struct Relationship: Codable, Hashable {
    enum Kind: String, Codable {
        case worksWith = "works_with"
        case worksAt = "works_at"
        case reportsTo = "reports_to"
        case knows = "knows"
        case introducedBy = "introduced_by"
    }

    var subject: String
    var kind: Kind
    var object: String
}

/// A company mentioned in conversation.
struct CompanyMention: Codable, Hashable {
    var name: String
    var icpKeywordsHit: Set<String> = []
}

/// The output of one capture window: a scored lead with its social context.
/// Mirrors the backend `Signal` schema (`packages/core/models/signal.py`).
struct Signal: Codable, Identifiable {
    var id: UUID = UUID()
    var person: PersonNode
    var company: CompanyMention?
    var relationships: [Relationship] = []
    /// 0–100 ICP fit score computed on-device.
    var score: Double
    var transcript: String
    var source: String = "event_audio"
    var detectedAt: Date = Date()

    /// On-device hint threshold ONLY — for an instant watch buzz while the
    /// backend computes the authoritative score. The real CRM (≥70) and
    /// Faxxing/Lightfern (≥80) thresholds live on the compute host.
    static let preScoreHintThreshold: Double = 50

    var isPreScoreHint: Bool { score >= Signal.preScoreHintThreshold }

    enum CodingKeys: String, CodingKey {
        case id
        case person
        case company
        case relationships
        case score = "icp_pre_score"
        case transcript = "raw_text"
        case source
        case detectedAt = "detected_at"
    }
}
