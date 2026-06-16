import { describe, it, expect } from "vitest";
import { cn, describeRunError } from "@/lib/utils";

describe("cn", () => {
  it("returns a single class unchanged", () => {
    expect(cn("foo")).toBe("foo");
  });

  it("merges multiple classes separated by spaces", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("deduplicates conflicting Tailwind classes (last wins)", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("ignores falsy values (false, undefined, null)", () => {
    expect(cn("foo", false, undefined, null, "bar")).toBe("foo bar");
  });

  it("handles conditional objects — true entries included, false excluded", () => {
    expect(cn({ "text-red-500": true, "text-blue-500": false })).toBe("text-red-500");
  });

  it("handles array of classes", () => {
    expect(cn(["foo", "bar"])).toBe("foo bar");
  });

  it("returns empty string when called with no arguments", () => {
    expect(cn()).toBe("");
  });

  it("returns empty string for only falsy inputs", () => {
    expect(cn(false, undefined, null)).toBe("");
  });

  it("merges with conditional and static classes together", () => {
    const active = true;
    expect(cn("base", active && "active")).toBe("base active");
    expect(cn("base", !active && "active")).toBe("base");
  });
});

describe("describeRunError", () => {
  it("classifies a json.JSONDecodeError as invalid_output", () => {
    const info = describeRunError("Expecting ',' delimiter: line 28 column 6 (char 7305)");
    expect(info.kind).toBe("invalid_output");
    expect(info.message).toMatch(/JSON v[aá]lida/i);
  });

  it("preserves the raw message in detail (trimmed)", () => {
    const raw = "  Expecting value: line 1 column 1 (char 0)  ";
    const info = describeRunError(raw);
    expect(info.kind).toBe("invalid_output");
    expect(info.detail).toBe(raw.trim());
  });

  it.each([
    "No JSON found in agent output",
    "Missing required keys: ['answer']",
    "El modelo devolvió una respuesta vacía",
    "Unterminated string starting at: line 5 column 2 (char 120)",
  ])("classifies %s as invalid_output", (raw) => {
    expect(describeRunError(raw).kind).toBe("invalid_output");
  });

  it.each([
    "429 Resource has been exhausted (e.g. check quota).",
    "ResourceExhausted: rate limit exceeded",
    "Deadline Exceeded: request timed out",
    "503 Service Unavailable",
    "Connection aborted",
  ])("classifies %s as api_error", (raw) => {
    expect(describeRunError(raw).kind).toBe("api_error");
  });

  it("falls back to unknown and echoes the raw text", () => {
    const info = describeRunError("algo raro pasó aquí");
    expect(info.kind).toBe("unknown");
    expect(info.message).toBe("algo raro pasó aquí");
  });

  it("handles null / undefined / empty input gracefully", () => {
    expect(describeRunError(null).kind).toBe("unknown");
    expect(describeRunError(undefined).kind).toBe("unknown");
    expect(describeRunError("").message).toBe("Error desconocido en la query.");
  });
});
