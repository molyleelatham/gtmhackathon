import { landingContent } from "../../content/landingContent";
import { GlassCard } from "../Glass";
import { ScrollReveal } from "./ScrollReveal";
import { AcronymText } from "../Acronym";

export function LifecycleSteps() {
  return (
    <section className="landing-section py-16">
      <ScrollReveal className="mb-10 text-center" variant="blur">
        <h2 className="text-3xl font-bold text-ink-900">How it works</h2>
        <p className="mt-2 text-ink-muted">Every connection moves through four stages.</p>
      </ScrollReveal>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {landingContent.lifecycle.map((item, i) => (
          <ScrollReveal key={item.step} delay={i * 90} variant="up">
            <GlassCard className="h-full p-5">
              <span className="text-xs font-bold uppercase tracking-wider text-flame">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-2 text-lg font-semibold text-ink-900">{item.step}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                <AcronymText>{item.description}</AcronymText>
              </p>
            </GlassCard>
          </ScrollReveal>
        ))}
      </div>
    </section>
  );
}
