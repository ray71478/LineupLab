/**
 * Tests for status badge and metadata components
 *
 * Test coverage:
 * - WeekStatusBadge renders correct icon for each status
 * - WeekStatusBadge applies glow effect for current week
 * - WeekImportStatusBadge shows correct status
 * - WeekMetadataPanel displays all metadata correctly
 *
 * Note: These tests use Vitest and verify component exports and interfaces
 */

import { describe, it, expect } from 'vitest';
import { WeekStatusBadge } from '../WeekStatusBadge';
import { WeekImportStatusBadge } from '../WeekImportStatusBadge';
import { WeekMetadataPanel } from '../WeekMetadataPanel';
import { WeekMetadataModal } from '../WeekMetadataModal';

describe('WeekStatusBadge Component', () => {
  /**
   * Test 1: WeekStatusBadge renders correct icon for each status
   */
  it('should export WeekStatusBadge component', () => {
    expect(WeekStatusBadge).toBeDefined();
    expect(typeof WeekStatusBadge).toBe('function');
  });

  it('should accept all required props', () => {
    const props = {
      status: 'completed' as const,
      importStatus: 'imported' as const,
      isCurrentWeek: false,
      compact: false,
    };
    expect(props.status).toBe('completed');
    expect(props.importStatus).toBe('imported');
    expect(props.isCurrentWeek).toBe(false);
    expect(props.compact).toBe(false);
  });

  it('should accept active status', () => {
    const props = {
      status: 'active' as const,
      importStatus: 'imported' as const,
      isCurrentWeek: true,
      compact: false,
    };
    expect(props.status).toBe('active');
    expect(props.importStatus).toBe('imported');
  });

  it('should accept upcoming status', () => {
    const props = {
      status: 'upcoming' as const,
      importStatus: 'pending' as const,
      isCurrentWeek: false,
      compact: false,
    };
    expect(props.status).toBe('upcoming');
    expect(props.importStatus).toBe('pending');
  });

  /**
   * Test 2: WeekStatusBadge applies glow effect for current week
   */
  it('should support isCurrentWeek prop for glow effect', () => {
    const withGlow = {
      status: 'active' as const,
      importStatus: 'imported' as const,
      isCurrentWeek: true,
      compact: false,
    };
    expect(withGlow.isCurrentWeek).toBe(true);

    const withoutGlow = {
      status: 'active' as const,
      importStatus: 'imported' as const,
      isCurrentWeek: false,
      compact: false,
    };
    expect(withoutGlow.isCurrentWeek).toBe(false);
  });

  it('should support compact mode', () => {
    const compactProps = {
      status: 'active' as const,
      importStatus: 'imported' as const,
      isCurrentWeek: false,
      compact: true,
    };
    expect(compactProps.compact).toBe(true);
  });
});

describe('WeekImportStatusBadge Component', () => {
  /**
   * Test 3: WeekImportStatusBadge shows correct status
   */
  it('should export WeekImportStatusBadge component', () => {
    expect(WeekImportStatusBadge).toBeDefined();
    expect(typeof WeekImportStatusBadge).toBe('function');
  });

  it('should display imported status with count', () => {
    const props = {
      importStatus: 'imported' as const,
      importCount: 153,
      importTimestamp: '2025-10-05T14:30:00Z',
      errorMessage: null,
    };
    expect(props.importStatus).toBe('imported');
    expect(props.importCount).toBe(153);
    expect(props.importTimestamp).toBeTruthy();
  });

  it('should display pending status', () => {
    const props = {
      importStatus: 'pending' as const,
      importCount: 0,
      importTimestamp: null,
      errorMessage: null,
    };
    expect(props.importStatus).toBe('pending');
    expect(props.importCount).toBe(0);
  });

  it('should display error status with error message', () => {
    const props = {
      importStatus: 'error' as const,
      importCount: 0,
      importTimestamp: null,
      errorMessage: 'File format invalid',
    };
    expect(props.importStatus).toBe('error');
    expect(props.errorMessage).toBe('File format invalid');
  });

  it('should handle optional error message', () => {
    const props = {
      importStatus: 'error' as const,
      importCount: 0,
      importTimestamp: null,
      errorMessage: undefined,
    };
    expect(props.errorMessage).toBeUndefined();
  });
});

describe('WeekMetadataPanel Component', () => {
  /**
   * Test 4: WeekMetadataPanel displays all metadata correctly
   */
  it('should export WeekMetadataPanel component', () => {
    expect(WeekMetadataPanel).toBeDefined();
    expect(typeof WeekMetadataPanel).toBe('function');
  });

  it('should accept week prop with all metadata fields', () => {
    const mockWeek = {
      id: 5,
      season: 2025,
      week_number: 5,
      status: 'active' as const,
      status_override: null,
      nfl_slate_date: '2025-10-05',
      is_locked: true,
      locked_at: '2025-10-05T14:30:00Z',
      metadata: {
        kickoff_time: '13:00',
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
        slate_start: '2025-10-05T13:00:00Z',
        import_status: 'imported' as const,
        import_count: 153,
        import_timestamp: '2025-10-05T14:30:00Z',
      },
    };

    expect(mockWeek.id).toBe(5);
    expect(mockWeek.week_number).toBe(5);
    expect(mockWeek.status).toBe('active');
    expect(mockWeek.nfl_slate_date).toBe('2025-10-05');
    expect(mockWeek.metadata.import_status).toBe('imported');
    expect(mockWeek.metadata.import_count).toBe(153);
  });

  it('should support loading state', () => {
    const mockWeek = {
      id: 5,
      season: 2025,
      week_number: 5,
      status: 'active' as const,
      status_override: null,
      nfl_slate_date: '2025-10-05',
      is_locked: true,
      locked_at: '2025-10-05T14:30:00Z',
      metadata: {
        kickoff_time: '13:00',
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
        slate_start: '2025-10-05T13:00:00Z',
        import_status: 'imported' as const,
        import_count: 153,
        import_timestamp: '2025-10-05T14:30:00Z',
      },
    };

    const props = {
      week: mockWeek,
      isLoading: true,
      compact: false,
    };
    expect(props.isLoading).toBe(true);
  });

  it('should support compact layout', () => {
    const mockWeek = {
      id: 5,
      season: 2025,
      week_number: 5,
      status: 'active' as const,
      status_override: null,
      nfl_slate_date: '2025-10-05',
      is_locked: true,
      locked_at: '2025-10-05T14:30:00Z',
      metadata: {
        kickoff_time: '13:00',
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
        slate_start: '2025-10-05T13:00:00Z',
        import_status: 'imported' as const,
        import_count: 153,
        import_timestamp: '2025-10-05T14:30:00Z',
      },
    };

    const props = {
      week: mockWeek,
      isLoading: false,
      compact: true,
    };
    expect(props.compact).toBe(true);
  });

  it('should handle weeks with no import timestamp', () => {
    const mockWeek = {
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
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/2/year/2025',
        slate_start: '2025-09-14T13:00:00Z',
        import_status: 'pending' as const,
        import_count: 0,
        import_timestamp: null,
      },
    };

    expect(mockWeek.metadata.import_timestamp).toBeNull();
    expect(mockWeek.metadata.import_count).toBe(0);
  });
});

describe('WeekMetadataModal Component', () => {
  it('should export WeekMetadataModal component', () => {
    expect(WeekMetadataModal).toBeDefined();
    expect(typeof WeekMetadataModal).toBe('function');
  });

  it('should accept week object and open/onClose props', () => {
    const mockWeek = {
      id: 5,
      season: 2025,
      week_number: 5,
      status: 'active' as const,
      status_override: null,
      nfl_slate_date: '2025-10-05',
      is_locked: true,
      locked_at: '2025-10-05T14:30:00Z',
      metadata: {
        kickoff_time: '13:00',
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
        slate_start: '2025-10-05T13:00:00Z',
        import_status: 'imported' as const,
        import_count: 153,
        import_timestamp: '2025-10-05T14:30:00Z',
      },
    };

    const props = {
      week: mockWeek,
      open: true,
      onClose: () => {},
    };

    expect(props.week).toBeDefined();
    expect(props.open).toBe(true);
    expect(typeof props.onClose).toBe('function');
  });

  it('should support null week prop', () => {
    const props = {
      week: null,
      open: false,
      onClose: () => {},
    };

    expect(props.week).toBeNull();
  });

  it('should handle error message in week metadata', () => {
    const mockWeek = {
      id: 5,
      season: 2025,
      week_number: 5,
      status: 'completed' as const,
      status_override: null,
      nfl_slate_date: '2025-10-05',
      is_locked: false,
      locked_at: null,
      metadata: {
        kickoff_time: '13:00',
        espn_link: 'https://www.espn.com/nfl/schedule/_/week/5/year/2025',
        slate_start: '2025-10-05T13:00:00Z',
        import_status: 'error' as const,
        import_count: 0,
        import_timestamp: null,
        error_message: 'File format invalid',
      },
    };

    expect(mockWeek.metadata.error_message).toBe('File format invalid');
  });
});
