import { describe, it, expect } from "vitest";
import { reducer } from "@/hooks/use-toast";

// ToastProps minimal shape required by the reducer
const makeToast = (id: string, open = true) => ({
  id,
  title: `Toast ${id}`,
  open,
  onOpenChange: (_: boolean) => {},
});

const empty = { toasts: [] };

describe("toast reducer — ADD_TOAST", () => {
  it("adds a toast to an empty state", () => {
    const next = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    expect(next.toasts).toHaveLength(1);
    expect(next.toasts[0].id).toBe("1");
  });

  it("respects TOAST_LIMIT=1: adding a second replaces the first", () => {
    const s1 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s2 = reducer(s1, { type: "ADD_TOAST", toast: makeToast("2") });
    expect(s2.toasts).toHaveLength(1);
    expect(s2.toasts[0].id).toBe("2");
  });

  it("newest toast appears first in the array", () => {
    // Starting with 0 toasts, add one — it should be at index 0
    const s = reducer(empty, { type: "ADD_TOAST", toast: makeToast("A") });
    expect(s.toasts[0].id).toBe("A");
  });
});

describe("toast reducer — UPDATE_TOAST", () => {
  it("updates the title of an existing toast", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, {
      type: "UPDATE_TOAST",
      toast: { id: "1", title: "Updated title" },
    });
    expect(s1.toasts[0].title).toBe("Updated title");
  });

  it("does not affect non-matching toasts", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, {
      type: "UPDATE_TOAST",
      toast: { id: "999", title: "Should not appear" },
    });
    expect(s1.toasts[0].title).toBe("Toast 1");
  });
});

describe("toast reducer — DISMISS_TOAST", () => {
  it("sets open=false for the targeted toast id", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "DISMISS_TOAST", toastId: "1" });
    expect(s1.toasts[0].open).toBe(false);
  });

  it("dismisses all toasts when toastId is undefined", () => {
    // TOAST_LIMIT=1 so start with a single toast
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "DISMISS_TOAST" });
    expect(s1.toasts.every((t) => !t.open)).toBe(true);
  });

  it("does not remove toasts — only marks them closed", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "DISMISS_TOAST", toastId: "1" });
    expect(s1.toasts).toHaveLength(1);
  });
});

describe("toast reducer — REMOVE_TOAST", () => {
  it("removes the toast with the given id", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "REMOVE_TOAST", toastId: "1" });
    expect(s1.toasts).toHaveLength(0);
  });

  it("clears all toasts when toastId is undefined", () => {
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "REMOVE_TOAST" });
    expect(s1.toasts).toHaveLength(0);
  });

  it("does not remove non-matching toasts", () => {
    // With TOAST_LIMIT=1 only one toast can exist
    const s0 = reducer(empty, { type: "ADD_TOAST", toast: makeToast("1") });
    const s1 = reducer(s0, { type: "REMOVE_TOAST", toastId: "999" });
    expect(s1.toasts).toHaveLength(1);
  });
});
