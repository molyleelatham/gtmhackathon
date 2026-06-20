import { useEffect, useState } from "react";
import { landingContent } from "../../content/landingContent";

export function DemoVideoPlayer() {
  const { demoVideo, demoVideoType } = landingContent;
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [demoVideo]);

  if (!demoVideo || failed) {
    return (
      <div className="glass-strong flex aspect-video flex-col items-center justify-center rounded-2xl border border-dashed border-subtle">
        <div className="mb-4 grid h-16 w-16 place-items-center rounded-full bg-orange/10 text-2xl text-flame">
          ▶
        </div>
        <p className="text-sm font-semibold text-ink-900">Demo video coming soon</p>
        <p className="mt-1 text-xs text-ink-faint">
          {failed ? "Upload demo.mp4 to the landing bucket — it will appear here automatically." : "Watch Warmth capture, score, and route live."}
        </p>
      </div>
    );
  }

  if (demoVideoType === "youtube") {
    return (
      <div className="glass-strong overflow-hidden rounded-2xl p-1">
        <iframe
          src={demoVideo}
          title="Warmth demo video"
          className="aspect-video w-full rounded-xl"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  return (
    <div className="glass-strong overflow-hidden rounded-2xl p-1">
      <video
        key={demoVideo}
        src={demoVideo}
        controls
        className="aspect-video w-full rounded-xl bg-ink-900"
        playsInline
        onError={() => setFailed(true)}
      >
        <track kind="captions" />
      </video>
    </div>
  );
}
