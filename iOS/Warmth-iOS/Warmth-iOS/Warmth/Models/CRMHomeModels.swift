import Foundation

struct CRMDashboardSummary: Sendable, Codable {
    let userId: String
    let events: Int
    let connections: Int
    let hotLeads: Int
    let leadsInCRM: Int
    let topLeads: [CRMConnection]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case events, connections
        case hotLeads = "hot_leads"
        case leadsInCRM = "leads_in_crm"
        case topLeads = "top_leads"
    }
}

struct CRMDetectedEvent: Sendable, Codable, Identifiable {
    let id: String
    let name: String
    let startDate: String?
    let endDate: String?
    let location: String?

    enum CodingKeys: String, CodingKey {
        case id, name, location
        case startDate = "start_date"
        case endDate = "end_date"
    }
}

struct CRMRosterMetRow: Sendable, Identifiable {
    let id: String
    let connection: CRMConnection
    let meetResult: CRMMeetResult?

    init(connection: CRMConnection, meetResult: CRMMeetResult?) {
        self.id = connection.id
        self.connection = connection
        self.meetResult = meetResult
    }
}

struct CRMRoster: Sendable {
    let event: CRMDetectedEvent?
    let attendees: [CRMConnection]
    let met: [CRMRosterMetRow]
}

struct CRMCommunityMember: Sendable, Codable, Identifiable {
    let userId: String
    let name: String
    let interests: [String]

    var id: String { userId }

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case name, interests
    }
}

struct CRMICPRow: Sendable, Codable, Identifiable {
    let label: String
    let value: String
    var id: String { label }
}

struct CRMMeetResult: Sendable, Codable {
    let signalId: String?
    let routedTo: String?
    let narrative: String?
    let recordedAt: String?
    let interests: [String]
    let matchedCandidates: [CRMMatchCandidate]
    let knowledgeGraph: [CRMKnowledgeGraphNode]

    enum CodingKeys: String, CodingKey {
        case signalId = "signal_id"
        case routedTo = "routed_to"
        case narrative
        case recordedAt = "recorded_at"
        case interests
        case matchedCandidates = "matched_candidates"
        case knowledgeGraph = "knowledge_graph"
    }

    init(
        signalId: String? = nil,
        routedTo: String? = nil,
        narrative: String? = nil,
        recordedAt: String? = nil,
        interests: [String] = [],
        matchedCandidates: [CRMMatchCandidate] = [],
        knowledgeGraph: [CRMKnowledgeGraphNode] = []
    ) {
        self.signalId = signalId
        self.routedTo = routedTo
        self.narrative = narrative
        self.recordedAt = recordedAt
        self.interests = interests
        self.matchedCandidates = matchedCandidates
        self.knowledgeGraph = knowledgeGraph
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        signalId = try container.decodeIfPresent(String.self, forKey: .signalId)
        routedTo = try container.decodeIfPresent(String.self, forKey: .routedTo)
        narrative = try container.decodeIfPresent(String.self, forKey: .narrative)
        recordedAt = try container.decodeIfPresent(String.self, forKey: .recordedAt)
        interests = try container.decodeIfPresent([String].self, forKey: .interests) ?? []
        matchedCandidates = try container.decodeIfPresent([CRMMatchCandidate].self, forKey: .matchedCandidates) ?? []
        knowledgeGraph = try container.decodeIfPresent([CRMKnowledgeGraphNode].self, forKey: .knowledgeGraph) ?? []
    }
}

struct CRMMatchCandidate: Sendable, Codable, Hashable {
    let userId: String?
    let name: String?
    let interests: [String]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case name, interests
    }
}

struct CRMKnowledgeGraphNode: Sendable, Codable {
    let name: String?
    let topicWeights: [String: Double]?

    enum CodingKeys: String, CodingKey {
        case name
        case topicWeights = "topic_weights"
    }
}

struct CRMFollowUpDraft: Sendable {
    let subject: String
    let body: String
}

extension CRMDashboardSummary {
    static let preview = CRMDashboardSummary(
        userId: "demo-user",
        events: 1,
        connections: 12,
        hotLeads: 4,
        leadsInCRM: 6,
        topLeads: CRMConnection.previewList
    )
}

extension CRMCommunityMember {
    static let previewList: [CRMCommunityMember] = [
        CRMCommunityMember(userId: "u1", name: "Alex Rivera", interests: ["RevOps", "AI"]),
        CRMCommunityMember(userId: "u2", name: "Jordan Lee", interests: ["Founders", "GTM"]),
    ]
}
