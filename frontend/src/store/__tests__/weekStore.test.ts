/**
 * Tests for Zustand weekStore
 *
 * Test coverage:
 * - setCurrentYear() updates state
 * - setCurrentWeek() updates state and localStorage
 * - setWeeks() updates weeks array
 * - getCurrentWeekData() returns correct week
 * - getWeekByNumber() finds week by number
 *
 * Note: These tests can be run with Vitest or Jest
 * They use the store directly without React components
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useWeekStore } from '../weekStore';

describe('weekStore', () => {
  // Reset store state before each test
  beforeEach(() => {
    useWeekStore.getState().reset?.();
    localStorage.clear();
  });

  /**
   * Test 1: setCurrentYear() updates state
   */
  it('should update currentYear when setCurrentYear is called', () => {
    const state = useWeekStore.getState();
    const initialYear = state.currentYear;

    expect(initialYear).toBe(new Date().getFullYear());

    state.setCurrentYear(2026);

    const updatedState = useWeekStore.getState();
    expect(updatedState.currentYear).toBe(2026);
  });

  /**
   * Test 2: setCurrentWeek() updates state and localStorage
   */
  it('should update currentWeek and persist to localStorage', () => {
    const state = useWeekStore.getState();

    state.setCurrentWeek(5);

    const updatedState = useWeekStore.getState();
    expect(updatedState.currentWeek).toBe(5);

    // Check localStorage was updated (Zustand persist middleware)
    const stored = localStorage.getItem('week-store');
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed.state?.currentWeek).toBe(5);
  });

  /**
   * Test 3: setWeeks() updates weeks array
   */
  it('should update weeks array when setWeeks is called', () => {
    const state = useWeekStore.getState();

    const mockWeeks = [
      {
        id: 1,
        season: 2025,
        week_number: 1,
        status: 'completed' as const,
        status_override: null,
        nfl_slate_date: '2025-09-07',
        is_locked: true,
        locked_at: '2025-09-10T14:30:00Z',
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/1',
          slate_start: '2025-09-07T13:00:00Z',
          import_status: 'imported' as const,
          import_count: 153,
          import_timestamp: '2025-09-10T14:30:00Z',
        },
      },
      {
        id: 2,
        season: 2025,
        week_number: 2,
        status: 'upcoming' as const,
        status_override: null,
        nfl_slate_date: '2025-09-14',
        is_locked: false,
        locked_at: null,
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/2',
          slate_start: '2025-09-14T13:00:00Z',
          import_status: 'pending' as const,
          import_count: 0,
          import_timestamp: null,
        },
      },
    ];

    state.setWeeks(mockWeeks);

    const updatedState = useWeekStore.getState();
    expect(updatedState.weeks).toEqual(mockWeeks);
    expect(updatedState.weeks).toHaveLength(2);
  });

  /**
   * Test 4: getCurrentWeekData() returns correct week
   */
  it('should return current week data when getCurrentWeekData is called', () => {
    const state = useWeekStore.getState();

    const mockWeeks = [
      {
        id: 1,
        season: 2025,
        week_number: 1,
        status: 'completed' as const,
        status_override: null,
        nfl_slate_date: '2025-09-07',
        is_locked: true,
        locked_at: '2025-09-10T14:30:00Z',
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/1',
          slate_start: '2025-09-07T13:00:00Z',
          import_status: 'imported' as const,
          import_count: 153,
          import_timestamp: '2025-09-10T14:30:00Z',
        },
      },
      {
        id: 5,
        season: 2025,
        week_number: 5,
        status: 'active' as const,
        status_override: null,
        nfl_slate_date: '2025-10-05',
        is_locked: false,
        locked_at: null,
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/5',
          slate_start: '2025-10-05T13:00:00Z',
          import_status: 'pending' as const,
          import_count: 0,
          import_timestamp: null,
        },
      },
    ];

    state.setWeeks(mockWeeks);
    state.setCurrentWeek(5);

    const updatedState = useWeekStore.getState();
    const currentWeekData = updatedState.getCurrentWeekData();
    expect(currentWeekData).toBeTruthy();
    expect(currentWeekData?.week_number).toBe(5);
    expect(currentWeekData?.status).toBe('active');
  });

  /**
   * Test 5: getWeekByNumber() finds week by number
   */
  it('should find week by week_number when getWeekByNumber is called', () => {
    const state = useWeekStore.getState();

    const mockWeeks = [
      {
        id: 1,
        season: 2025,
        week_number: 1,
        status: 'completed' as const,
        status_override: null,
        nfl_slate_date: '2025-09-07',
        is_locked: true,
        locked_at: '2025-09-10T14:30:00Z',
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/1',
          slate_start: '2025-09-07T13:00:00Z',
          import_status: 'imported' as const,
          import_count: 153,
          import_timestamp: '2025-09-10T14:30:00Z',
        },
      },
      {
        id: 8,
        season: 2025,
        week_number: 8,
        status: 'upcoming' as const,
        status_override: null,
        nfl_slate_date: '2025-10-26',
        is_locked: false,
        locked_at: null,
        metadata: {
          kickoff_time: '13:00',
          espn_link: 'https://www.espn.com/nfl/schedule/_/week/8',
          slate_start: '2025-10-26T13:00:00Z',
          import_status: 'pending' as const,
          import_count: 0,
          import_timestamp: null,
        },
      },
    ];

    state.setWeeks(mockWeeks);

    const updatedState = useWeekStore.getState();
    const week8 = updatedState.getWeekByNumber(8);
    expect(week8).toBeTruthy();
    expect(week8?.id).toBe(8);
    expect(week8?.week_number).toBe(8);

    const week10 = updatedState.getWeekByNumber(10);
    expect(week10).toBeNull();
  });
});
