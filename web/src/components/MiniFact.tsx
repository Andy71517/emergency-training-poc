export function MiniFact({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="mini-fact">
      <span className="text-azure-300">{icon}</span>
      <span><span className="block text-xs text-slate-500">{label}</span><span className="mt-0.5 block text-sm font-medium">{value}</span></span>
    </div>
  );
}
