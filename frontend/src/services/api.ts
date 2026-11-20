import type {
  AdaptResponse,
  AnswerSubmission,
  CheckInResponse,
  Goal,
  QuestionSetResponse,
  Roadmap,
  Task,
  TaskStatus,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });
  } catch {
    throw new ApiError("Could not reach the server. Check your connection and try again.", 0);
  }

  if (!response.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // response had no JSON body; keep the generic message
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export const api = {
  createGoal: (payload: { title: string; description?: string; category?: string; target_date?: string }) =>
    request<Goal>("/api/goals", { method: "POST", body: JSON.stringify(payload) }),

  getGoal: (goalId: number) => request<Goal>(`/api/goals/${goalId}`),

  getNextQuestions: (goalId: number) =>
    request<QuestionSetResponse>(`/api/goals/${goalId}/questions`, { method: "POST" }),

  submitAnswers: (goalId: number, answers: AnswerSubmission[]) =>
    request<Goal>(`/api/goals/${goalId}/answers`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  finalizeProfile: (goalId: number) => request<Goal>(`/api/goals/${goalId}/profile`, { method: "POST" }),

  generateRoadmap: (goalId: number) => request<Roadmap>(`/api/goals/${goalId}/roadmap`, { method: "POST" }),

  getRoadmap: (goalId: number) => request<Roadmap>(`/api/goals/${goalId}/roadmap`),

  updateTaskStatus: (taskId: number, status: TaskStatus) =>
    request<Task>(`/api/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify({ status }) }),

  submitCheckin: (goalId: number, message: string) =>
    request<CheckInResponse>(`/api/goals/${goalId}/checkins`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  adaptRoadmap: (goalId: number) => request<AdaptResponse>(`/api/goals/${goalId}/adapt`, { method: "POST" }),
};
