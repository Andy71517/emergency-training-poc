import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleStop,
  Clock3,
  Flame,
  ListChecks,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Waypoints,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type DemoPath = {
  demo_id: string;
  label: string;
  short_label: string;
  scenario_id: string;
  tone: "expected" | "review";
  description: string;
  actions: string[];
};

type Finding = {
  code?: string;
  message?: string;
  instructor_note?: string;
};

type TimelineItem = {
  sequence_number: number;
  action_type: string;
  validation_status: "ok" | "warning" | "error" | string;
  phase_after?: string | null;
};

type Review = {
  review_headline: string;
  scenario_id: string;
  scenario_outcome: string | null;
  end_condition_reached: boolean;
  total_actions: number;
  action_timeline: TimelineItem[];
  progress_stories: string[];
  warnings: Finding[];
  errors: Finding[];
  environment_review: {
    room_cues?: Record<string, unknown>;
  };
};

type UpdateMessage = {
  message_type: string;
  validation_result?: {
    status: string;
  };
  scenario_state?: {
    is_terminal: boolean;
    state?: {
      phase?: string;
    };
  };
  message?: string;
};

type RunStage = "idle" | "pacing" | "running" | "review" | "error";

const PRESENTATION_DELAY_MS = 2500;
const ACTION_PACING_MS = 140;

const sleep = (milliseconds: number) =>
  new Promise((resolve) => window.setTimeout(resolve, milliseconds));

const friendlyLabel = (value: string) =>
  value
    .replace(/_v0$/, "")
    .replace(/_poc$/, "")
    .replaceAll("_", " ")
    .replace(/\bppe\b/i, "PPE")
    .replace(/^./, (letter) => letter.toUpperCase());

const receiveJson = (socket: WebSocket) =>
  new Promise<UpdateMessage>((resolve, reject) => {
    const handleMessage = (event: MessageEvent<string>) => {
      cleanup();
      resolve(JSON.parse(event.data) as UpdateMessage);
    };
    const handleError = () => {
      cleanup();
      reject(new Error("The browser lost its connection to the local backend."));
    };
    const cleanup = () => {
      socket.removeEventListener("message", handleMessage);
      socket.removeEventListener("error", handleError);
    };
    socket.addEventListener("message", handleMessage);
    socket.addEventListener("error", handleError);
  });

const openSocket = (sessionId: string) =>
  new Promise<WebSocket>((resolve, reject) => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/ws/sessions/${sessionId}`);
    socket.addEventListener("open", () => resolve(socket), { once: true });
    socket.addEventListener(
      "error",
      () => reject(new Error("Start the local FastAPI backend, then try again.")),
      { once: true },
    );
  });

function App() {
  const [paths, setPaths] = useState<DemoPath[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [disclaimer, setDisclaimer] = useState("");
  const [backendOnline, setBackendOnline] = useState(false);
  const [stage, setStage] = useState<RunStage>("idle");
  const [progress, setProgress] = useState(0);
  const [currentAction, setCurrentAction] = useState("");
  const [currentPhase, setCurrentPhase] = useState("awaiting_assessment");
  const [review, setReview] = useState<Review | null>(null);
  const [logName, setLogName] = useState("");
  const [error, setError] = useState("");
  const [showActions, setShowActions] = useState(false);

  const selected = paths.find((path) => path.demo_id === selectedId) ?? paths[0];
  const selectedIndex = Math.max(0, paths.findIndex((path) => path.demo_id === selected?.demo_id));

  useEffect(() => {
    const load = async () => {
      try {
        const [healthResponse, pathsResponse] = await Promise.all([
          fetch("/health"),
          fetch("/api/demo/paths"),
        ]);
        if (!healthResponse.ok || !pathsResponse.ok) throw new Error();
        const payload = (await pathsResponse.json()) as {
          paths: DemoPath[];
          disclaimer: string;
        };
        setPaths(payload.paths);
        setSelectedId(payload.paths[0]?.demo_id ?? "");
        setDisclaimer(payload.disclaimer);
        setBackendOnline(true);
      } catch {
        setError("The local backend is offline. Start it, then refresh this page.");
      }
    };
    void load();
  }, []);

  const resetReview = () => {
    setReview(null);
    setLogName("");
    setProgress(0);
    setCurrentAction("");
    setCurrentPhase("awaiting_assessment");
    setShowActions(false);
    setError("");
    setStage("idle");
  };

  const runDemo = async () => {
    if (!selected || stage === "running" || stage === "pacing") return;
    setReview(null);
    setError("");
    setProgress(0);
    setCurrentPhase("awaiting_assessment");
    setShowActions(false);
    setStage("pacing");

    try {
      await sleep(PRESENTATION_DELAY_MS);
      setStage("running");
      const sessionId = `web-${selected.demo_id}-${Date.now().toString(36)}`.slice(0, 64);
      const socket = await openSocket(sessionId);
      socket.send(JSON.stringify({ message_type: "start_session", scenario_id: selected.scenario_id }));
      const started = await receiveJson(socket);
      if (started.message_type === "error") throw new Error(started.message ?? "Session could not start.");

      for (const [index, action] of selected.actions.entries()) {
        setCurrentAction(friendlyLabel(action));
        const eventId = `event-${crypto.randomUUID()}`;
        socket.send(
          JSON.stringify({
            schema_version: "0.1.0",
            message_type: "trainee_action",
            session_id: sessionId,
            scenario_id: selected.scenario_id,
            message_id: `message-${crypto.randomUUID()}`,
            timestamp: new Date().toISOString(),
            sequence_number: index + 1,
            correlation_event_id: eventId,
            trainee_action: {
              schema_version: "0.1.0",
              session_id: sessionId,
              scenario_id: selected.scenario_id,
              event_id: eventId,
              timestamp: new Date().toISOString(),
              actor_id: "web-demo-trainee",
              action_type: action,
              payload: {},
              sequence_number: index + 1,
            },
          }),
        );
        const update = await receiveJson(socket);
        if (update.message_type === "error") throw new Error(update.message ?? "An action failed.");
        setCurrentPhase(update.scenario_state?.state?.phase ?? currentPhase);
        setProgress(((index + 1) / selected.actions.length) * 100);
        if (update.scenario_state?.is_terminal) {
          await receiveJson(socket);
          break;
        }
        await sleep(ACTION_PACING_MS);
      }

      const response = await fetch(`/api/demo/reviews/${sessionId}`);
      if (!response.ok) throw new Error("The review could not be loaded from the backend.");
      const payload = (await response.json()) as { review: Review; log_name: string };
      setReview(payload.review);
      setLogName(payload.log_name);
      setCurrentAction("");
      setStage("review");
    } catch (caught) {
      setStage("error");
      setError(caught instanceof Error ? caught.message : "The demo could not finish.");
    }
  };

  const continueToNextPath = () => {
    if (!paths.length) return;
    const nextPath = paths[(selectedIndex + 1) % paths.length];
    setSelectedId(nextPath.demo_id);
    resetReview();
  };

  return (
    <main className="min-h-screen overflow-hidden bg-ink text-slate-100">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="relative mx-auto flex min-h-screen max-w-[1540px] flex-col px-5 py-5 sm:px-8 lg:px-10">
        <header className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-2xl border border-amber-300/30 bg-amber-300/10 text-amber-300 shadow-glow-amber">
              <Flame size={22} strokeWidth={1.8} />
            </div>
            <div>
              <p className="eyebrow">Adaptive emergency training · proof of concept</p>
              <h1 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">
                Scenario Review Console
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`status-pill ${backendOnline ? "status-online" : "status-offline"}`}>
              <span className="status-dot" />
              Backend {backendOnline ? "online" : "offline"}
            </span>
            <span className="hidden rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-400 sm:inline">
              Local demo · deterministic rules
            </span>
          </div>
        </header>

        <section className="grid flex-1 gap-6 py-6 lg:grid-cols-[0.88fr_1.55fr]">
          <aside className="panel flex flex-col p-5 sm:p-6">
            <div className="mb-5">
              <p className="eyebrow text-azure-300">Choose a demonstration</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Four paths. Two review stories.</h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                Expected paths show a clean backend-owned state transition. Review paths deliberately
                create discussion points.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {paths.map((path, index) => (
                <button
                  key={path.demo_id}
                  className={`scenario-card ${selected?.demo_id === path.demo_id ? "scenario-selected" : ""}`}
                  onClick={() => {
                    setSelectedId(path.demo_id);
                    resetReview();
                  }}
                  type="button"
                >
                  <span className="scenario-index">0{index + 1}</span>
                  <span className="min-w-0 flex-1 text-left">
                    <span className="block font-display text-base font-semibold text-slate-100">
                      {path.short_label}
                    </span>
                    <span className="mt-1 block text-xs leading-5 text-slate-400">{path.description}</span>
                  </span>
                  <span className={`tone-mark ${path.tone === "review" ? "tone-review" : "tone-expected"}`}>
                    {path.tone === "review" ? <AlertTriangle size={16} /> : <Check size={16} />}
                  </span>
                </button>
              ))}
            </div>

            <div className="mt-auto pt-5">
              <button
                className="run-button"
                disabled={!selected || !backendOnline || stage === "running" || stage === "pacing"}
                onClick={() => void runDemo()}
                type="button"
              >
                {stage === "pacing" ? <Clock3 size={18} /> : <Play size={18} fill="currentColor" />}
                {stage === "pacing" ? "Preparing presentation…" : "Run selected path"}
                <ArrowRight className="ml-auto" size={18} />
              </button>
              <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-slate-500">
                <ShieldCheck className="mt-0.5 shrink-0" size={14} />
                Backend state, validation findings, and saved reviews remain the source of truth.
              </p>
            </div>
          </aside>

          <section className="panel relative min-h-[620px] overflow-hidden">
            {stage === "idle" && <IdleView selected={selected} />}
            {stage === "pacing" && <PacingView selected={selected} />}
            {stage === "running" && (
              <RunningView
                selected={selected}
                progress={progress}
                currentAction={currentAction}
                currentPhase={currentPhase}
              />
            )}
            {stage === "review" && review && (
              <ReviewView
                logName={logName}
                nextLabel={selectedIndex === paths.length - 1 ? "Return to first path" : "Continue to next path"}
                onNext={continueToNextPath}
                onReset={resetReview}
                review={review}
                selected={selected}
                setShowActions={setShowActions}
                showActions={showActions}
              />
            )}
            {stage === "error" && <ErrorView error={error} onReset={resetReview} />}
          </section>
        </section>

        <footer className="flex flex-col gap-2 border-t border-white/10 pt-4 text-xs leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>{disclaimer || "Deterministic POC rule checks only—not operational guidance."}</p>
          <p className="shrink-0">No real AI adaptation, smoke physics, sensing, or trainee scoring.</p>
        </footer>
      </div>
    </main>
  );
}

function IdleView({ selected }: { selected?: DemoPath }) {
  return (
    <div className="flex h-full min-h-[620px] flex-col justify-between p-7 sm:p-10">
      <div className="flex items-center justify-between">
        <span className="section-chip"><Sparkles size={14} /> Presenter view</span>
        <span className={`path-chip ${selected?.tone === "review" ? "path-review" : "path-expected"}`}>
          {selected?.tone === "review" ? "Review-focused" : "Expected path"}
        </span>
      </div>
      <div className="max-w-2xl py-14">
        <p className="eyebrow text-amber-300">Selected scenario</p>
        <h2 className="mt-4 font-display text-4xl font-semibold leading-[1.08] tracking-tight sm:text-6xl">
          {selected?.short_label ?? "Loading demo paths…"}
        </h2>
        <p className="mt-5 max-w-xl text-base leading-7 text-slate-400 sm:text-lg">
          {selected?.description ?? "Connecting to the local deterministic backend."}
        </p>
      </div>
      <div className="grid gap-3 border-t border-white/10 pt-5 sm:grid-cols-3">
        <MiniFact icon={<Waypoints size={17} />} label="Scripted actions" value={`${selected?.actions.length ?? 0}`} />
        <MiniFact icon={<Activity size={17} />} label="State owner" value="FastAPI backend" />
        <MiniFact icon={<ListChecks size={17} />} label="Review style" value="Plain English" />
      </div>
    </div>
  );
}

function PacingView({ selected }: { selected?: DemoPath }) {
  return (
    <div className="grid h-full min-h-[620px] place-items-center p-8 text-center">
      <div className="max-w-lg">
        <div className="pulse-orbit mx-auto"><Clock3 size={32} /></div>
        <p className="eyebrow mt-8 text-amber-300">Presentation pacing</p>
        <h2 className="mt-3 font-display text-4xl font-semibold">Beginning in 2.5 seconds</h2>
        <p className="mt-4 leading-7 text-slate-400">
          A short intentional pause gives the audience time to settle before the backend runs
          <span className="text-slate-200"> {selected?.short_label}</span>.
        </p>
        <div className="countdown-track mt-8"><span /></div>
      </div>
    </div>
  );
}

function RunningView({
  selected,
  progress,
  currentAction,
  currentPhase,
}: {
  selected?: DemoPath;
  progress: number;
  currentAction: string;
  currentPhase: string;
}) {
  return (
    <div className="flex h-full min-h-[620px] flex-col justify-center p-8 sm:p-12">
      <div className="mb-10 flex items-end justify-between gap-4">
        <div>
          <p className="eyebrow text-azure-300">Backend session running</p>
          <h2 className="mt-2 font-display text-3xl font-semibold sm:text-4xl">{selected?.short_label}</h2>
        </div>
        <span className="font-mono text-2xl text-azure-300">{Math.round(progress)}%</span>
      </div>
      <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
      <div className="progress-steps" aria-label="Scenario progress">
        {["Assess", "Access", "Observe", "Resolve"].map((label, index) => {
          const reached = progress >= index * 25;
          return <span className={reached ? "progress-step reached" : "progress-step"} key={label}><i />{label}</span>;
        })}
      </div>
      <div className="mt-8 rounded-2xl border border-azure-300/15 bg-azure-300/[0.05] p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Current recorded action</p>
        <p className="mt-2 font-display text-2xl font-semibold text-slate-100">
          {currentAction || "Starting session…"}
        </p>
        <div className="phase-badge mt-4">
          <Waypoints size={14} /> Backend progress state: {friendlyLabel(currentPhase)}
        </div>
      </div>
      <p className="mt-6 flex items-center gap-2 text-sm text-slate-500">
        <Activity className="animate-pulse text-azure-300" size={16} />
        Applying deterministic scenario transitions and saving ordered JSONL events.
      </p>
    </div>
  );
}

function ReviewView({
  review,
  selected,
  logName,
  showActions,
  setShowActions,
  onReset,
  onNext,
  nextLabel,
}: {
  review: Review;
  selected?: DemoPath;
  logName: string;
  showActions: boolean;
  setShowActions: (value: boolean) => void;
  onReset: () => void;
  onNext: () => void;
  nextLabel: string;
}) {
  const cues = review.environment_review.room_cues ?? {};
  const cueRows = [
    ["Area checked", Boolean(cues.room_scanned)],
    ["Door checked", Boolean(cues.door_checked)],
    ["Status communicated", Boolean(cues.status_communicated)],
    ["Environment monitored", Boolean(cues.environment_monitored)],
    ["Exit path clear", Boolean(cues.exit_path_clear)],
  ] as const;
  const findings = useMemo(() => {
    const unique = new Map<string, Finding>();
    [...review.errors, ...review.warnings].forEach((finding) => {
      const message = finding.message ?? "A toy rule flagged an action for review.";
      unique.set(message, finding);
    });
    return [...unique.values()];
  }, [review.errors, review.warnings]);
  const statusCounts = review.action_timeline.reduce(
    (counts, item) => ({ ...counts, [item.validation_status]: (counts[item.validation_status] ?? 0) + 1 }),
    {} as Record<string, number>,
  );

  return (
    <div className="h-full min-h-[620px] overflow-y-auto p-6 sm:p-8 lg:p-10">
      <div className="flex flex-col gap-5 border-b border-white/10 pb-6 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="eyebrow text-azure-300">Post-scenario review</p>
          <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight sm:text-4xl">
            {selected?.short_label}
          </h2>
          <p className="mt-3 max-w-2xl leading-6 text-slate-400">{review.review_headline}</p>
        </div>
        <div className={`result-seal ${review.errors.length ? "result-review" : "result-complete"}`}>
          {review.errors.length ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          {review.errors.length ? "Review needed" : "Path complete"}
        </div>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <Metric label="Actions recorded" value={review.total_actions} tone="azure" />
        <Metric label="Review suggestions" value={review.warnings.length} tone="amber" />
        <Metric label="Blocked actions" value={review.errors.length} tone="red" />
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[0.92fr_1.08fr]">
        <div className="review-card">
          <div className="review-card-title"><ListChecks size={17} /> Important cues</div>
          <div className="mt-4 space-y-2.5">
            {cueRows.map(([label, complete]) => (
              <div className="cue-row" key={label}>
                <span>{label}</span>
                <span className={complete ? "cue-complete" : "cue-missing"}>
                  {complete ? <Check size={14} /> : <CircleStop size={14} />}
                  {complete ? "Complete" : "Missing"}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="review-card">
          <div className="review-card-title"><AlertTriangle size={17} /> Discussion points</div>
          <div className="mt-4 space-y-3">
            {findings.length ? (
              findings.map((finding) => (
                <div className="finding" key={finding.message}>
                  <span className="finding-dot" />
                  <p>{finding.message}</p>
                </div>
              ))
            ) : (
              <div className="finding finding-clear">
                <CheckCircle2 size={18} />
                <p>No warnings or errors were recorded by the toy rules.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {review.progress_stories?.length > 0 && (
        <div className="progress-story mt-5">
          <div className="review-card-title"><Waypoints size={17} /> Why an action was retried</div>
          {review.progress_stories.map((story) => <p className="mt-3 leading-6 text-slate-300" key={story}>{story}</p>)}
        </div>
      )}

      <button className="action-disclosure" onClick={() => setShowActions(!showActions)} type="button">
        <span><Waypoints size={16} /> Full action sequence</span>
        <span className="text-xs text-slate-500">
          {statusCounts.ok ?? 0} accepted · {statusCounts.warning ?? 0} review · {statusCounts.error ?? 0} blocked
        </span>
        <ChevronDown className={`transition-transform ${showActions ? "rotate-180" : ""}`} size={17} />
      </button>
      {showActions && (
        <ol className="action-list">
          {review.action_timeline.map((item) => (
            <li key={`${item.sequence_number}-${item.action_type}`}>
              <span className="action-number">{String(item.sequence_number).padStart(2, "0")}</span>
              <span className="flex-1">{friendlyLabel(item.action_type)}</span>
              {item.phase_after && <span className="hidden text-[.67rem] text-slate-600 lg:inline">{friendlyLabel(item.phase_after)}</span>}
              <ActionStatus status={item.validation_status} />
            </li>
          ))}
        </ol>
      )}

      <div className="mt-6 flex flex-col gap-3 border-t border-white/10 pt-5 sm:flex-row sm:items-center sm:justify-between">
        <p className="truncate text-xs text-slate-600">Saved locally · {logName}</p>
        <div className="flex flex-wrap gap-2">
          <button className="secondary-button" onClick={onReset} type="button">
            <RotateCcw size={15} /> Choose a path
          </button>
          <button className="next-button" onClick={onNext} type="button">
            {nextLabel} <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}

function ErrorView({ error, onReset }: { error: string; onReset: () => void }) {
  return (
    <div className="grid h-full min-h-[620px] place-items-center p-8 text-center">
      <div className="max-w-md">
        <div className="mx-auto grid size-16 place-items-center rounded-3xl border border-red-300/20 bg-red-400/10 text-red-300">
          <XCircle size={30} />
        </div>
        <h2 className="mt-6 font-display text-3xl font-semibold">The demo could not finish</h2>
        <p className="mt-3 leading-7 text-slate-400">{error}</p>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          If the backend was restarted, reload this local page to reconnect. No session result is claimed when a run does not finish.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-2">
          <button className="secondary-button" onClick={onReset} type="button">
            <RotateCcw size={15} /> Return to selection
          </button>
          <button className="next-button" onClick={() => window.location.reload()} type="button">
            Reload local connection
          </button>
        </div>
      </div>
    </div>
  );
}

function MiniFact({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="mini-fact">
      <span className="text-azure-300">{icon}</span>
      <span><span className="block text-xs text-slate-500">{label}</span><span className="mt-0.5 block text-sm font-medium">{value}</span></span>
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`metric metric-${tone}`}>
      <span className="font-mono text-3xl font-semibold">{String(value).padStart(2, "0")}</span>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}

function ActionStatus({ status }: { status: string }) {
  if (status === "ok") return <span className="action-status status-ok"><Check size={13} /> Accepted</span>;
  if (status === "warning") return <span className="action-status status-warn"><AlertTriangle size={13} /> Review</span>;
  return <span className="action-status status-block"><XCircle size={13} /> Blocked</span>;
}

export default App;
