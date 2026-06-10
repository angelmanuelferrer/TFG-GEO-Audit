import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  DeltaIndicator,
  MetricBadge,
  EngineTag,
  CategoryBadge,
  SemaphoreIndicator,
  OriginalStar,
} from "@/components/shared";

// ── DeltaIndicator ────────────────────────────────────────────────────────────

describe("DeltaIndicator", () => {
  it("renders em dash when value is null", () => {
    const { container } = render(<DeltaIndicator value={null} />);
    expect(container.textContent).toContain("—");
  });

  it("renders em dash when value is undefined", () => {
    const { container } = render(<DeltaIndicator value={undefined} />);
    expect(container.textContent).toContain("—");
  });

  it("renders positive value with + prefix", () => {
    const { container } = render(<DeltaIndicator value={1.5} />);
    expect(container.textContent).toContain("+1.50");
  });

  it("renders negative value without + prefix", () => {
    const { container } = render(<DeltaIndicator value={-0.5} />);
    expect(container.textContent).toContain("-0.50");
  });

  it("renders zero with + prefix", () => {
    const { container } = render(<DeltaIndicator value={0} />);
    expect(container.textContent).toContain("+0.00");
  });

  it("appends suffix when provided", () => {
    const { container } = render(<DeltaIndicator value={2.5} suffix="%" />);
    expect(container.textContent).toContain("+2.50%");
  });

  it("applies success color class for positive values", () => {
    const { container } = render(<DeltaIndicator value={1} />);
    expect(container.querySelector("span")?.className).toContain("text-success");
  });

  it("applies destructive color class for negative values", () => {
    const { container } = render(<DeltaIndicator value={-1} />);
    expect(container.querySelector("span")?.className).toContain("text-destructive");
  });
});

// ── MetricBadge ───────────────────────────────────────────────────────────────

describe("MetricBadge", () => {
  it("renders 'Visible' when visible=true", () => {
    render(<MetricBadge visible={true} />);
    expect(screen.getByText("Visible")).toBeTruthy();
  });

  it("renders 'No visible' when visible=false", () => {
    render(<MetricBadge visible={false} />);
    expect(screen.getByText("No visible")).toBeTruthy();
  });
});

// ── EngineTag ─────────────────────────────────────────────────────────────────

describe("EngineTag", () => {
  it("renders the engine name as text", () => {
    render(<EngineTag engine="gemini" />);
    expect(screen.getByText("gemini")).toBeTruthy();
  });

  it("renders 'claude' correctly", () => {
    render(<EngineTag engine="claude" />);
    expect(screen.getByText("claude")).toBeTruthy();
  });

  it("renders 'openai' correctly", () => {
    render(<EngineTag engine="openai" />);
    expect(screen.getByText("openai")).toBeTruthy();
  });

  it("renders unknown engine names using fallback styles", () => {
    render(<EngineTag engine="mistral" />);
    expect(screen.getByText("mistral")).toBeTruthy();
  });
});

// ── CategoryBadge ─────────────────────────────────────────────────────────────

describe("CategoryBadge", () => {
  it("renders 'informacional'", () => {
    render(<CategoryBadge category="informacional" />);
    expect(screen.getByText("informacional")).toBeTruthy();
  });

  it("renders 'comparativa'", () => {
    render(<CategoryBadge category="comparativa" />);
    expect(screen.getByText("comparativa")).toBeTruthy();
  });

  it("renders 'navegacional'", () => {
    render(<CategoryBadge category="navegacional" />);
    expect(screen.getByText("navegacional")).toBeTruthy();
  });

  it("renders unknown category with fallback styles", () => {
    render(<CategoryBadge category="transaccional" />);
    expect(screen.getByText("transaccional")).toBeTruthy();
  });
});

// ── SemaphoreIndicator ────────────────────────────────────────────────────────

describe("SemaphoreIndicator", () => {
  it("renders value with unit", () => {
    const { container } = render(
      <SemaphoreIndicator value={5} thresholds={[10, 20]} unit="s" />
    );
    expect(container.textContent).toBe("5s");
  });

  it("applies success class when value <= first threshold", () => {
    const { container } = render(
      <SemaphoreIndicator value={5} thresholds={[10, 20]} unit="s" />
    );
    expect(container.querySelector("span")?.className).toContain("text-success");
  });

  it("applies warning class when value between thresholds", () => {
    const { container } = render(
      <SemaphoreIndicator value={15} thresholds={[10, 20]} unit="s" />
    );
    expect(container.querySelector("span")?.className).toContain("text-warning");
  });

  it("applies destructive class when value > second threshold", () => {
    const { container } = render(
      <SemaphoreIndicator value={25} thresholds={[10, 20]} unit="s" />
    );
    expect(container.querySelector("span")?.className).toContain("text-destructive");
  });

  it("applies success class exactly at first threshold (boundary)", () => {
    const { container } = render(
      <SemaphoreIndicator value={10} thresholds={[10, 20]} unit="ms" />
    );
    expect(container.querySelector("span")?.className).toContain("text-success");
  });

  it("applies warning class exactly at second threshold (boundary)", () => {
    const { container } = render(
      <SemaphoreIndicator value={20} thresholds={[10, 20]} unit="ms" />
    );
    expect(container.querySelector("span")?.className).toContain("text-warning");
  });
});

// ── OriginalStar ──────────────────────────────────────────────────────────────

describe("OriginalStar", () => {
  it("renders nothing when is=false", () => {
    const { container } = render(<OriginalStar is={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders an SVG icon when is=true", () => {
    const { container } = render(<OriginalStar is={true} />);
    expect(container.querySelector("svg")).toBeTruthy();
  });
});
