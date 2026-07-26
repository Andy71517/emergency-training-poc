import { Activity, Waypoints } from "lucide-react";
import type { DemoPath, LiveEvent } from "../types";
import { friendlyLabel } from "../helpers";
import { ActionStatus } from "./ActionStatus";

export function RunningView({
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
