import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import LayerPanel from "@/components/canvas/LayerPanel";
import type { TextLayer } from "@/types/canvas";

const createMockLayer = (id: string, name: string, text: string = "Sample text"): TextLayer => ({
  id,
  name,
  text,
  fontFamily: "Arial",
  fontSize: 32,
  fontWeight: "normal",
  fontStyle: "normal",
  textAlign: "center",
  fill: "#ffffff",
  backgroundColor: "transparent",
  shadow: null,
  position: { x: 100, y: 100 },
  rotation: 0,
  scaleX: 1,
  scaleY: 1,
  visible: true,
  locked: false,
  opacity: 1,
  underline: false,
  linethrough: false,
  charSpacing: 0,
  lineHeight: 1.2,
});

describe("LayerPanel", () => {
  const defaultProps = {
    layers: [] as TextLayer[],
    selectedLayerId: null,
    onSelectLayer: vi.fn(),
    onAddLayer: vi.fn(),
    onRemoveLayer: vi.fn(),
    onDuplicateLayer: vi.fn(),
    onMoveLayerUp: vi.fn(),
    onMoveLayerDown: vi.fn(),
    onBringToFront: vi.fn(),
    onSendToBack: vi.fn(),
    onToggleVisibility: vi.fn(),
    onToggleLock: vi.fn(),
    onUpdateLayerName: vi.fn(),
  };

  describe("empty state", () => {
    it("should display empty state message when no layers", () => {
      render(<LayerPanel {...defaultProps} />);

      expect(screen.getByText("레이어가 없습니다")).toBeInTheDocument();
      expect(screen.getByText("+ 텍스트 추가")).toBeInTheDocument();
    });

    it("should call onAddLayer when clicking add text link", () => {
      const onAddLayer = vi.fn();
      render(<LayerPanel {...defaultProps} onAddLayer={onAddLayer} />);

      fireEvent.click(screen.getByText("+ 텍스트 추가"));
      expect(onAddLayer).toHaveBeenCalledTimes(1);
    });
  });

  describe("with layers", () => {
    it("should display all layers", () => {
      const layers = [
        createMockLayer("1", "텍스트 1"),
        createMockLayer("2", "텍스트 2"),
      ];

      render(<LayerPanel {...defaultProps} layers={layers} />);

      expect(screen.getByText("텍스트 1")).toBeInTheDocument();
      expect(screen.getByText("텍스트 2")).toBeInTheDocument();
    });

    it("should call onSelectLayer when clicking a layer", () => {
      const onSelectLayer = vi.fn();
      const layers = [createMockLayer("1", "텍스트 1")];

      render(
        <LayerPanel {...defaultProps} layers={layers} onSelectLayer={onSelectLayer} />
      );

      fireEvent.click(screen.getByText("텍스트 1"));
      expect(onSelectLayer).toHaveBeenCalledWith("1");
    });

    it("should highlight selected layer", () => {
      const layers = [createMockLayer("1", "텍스트 1")];

      const { container } = render(
        <LayerPanel {...defaultProps} layers={layers} selectedLayerId="1" />
      );

      const layerElement = container.querySelector('[class*="bg-accent-500"]');
      expect(layerElement).toBeInTheDocument();
    });
  });

  describe("add layer", () => {
    it("should call onAddLayer when clicking add button", () => {
      const onAddLayer = vi.fn();
      render(<LayerPanel {...defaultProps} onAddLayer={onAddLayer} />);

      fireEvent.click(screen.getByText("추가"));
      expect(onAddLayer).toHaveBeenCalledTimes(1);
    });
  });

  describe("layer actions with selection", () => {
    const layers = [createMockLayer("1", "텍스트 1")];

    it("should show action buttons when layer is selected", () => {
      render(<LayerPanel {...defaultProps} layers={layers} selectedLayerId="1" />);

      expect(screen.getByText("복제")).toBeInTheDocument();
      expect(screen.getByText("삭제")).toBeInTheDocument();
    });

    it("should call onDuplicateLayer when clicking duplicate", () => {
      const onDuplicateLayer = vi.fn();
      render(
        <LayerPanel
          {...defaultProps}
          layers={layers}
          selectedLayerId="1"
          onDuplicateLayer={onDuplicateLayer}
        />
      );

      fireEvent.click(screen.getByText("복제"));
      expect(onDuplicateLayer).toHaveBeenCalledWith("1");
    });

    it("should call onRemoveLayer when clicking delete", () => {
      const onRemoveLayer = vi.fn();
      const onSelectLayer = vi.fn();
      render(
        <LayerPanel
          {...defaultProps}
          layers={layers}
          selectedLayerId="1"
          onRemoveLayer={onRemoveLayer}
          onSelectLayer={onSelectLayer}
        />
      );

      fireEvent.click(screen.getByText("삭제"));
      expect(onRemoveLayer).toHaveBeenCalledWith("1");
      expect(onSelectLayer).toHaveBeenCalledWith(null);
    });

    it("should show ordering controls when layer is selected", () => {
      render(<LayerPanel {...defaultProps} layers={layers} selectedLayerId="1" />);

      expect(screen.getByText("맨 앞")).toBeInTheDocument();
      expect(screen.getByText("앞으로")).toBeInTheDocument();
      expect(screen.getByText("뒤로")).toBeInTheDocument();
      expect(screen.getByText("맨 뒤")).toBeInTheDocument();
    });

    it("should call ordering functions", () => {
      const onBringToFront = vi.fn();
      const onMoveLayerUp = vi.fn();
      const onMoveLayerDown = vi.fn();
      const onSendToBack = vi.fn();

      render(
        <LayerPanel
          {...defaultProps}
          layers={layers}
          selectedLayerId="1"
          onBringToFront={onBringToFront}
          onMoveLayerUp={onMoveLayerUp}
          onMoveLayerDown={onMoveLayerDown}
          onSendToBack={onSendToBack}
        />
      );

      fireEvent.click(screen.getByText("맨 앞"));
      expect(onBringToFront).toHaveBeenCalledWith("1");

      fireEvent.click(screen.getByText("앞으로"));
      expect(onMoveLayerUp).toHaveBeenCalledWith("1");

      fireEvent.click(screen.getByText("뒤로"));
      expect(onMoveLayerDown).toHaveBeenCalledWith("1");

      fireEvent.click(screen.getByText("맨 뒤"));
      expect(onSendToBack).toHaveBeenCalledWith("1");
    });
  });

  describe("visibility and lock", () => {
    it("should show visibility icon for visible layers", () => {
      const layers = [createMockLayer("1", "텍스트 1")];
      const { container } = render(
        <LayerPanel {...defaultProps} layers={layers} />
      );

      // Look for eye icon (visible state)
      const visibilityButton = container.querySelector('[title="숨기기"]');
      expect(visibilityButton).toBeInTheDocument();
    });

    it("should show hidden icon for invisible layers", () => {
      const layers = [{ ...createMockLayer("1", "텍스트 1"), visible: false }];
      const { container } = render(
        <LayerPanel {...defaultProps} layers={layers} />
      );

      const visibilityButton = container.querySelector('[title="보이기"]');
      expect(visibilityButton).toBeInTheDocument();
    });

    it("should call onToggleVisibility when clicking visibility button", () => {
      const onToggleVisibility = vi.fn();
      const layers = [createMockLayer("1", "텍스트 1")];
      const { container } = render(
        <LayerPanel
          {...defaultProps}
          layers={layers}
          onToggleVisibility={onToggleVisibility}
        />
      );

      // Hover over layer to show controls
      const layerItem = screen.getByText("텍스트 1").closest(".group");
      if (layerItem) {
        fireEvent.mouseEnter(layerItem);
      }

      const visibilityButton = container.querySelector('[title="숨기기"]');
      if (visibilityButton) {
        fireEvent.click(visibilityButton);
        expect(onToggleVisibility).toHaveBeenCalledWith("1");
      }
    });

    it("should not select locked layers when clicked", () => {
      const onSelectLayer = vi.fn();
      const layers = [{ ...createMockLayer("1", "텍스트 1"), locked: true }];

      render(
        <LayerPanel
          {...defaultProps}
          layers={layers}
          onSelectLayer={onSelectLayer}
        />
      );

      fireEvent.click(screen.getByText("텍스트 1"));
      expect(onSelectLayer).not.toHaveBeenCalled();
    });
  });

  describe("layer preview", () => {
    it("should show truncated text preview", () => {
      const longText = "This is a very long text that should be truncated";
      const layers = [createMockLayer("1", "텍스트 1", longText)];

      render(<LayerPanel {...defaultProps} layers={layers} />);

      // Text should be truncated to 20 characters + "..."
      expect(screen.getByText(longText.substring(0, 20) + "...")).toBeInTheDocument();
    });

    it("should show full text if under 20 characters", () => {
      const shortText = "Short text";
      const layers = [createMockLayer("1", "텍스트 1", shortText)];

      render(<LayerPanel {...defaultProps} layers={layers} />);

      expect(screen.getByText(shortText)).toBeInTheDocument();
    });
  });
});
