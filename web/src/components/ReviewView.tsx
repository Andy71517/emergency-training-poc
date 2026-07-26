import { useMemo } from "react";
import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleStop,
  Dices,
  FileText,
  ListChecks,
  RotateCcw,
  ShieldCheck,
  Waypoints,
} from "lucide-react";
import type { DemoPath, Finding, Review } from "../types";
import { friendlyLabel } from "../helpers";
import { ActionStatus } from "./ActionStatus";
import { Metric } from "./Metric";

export function ReviewView({
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
