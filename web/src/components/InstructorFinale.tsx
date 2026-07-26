import { ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import type { DemoPath, Review } from "../types";

export function InstructorFinale({
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
