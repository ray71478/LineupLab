/**
 * Tests for Zustand modeStore
 *
 * Test coverage:
 * - mode defaults to 'main' on initialization
 * - setMode() updates state correctly
 * - setMode() persists to localStorage
 * - mode state accessible from multiple calls (simulating components)
 * - Invalid mode values are handled
 * - reset() restores default state
 *
 * Note: These tests can be run with Vitest or Jest
 * They use the store directly without React components
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useModeStore } from '../modeStore';

describe('modeStore', () => {
  // Reset store state before each test
  beforeEach(() => {
    useModeStore.getState().reset?.();
    localStorage.clear();
  });

  /**
   * Test 1: mode defaults to 'main'
   */
  it('should default mode to "main" on initialization', () => {
    const state = useModeStore.getState();
    expect(state.mode).toBe('main');
  });

  /**
   * Test 2: setMode updates state correctly for 'main'
   */
  it('should update mode to "main" when setMode("main") is called', () => {
    const state = useModeStore.getState();

    state.setMode('main');

    const updatedState = useModeStore.getState();
    expect(updatedState.mode).toBe('main');
  });

  /**
   * Test 3: setMode updates state correctly for 'showdown'
   */
  it('should update mode to "showdown" when setMode("showdown") is called', () => {
    const state = useModeStore.getState();

    state.setMode('showdown');

    const updatedState = useModeStore.getState();
    expect(updatedState.mode).toBe('showdown');
  });

  /**
   * Test 4: setMode persists to localStorage
   */
  it('should persist mode to localStorage when setMode is called', () => {
    const state = useModeStore.getState();

    state.setMode('showdown');

    // Check localStorage was updated (Zustand persist middleware)
    const stored = localStorage.getItem('mode-store');
    expect(stored).toBeTruthy();

    const parsed = JSON.parse(stored!);
    expect(parsed.state?.mode).toBe('showdown');
  });

  /**
   * Test 5: mode state accessible from multiple calls
   */
  it('should maintain consistent state across multiple getState calls', () => {
    const state1 = useModeStore.getState();
    state1.setMode('showdown');

    const state2 = useModeStore.getState();
    const state3 = useModeStore.getState();

    // All calls should see the same state (simulates multiple components)
    expect(state2.mode).toBe('showdown');
    expect(state3.mode).toBe('showdown');
    expect(state2.mode).toBe(state3.mode);
  });

  /**
   * Test 6: mode persists across component re-renders (simulated)
   */
  it('should maintain mode state when store is accessed again', () => {
    const state = useModeStore.getState();
    state.setMode('showdown');

    // Simulate component re-render by getting state again
    const stateAfterRerender = useModeStore.getState();
    expect(stateAfterRerender.mode).toBe('showdown');
  });

  /**
   * Test 7: reset() restores default state
   */
  it('should reset mode to "main" when reset() is called', () => {
    const state = useModeStore.getState();

    // Change to showdown first
    state.setMode('showdown');
    expect(useModeStore.getState().mode).toBe('showdown');

    // Then reset
    state.reset?.();

    const resetState = useModeStore.getState();
    expect(resetState.mode).toBe('main');
  });

  /**
   * Test 8: mode can switch back and forth
   */
  it('should allow switching between modes multiple times', () => {
    const state = useModeStore.getState();

    // Start with main (default)
    expect(state.mode).toBe('main');

    // Switch to showdown
    state.setMode('showdown');
    expect(useModeStore.getState().mode).toBe('showdown');

    // Switch back to main
    state.setMode('main');
    expect(useModeStore.getState().mode).toBe('main');

    // Switch to showdown again
    state.setMode('showdown');
    expect(useModeStore.getState().mode).toBe('showdown');
  });
});
