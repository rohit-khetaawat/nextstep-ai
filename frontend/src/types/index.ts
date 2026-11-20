export type TaskStatus = "NOT_STARTED" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED";

export interface Goal {
  id: number;
  title: string;
  description: string;
  category: string;
  target_date: string;
  status: string;
  profile: Record<string, unknown>;
}

export type QuestionType =
  | "single_choice"
  | "multi_choice"
  | "numeric"
  | "date"
  | "short_text"
  | "long_text";

export interface Question {
  id: string;
  text: string;
  type: QuestionType;
  options: string[];
  required: boolean;
  reason: string;
}

export interface QuestionSetResponse {
  questions: Question[];
  is_complete: boolean;
  inferred_category: string;
}

export interface AnswerSubmission {
  question_id: string;
  question_text: string;
  answer: string | string[];
}

export interface Task {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: number;
  estimated_effort: string;
  order_index: number;
  depends_on: number[];
}

export interface Milestone {
  id: number;
  title: string;
  description: string;
  status: TaskStatus;
  target_date: string;
  order_index: number;
  tasks: Task[];
}

export interface Phase {
  id: number;
  title: string;
  objective: string;
  order_index: number;
  milestones: Milestone[];
}

export interface Roadmap {
  id: number;
  version: number;
  summary: string;
  active: boolean;
  phases: Phase[];
  overall_progress: number;
  current_phase: string | null;
  current_milestone: string | null;
  next_action: string | null;
  started_at?: string | null;
}

export interface CheckInResponse {
  id: number;
  message: string;
  classification: {
    category: string;
    summary: string;
    completed_task_titles: string[];
    blocked_task_titles: string[];
    blocker_description: string;
    should_adapt_roadmap: boolean;
  };
  created_at: string;
}

export interface AdaptResponse {
  adapted: boolean;
  new_roadmap_version: number | null;
  explanation: string;
}

export interface ApiErrorBody {
  detail: string;
}

export interface UserAccount {
  id: number;
  username: string;
}

export interface HistoryGoal {
  id: number;
  title: string;
  status: string;
  has_roadmap: boolean;
  created_at: string;
  answers: { question: string; answer: string; created_at: string }[];
  checkins: { message: string; summary: string; created_at: string }[];
}

export interface HistoryResponse {
  user: UserAccount;
  goals: HistoryGoal[];
}
