import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export type RunErrorKind = "invalid_output" | "api_error" | "unknown";

export interface RunErrorInfo {
  kind: RunErrorKind;
  /** Mensaje legible para mostrar al usuario. */
  message: string;
  /** Texto crudo del error (para tooltip / depuración). */
  detail: string;
}

/**
 * Traduce el mensaje de error crudo guardado en los runs (str(exc) de Python)
 * a algo legible, sin necesidad de reejecutar el pipeline.
 *
 * - invalid_output: la API respondió pero el modelo no devolvió JSON válido
 *   (json.JSONDecodeError, schema inválido). Ej: "Expecting ',' delimiter: ...".
 * - api_error: fallo real de la API (cuota, rate limit, timeout, 5xx).
 */
export function describeRunError(raw: string | null | undefined): RunErrorInfo {
  const detail = (raw ?? "").trim();
  const text = detail.toLowerCase();

  const invalidOutput =
    /expecting .*delimiter|expecting value|unterminated string|extra data|no json found|respuesta vac[ií]a|missing required keys|missing keys|invalid \\escape|char \d+/.test(
      text,
    );
  if (invalidOutput) {
    return {
      kind: "invalid_output",
      message: "El modelo no devolvió una respuesta JSON válida tras varios reintentos.",
      detail,
    };
  }

  const apiError =
    /429|quota|rate.?limit|resource.?exhausted|timeout|timed out|deadline|503|502|500|connection|unavailable|permission|api key|unauthenticated|503/.test(
      text,
    );
  if (apiError) {
    return {
      kind: "api_error",
      message: "Error de la API del modelo (cuota, límite de uso o conexión) tras varios reintentos.",
      detail,
    };
  }

  return {
    kind: "unknown",
    message: detail || "Error desconocido en la query.",
    detail,
  };
}
