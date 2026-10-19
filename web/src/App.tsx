import {
  AlertTriangle,
  ArrowRight,
  Check,
  Clock3,
  Dices,
  Flame,
  MousePointerClick,
  Play,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { lazy, Suspense, useEffect, useRef, useState } from "react";
const PhysicsLab = lazy(() => import("./PhysicsLab").then(module => ({ default: module.PhysicsLab })));
import { SpatialWorkbench } from "./SpatialWorkbench";
import { ScenarioStudio } from "./ScenarioStudio";
import { ErrorView } from "./components/ErrorView";
import { IdleView } from "./components/IdleView";
import { InstructorFinale } from "./components/InstructorFinale";
import { InteractiveView } from "./components/InteractiveView";
import { PacingView } from "./components/PacingView";
import { ReviewView } from "./components/ReviewView";
import { RunningView } from "./components/RunningView";
import {
  ACTION_PACING_MS,
  PRESENTATION_DELAY_MS,
  friendlyLabel,
  openSocket,
  receiveJson,
  sleep,
} from "./helpers";
import type { DemoPath, LiveEvent, Review, RunStage } from "./types";

function App() {
  const [appView, setAppView] = useState<"sessions" | "studio" | "physics" | "workbench">("workbench");
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

  if (appView === "workbench") {
    return <SpatialWorkbench onLegacy={() => setAppView("sessions")} />;
  }

  if (appView === "studio") {
    return <ScenarioStudio onBack={() => setAppView("sessions")} />;
  }

  if (appView === "physics") {
    return <Suspense fallback={<p>Loading physics lab…</p>}><PhysicsLab onBack={() => setAppView("sessions")} /></Suspense>;
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
            <button className="secondary-button" onClick={() => setAppView("workbench")} type="button">
              <Sparkles size={16} /> ARC workspace
            </button>
            <button className="secondary-button" onClick={() => setAppView("physics")} type="button">
              <Play size={16} /> Visual physics lab
            </button>
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

export default App;
