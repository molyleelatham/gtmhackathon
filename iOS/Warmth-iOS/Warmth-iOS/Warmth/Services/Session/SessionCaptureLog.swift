import Foundation

/// In-memory, session-scoped log of everyone captured since launch. Cleared on
/// relaunch by design — Connections merges this with seeded mock data for the demo.
@MainActor
@Observable
final class SessionCaptureLog {
    /// Unique session id included in every signal payload.
    let sessionId: String
    /// People captured this session, most recent first.
    private(set) var people: [PersonNode] = []

    init(sessionId: String = UUID().uuidString) {
        self.sessionId = sessionId
    }

    /// Insert or merge a captured person. People with the same name (case-insensitive)
    /// are merged so repeated mentions enrich one node rather than duplicating.
    @discardableResult
    func record(_ node: PersonNode) -> PersonNode {
        if let index = people.firstIndex(where: { $0.name.caseInsensitiveCompare(node.name) == .orderedSame }) {
            var merged = people[index]
            merged.org = node.org ?? merged.org
            merged.role = node.role ?? merged.role
            merged.interests = Array(Set(merged.interests + node.interests)).sorted()
            merged.relations = Array(Set(merged.relations + node.relations))
            merged.icpScore = max(merged.icpScore, node.icpScore)
            if !node.transcriptExcerpt.isEmpty { merged.transcriptExcerpt = node.transcriptExcerpt }
            merged.capturedAt = node.capturedAt
            people.remove(at: index)
            people.insert(merged, at: 0)
            return merged
        } else {
            people.insert(node, at: 0)
            return node
        }
    }

    func update(_ node: PersonNode) {
        if let index = people.firstIndex(where: { $0.id == node.id }) {
            people[index] = node
        } else if let index = people.firstIndex(where: {
            $0.name.caseInsensitiveCompare(node.name) == .orderedSame
        }) {
            // Fallback when the caller still has a mock/demo id but the name matches.
            people[index] = node
        }
    }

    func clear() { people.removeAll() }

    static var preview: SessionCaptureLog {
        let log = SessionCaptureLog()
        log.people = Array(PersonNode.mockData.prefix(2))
        return log
    }
}
