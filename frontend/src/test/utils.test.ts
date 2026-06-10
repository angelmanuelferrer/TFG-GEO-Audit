import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

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
