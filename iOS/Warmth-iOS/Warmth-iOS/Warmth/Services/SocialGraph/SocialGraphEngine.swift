import Foundation
import NaturalLanguage

/// 100% on-device extraction over a transcript:
/// 1. NLTagger NER → PersonalName + OrganizationName
/// 2. Regex SPO relation extraction (subject·predicate·object)
/// 3. ICP keyword-proximity scoring (rule-based 0–100)
///
/// Stateless and `Sendable`; the session-scoped person dictionary lives in
/// `SessionCaptureLog`. Pure value-in/value-out so it's trivially unit-testable.
struct SocialGraphEngine: SocialGraphProcessing {
    /// ICP keywords that signal a high-value lead. Tunable.
    let icpKeywords: Set<String>

    init(icpKeywords: Set<String> = SocialGraphEngine.defaultICPKeywords) {
        self.icpKeywords = icpKeywords
    }

    static let defaultICPKeywords: Set<String> = [
        "revops", "attribution", "pipeline", "go-to-market", "gtm", "saas",
        "metrics", "fundraising", "investing", "data platform", "ml", "ai",
        "compliance", "analytics", "growth", "sales", "marketing", "automation"
    ]

    // MARK: - Public API

    func process(transcript: String) -> PersonNode? {
        let trimmed = transcript.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }

        let names = entities(in: trimmed, tag: .personalName)
        let orgs = entities(in: trimmed, tag: .organizationName)

        // We need at least a person to anchor a node.
        guard let primaryName = names.first else { return nil }

        let org = orgs.first
        let interests = self.interests(in: trimmed)
        let relations = self.relations(in: trimmed, names: names, orgs: orgs)
        let score = icpScore(transcript: trimmed, interests: interests)

        return PersonNode(
            name: primaryName,
            org: org,
            role: role(in: trimmed),
            interests: interests,
            relations: relations,
            icpScore: score,
            transcriptExcerpt: excerpt(from: trimmed)
        )
    }

    // MARK: - NER

    func entities(in text: String, tag targetTag: NLTag) -> [String] {
        let tagger = NLTagger(tagSchemes: [.nameType])
        tagger.string = text
        let options: NLTagger.Options = [.omitPunctuation, .omitWhitespace, .joinNames]
        var results: [String] = []
        tagger.enumerateTags(in: text.startIndex..<text.endIndex, unit: .word, scheme: .nameType, options: options) { tag, range in
            if tag == targetTag {
                let value = String(text[range]).trimmingCharacters(in: .whitespaces)
                if !value.isEmpty && !results.contains(value) { results.append(value) }
            }
            return true
        }
        return results
    }

    // MARK: - Relations (regex SPO)

    /// Patterns mapping verb phrases to canonical predicates.
    private static let relationPatterns: [(predicate: String, regex: String)] = [
        ("works_at", #"(?:work|works|working)\s+(?:at|for)\s+([A-Z][\w&.\- ]+)"#),
        ("founded", #"(?:founded|started|co-?founded)\s+([A-Z][\w&.\- ]+)"#),
        ("leads", #"(?:lead|leads|leading|heads|head of|run|runs)\s+([\w&.\- ]+)"#),
        ("invests_at", #"(?:invest|invests|investing|partner)\s+(?:at|in)\s+([A-Z][\w&.\- ]+)"#),
        ("interested_in", #"(?:interested in|focused on|working on|building)\s+([\w&.\- ]+)"#)
    ]

    func relations(in text: String, names: [String], orgs: [String]) -> [CapturedSignal.Relation] {
        let subject = names.first?.split(separator: " ").first.map(String.init) ?? names.first ?? "They"
        var found: [CapturedSignal.Relation] = []
        for pattern in Self.relationPatterns {
            guard let regex = try? NSRegularExpression(pattern: pattern.regex, options: [.caseInsensitive]) else { continue }
            let range = NSRange(text.startIndex..., in: text)
            regex.enumerateMatches(in: text, options: [], range: range) { match, _, _ in
                guard let match, match.numberOfRanges > 1,
                      let objectRange = Range(match.range(at: 1), in: text) else { return }
                let object = String(text[objectRange])
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                    .trimmingCharacters(in: CharacterSet(charactersIn: ".,;"))
                guard object.count > 1 else { return }
                let relation = CapturedSignal.Relation(subject: subject, predicate: pattern.predicate, object: object)
                if !found.contains(relation) { found.append(relation) }
            }
        }
        return found
    }

    // MARK: - Role / title

    private static let roleRegex = try? NSRegularExpression(
        pattern: #"\b((?:VP|Head|Chief|Director|Lead|Founder|Co-?founder|Partner|CEO|CTO|CFO|COO|Manager|Engineer|Designer)[\w ]*?)(?:\s+(?:at|of|for)\b|[.,]|$)"#,
        options: [.caseInsensitive]
    )

    func role(in text: String) -> String? {
        guard let regex = Self.roleRegex else { return nil }
        let range = NSRange(text.startIndex..., in: text)
        guard let match = regex.firstMatch(in: text, options: [], range: range),
              match.numberOfRanges > 1,
              let r = Range(match.range(at: 1), in: text) else { return nil }
        let role = String(text[r]).trimmingCharacters(in: .whitespacesAndNewlines)
        return role.isEmpty ? nil : role
    }

    // MARK: - Interests + ICP scoring

    func interests(in text: String) -> [String] {
        let lower = text.lowercased()
        var hits: [String] = []
        for keyword in icpKeywords where lower.contains(keyword) {
            hits.append(displayInterest(keyword))
        }
        return Array(Set(hits)).sorted()
    }

    /// ICP keyword-proximity score 0–100: density of ICP keywords near the person/org
    /// mention, with diminishing returns. Rule-based, deterministic.
    func icpScore(transcript: String, interests: [String]) -> Int {
        let lower = transcript.lowercased()
        let words = lower.split(whereSeparator: { !$0.isLetter && $0 != "-" }).map(String.init)
        guard !words.isEmpty else { return 0 }

        var matches = 0
        for keyword in icpKeywords where lower.contains(keyword) { matches += 1 }

        // Base from unique keyword matches (each worth ~18, capped).
        let base = min(matches * 18, 80)
        // Proximity bonus: keywords appearing in the first third of the transcript
        // (usually the intro) score higher.
        let introSlice = words.prefix(max(1, words.count / 3)).joined(separator: " ")
        let introHits = icpKeywords.filter { introSlice.contains($0) }.count
        let proximity = min(introHits * 6, 20)

        return min(base + proximity, 100)
    }

    // MARK: - Helpers

    private func displayInterest(_ keyword: String) -> String {
        switch keyword {
        case "revops": return "RevOps"
        case "gtm", "go-to-market": return "go-to-market"
        case "ml": return "ML"
        case "ai": return "AI"
        case "saas": return "SaaS"
        default: return keyword
        }
    }

    private func excerpt(from text: String, limit: Int = 220) -> String {
        guard text.count > limit else { return text }
        let end = text.index(text.startIndex, offsetBy: limit)
        return String(text[..<end]).trimmingCharacters(in: .whitespaces) + "…"
    }
}
