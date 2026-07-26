import { Activity, Dices, ListChecks, Sparkles, Waypoints } from "lucide-react";
import type { DemoPath } from "../types";
import { MiniFact } from "./MiniFact";

export function IdleView({ selected }: { selected?: DemoPath }) {
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
