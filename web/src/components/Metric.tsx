export function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`metric metric-${tone}`}>
      <span className="font-mono text-3xl font-semibold">{String(value).padStart(2, "0")}</span>
      <span className="text-xs text-slate-400">{label}</span>
    </div>
  );
}
