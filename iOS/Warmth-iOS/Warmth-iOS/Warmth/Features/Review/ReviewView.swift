import SwiftUI

/// Post-conference review screen: a scrollable stack of editable cards for every
/// person captured this session. Saving writes the edits back into the session log.
struct ReviewView: View {
    @Environment(AppModel.self) private var model

    private var people: [PersonNode] {
        model.sessionLog.people.isEmpty ? PersonNode.mockData : model.sessionLog.people
    }

    var body: some View {
        NavigationStack {
            ZStack {
                MeshGradientBackground()

                ScrollView {
                    VStack(spacing: 18) {
                        Text("Tidy up the people you met before they sync.")
                            .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.horizontal, 4)

                        ForEach(people) { person in
                            ReviewCardView(person: person) { updated in
                                saveReviewedPerson(updated)
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 8)
                    .padding(.bottom, 40)
                }
                .scrollContentBackground(.hidden)
            }
            .navigationTitle("Review")
        }
        .tint(WarmthColor.emberRed)
    }

    /// Persist edits: update an existing session capture, or record mock/demo rows
    /// the first time the user saves them.
    private func saveReviewedPerson(_ updated: PersonNode) {
        if model.sessionLog.people.contains(where: { $0.id == updated.id }) {
            model.sessionLog.update(updated)
        } else {
            _ = model.sessionLog.record(updated)
        }
    }
}

#Preview {
    ReviewView()
        .environment(AppModel.preview)
}
