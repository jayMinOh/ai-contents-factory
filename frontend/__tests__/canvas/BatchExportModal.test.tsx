/**
 * BatchExportModal Component Tests
 * TAG-EX-003: Batch Export with ZIP Download
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import BatchExportModal from "@/components/canvas/BatchExportModal";
import type { PlatformExportPreset, ImageExportOptions } from "@/types/canvas";

describe("BatchExportModal", () => {
  const mockOnClose = vi.fn();
  const mockOnExport = vi.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onExport: mockOnExport,
    canvasWidth: 1080,
    canvasHeight: 1080,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockOnExport.mockResolvedValue(undefined);
  });

  it("should not render when isOpen is false", () => {
    render(<BatchExportModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText("일괄 내보내기")).not.toBeInTheDocument();
  });

  it("should render modal when isOpen is true", () => {
    render(<BatchExportModal {...defaultProps} />);

    expect(screen.getByText("일괄 내보내기")).toBeInTheDocument();
    expect(
      screen.getByText("여러 플랫폼에 맞는 크기로 한번에 내보내기")
    ).toBeInTheDocument();
  });

  it("should display export options toggle button", () => {
    render(<BatchExportModal {...defaultProps} />);

    expect(screen.getByText("내보내기 옵션")).toBeInTheDocument();
  });

  it("should toggle export options visibility", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Initially options are hidden
    expect(screen.queryByText("포맷")).not.toBeInTheDocument();

    // Click to show options
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // Options should now be visible
    expect(screen.getByText("포맷")).toBeInTheDocument();
    expect(screen.getByText("해상도 배율")).toBeInTheDocument();
  });

  it("should show format selection buttons when options are expanded", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // Check format buttons
    expect(screen.getByRole("button", { name: /PNG/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /JPEG/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /WEBP/i })).toBeInTheDocument();
  });

  it("should show quality slider for JPEG format", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // Select JPEG format
    fireEvent.click(screen.getByRole("button", { name: /JPEG/i }));

    // Quality slider should be visible
    expect(screen.getByText("품질")).toBeInTheDocument();
    expect(screen.getByRole("slider")).toBeInTheDocument();
  });

  it("should show transparent background option for PNG format", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // PNG is default, so transparent option should be visible
    expect(screen.getByText("투명 배경")).toBeInTheDocument();
    expect(screen.getByText("PNG는 투명 배경을 지원합니다")).toBeInTheDocument();
  });

  it("should show resolution multiplier options", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // Check multiplier buttons
    expect(screen.getByRole("button", { name: /1x.*표준/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /2x.*레티나/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /3x.*초고해상도/i })).toBeInTheDocument();
  });

  it("should render platform presets selector", () => {
    render(<BatchExportModal {...defaultProps} />);

    expect(screen.getByText("플랫폼 선택")).toBeInTheDocument();
    expect(screen.getByText("Instagram")).toBeInTheDocument();
    expect(screen.getByText("Facebook")).toBeInTheDocument();
  });

  it("should display selection count in footer", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Footer has the selection count with font-medium class
    const footerSelectionCount = screen.getByText("0", {
      selector: ".font-medium",
    });
    expect(footerSelectionCount).toBeInTheDocument();
    expect(footerSelectionCount.parentElement).toHaveTextContent("0개 선택됨");
  });

  it("should disable download button when no presets selected", () => {
    render(<BatchExportModal {...defaultProps} />);

    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    expect(downloadButton).toBeDisabled();
  });

  it("should enable download button when presets are selected", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand Instagram and select Feed preset
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Download button should be enabled
    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    expect(downloadButton).not.toBeDisabled();
  });

  it("should call onClose when close button is clicked", () => {
    render(<BatchExportModal {...defaultProps} />);

    const closeButton = screen.getByRole("button", { name: "" });
    // Find the X button in header
    const closeButtons = screen.getAllByRole("button");
    const closeBtn = closeButtons.find(
      (btn) => btn.querySelector("svg.lucide-x") !== null
    );
    if (closeBtn) {
      fireEvent.click(closeBtn);
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    }
  });

  it("should call onClose when cancel button is clicked", () => {
    render(<BatchExportModal {...defaultProps} />);

    const cancelButton = screen.getByRole("button", { name: /취소/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should call onExport with selected presets when download is clicked", async () => {
    render(<BatchExportModal {...defaultProps} />);

    // Select a preset
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Click download
    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(mockOnExport).toHaveBeenCalledTimes(1);
    });

    // Check that it was called with the selected preset
    expect(mockOnExport).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          id: "ig-feed",
          platform: "instagram",
          name: "Feed",
        }),
      ]),
      expect.objectContaining({
        format: "png",
        quality: expect.any(Number),
        multiplier: expect.any(Number),
      })
    );
  });

  it("should show progress indicator during export", async () => {
    // Make export take some time
    mockOnExport.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<BatchExportModal {...defaultProps} />);

    // Select a preset
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Click download
    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    fireEvent.click(downloadButton);

    // Progress indicator should appear
    await waitFor(() => {
      expect(screen.getByText("처리 중...")).toBeInTheDocument();
    });
  });

  it("should show success message after export completes", async () => {
    render(<BatchExportModal {...defaultProps} />);

    // Select a preset
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Click download
    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText("내보내기 완료")).toBeInTheDocument();
    });
  });

  it("should show error message when export fails", async () => {
    mockOnExport.mockRejectedValue(new Error("Export failed"));

    render(<BatchExportModal {...defaultProps} />);

    // Select a preset
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Click download
    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    fireEvent.click(downloadButton);

    await waitFor(() => {
      expect(screen.getByText("내보내기 실패")).toBeInTheDocument();
    });
  });

  it("should display estimated file size", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Select multiple presets
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    const storyButton = screen.getByRole("button", { name: /Story.*9:16/i });
    fireEvent.click(storyButton);

    // Should show estimated size
    expect(screen.getByText(/예상 크기:/)).toBeInTheDocument();
  });

  it("should update quality when slider is moved", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options and select JPEG
    fireEvent.click(screen.getByText("내보내기 옵션"));
    fireEvent.click(screen.getByRole("button", { name: /JPEG/i }));

    // Find and change slider
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "50" } });

    // Quality should be updated
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("should toggle transparent background option", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Expand options (PNG is default)
    fireEvent.click(screen.getByText("내보내기 옵션"));

    // Find transparent background toggle
    const toggleContainer = screen.getByText("투명 배경").parentElement;
    const toggle = toggleContainer?.querySelector("button");

    if (toggle) {
      // Initially off (not translated)
      expect(toggle).toHaveClass("bg-muted");

      // Click to enable
      fireEvent.click(toggle);

      // Should now be enabled
      expect(toggle).toHaveClass("bg-accent-500");
    }
  });

  it("should prevent closing during export", async () => {
    mockOnExport.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 200))
    );

    render(<BatchExportModal {...defaultProps} />);

    // Select a preset and start export
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    const downloadButton = screen.getByRole("button", { name: /ZIP으로 다운로드/i });
    fireEvent.click(downloadButton);

    // Wait for export to start
    await waitFor(() => {
      expect(screen.getByText("처리 중...")).toBeInTheDocument();
    });

    // Cancel button should be disabled
    const cancelButton = screen.getByRole("button", { name: /취소/i });
    expect(cancelButton).toBeDisabled();
  });

  it("should select multiple presets from different platforms", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Select Instagram Feed
    const feedButton = screen.getByRole("button", { name: /Feed.*1:1/i });
    fireEvent.click(feedButton);

    // Expand Facebook and select Link
    const facebookButton = screen.getByRole("button", { name: /Facebook/i });
    fireEvent.click(facebookButton);

    const linkButton = screen.getByRole("button", { name: /Link.*1.91:1/i });
    fireEvent.click(linkButton);

    // Should show 2 selected
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("should select all presets for a platform", () => {
    render(<BatchExportModal {...defaultProps} />);

    // Instagram is expanded by default
    const selectAllButton = screen.getByRole("button", { name: /전체 선택/i });
    fireEvent.click(selectAllButton);

    // All 4 Instagram presets should be selected
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("should deselect all presets for a platform", () => {
    render(<BatchExportModal {...defaultProps} />);

    // First select all
    const selectAllButton = screen.getByRole("button", { name: /전체 선택/i });
    fireEvent.click(selectAllButton);

    // Then deselect all
    const deselectAllButton = screen.getByRole("button", { name: /전체 해제/i });
    fireEvent.click(deselectAllButton);

    // Should show 0 selected
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
