import { Clock3 } from "lucide-react";
import type { DemoPath } from "../types";

export function PacingView({ selected }: { selected?: DemoPath }) {
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
