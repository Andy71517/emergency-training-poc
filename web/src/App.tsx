import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleStop,
  Clock3,
  Dices,
  FileText,
  Flame,
  ListChecks,
  MousePointerClick,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Waypoints,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { ScenarioStudio } from "./ScenarioStudio";

type DemoPath = {
  demo_id: string;
  label: string;
  short_label: string;
  scenario_id: string;
  tone: "expected" | "review" | "explore" | "interactive";
  description: string;
  actions: string[];
  mode?: "scripted" | "seeded_exploration" | "user_controlled";
  seed?: number | null;
  available_actions?: string[];
};

type Finding = {
  code?: string;
  message?: string;
  instructor_note?: string;
};

type TimelineItem = {
  sequence_number: number;
  action_type: string;
  action_description?: string;
  result_summary?: string;
  validation_status: "ok" | "warning" | "error" | string;
  phase_before?: string | null;
  phase_after?: string | null;
  state_changes?: string[];
  finding_messages?: string[];
};

type Review = {
  review_headline: string;
  scenario_id: string;
  scenario_outcome: string | null;
  end_condition_reached: boolean;
  total_actions: number;
  action_timeline: TimelineItem[];
  progress_stories: string[];
  instructor_review: {
    title: string;
    summary: string;
    evidence: string[];
    discussion_prompt: string;
    boundary: string;
  };
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
    warnings?: Finding[];
    errors?: Finding[];
  };
  scenario_state?: {
    is_terminal: boolean;
    state?: {
      phase?: string;
    };
  };
  message?: string;
};

type RunStage = "idle" | "pacing" | "running" | "interactive" | "review" | "error";

type LiveEvent = {
  action: string;
  status: string;
  phase: string;
  message?: string;
};

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
  const [appView, setAppView] = useState<"sessions" | "studio">("sessions");
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
  const [explorationPath, setExplorationPath] = useState<DemoPath | null>(null);
  const [generatingExploration, setGeneratingExploration] = useState(false);
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([]);
  const [showInstructorFinale, setShowInstructorFinale] = useState(false);
  const [interactiveSessionId, setInteractiveSessionId] = useState("");
  const [interactiveFeedback, setInteractiveFeedback] = useState<LiveEvent | null>(null);
  const [interactiveBusy, setInteractiveBusy] = useState(false);
  const interactiveSocket = useRef<WebSocket | null>(null);
  const interactiveSequence = useRef(0);

  const displayPaths = explorationPath ? [...paths, explorationPath] : paths;
  const selected = displayPaths.find((path) => path.demo_id === selectedId) ?? displayPaths[0];
  const selectedIndex = Math.max(0, displayPaths.findIndex((path) => path.demo_id === selected?.demo_id));

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
    interactiveSocket.current?.close();
    interactiveSocket.current = null;
    interactiveSequence.current = 0;
    setReview(null);
    setLogName("");
    setProgress(0);
    setCurrentAction("");
    setCurrentPhase("awaiting_assessment");
    setShowActions(false);
    setLiveEvents([]);
    setShowInstructorFinale(false);
    setInteractiveSessionId("");
    setInteractiveFeedback(null);
    setInteractiveBusy(false);
    setError("");
    setStage("idle");
  };

  const loadReview = async (sessionId: string) => {
    const response = await fetch(`/api/demo/reviews/${sessionId}`);
    if (!response.ok) throw new Error("The review could not be loaded from the backend.");
    const payload = (await response.json()) as { review: Review; log_name: string };
    setReview(payload.review);
    setLogName(payload.log_name);
    setCurrentAction("");
    setShowInstructorFinale(true);
    setStage("review");
  };

  const runDemo = async () => {
    if (!selected || stage === "running" || stage === "pacing") return;
    if (selected.mode === "user_controlled") {
      await startInteractiveRun();
      return;
    }
    setReview(null);
    setError("");
    setProgress(0);
    setCurrentPhase("awaiting_assessment");
    setShowActions(false);
    setLiveEvents([]);
    setStage("pacing");

    try {
      await sleep(PRESENTATION_DELAY_MS);
      setStage("running");
      const sessionId = `web-${selected.demo_id}-${crypto.randomUUID()}`.slice(0, 64);
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
              actor_id: selected.mode === "seeded_exploration" ? "simulated-trainee-inputs" : "web-demo-trainee",
              action_type: action,
              payload: {},
              sequence_number: index + 1,
            },
          }),
        );
        const update = await receiveJson(socket);
        if (update.message_type === "error") throw new Error(update.message ?? "An action failed.");
        const nextPhase = update.scenario_state?.state?.phase ?? currentPhase;
        const status = update.validation_result?.status ?? "unknown";
        setCurrentPhase(nextPhase);
        setLiveEvents((events) => [
          ...events,
          { action: friendlyLabel(action), status, phase: friendlyLabel(nextPhase) },
        ]);
        setProgress(((index + 1) / selected.actions.length) * 100);
        if (update.scenario_state?.is_terminal) {
          await receiveJson(socket);
          break;
        }
        await sleep(ACTION_PACING_MS);
      }

      await loadReview(sessionId);
    } catch (caught) {
      setStage("error");
      setError(caught instanceof Error ? caught.message : "The demo could not finish.");
    }
  };

  const startInteractiveRun = async () => {
    if (!selected) return;
    setReview(null);
    setError("");
    setLiveEvents([]);
    setInteractiveFeedback(null);
    setCurrentPhase("awaiting_assessment");
    setStage("pacing");
    try {
      await sleep(PRESENTATION_DELAY_MS);
      const sessionId = `web-user-controlled-${crypto.randomUUID()}`.slice(0, 64);
      const socket = await openSocket(sessionId);
      socket.send(JSON.stringify({ message_type: "start_session", scenario_id: selected.scenario_id }));
      const started = await receiveJson(socket);
      if (started.message_type === "error") throw new Error(started.message ?? "Session could not start.");
      interactiveSocket.current = socket;
      interactiveSequence.current = 0;
      setInteractiveSessionId(sessionId);
      setStage("interactive");
    } catch (caught) {
      setStage("error");
      setError(caught instanceof Error ? caught.message : "The user-controlled run could not start.");
    }
  };

  const submitInteractiveAction = async (action: string) => {
    const socket = interactiveSocket.current;
    if (!socket || !selected || !interactiveSessionId || interactiveBusy) return;
    setInteractiveBusy(true);
    interactiveSequence.current += 1;
    const sequenceNumber = interactiveSequence.current;
    const eventId = `event-${crypto.randomUUID()}`;
    setCurrentAction(friendlyLabel(action));
    try {
      socket.send(
        JSON.stringify({
          schema_version: "0.1.0",
          message_type: "trainee_action",
          session_id: interactiveSessionId,
          scenario_id: selected.scenario_id,
          message_id: `message-${crypto.randomUUID()}`,
          timestamp: new Date().toISOString(),
          sequence_number: sequenceNumber,
          correlation_event_id: eventId,
          trainee_action: {
            schema_version: "0.1.0",
            session_id: interactiveSessionId,
            scenario_id: selected.scenario_id,
            event_id: eventId,
            timestamp: new Date().toISOString(),
            actor_id: "user-controlled-poc",
            action_type: action,
            payload: {},
            sequence_number: sequenceNumber,
          },
        }),
      );
      const update = await receiveJson(socket);
      if (update.message_type === "error") throw new Error(update.message ?? "The action could not be processed.");
      const nextPhase = update.scenario_state?.state?.phase ?? currentPhase;
      const status = update.validation_result?.status ?? "unknown";
      const findings = [
        ...(update.validation_result?.errors ?? []),
        ...(update.validation_result?.warnings ?? []),
      ];
      const feedback = {
        action: friendlyLabel(action),
        status,
        phase: friendlyLabel(nextPhase),
        message: findings[0]?.message,
      };
      setCurrentPhase(nextPhase);
      setInteractiveFeedback(feedback);
      setLiveEvents((events) => [...events, feedback]);
      if (update.scenario_state?.is_terminal) {
        await receiveJson(socket);
        interactiveSocket.current = null;
        await loadReview(interactiveSessionId);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The action could not be processed.");
      setStage("error");
    } finally {
      setInteractiveBusy(false);
    }
  };

  const generateExploration = async () => {
    const scenarioId = selected?.scenario_id ?? "smoke_inhalation_room_v0";
    setGeneratingExploration(true);
    setError("");
    try {
      const response = await fetch(`/api/demo/exploration/${scenarioId}`);
      if (!response.ok) throw new Error("The backend could not generate an exploration run.");
      const payload = (await response.json()) as { path: DemoPath };
      setExplorationPath(payload.path);
      setSelectedId(payload.path.demo_id);
      resetReview();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Exploration generation failed.");
      setStage("error");
    } finally {
      setGeneratingExploration(false);
    }
  };

  const continueToNextPath = () => {
    if (!paths.length) return;
    const nextPath = displayPaths[(selectedIndex + 1) % displayPaths.length];
    setSelectedId(nextPath.demo_id);
    resetReview();
  };

  if (appView === "studio") {
    return <ScenarioStudio onBack={() => setAppView("sessions")} />;
  }

  return (
    <main className="app-shell min-h-screen overflow-hidden bg-ink text-slate-100">
      <div className="technical-grid" />
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="app-frame relative mx-auto flex min-h-screen max-w-[1540px] flex-col px-5 py-5 sm:px-8 lg:px-10">
        <header className="app-header flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-center sm:justify-between">
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
            <button className="secondary-button" onClick={() => setAppView("studio")} type="button">
              <Sparkles size={16} /> Scenario studio
            </button>
            <span className={`status-pill ${backendOnline ? "status-online" : "status-offline"}`}>
              <span className="status-dot" />
              Backend {backendOnline ? "online" : "offline"}
            </span>
            <span className="hidden rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-400 sm:inline">
              Local demo · deterministic rules
            </span>
          </div>
        </header>

        <section className="workspace-grid grid flex-1 gap-6 py-6 lg:grid-cols-[0.82fr_1.62fr]">
          <aside className="panel scenario-sidebar flex flex-col p-5 sm:p-6">
            <div className="mb-5">
              <p className="eyebrow text-azure-300">Choose a demonstration</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Clear paths. Rich review stories.</h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-slate-400">
                Guided paths stay repeatable for presentation. A separate seeded exploration mode
                creates varied simulated-trainee inputs that can still be reproduced.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              {displayPaths.map((path, index) => (
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
                  <span className={`tone-mark tone-${path.tone}`}>
                    {path.tone === "review" ? <AlertTriangle size={16} /> : path.tone === "explore" ? <Dices size={16} /> : path.tone === "interactive" ? <MousePointerClick size={16} /> : <Check size={16} />}
                  </span>
                </button>
              ))}
            </div>

            <div className="mt-auto pt-5">
              <button
                className="explore-button mb-3"
                disabled={!backendOnline || generatingExploration || stage === "running" || stage === "pacing" || stage === "interactive"}
                onClick={() => void generateExploration()}
                type="button"
              >
                <Dices size={17} />
                <span><strong>{generatingExploration ? "Generating…" : "Generate seeded exploration"}</strong><small>Developer tool · uses selected scenario</small></span>
              </button>
              <button
                className="run-button"
                disabled={!selected || !backendOnline || stage === "running" || stage === "pacing" || stage === "interactive"}
                onClick={() => void runDemo()}
                type="button"
              >
                {stage === "pacing" ? <Clock3 size={18} /> : <Play size={18} fill="currentColor" />}
                {stage === "pacing" ? "Preparing presentation…" : selected?.mode === "user_controlled" ? "Start choosing actions" : "Run selected path"}
                <ArrowRight className="ml-auto" size={18} />
              </button>
              <p className="mt-3 flex items-start gap-2 text-xs leading-5 text-slate-500">
                <ShieldCheck className="mt-0.5 shrink-0" size={14} />
                Backend state, validation findings, and saved reviews remain the source of truth.
              </p>
            </div>
          </aside>

          <section className="panel workspace-panel relative min-h-[620px] overflow-hidden">
            {stage === "idle" && <IdleView selected={selected} />}
            {stage === "pacing" && <PacingView selected={selected} />}
            {stage === "running" && (
              <RunningView
                selected={selected}
                progress={progress}
                currentAction={currentAction}
                currentPhase={currentPhase}
                liveEvents={liveEvents}
              />
            )}
            {stage === "interactive" && (
              <InteractiveView
                actions={(selected?.available_actions ?? []).filter((action) => action !== "stop_scenario")}
                busy={interactiveBusy}
                currentPhase={currentPhase}
                feedback={interactiveFeedback}
                history={liveEvents}
                onAction={(action) => void submitInteractiveAction(action)}
                onFinish={() => void submitInteractiveAction("stop_scenario")}
                selected={selected}
              />
            )}
            {stage === "review" && review && showInstructorFinale && (
              <InstructorFinale
                onOpenReview={() => setShowInstructorFinale(false)}
                review={review}
                selected={selected}
              />
            )}
            {stage === "review" && review && !showInstructorFinale && (
              <ReviewView
                logName={logName}
                nextLabel={selectedIndex === displayPaths.length - 1 ? "Return to first path" : "Continue to next path"}
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

        <footer className="app-footer flex flex-col gap-2 border-t border-white/10 pt-4 text-xs leading-5 text-slate-500 sm:flex-row sm:items-center sm:justify-between">
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
        <span className={`path-chip path-${selected?.tone ?? "expected"}`}>
          {selected?.tone === "review" ? "Review-focused" : selected?.tone === "explore" ? "Seeded exploration" : selected?.tone === "interactive" ? "User controlled" : "Expected path"}
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
        <MiniFact icon={<Waypoints size={17} />} label={selected?.mode === "seeded_exploration" ? "Generated actions" : selected?.mode === "user_controlled" ? "Available actions" : "Scripted actions"} value={`${selected?.mode === "user_controlled" ? selected.available_actions?.length ?? 0 : selected?.actions.length ?? 0}`} />
        <MiniFact icon={<Activity size={17} />} label="State owner" value="FastAPI backend" />
        <MiniFact icon={selected?.seed ? <Dices size={17} /> : <ListChecks size={17} />} label={selected?.seed ? "Reproducible seed" : "Review style"} value={selected?.seed ? String(selected.seed) : "Plain English"} />
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
  liveEvents,
}: {
  selected?: DemoPath;
  progress: number;
  currentAction: string;
  currentPhase: string;
  liveEvents: LiveEvent[];
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
      <div className="live-trail mt-5">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Latest backend results</p>
          <span className="text-xs text-slate-600">Showing the latest four</span>
        </div>
        <div className="mt-3 space-y-2">
          {liveEvents.slice(-4).reverse().map((event, index) => (
            <div className="live-event" key={`${event.action}-${liveEvents.length - index}`}>
              <ActionStatus status={event.status} />
              <span className="min-w-0 flex-1 truncate text-sm text-slate-200">{event.action}</span>
              <span className="hidden text-xs text-slate-500 sm:inline">{event.phase}</span>
            </div>
          ))}
          {!liveEvents.length && <p className="text-sm text-slate-500">Waiting for the first recorded action…</p>}
        </div>
      </div>
      <p className="mt-6 flex items-center gap-2 text-sm text-slate-500">
        <Activity className="animate-pulse text-azure-300" size={16} />
        Applying deterministic scenario transitions and saving ordered JSONL events.
      </p>
    </div>
  );
}

function InteractiveView({
  selected,
  actions,
  currentPhase,
  feedback,
  history,
  busy,
  onAction,
  onFinish,
}: {
  selected?: DemoPath;
  actions: string[];
  currentPhase: string;
  feedback: LiveEvent | null;
  history: LiveEvent[];
  busy: boolean;
  onAction: (action: string) => void;
  onFinish: () => void;
}) {
  return (
    <div className="interactive-stage h-full min-h-[620px] overflow-y-auto p-6 sm:p-8 lg:p-10">
      <div className="flex flex-col gap-4 border-b border-white/10 pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="eyebrow text-violet-300">User-controlled POC run</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">{selected?.short_label}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            Choose one action at a time. The backend checks the action against its current scenario state and responds immediately.
          </p>
        </div>
        <div className="phase-badge"><Waypoints size={14} /> Current progress: {friendlyLabel(currentPhase)}</div>
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
        <section className="review-card">
          <div className="review-card-title"><MousePointerClick size={17} /> Choose the next action</div>
          <div className="action-choice-grid mt-4">
            {actions.map((action) => (
              <button disabled={busy} key={action} onClick={() => onAction(action)} type="button">
                <span>{friendlyLabel(action)}</span><ArrowRight size={14} />
              </button>
            ))}
          </div>
          <button className="finish-run-button mt-4" disabled={busy} onClick={onFinish} type="button">
            <CircleStop size={16} /> Finish run and create review
          </button>
        </section>

        <div className="space-y-5">
          <section className={`response-card response-${feedback?.status ?? "waiting"}`}>
            <div className="review-card-title"><Activity size={17} /> Backend response</div>
            {feedback ? (
              <div className="mt-4">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-lg text-slate-100">{feedback.action}</strong>
                  <ActionStatus status={feedback.status} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">
                  {feedback.message ?? (feedback.status === "ok" ? "The action was accepted by the current POC state." : "The backend recorded a review finding for this action.")}
                </p>
                <p className="mt-3 text-xs text-slate-500">Progress after action: {feedback.phase}</p>
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-slate-500">Choose an action to see what the backend records and whether the scenario moves forward.</p>
            )}
          </section>

          <section className="review-card">
            <div className="flex items-center justify-between">
              <div className="review-card-title"><ListChecks size={17} /> Recorded so far</div>
              <span className="text-xs text-slate-600">{history.length} actions</span>
            </div>
            <div className="mt-3 space-y-2">
              {history.slice(-5).reverse().map((event, index) => (
                <div className="live-event" key={`${event.action}-${history.length - index}`}>
                  <ActionStatus status={event.status} />
                  <span className="min-w-0 flex-1 truncate text-sm">{event.action}</span>
                </div>
              ))}
              {!history.length && <p className="text-sm text-slate-500">No actions recorded yet.</p>}
            </div>
          </section>
        </div>
      </div>

      <p className="mt-5 flex items-start gap-2 text-xs leading-5 text-slate-500">
        <ShieldCheck className="mt-0.5 shrink-0" size={14} />
        This interaction demonstrates backend state and deterministic POC findings. It does not provide protocol guidance or a trainee score.
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
          {selected?.seed && <div className="seed-badge mt-4"><Dices size={14} /> Reproducible exploration seed: {selected.seed}</div>}
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

      <div className="story-banner mt-5">
        <div className="story-icon"><FileText size={20} /></div>
        <div>
          <p className="eyebrow text-azure-300">Session story</p>
          <p className="mt-1 text-sm leading-6 text-slate-300">
            The run finished in <strong>{friendlyLabel(review.scenario_outcome ?? "unknown")}</strong> state after {review.total_actions} recorded actions.
            {review.errors.length ? ` ${review.errors.length} action${review.errors.length === 1 ? " was" : "s were"} blocked by the current POC state.` : " No actions were blocked by the POC rules."}
          </p>
        </div>
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
        <ol className="action-list action-detail-list">
          {review.action_timeline.map((item) => (
            <li key={`${item.sequence_number}-${item.action_type}`}>
              <span className="action-number">{String(item.sequence_number).padStart(2, "0")}</span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="text-sm text-slate-100">{friendlyLabel(item.action_type)}</strong>
                  <ActionStatus status={item.validation_status} />
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-400">{item.action_description}</p>
                <p className="mt-1 text-xs font-medium leading-5 text-slate-300">{item.result_summary}</p>
                {(item.state_changes?.length ?? 0) > 0 && (
                  <div className="state-change-list mt-2">
                    {item.state_changes?.map((change) => <span key={change}>{change}</span>)}
                  </div>
                )}
                {(item.finding_messages?.length ?? 0) > 0 && (
                  <p className="mt-2 text-xs leading-5 text-amber-200/80">Review note: {item.finding_messages?.join(" ")}</p>
                )}
              </div>
              {item.phase_after && <span className="phase-mini">{friendlyLabel(item.phase_after)}</span>}
            </li>
          ))}
        </ol>
      )}

      <section className="instructor-message mt-6" aria-labelledby="instructor-review-title">
        <div className="instructor-message-header">
          <div className="instructor-mark"><ShieldCheck size={22} /></div>
          <div>
            <p className="eyebrow text-amber-300">Final discussion aid</p>
            <h3 className="mt-1 font-display text-xl font-semibold" id="instructor-review-title">
              {review.instructor_review.title}
            </h3>
          </div>
        </div>
        <p className="mt-4 leading-6 text-slate-200">{review.instructor_review.summary}</p>
        <ul className="instructor-evidence mt-4">
          {review.instructor_review.evidence.map((item) => <li key={item}>{item}</li>)}
        </ul>
        <div className="discussion-prompt mt-4">
          <span>Suggested discussion prompt</span>
          <p>{review.instructor_review.discussion_prompt}</p>
        </div>
        <p className="mt-4 border-t border-white/10 pt-3 text-xs leading-5 text-slate-500">
          {review.instructor_review.boundary}
        </p>
      </section>

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

function InstructorFinale({
  review,
  selected,
  onOpenReview,
}: {
  review: Review;
  selected?: DemoPath;
  onOpenReview: () => void;
}) {
  return (
    <div className="finale-stage min-h-[620px] p-6 sm:p-10">
      <div className="finale-heading">
        <span className="section-chip"><CheckCircle2 size={14} /> Session review ready</span>
        <p>{selected?.short_label}</p>
      </div>
      <button
        aria-label="Open the full post-scenario review"
        className="instructor-message instructor-finale-card"
        onClick={onOpenReview}
        type="button"
      >
        <div className="instructor-message-header">
          <div className="instructor-mark"><ShieldCheck size={24} /></div>
          <div className="text-left">
            <p className="eyebrow text-amber-300">Final discussion aid</p>
            <h2 className="mt-1 font-display text-2xl font-semibold sm:text-3xl">
              {review.instructor_review.title}
            </h2>
          </div>
        </div>
        <p className="mt-5 text-left text-lg leading-7 text-slate-100">
          {review.instructor_review.summary}
        </p>
        <ul className="instructor-evidence mt-5 text-left">
          {review.instructor_review.evidence.map((item) => <li key={item}>{item}</li>)}
        </ul>
        <div className="discussion-prompt mt-5 text-left">
          <span>Suggested discussion prompt</span>
          <p>{review.instructor_review.discussion_prompt}</p>
        </div>
        <p className="mt-5 border-t border-white/10 pt-4 text-left text-xs leading-5 text-slate-500">
          {review.instructor_review.boundary}
        </p>
        <span className="finale-open-hint">
          Open full session review <ArrowRight size={16} />
        </span>
      </button>
      <p className="finale-footnote">One click opens cues, findings, action details, and path controls.</p>
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
