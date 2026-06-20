import Foundation
import NaturalLanguage

/// Builds a lightweight on-device social graph from capture-window transcripts:
/// named-entity extraction, relationship pattern detection, and ICP keyword
/// proximity scoring. Accumulates `PersonNode`s across windows.
@MainActor
final class SocialGraphEngine {
    private(set) var graph: [String: PersonNode] = [:]
    private let vocabulary: ICPVocabulary

    /// Relationship trigger phrases mapped to a relationship kind.
    private let relationshipCues: [(cue: String, kind: Relationship.Kind)] = [
        ("works with", .worksWith),
        ("work with", .worksWith),
        ("works at", .worksAt),
        ("work at", .worksAt),
        ("over at", .worksAt),
        ("reports to", .reportsTo),
        ("introduced me to", .introducedBy),
        ("introduced by", .introducedBy),
        ("you should meet", .knows),
        ("do you know", .knows),
    ]

    init(vocabulary: ICPVocabulary = .default) {
        self.vocabulary = vocabulary
    }

    /// Process one transcript. `focusName` is the contact named by the wake word,
    /// if any — it becomes the primary person of the returned Signal.
    func ingest(transcript: String, focusName: String?) -> Signal? {
        guard !transcript.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            return nil
        }

        let people = extractEntities(transcript, scheme: .nameTypeOrLexicalClass, tag: .personalName)
        let orgs = extractEntities(transcript, scheme: .nameTypeOrLexicalClass, tag: .organizationName)
        let icpHits = vocabulary.matches(in: transcript)

        // Decide the primary person: the wake-word focus, else first/strongest entity.
        let primaryName = focusName ?? people.first?.text
        guard let primaryName else { return nil }

        let company = orgs.first.map { org -> CompanyMention in
            CompanyMention(
                name: org.text,
                icpKeywordsHit: Set(proximityKeywords(around: org.range, in: transcript, hits: icpHits))
            )
        }

        // Update / create the primary node.
        var node = graph[primaryName.lowercased()] ?? PersonNode(name: primaryName)
        node.lastSeen = Date()
        node.mentionCount += 1
        node.company = node.company ?? company?.name
        node.relatedNames.formUnion(
            people.map(\.text).filter { $0.lowercased() != primaryName.lowercased() }
        )
        node.icpKeywordsHit.formUnion(icpHits.map(\.keyword))
        graph[primaryName.lowercased()] = node

        // Ensure related people exist in the graph too.
        for other in node.relatedNames {
            if graph[other.lowercased()] == nil {
                graph[other.lowercased()] = PersonNode(name: other)
            }
        }

        let relationships = detectRelationships(transcript, primary: primaryName, company: company?.name)
        let score = icpScore(for: node, company: company)

        return Signal(
            person: node,
            company: company,
            relationships: relationships,
            score: score,
            transcript: transcript
        )
    }

    // MARK: - Entity extraction

    private struct Entity { let text: String; let range: Range<String.Index> }

    private func extractEntities(
        _ text: String,
        scheme: NLTagScheme,
        tag wanted: NLTag
    ) -> [Entity] {
        let tagger = NLTagger(tagSchemes: [scheme])
        tagger.string = text
        var results: [Entity] = []
        let options: NLTagger.Options = [.omitPunctuation, .omitWhitespace, .joinNames]

        tagger.enumerateTags(
            in: text.startIndex..<text.endIndex,
            unit: .word,
            scheme: scheme,
            options: options
        ) { tag, range in
            if tag == wanted {
                results.append(Entity(text: String(text[range]), range: range))
            }
            return true
        }
        return dedupe(results)
    }

    private func dedupe(_ entities: [Entity]) -> [Entity] {
        var seen = Set<String>()
        return entities.filter { seen.insert($0.text.lowercased()).inserted }
    }

    // MARK: - Relationships

    private func detectRelationships(
        _ text: String,
        primary: String,
        company: String?
    ) -> [Relationship] {
        var rels: [Relationship] = []
        let lower = text.lowercased()

        if let company {
            rels.append(Relationship(subject: primary, kind: .worksAt, object: company))
        }

        for (cue, kind) in relationshipCues where lower.contains(cue) {
            // Attach the nearest other person mentioned to the primary.
            let others = extractEntities(text, scheme: .nameTypeOrLexicalClass, tag: .personalName)
                .map(\.text)
                .filter { $0.lowercased() != primary.lowercased() }
            if let other = others.first {
                rels.append(Relationship(subject: primary, kind: kind, object: other))
            }
        }
        return rels
    }

    // MARK: - Scoring

    /// ICP keywords appearing within ~60 characters of an entity range.
    private func proximityKeywords(
        around range: Range<String.Index>,
        in text: String,
        hits: [(keyword: String, weight: Double)]
    ) -> [String] {
        let window = 60
        let lower = text.lowercased()
        let start = text.distance(from: text.startIndex, to: range.lowerBound)
        return hits.filter { hit in
            guard let r = lower.range(of: hit.keyword.lowercased()) else { return false }
            let hitPos = lower.distance(from: lower.startIndex, to: r.lowerBound)
            return abs(hitPos - start) <= window
        }.map(\.keyword)
    }

    private func icpScore(for node: PersonNode, company: CompanyMention?) -> Double {
        var score = 0.0
        for keyword in node.icpKeywordsHit {
            score += vocabulary.keywordWeights[keyword] ?? 0
        }
        // Company-proximate keywords reinforce fit.
        for keyword in company?.icpKeywordsHit ?? [] {
            score += (vocabulary.keywordWeights[keyword] ?? 0) * 0.5
        }
        // Conference audio source bonus, matching the backend pre-scorer.
        score += 5
        return min(score, 100)
    }

    func reset() { graph.removeAll() }
}
