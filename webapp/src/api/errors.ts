import { toast } from "sonner";
import { ZodError } from "zod";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public endpoint: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class ValidationError extends Error {
  constructor(
    message: string,
    public zodError: ZodError,
    public endpoint: string,
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

export function handleError(error: unknown): void {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      window.location.href = `${import.meta.env.VITE_API_URL}/auth/login?redirect=${import.meta.env.VITE_BASE_URL}/home?auth=true`;
      return;
    }
    toast.error(error.message);
  } else if (error instanceof ValidationError) {
    console.error(`[ValidationError] ${error.endpoint}:`, error.zodError.issues);
    toast.error("Received unexpected data from the server");
  } else if (error instanceof Error) {
    toast.error(error.message);
  } else {
    toast.error("An unexpected error occurred");
  }
}
