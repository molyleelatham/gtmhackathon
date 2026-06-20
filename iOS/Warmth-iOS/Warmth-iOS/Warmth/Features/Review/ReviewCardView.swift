import SwiftUI

/// An editable review card for one captured person. Lets the user correct the
/// name/org/role, curate interests, tune the ICP score, and edit the transcript
/// before saving. `id`, `capturedAt`, and `relations` are preserved on save.
struct ReviewCardView: View {
    let person: PersonNode
    var onSave: (PersonNode) -> Void

    @State private var name: String
    @State private var org: String
    @State private var role: String
    @State private var interests: [String]
    @State private var newInterest: String = ""
    @State private var icpScore: Int
    @State private var transcript: String
    @State private var didSave = false

    init(person: PersonNode, onSave: @escaping (PersonNode) -> Void) {
        self.person = person
        self.onSave = onSave
        _name = State(initialValue: person.name)
        _org = State(initialValue: person.org ?? "")
        _role = State(initialValue: person.role ?? "")
        _interests = State(initialValue: person.interests)
        _icpScore = State(initialValue: person.icpScore)
        _transcript = State(initialValue: person.transcriptExcerpt)
    }

    private var band: WarmthBand { WarmthBand(score: icpScore) }

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 18) {
                header

                fieldGroup

                interestEditor

                if !person.relations.isEmpty {
                    relationsSection
                }

                icpSection

                transcriptSection

                EmberButton(title: didSave ? "Saved" : "Save",
                            systemImage: didSave ? "checkmark" : "tray.and.arrow.down") {
                    save()
                }
            }
        }
    }

    // MARK: - Sections

    private var header: some View {
        HStack(spacing: 14) {
            AvatarBadge(initials: initials, size: 52, glow: true)
            VStack(alignment: .leading, spacing: 2) {
                Text(name.isEmpty ? "New contact" : name)
                    .warmthText(.Warmth.title2)
                    .lineLimit(1)
                Text("Captured \(person.capturedAt.formatted(date: .abbreviated, time: .shortened))")
                    .warmthText(.Warmth.footnote, color: WarmthColor.inkSecondary)
            }
            Spacer(minLength: 8)
            WarmthBadge(band: band, score: icpScore)
        }
    }

    private var fieldGroup: some View {
        VStack(spacing: 10) {
            labeledField("Name", text: $name, placeholder: "Full name")
            labeledField("Org", text: $org, placeholder: "Company")
            labeledField("Role", text: $role, placeholder: "Title")
        }
    }

    private var interestEditor: some View {
        VStack(alignment: .leading, spacing: 10) {
            sectionLabel("Interests")

            if !interests.isEmpty {
                WarmthFlowLayout(spacing: 8, lineSpacing: 8) {
                    ForEach(interests, id: \.self) { interest in
                        Button {
                            remove(interest)
                        } label: {
                            HStack(spacing: 4) {
                                Text(interest)
                                    .font(.Warmth.caption)
                                    .foregroundStyle(WarmthColor.ink)
                                Image(systemName: "xmark")
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundStyle(WarmthColor.inkSecondary)
                            }
                            .padding(.horizontal, 12)
                            .padding(.vertical, 6)
                            .background(band.tint.opacity(0.18), in: .capsule)
                            .overlay(Capsule().strokeBorder(band.tint.opacity(0.4), lineWidth: 0.5))
                        }
                        .buttonStyle(.plain)
                    }
                }
            }

            HStack(spacing: 8) {
                TextField("Add interest", text: $newInterest)
                    .textFieldStyle(.plain)
                    .font(.Warmth.callout)
                    .foregroundStyle(WarmthColor.ink)
                    .submitLabel(.done)
                    .onSubmit(addInterest)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 9)
                    .background(WarmthColor.surfaceMuted, in: .capsule)

                Button(action: addInterest) {
                    Image(systemName: "plus")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundStyle(WarmthColor.warmWhite)
                        .frame(width: 34, height: 34)
                        .background(WarmthColor.emberGradient, in: .circle)
                }
                .buttonStyle(.plain)
                .disabled(newInterest.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
    }

    private var relationsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionLabel("Relations")
            ForEach(person.relations, id: \.self) { relation in
                Text("\(relation.subject) · \(humanize(relation.predicate)) · \(relation.object)")
                    .warmthText(.Warmth.callout, color: WarmthColor.inkSecondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var icpSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionLabel("ICP score")
            Stepper(value: $icpScore, in: 0...100, step: 1) {
                HStack(spacing: 8) {
                    Text("\(icpScore)")
                        .warmthText(.Warmth.title2, color: band.tint)
                    Text(band.label)
                        .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                }
            }
            .tint(band.tint)
        }
    }

    private var transcriptSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionLabel("Transcript")
            TextEditor(text: $transcript)
                .font(.Warmth.body)
                .foregroundStyle(WarmthColor.ink)
                .scrollContentBackground(.hidden)
                .frame(minHeight: 90)
                .padding(10)
                .background(WarmthColor.surfaceMuted, in: .rect(cornerRadius: 14))
        }
    }

    // MARK: - Helpers

    private var initials: String {
        let parts = name.split(separator: " ").prefix(2)
        let joined = parts.compactMap { $0.first.map(String.init) }.joined().uppercased()
        return joined.isEmpty ? "?" : joined
    }

    @ViewBuilder
    private func labeledField(_ label: String, text: Binding<String>, placeholder: String) -> some View {
        HStack(spacing: 12) {
            Text(label)
                .warmthText(.Warmth.subheadline, color: WarmthColor.inkSecondary)
                .frame(width: 56, alignment: .leading)
            TextField(placeholder, text: text)
                .textFieldStyle(.plain)
                .font(.Warmth.body)
                .foregroundStyle(WarmthColor.ink)
                .padding(.horizontal, 12)
                .padding(.vertical, 9)
                .background(WarmthColor.surfaceMuted, in: .rect(cornerRadius: 12))
        }
    }

    private func sectionLabel(_ title: String) -> some View {
        Text(title.uppercased())
            .font(.Warmth.caption)
            .tracking(1.2)
            .foregroundStyle(WarmthColor.inkSecondary)
    }

    private func humanize(_ predicate: String) -> String {
        predicate.replacingOccurrences(of: "_", with: " ")
    }

    private func addInterest() {
        let trimmed = newInterest.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty,
              !interests.contains(where: { $0.caseInsensitiveCompare(trimmed) == .orderedSame }) else {
            newInterest = ""
            return
        }
        WarmthHaptics.selection()
        interests.append(trimmed)
        newInterest = ""
    }

    private func remove(_ interest: String) {
        WarmthHaptics.selection()
        interests.removeAll { $0 == interest }
    }

    private func save() {
        let updated = PersonNode(
            id: person.id,
            name: name.trimmingCharacters(in: .whitespacesAndNewlines),
            org: org.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : org,
            role: role.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? nil : role,
            interests: interests,
            relations: person.relations,
            icpScore: icpScore,
            transcriptExcerpt: transcript,
            capturedAt: person.capturedAt,
            isMock: person.isMock
        )
        WarmthHaptics.success()
        withAnimation(WarmthMotion.snappy) { didSave = true }
        onSave(updated)
    }
}

#Preview {
    ZStack {
        MeshGradientBackground()
        ScrollView {
            ReviewCardView(person: PersonNode.preview) { _ in }
                .padding()
        }
    }
    .environment(AppModel.preview)
}
