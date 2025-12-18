/**
 * PlatformPresets Component Tests
 * TAG-EX-001: Platform-Specific Dimension Presets
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PlatformPresets, { PlatformPresetsCompact } from "@/components/canvas/PlatformPresets";
import type { BatchExportItem, PlatformExportPreset } from "@/types/canvas";
import { PLATFORM_EXPORT_PRESETS } from "@/types/canvas";

// Create mock batch export items
const createMockBatchItems = (selectedIds: string[] = []): BatchExportItem[] => {
  return PLATFORM_EXPORT_PRESETS.flatMap((platform) =>
    platform.presets.map((preset) => ({
      preset,
      selected: selectedIds.includes(preset.id),
    }))
  );
};

describe("PlatformPresets", () => {
  const mockOnPresetToggle = vi.fn();
  const mockOnSelectAll = vi.fn();
  const mockOnDeselectAll = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render platform list header with selection count", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    expect(screen.getByText("플랫폼 선택")).toBeInTheDocument();
    expect(screen.getByText("0개 선택됨")).toBeInTheDocument();
  });

  it("should display correct selection count", () => {
    const items = createMockBatchItems(["ig-feed", "ig-story", "fb-link"]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    expect(screen.getByText("3개 선택됨")).toBeInTheDocument();
  });

  it("should render all platform names", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("Facebook")).toBeInTheDocument();
    expect(screen.getByText("Pinterest")).toBeInTheDocument();
    expect(screen.getByText("Twitter/X")).toBeInTheDocument();
    expect(screen.getByText("YouTube")).toBeInTheDocument();
    expect(screen.getByText("LinkedIn")).toBeInTheDocument();
  });

  it("should expand platform on click to show presets", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Instagram should be expanded by default
    expect(screen.getByText("Feed")).toBeInTheDocument();
    expect(screen.getByText("Portrait")).toBeInTheDocument();
    expect(screen.getByText("Story/Reels")).toBeInTheDocument();
  });

  it("should toggle platform expansion", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Click Facebook to expand
    const facebookButton = screen.getByRole("button", { name: /Facebook/i });
    fireEvent.click(facebookButton);

    // Facebook presets should now be visible
    expect(screen.getByText("Link")).toBeInTheDocument();
    expect(screen.getByText("Share")).toBeInTheDocument();
    expect(screen.getByText("Post")).toBeInTheDocument();
  });

  it("should call onPresetToggle when preset is clicked", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Find and click the Feed preset button
    const feedPresetButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedPresetButton);

    expect(mockOnPresetToggle).toHaveBeenCalledTimes(1);
    expect(mockOnPresetToggle).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "ig-feed",
        platform: "instagram",
        name: "Feed",
      })
    );
  });

  it("should call onSelectAll when select all button is clicked", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Instagram is expanded by default, find select all button
    const selectAllButton = screen.getByRole("button", { name: /전체 선택/i });
    fireEvent.click(selectAllButton);

    expect(mockOnSelectAll).toHaveBeenCalledTimes(1);
    expect(mockOnSelectAll).toHaveBeenCalledWith("instagram");
  });

  it("should call onDeselectAll when deselect all button is clicked", () => {
    const items = createMockBatchItems(["ig-feed", "ig-story"]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    const deselectAllButton = screen.getByRole("button", { name: /전체 해제/i });
    fireEvent.click(deselectAllButton);

    expect(mockOnDeselectAll).toHaveBeenCalledTimes(1);
    expect(mockOnDeselectAll).toHaveBeenCalledWith("instagram");
  });

  it("should display preset dimensions", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Check for Instagram Feed dimensions
    expect(screen.getByText("1080 x 1080")).toBeInTheDocument();
    expect(screen.getByText("1080 x 1920")).toBeInTheDocument();
  });

  it("should show selection count per platform", () => {
    const items = createMockBatchItems(["ig-feed", "ig-story"]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Should show 2/4 for Instagram (2 selected out of 4)
    expect(screen.getByText("2/4")).toBeInTheDocument();
  });

  it("should apply correct styling to selected presets", () => {
    const items = createMockBatchItems(["ig-feed"]);
    render(
      <PlatformPresets
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
        onSelectAll={mockOnSelectAll}
        onDeselectAll={mockOnDeselectAll}
      />
    );

    // Find the Feed preset button and check it has the selected styling
    const feedPresetButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    expect(feedPresetButton).toHaveClass("bg-accent-500/10");
    expect(feedPresetButton).toHaveClass("border-accent-500");
  });
});

describe("PlatformPresetsCompact", () => {
  const mockOnPresetToggle = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render compact header with selection count", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresetsCompact
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
      />
    );

    expect(screen.getByText("내보내기 크기")).toBeInTheDocument();
    expect(screen.getByText("0개 선택")).toBeInTheDocument();
  });

  it("should display first two presets per platform", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresetsCompact
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
      />
    );

    // Should show first 2 presets from each platform
    // Instagram: Feed, Portrait (first 2)
    expect(screen.getByText("Feed")).toBeInTheDocument();
    expect(screen.getByText("Portrait")).toBeInTheDocument();
  });

  it("should call onPresetToggle when preset is clicked", () => {
    const items = createMockBatchItems([]);
    render(
      <PlatformPresetsCompact
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
      />
    );

    const feedButton = screen.getByRole("button", { name: /Feed/i });
    fireEvent.click(feedButton);

    expect(mockOnPresetToggle).toHaveBeenCalled();
  });

  it("should update selection count when presets are selected", () => {
    const items = createMockBatchItems(["ig-feed", "fb-link"]);
    render(
      <PlatformPresetsCompact
        selectedPresets={items}
        onPresetToggle={mockOnPresetToggle}
      />
    );

    expect(screen.getByText("2개 선택")).toBeInTheDocument();
  });
});
