import SwiftUI

/// Multi-step onboarding + auth experience shown until the user finishes setup.
/// Drives a small `Step` state machine and composes self-contained step views over
/// the ambient `MeshGradientBackground`.
struct OnboardingFlow: View {
    @Environment(AppModel.self) private var model

    /// Ordered onboarding steps. `rawValue` doubles as the progress index.
    enum Step: Int, CaseIterable, Comparable {
        case welcome, signIn, permissions, calendar, finish

        static func < (lhs: Step, rhs: Step) -> Bool { lhs.rawValue < rhs.rawValue }
    }

    @State private var step: Step = .welcome

    var body: some View {
        ZStack {
            MeshGradientBackground(intensity: 1.05)

            // Soft ember glow that anchors the eye toward center.
            WarmthColor.emberGlow
                .frame(width: 520, height: 520)
                .blur(radius: 30)
                .opacity(0.5)
                .allowsHitTesting(false)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                ProgressDots(current: step.rawValue, total: Step.allCases.count)
                    .padding(.top, 12)
                    .opacity(step == .welcome ? 0 : 1)
                    .animation(WarmthMotion.gentle, value: step)

                Spacer(minLength: 0)

                stepContent
                    .frame(maxWidth: 480)
                    .padding(.horizontal, 28)

                Spacer(minLength: 0)
            }
            .padding(.vertical, 24)
        }
        .animation(WarmthMotion.gentle, value: step)
    }

    @ViewBuilder
    private var stepContent: some View {
        switch step {
        case .welcome:
            WelcomeStepView(advance: advance)
                .transition(stepTransition)
        case .signIn:
            SignInStepView(advance: advance)
                .transition(stepTransition)
        case .permissions:
            PermissionsStepView(advance: advance)
                .transition(stepTransition)
        case .calendar:
            CalendarStepView(advance: advance)
                .transition(stepTransition)
        case .finish:
            FinishStepView(finish: finish)
                .transition(stepTransition)
        }
    }

    private var stepTransition: AnyTransition {
        .asymmetric(
            insertion: .move(edge: .trailing).combined(with: .opacity),
            removal: .move(edge: .leading).combined(with: .opacity)
        )
    }

    /// Advance to the next step (no-op past the end).
    private func advance() {
        guard let next = Step(rawValue: step.rawValue + 1) else { return }
        WarmthHaptics.selection()
        withAnimation(WarmthMotion.gentle) { step = next }
    }

    /// Final action: persist completion so `RootView` swaps to the main shell.
    private func finish() {
        WarmthHaptics.success()
        model.completeOnboarding()
    }
}

/// A row of progress dots; the current dot stretches into an ember pill.
private struct ProgressDots: View {
    let current: Int
    let total: Int

    var body: some View {
        HStack(spacing: 8) {
            ForEach(0..<total, id: \.self) { index in
                Capsule()
                    .fill(index == current ? AnyShapeStyle(WarmthColor.emberGradient)
                                           : AnyShapeStyle(WarmthColor.surfaceBorder))
                    .frame(width: index == current ? 22 : 7, height: 7)
            }
        }
        .animation(WarmthMotion.snappy, value: current)
    }
}

#Preview {
    OnboardingFlow()
        .environment(AppModel.preview)
}
