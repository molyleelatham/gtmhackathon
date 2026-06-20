import Foundation

/// Rich, in-memory representation of a person met during the session. This is the
/// model the UI (Connections, Review) renders. The `SocialGraphEngine` builds and
/// updates these; a mapper converts one into a `CapturedSignal` for upload.
struct PersonNode: Identifiable, Hashable, Sendable {
    let id: UUID
    var name: String
    var org: String?
    var role: String?
    var interests: [String]
    var relations: [CapturedSignal.Relation]
    var icpScore: Int
    var transcriptExcerpt: String
    var capturedAt: Date
    /// True for seeded demo data so the UI can subtly distinguish it if needed.
    var isMock: Bool

    init(
        id: UUID = UUID(),
        name: String,
        org: String? = nil,
        role: String? = nil,
        interests: [String] = [],
        relations: [CapturedSignal.Relation] = [],
        icpScore: Int = 0,
        transcriptExcerpt: String = "",
        capturedAt: Date = .now,
        isMock: Bool = false
    ) {
        self.id = id
        self.name = name
        self.org = org
        self.role = role
        self.interests = interests
        self.relations = relations
        self.icpScore = icpScore
        self.transcriptExcerpt = transcriptExcerpt
        self.capturedAt = capturedAt
        self.isMock = isMock
    }

    var band: WarmthBand { WarmthBand(score: icpScore) }

    /// Initials for avatar fallbacks.
    var initials: String {
        let parts = name.split(separator: " ").prefix(2)
        return parts.compactMap { $0.first.map(String.init) }.joined().uppercased()
    }

    /// Convert into the wire payload given the signed-in user + session id.
    func makeSignal(user: CapturedSignal.User, sessionId: String) -> CapturedSignal {
        CapturedSignal(
            user: user,
            sessionId: sessionId,
            capturedAt: capturedAt,
            person: .init(name: name, org: org, role: role),
            relations: relations,
            interests: interests,
            icpKeywordScore: icpScore,
            transcriptExcerpt: transcriptExcerpt,
            device: .current
        )
    }
}

extension PersonNode {
    /// Seeded demo people so the Connections tab always looks full in a demo.
    static let mockData: [PersonNode] = [
        PersonNode(
            name: "Maya Chen", org: "NorthWind Labs", role: "VP RevOps",
            interests: ["RevOps", "attribution", "pipeline"],
            relations: [.init(subject: "Maya", predicate: "works_at", object: "NorthWind Labs")],
            icpScore: 88,
            transcriptExcerpt: "Maya leads RevOps at NorthWind Labs — they're rebuilding attribution from scratch this quarter.",
            capturedAt: .now.addingTimeInterval(-600), isMock: true
        ),
        PersonNode(
            name: "Diego Alvarez", org: "Helio Robotics", role: "Founder",
            interests: ["fundraising", "go-to-market", "robotics"],
            relations: [.init(subject: "Diego", predicate: "founded", object: "Helio Robotics")],
            icpScore: 64,
            transcriptExcerpt: "Diego founded Helio Robotics, raising a seed round and figuring out GTM motion.",
            capturedAt: .now.addingTimeInterval(-1800), isMock: true
        ),
        PersonNode(
            name: "Priya Nair", org: "Lumen Health", role: "Head of Data",
            interests: ["data platform", "ML", "compliance"],
            relations: [.init(subject: "Priya", predicate: "leads", object: "Data at Lumen Health")],
            icpScore: 73,
            transcriptExcerpt: "Priya heads data at Lumen Health, dealing with compliance for an ML platform.",
            capturedAt: .now.addingTimeInterval(-3600), isMock: true
        ),
        PersonNode(
            name: "Tomás Becker", org: "Drift Studio", role: "Design Lead",
            interests: ["design systems", "branding"],
            relations: [.init(subject: "Tomás", predicate: "works_at", object: "Drift Studio")],
            icpScore: 38,
            transcriptExcerpt: "Tomás runs design at Drift Studio, mostly brand and design-system work.",
            capturedAt: .now.addingTimeInterval(-5400), isMock: true
        ),
        PersonNode(
            name: "Aisha Khan", org: "Vertex Capital", role: "Partner",
            interests: ["investing", "SaaS metrics", "RevOps"],
            relations: [.init(subject: "Aisha", predicate: "invests_at", object: "Vertex Capital")],
            icpScore: 91,
            transcriptExcerpt: "Aisha is a partner at Vertex Capital focused on SaaS metrics and RevOps tooling.",
            capturedAt: .now.addingTimeInterval(-7200), isMock: true
        )
    ]

    static var preview: PersonNode { mockData[0] }
}
