export type DemoPath = {
  demo_id: string;
  label: string;
  short_label: string;
  scenario_id: string;
  tone: "expected" | "review" | "explore" | "interactive";
  description: string;
  actions: string[];
  mode?: "scripted" | "seeded_exploration" | "user_controlled";
  seed?: number | null;
  available_actions?: string[];
};

export type Finding = {
  code?: string;
  message?: string;
  instructor_note?: string;
};

export type TimelineItem = {
  sequence_number: number;
  action_type: string;
  action_description?: string;
  result_summary?: string;
  validation_status: "ok" | "warning" | "error" | string;
  phase_before?: string | null;
  phase_after?: string | null;
  state_changes?: string[];
  finding_messages?: string[];
};

export type Review = {
  review_headline: string;
  scenario_id: string;
  scenario_outcome: string | null;
  end_condition_reached: boolean;
  total_actions: number;
  action_timeline: TimelineItem[];
  progress_stories: string[];
  instructor_review: {
    title: string;
    summary: string;
    evidence: string[];
    discussion_prompt: string;
    boundary: string;
  };
  warnings: Finding[];
  errors: Finding[];
  environment_review: {
    room_cues?: Record<string, unknown>;
  };
};

export type UpdateMessage = {
  message_type: string;
  validation_result?: {
    status: string;
    warnings?: Finding[];
    errors?: Finding[];
  };
  scenario_state?: {
    is_terminal: boolean;
    state?: {
      phase?: string;
    };
  };
  message?: string;
};

export type RunStage = "idle" | "pacing" | "running" | "interactive" | "review" | "error";

export type LiveEvent = {
  action: string;
  status: string;
  phase: string;
  message?: string;
};
