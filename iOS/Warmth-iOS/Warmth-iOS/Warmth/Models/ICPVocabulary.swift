import Foundation

/// On-device mirror of the backend ICP config (`packages/core/models/icp.py`).
/// Used to bias speech recognition (custom language model) and to score leads.
struct ICPVocabulary {
    /// Weighted keywords. Higher weight => stronger ICP signal when heard near a person.
    let keywordWeights: [String: Double]

    /// Phrases used to bias the speech recognizer toward our domain vocabulary.
    var biasPhrases: [String] { Array(keywordWeights.keys) }

    static let `default` = ICPVocabulary(keywordWeights: [
        "RevOps": 30,
        "Revenue Operations": 30,
        "Sales Engineer": 25,
        "Series A": 20,
        "Series B": 20,
        "pipeline": 15,
        "pipeline visibility": 15,
        "attribution": 15,
        "manual data entry": 15,
        "HubSpot": 10,
        "Salesforce": 10,
    ])

    /// Returns the keywords found in `text` (case-insensitive) with their weights.
    func matches(in text: String) -> [(keyword: String, weight: Double)] {
        let lower = text.lowercased()
        return keywordWeights.compactMap { keyword, weight in
            lower.contains(keyword.lowercased()) ? (keyword, weight) : nil
        }
    }
}
