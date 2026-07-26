import { RotateCcw, XCircle } from "lucide-react";

export function ErrorView({ error, onReset }: { error: string; onReset: () => void }) {
  return (
    <div className="grid h-full min-h-[620px] place-items-center p-8 text-center">
      <div className="max-w-md">
        <div className="mx-auto grid size-16 place-items-center rounded-3xl border border-red-300/20 bg-red-400/10 text-red-300">
          <XCircle size={30} />
        </div>
        <h2 className="mt-6 font-display text-3xl font-semibold">The demo could not finish</h2>
        <p className="mt-3 leading-7 text-slate-400">{error}</p>
        <p className="mt-3 text-sm leading-6 text-slate-500">
          If the backend was restarted, reload this local page to reconnect. No session result is
          claimed when a run does not finish.
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
