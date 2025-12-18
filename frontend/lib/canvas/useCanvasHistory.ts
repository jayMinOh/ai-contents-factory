/**
 * Canvas History Hook for Undo/Redo functionality
 * TAG-FE-004: Canvas State Persistence
 */

import { useState, useCallback, useRef } from "react";
import type { CanvasState, HistoryState } from "@/types/canvas";

const MAX_HISTORY_LENGTH = 50;

export interface UseCanvasHistoryReturn {
  pushState: (state: CanvasState) => void;
  undo: () => CanvasState | null;
  redo: () => CanvasState | null;
  canUndo: boolean;
  canRedo: boolean;
  clearHistory: () => void;
  currentState: CanvasState | null;
}

export function useCanvasHistory(
  initialState: CanvasState | null = null
): UseCanvasHistoryReturn {
  const [history, setHistory] = useState<HistoryState>({
    past: [],
    present: initialState,
    future: [],
  });

  // Track if we're currently performing undo/redo to avoid pushing state
  const isUndoRedoRef = useRef(false);

  const pushState = useCallback((state: CanvasState) => {
    // Don't push state if we're in the middle of undo/redo
    if (isUndoRedoRef.current) {
      isUndoRedoRef.current = false;
      return;
    }

    setHistory((prev) => {
      const newPast = prev.present
        ? [...prev.past, prev.present].slice(-MAX_HISTORY_LENGTH)
        : prev.past;

      return {
        past: newPast,
        present: state,
        future: [], // Clear future on new action
      };
    });
  }, []);

  const undo = useCallback((): CanvasState | null => {
    let undoneState: CanvasState | null = null;

    setHistory((prev) => {
      if (prev.past.length === 0) return prev;

      const previous = prev.past[prev.past.length - 1];
      const newPast = prev.past.slice(0, -1);

      undoneState = previous;
      isUndoRedoRef.current = true;

      return {
        past: newPast,
        present: previous,
        future: prev.present ? [prev.present, ...prev.future] : prev.future,
      };
    });

    return undoneState;
  }, []);

  const redo = useCallback((): CanvasState | null => {
    let redoneState: CanvasState | null = null;

    setHistory((prev) => {
      if (prev.future.length === 0) return prev;

      const next = prev.future[0];
      const newFuture = prev.future.slice(1);

      redoneState = next;
      isUndoRedoRef.current = true;

      return {
        past: prev.present ? [...prev.past, prev.present] : prev.past,
        present: next,
        future: newFuture,
      };
    });

    return redoneState;
  }, []);

  const clearHistory = useCallback(() => {
    setHistory({
      past: [],
      present: null,
      future: [],
    });
  }, []);

  return {
    pushState,
    undo,
    redo,
    canUndo: history.past.length > 0,
    canRedo: history.future.length > 0,
    clearHistory,
    currentState: history.present,
  };
}
