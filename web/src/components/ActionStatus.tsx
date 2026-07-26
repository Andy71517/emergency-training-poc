import { Check, AlertTriangle, XCircle } from "lucide-react";

export function ActionStatus({ status }: { status: string }) {
  if (status === "ok") return <span className="action-status status-ok"><Check size={13} /> Accepted</span>;
  if (status === "warning") return <span className="action-status status-warn"><AlertTriangle size={13} /> Review</span>;
  return <span className="action-status status-block"><XCircle size={13} /> Blocked</span>;
}
