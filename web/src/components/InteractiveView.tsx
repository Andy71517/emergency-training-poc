import { Activity, ArrowRight, CircleStop, ListChecks, MousePointerClick, ShieldCheck, Waypoints } from "lucide-react";
import type { DemoPath, LiveEvent } from "../types";
import { friendlyLabel } from "../helpers";
import { ActionStatus } from "./ActionStatus";

export function InteractiveView({
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
