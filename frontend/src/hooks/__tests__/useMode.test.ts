/**
 * Tests for useMode custom hook
 *
 * Test coverage:
 * - Hook returns current mode from store
 * - Hook returns setMode function
 * - Hook updates when mode changes
 * - Multiple hook instances share same state
 *
 * Note: These tests can be run with Vitest or Jest
 * They test the hook integration with the mode store
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useMode } from '../useMode';
import { useModeStore } from '../../store/modeStore';

describe('useMode', () => {
  // Reset store state before each test
  beforeEach(() => {
    useModeStore.getState().reset?.();
    localStorage.clear();
  });

  /**
   * Test 1: Hook returns current mode from store
   */
  it('should return current mode from store', () => {
    const { result } = renderHook(() => useMode());

    expect(result.current.mode).toBe('main');
  });

  /**
   * Test 2: Hook returns setMode function
   */
  it('should return setMode function', () => {
    const { result } = renderHook(() => useMode());

    expect(result.current.setMode).toBeDefined();
    expect(typeof result.current.setMode).toBe('function');
  });

  /**
   * Test 3: Hook updates when mode changes
   */
  it('should update mode when setMode is called', () => {
    const { result } = renderHook(() => useMode());

    // Initial state
    expect(result.current.mode).toBe('main');

    // Change mode
    act(() => {
      result.current.setMode('showdown');
    });

    // Verify update
    expect(result.current.mode).toBe('showdown');
  });

  /**
   * Test 4: Multiple hook instances share same state
   */
  it('should share state between multiple hook instances', () => {
    const { result: result1 } = renderHook(() => useMode());
    const { result: result2 } = renderHook(() => useMode());

    // Both should start with 'main'
    expect(result1.current.mode).toBe('main');
    expect(result2.current.mode).toBe('main');

    // Change mode in first hook
    act(() => {
      result1.current.setMode('showdown');
    });

    // Both should see the update
    expect(result1.current.mode).toBe('showdown');
    expect(result2.current.mode).toBe('showdown');
  });

  /**
   * Test 5: Hook can switch modes back and forth
   */
  it('should allow switching between modes', () => {
    const { result } = renderHook(() => useMode());

    // Start with main
    expect(result.current.mode).toBe('main');

    // Switch to showdown
    act(() => {
      result.current.setMode('showdown');
    });
    expect(result.current.mode).toBe('showdown');

    // Switch back to main
    act(() => {
      result.current.setMode('main');
    });
    expect(result.current.mode).toBe('main');
  });
});
