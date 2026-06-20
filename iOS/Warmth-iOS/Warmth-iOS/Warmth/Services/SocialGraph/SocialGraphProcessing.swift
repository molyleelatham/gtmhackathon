import Foundation

/// Pure, on-device extraction over a transcript. Implemented by `SocialGraphEngine`
/// (NLTagger NER + regex SPO relations + ICP keyword scoring). Abstracted so the
/// capture flow and tests can swap a deterministic mock.
protocol SocialGraphProcessing: Sendable {
    /// Extract a `PersonNode` from a transcript chunk, or nil if no person is found.
    func process(transcript: String) -> PersonNode?
}

/// Deterministic stub for previews/tests that don't exercise NLTagger.
struct MockSocialGraph: SocialGraphProcessing {
    func process(transcript: String) -> PersonNode? {
        guard !transcript.isEmpty else { return nil }
        return PersonNode(
            name: "Maya Chen", org: "NorthWind Labs",
            interests: ["RevOps", "attribution"], icpScore: 72,
            transcriptExcerpt: transcript
        )
    }
}
