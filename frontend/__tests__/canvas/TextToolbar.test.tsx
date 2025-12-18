import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import TextToolbar from "@/components/canvas/TextToolbar";
import type { TextLayer } from "@/types/canvas";

const createMockLayer = (overrides: Partial<TextLayer> = {}): TextLayer => ({
  id: "test-layer",
  name: "텍스트 1",
  text: "Sample text",
  fontFamily: "Noto Sans KR, sans-serif",
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
  ...overrides,
});

describe("TextToolbar", () => {
  describe("no selection state", () => {
    it("should display placeholder when no layer is selected", () => {
      render(<TextToolbar selectedLayer={null} onUpdate={vi.fn()} />);

      expect(screen.getByText("텍스트 레이어를 선택하세요")).toBeInTheDocument();
    });
  });

  describe("with selected layer", () => {
    it("should display font controls", () => {
      const layer = createMockLayer();
      render(<TextToolbar selectedLayer={layer} onUpdate={vi.fn()} />);

      // Font selector should show current font
      expect(screen.getByText("Noto Sans KR")).toBeInTheDocument();
    });

    it("should display font size input", () => {
      const layer = createMockLayer({ fontSize: 48 });
      render(<TextToolbar selectedLayer={layer} onUpdate={vi.fn()} />);

      const sizeInput = screen.getByDisplayValue("48");
      expect(sizeInput).toBeInTheDocument();
    });

    it("should display text alignment buttons", () => {
      const layer = createMockLayer();
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={vi.fn()} />
      );

      expect(container.querySelector('[title="왼쪽 정렬"]')).toBeInTheDocument();
      expect(container.querySelector('[title="가운데 정렬"]')).toBeInTheDocument();
      expect(container.querySelector('[title="오른쪽 정렬"]')).toBeInTheDocument();
    });
  });

  describe("font size controls", () => {
    it("should increase font size when clicking plus button", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontSize: 32 });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const plusButton = container.querySelector('[title="글자 크기 늘리기"]');
      if (plusButton) {
        fireEvent.click(plusButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontSize: 34 });
      }
    });

    it("should decrease font size when clicking minus button", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontSize: 32 });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const minusButton = container.querySelector('[title="글자 크기 줄이기"]');
      if (minusButton) {
        fireEvent.click(minusButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontSize: 30 });
      }
    });

    it("should not go below minimum font size (12)", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontSize: 12 });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const minusButton = container.querySelector('[title="글자 크기 줄이기"]');
      if (minusButton) {
        fireEvent.click(minusButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontSize: 12 });
      }
    });

    it("should not go above maximum font size (120)", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontSize: 120 });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const plusButton = container.querySelector('[title="글자 크기 늘리기"]');
      if (plusButton) {
        fireEvent.click(plusButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontSize: 120 });
      }
    });

    it("should update font size from input", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontSize: 32 });
      render(<TextToolbar selectedLayer={layer} onUpdate={onUpdate} />);

      const input = screen.getByDisplayValue("32");
      fireEvent.change(input, { target: { value: "48" } });
      expect(onUpdate).toHaveBeenCalledWith({ fontSize: 48 });
    });
  });

  describe("text style toggles", () => {
    it("should toggle bold", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontWeight: "normal" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const boldButton = container.querySelector('[title="굵게 (Bold)"]');
      if (boldButton) {
        fireEvent.click(boldButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontWeight: "bold" });
      }
    });

    it("should toggle bold off", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontWeight: "bold" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const boldButton = container.querySelector('[title="굵게 (Bold)"]');
      if (boldButton) {
        fireEvent.click(boldButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontWeight: "normal" });
      }
    });

    it("should toggle italic", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ fontStyle: "normal" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const italicButton = container.querySelector('[title="기울임 (Italic)"]');
      if (italicButton) {
        fireEvent.click(italicButton);
        expect(onUpdate).toHaveBeenCalledWith({ fontStyle: "italic" });
      }
    });

    it("should toggle underline", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ underline: false });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const underlineButton = container.querySelector('[title="밑줄 (Underline)"]');
      if (underlineButton) {
        fireEvent.click(underlineButton);
        expect(onUpdate).toHaveBeenCalledWith({ underline: true });
      }
    });

    it("should toggle strikethrough", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ linethrough: false });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const strikeButton = container.querySelector(
        '[title="취소선 (Strikethrough)"]'
      );
      if (strikeButton) {
        fireEvent.click(strikeButton);
        expect(onUpdate).toHaveBeenCalledWith({ linethrough: true });
      }
    });
  });

  describe("text alignment", () => {
    it("should set left alignment", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ textAlign: "center" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const leftButton = container.querySelector('[title="왼쪽 정렬"]');
      if (leftButton) {
        fireEvent.click(leftButton);
        expect(onUpdate).toHaveBeenCalledWith({ textAlign: "left" });
      }
    });

    it("should set center alignment", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ textAlign: "left" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const centerButton = container.querySelector('[title="가운데 정렬"]');
      if (centerButton) {
        fireEvent.click(centerButton);
        expect(onUpdate).toHaveBeenCalledWith({ textAlign: "center" });
      }
    });

    it("should set right alignment", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ textAlign: "center" });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      const rightButton = container.querySelector('[title="오른쪽 정렬"]');
      if (rightButton) {
        fireEvent.click(rightButton);
        expect(onUpdate).toHaveBeenCalledWith({ textAlign: "right" });
      }
    });
  });

  describe("opacity control", () => {
    it("should display current opacity", () => {
      const layer = createMockLayer({ opacity: 0.75 });
      render(<TextToolbar selectedLayer={layer} onUpdate={vi.fn()} />);

      expect(screen.getByText("75%")).toBeInTheDocument();
    });

    it("should update opacity", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ opacity: 1 });
      render(<TextToolbar selectedLayer={layer} onUpdate={onUpdate} />);

      const slider = screen.getByRole("slider");
      fireEvent.change(slider, { target: { value: "50" } });
      expect(onUpdate).toHaveBeenCalledWith({ opacity: 0.5 });
    });
  });

  describe("shadow control", () => {
    it("should show shadow toggle button", () => {
      const layer = createMockLayer();
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={vi.fn()} />
      );

      const shadowButton = container.querySelector('[title="그림자"]');
      expect(shadowButton).toBeInTheDocument();
    });

    it("should toggle shadow on", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({ shadow: null });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      // Open shadow panel
      const shadowButton = container.querySelector('[title="그림자"]');
      if (shadowButton) {
        fireEvent.click(shadowButton);
      }

      // Toggle shadow on
      const toggleButton = screen.getByText("OFF");
      fireEvent.click(toggleButton);

      expect(onUpdate).toHaveBeenCalledWith({
        shadow: {
          color: "#000000",
          blur: 4,
          offsetX: 2,
          offsetY: 2,
        },
      });
    });

    it("should toggle shadow off", () => {
      const onUpdate = vi.fn();
      const layer = createMockLayer({
        shadow: { color: "#000000", blur: 4, offsetX: 2, offsetY: 2 },
      });
      const { container } = render(
        <TextToolbar selectedLayer={layer} onUpdate={onUpdate} />
      );

      // Open shadow panel
      const shadowButton = container.querySelector('[title="그림자"]');
      if (shadowButton) {
        fireEvent.click(shadowButton);
      }

      // Toggle shadow off
      const toggleButton = screen.getByText("ON");
      fireEvent.click(toggleButton);

      expect(onUpdate).toHaveBeenCalledWith({ shadow: null });
    });
  });
});
