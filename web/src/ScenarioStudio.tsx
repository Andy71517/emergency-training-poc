import {
  ArrowLeft,
  Bot,
  CheckCircle2,
  ClipboardCheck,
  FilePenLine,
  LoaderCircle,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import { useState } from "react";

type ScenarioDraftContent = {
  title: string;
  summary: string;
  training_goals: string[];
  environment: string;
  difficulty: string;
  estimated_duration_minutes: number;
  occupants: string[];
  cues: unknown[];
  actions: unknown[];
  transitions: unknown[];
  end_conditions: string[];
  assets: unknown[];
  review_priorities: string[];
  constraints: string[];
  instructor_notes: string;
};

type ScenarioDraft = {
  draft_id: string;
  revision: number;
  status: "suggested" | "instructor_edited" | "approved" | "rejected";
  authority: string;
  original_prompt: string;
  content: ScenarioDraftContent;
  boundary: string;
  rejection_reason?: string | null;
};

type GenerationJob = {
  job_id: string;
  status: string;
  provider: string;
  model_label: string;
  stages: string[];
  note: string;
  draft: ScenarioDraft;
};

type StudioPhase = "request" | "generating" | "review";

const defaultPrompt =
  "Suggest an eight-minute immersive smoke-room scenario with environmental cues, one occupant placeholder, and a leather chair that can later be reviewed for Unreal physics.";

const lines = (values: string[]) => values.join("\n");
const fromLines = (value: string) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

export function ScenarioStudio({ onBack }: { onBack: () => void }) {
  const [phase, setPhase] = useState<StudioPhase>("request");
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [draft, setDraft] = useState<ScenarioDraft | null>(null);
  const [contentText, setContentText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const requestSuggestion = async () => {
    setError("");
    setPhase("generating");
    try {
      const response = await fetch("/api/authoring/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, requested_by: "local-instructor" }),
      });
      if (!response.ok) throw new Error("The mock suggestion could not be created.");
      const nextJob = (await response.json()) as GenerationJob;
      await new Promise((resolve) => window.setTimeout(resolve, 650));
      setJob(nextJob);
      setDraft(nextJob.draft);
      setContentText(JSON.stringify(nextJob.draft.content, null, 2));
      setPhase("review");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Something went wrong.");
      setPhase("request");
    }
  };

  const saveAllChanges = async () => {
    if (!draft) return;
    setBusy(true);
    setError("");
    try {
      const content = JSON.parse(contentText) as ScenarioDraftContent;
      const response = await fetch(`/api/authoring/drafts/${draft.draft_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          expected_revision: draft.revision,
          edited_by: "local-instructor",
          content,
        }),
      });
      if (!response.ok) throw new Error(await responseMessage(response, "Changes could not be saved."));
      const updated = (await response.json()) as ScenarioDraft;
      setDraft(updated);
      setContentText(JSON.stringify(updated.content, null, 2));
    } catch (saveError) {
      setError(
        saveError instanceof SyntaxError
          ? "The full scenario structure contains invalid JSON. Check commas and quotation marks."
          : saveError instanceof Error
            ? saveError.message
            : "Changes could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  };

  const updateSimpleField = <Key extends keyof ScenarioDraftContent>(
    key: Key,
    value: ScenarioDraftContent[Key],
  ) => {
    if (!draft) return;
    const content = { ...draft.content, [key]: value };
    setDraft({ ...draft, content });
    setContentText(JSON.stringify(content, null, 2));
  };

  const decide = async (decision: "approve" | "reject") => {
    if (!draft) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/authoring/drafts/${draft.draft_id}/${decision}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          decision === "approve"
            ? { expected_revision: draft.revision, approved_by: "local-instructor" }
            : {
                expected_revision: draft.revision,
                rejected_by: "local-instructor",
                reason: "Instructor rejected this suggestion for revision or replacement.",
              },
        ),
      });
      if (!response.ok) throw new Error(await responseMessage(response, "Decision could not be saved."));
      setDraft((await response.json()) as ScenarioDraft);
    } catch (decisionError) {
      setError(decisionError instanceof Error ? decisionError.message : "Decision could not be saved.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="studio-shell min-h-screen bg-ink text-slate-100">
      <div className="technical-grid" />
      <div className="ambient ambient-one" />
      <div className="studio-frame relative mx-auto max-w-[1500px] px-5 py-6 sm:px-8 lg:px-10">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div className="flex items-center gap-3">
            <div className="studio-logo"><Sparkles size={21} /></div>
            <div>
              <p className="eyebrow">Funding-proof workflow · local mock</p>
              <h1 className="font-display text-2xl font-semibold">Scenario and Asset Studio</h1>
            </div>
          </div>
          <button className="secondary-button" onClick={onBack} type="button">
            <ArrowLeft size={16} /> Session demo
          </button>
        </header>

        {phase === "request" && (
          <section className="studio-request-grid">
            <div className="panel studio-request-card">
              <span className="section-chip"><Bot size={14} /> Ask for a suggestion</span>
              <h2 className="mt-5 font-display text-3xl font-semibold">Describe the scenario you want to build.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                The mock assistant gives you a starting draft. You can change every field, reject
                the whole suggestion, or approve only the exact revision you reviewed.
              </p>
              <label className="studio-label mt-7" htmlFor="scenario-prompt">Instructor request</label>
              <textarea
                className="studio-input studio-prompt"
                id="scenario-prompt"
                onChange={(event) => setPrompt(event.target.value)}
                value={prompt}
              />
              {error && <p className="studio-error">{error}</p>}
              <button
                className="run-button mt-5 max-w-sm"
                disabled={prompt.trim().length < 10}
                onClick={() => void requestSuggestion()}
                type="button"
              >
                <Sparkles size={18} /> Create mock suggestion
              </button>
            </div>
            <AuthorityCard />
          </section>
        )}

        {phase === "generating" && (
          <section className="panel studio-loading">
            <LoaderCircle className="animate-spin text-azure-300" size={40} />
            <p className="eyebrow text-azure-300">Visible job stages</p>
            <h2 className="font-display text-3xl font-semibold">Preparing a local fixture…</h2>
            <p className="text-sm text-slate-400">No AI model, API, or ARC job is running in this slice.</p>
          </section>
        )}

        {phase === "review" && draft && job && (
          <section className="studio-review-grid">
            <aside className="panel studio-control-column">
              <div className="flex items-center justify-between gap-3">
                <span className="section-chip"><ClipboardCheck size={14} /> Instructor control</span>
                <StatusBadge status={draft.status} />
              </div>
              <h2 className="mt-5 font-display text-2xl font-semibold">Review the suggestion</h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Revision {draft.revision}. Saving changes creates a new revision and removes any
                earlier approval.
              </p>

              <div className="studio-job-card mt-5">
                <p className="eyebrow text-azure-300">Mock job trail</p>
                {job.stages.map((stage) => (
                  <div className="studio-job-stage" key={stage}>
                    <CheckCircle2 size={15} /> {friendlyStage(stage)}
                  </div>
                ))}
                <p className="mt-3 text-xs leading-5 text-slate-500">{job.note}</p>
              </div>

              <div className="mt-5 grid gap-2">
                <button className="studio-save-button" disabled={busy} onClick={() => void saveAllChanges()} type="button">
                  <FilePenLine size={17} /> Save all instructor changes
                </button>
                <button className="studio-approve-button" disabled={busy} onClick={() => void decide("approve")} type="button">
                  <CheckCircle2 size={17} /> Approve this exact revision
                </button>
                <button className="studio-reject-button" disabled={busy} onClick={() => void decide("reject")} type="button">
                  <XCircle size={17} /> Reject suggestion
                </button>
              </div>
              {error && <p className="studio-error">{error}</p>}
              <p className="mt-5 text-xs leading-5 text-slate-500">{draft.boundary}</p>
            </aside>

            <div className="panel studio-editor">
              <div className="studio-editor-heading">
                <div>
                  <p className="eyebrow text-amber-300">Everything below belongs to the instructor</p>
                  <h2 className="mt-2 font-display text-2xl font-semibold">Scenario draft</h2>
                </div>
                <span className="authority-pill"><ShieldCheck size={14} /> AI suggests · instructor decides</span>
              </div>

              <div className="studio-fields">
                <TextField label="Scenario title" value={draft.content.title} onChange={(value) => updateSimpleField("title", value)} />
                <TextField label="Difficulty framing" value={draft.content.difficulty} onChange={(value) => updateSimpleField("difficulty", value)} />
                <TextAreaField label="Scenario summary" value={draft.content.summary} onChange={(value) => updateSimpleField("summary", value)} />
                <TextAreaField label="Room and environment" value={draft.content.environment} onChange={(value) => updateSimpleField("environment", value)} />
                <TextAreaField label="Training goals · one per line" value={lines(draft.content.training_goals)} onChange={(value) => updateSimpleField("training_goals", fromLines(value))} />
                <TextAreaField label="End conditions · one per line" value={lines(draft.content.end_conditions)} onChange={(value) => updateSimpleField("end_conditions", fromLines(value))} />
                <TextAreaField label="Review priorities · one per line" value={lines(draft.content.review_priorities)} onChange={(value) => updateSimpleField("review_priorities", fromLines(value))} />
                <TextAreaField label="Instructor notes" value={draft.content.instructor_notes} onChange={(value) => updateSimpleField("instructor_notes", value)} />
              </div>

              <details className="studio-advanced mt-5">
                <summary>Full scenario structure · advanced control</summary>
                <p>
                  This contains every field, including cues, actions, state transitions, assets,
                  occupants, constraints, and duration. Technical instructors or developers can
                  replace any part of the suggestion before saving.
                </p>
                <textarea
                  aria-label="Full scenario structure"
                  className="studio-json"
                  onChange={(event) => setContentText(event.target.value)}
                  spellCheck={false}
                  value={contentText}
                />
              </details>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function AuthorityCard() {
  return (
    <aside className="panel authority-card">
      <div className="instructor-mark"><ShieldCheck size={21} /></div>
      <p className="eyebrow mt-5 text-amber-300">Authority boundary</p>
      <h2 className="mt-2 font-display text-2xl font-semibold">The instructor stays in charge.</h2>
      <ul className="mt-5 grid gap-4 text-sm leading-6 text-slate-300">
        <li><CheckCircle2 size={17} /> Edit every scenario field</li>
        <li><CheckCircle2 size={17} /> Add or remove cues, actions, assets, and conditions</li>
        <li><CheckCircle2 size={17} /> Reject the entire AI suggestion</li>
        <li><CheckCircle2 size={17} /> Approve only the revision they actually reviewed</li>
      </ul>
      <p className="mt-6 text-xs leading-5 text-slate-500">
        Approval means “accepted for the next POC stage.” It does not mean clinically validated,
        operationally authoritative, or ready for real responder training.
      </p>
    </aside>
  );
}

function TextField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="studio-field">
      <span>{label}</span>
      <input className="studio-input" onChange={(event) => onChange(event.target.value)} value={value} />
    </label>
  );
}

function TextAreaField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="studio-field studio-field-wide">
      <span>{label}</span>
      <textarea className="studio-input" onChange={(event) => onChange(event.target.value)} value={value} />
    </label>
  );
}

function StatusBadge({ status }: { status: ScenarioDraft["status"] }) {
  return <span className={`studio-status studio-status-${status}`}>{status.replaceAll("_", " ")}</span>;
}

const friendlyStage = (stage: string) =>
  stage.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase());

async function responseMessage(response: Response, fallback: string) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}
