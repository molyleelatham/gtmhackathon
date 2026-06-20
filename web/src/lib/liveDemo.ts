import { api } from "./api";
import type { AttendeeMatchResult } from "../types";
import type { Attendee } from "./uiTypes";

export type PipelineStepStatus = "pending" | "running" | "done" | "error";

export interface PipelineStep {
  id: string;
  label: string;
  detail: string;
  status: PipelineStepStatus;
}

export const LIVE_DEMO_STEPS: Omit<PipelineStep, "status">[] = [
  {
    id: "listen",
    label: "Passive listen",
    detail: "Mic open · scanning for wake phrase on the floor",
  },
  {
    id: "transcribe",
    label: "Transcribe greeting",
    detail: 'Speech-to-text · parsing "Hi {name}"',
  },
  {
    id: "match",
    label: "Match event roster",
    detail: "AttendeeMatcher · calendar + HubSpot + pipeline leads",
  },
  {
    id: "resolve",
    label: "Resolve identity",
    detail: "Attach live signal to PreMeetConnection id",
  },
  {
    id: "kg",
    label: "Build knowledge graph",
    detail: "Merge interests, topic weights, and values",
  },
  {
    id: "score",
    label: "Score warmth",
    detail: "ICP fit · predicted warmth band · routing hint",
  },
  {
    id: "connect",
    label: "Establish connection",
    detail: "Push match to rep dashboard + iOS overlay",
  },
];

function initialSteps(): PipelineStep[] {
  return LIVE_DEMO_STEPS.map((s) => ({ ...s, status: "pending" }));
}

export { initialSteps };

function sleep(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });
}

export interface LiveDemoCallbacks {
  onSteps: (steps: PipelineStep[]) => void;
  onComplete: (match: AttendeeMatchResult, transcript: string) => void;
  onError: (message: string) => void;
}

export async function runLiveDemo(
  target: Attendee,
  callbacks: LiveDemoCallbacks,
  signal?: AbortSignal,
) {
  let steps = initialSteps();
  const firstName = target.name.split(" ")[0];
  const transcript = `Hi ${firstName}, nice to meet you — great to connect at the event.`;

  const patch = (id: string, patchStep: Partial<PipelineStep>) => {
    steps = steps.map((s) => (s.id === id ? { ...s, ...patchStep } : s));
    callbacks.onSteps([...steps]);
  };

  const runStep = async (
    id: string,
    ms: number,
    detail?: string,
    work?: () => Promise<void>,
  ) => {
    patch(id, { status: "running", ...(detail ? { detail } : {}) });
    await sleep(ms, signal);
    if (work) await work();
    patch(id, { status: "done" });
  };

  try {
    callbacks.onSteps(steps);

    await runStep(
      "listen",
      700,
      'Wake phrase heard · "hey it\'s nice to meet you"',
    );

    await runStep(
      "transcribe",
      900,
      `Transcript · "${transcript.slice(0, 48)}…"`,
    );

    let matchResult: AttendeeMatchResult | null = null;

    patch("match", {
      status: "running",
      detail: `Scoring roster for "${firstName}"…`,
    });
    await sleep(500, signal);
    matchResult = await api.matchAttendee({
      name: firstName,
      company: target.company,
      transcript,
    });
    if (!matchResult.matched) {
      patch("match", {
        status: "error",
        detail: matchResult.message,
      });
      callbacks.onError(matchResult.message);
      return;
    }
    patch("match", {
      status: "done",
      detail: `Match ${Math.round((matchResult.score ?? 0) * 100)}% · ${matchResult.matched_on?.join(", ") ?? "name"}`,
    });

    const conn = matchResult.connection;
    await runStep(
      "resolve",
      650,
      conn?.id
        ? `Linked ${conn.name ?? firstName} · ${conn.company_name ?? target.company}`
        : `Resolved ${firstName}`,
    );

    const interestCount = matchResult.interests?.length ?? target.interests.length;
    const kgTopics = Object.keys(matchResult.knowledge_graph?.[0]?.topic_weights ?? {}).length;
    await runStep(
      "kg",
      800,
      kgTopics > 0
        ? `${kgTopics} topics · ${interestCount} interests merged`
        : `${interestCount} interests from roster profile`,
    );

    const warmth = conn?.predicted_warmth ?? target.icpScore;
    const icp = conn?.icp_score ?? target.icpScore;
    await runStep(
      "score",
      700,
      `ICP ${Math.round(icp)} · warmth ${Math.round(warmth)} · band ${warmth >= 70 ? "hot" : "warm"}`,
    );

    await runStep(
      "connect",
      500,
      matchResult.message,
    );

    callbacks.onComplete(matchResult, transcript);
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") return;
    const message = e instanceof Error ? e.message : "Live demo failed";
    const running = steps.find((s) => s.status === "running");
    if (running) patch(running.id, { status: "error", detail: message });
    callbacks.onError(message);
  }
}
