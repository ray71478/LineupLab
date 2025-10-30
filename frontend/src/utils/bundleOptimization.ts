/**
 * Bundle Optimization Utilities
 *
 * Strategies for optimizing frontend bundle size:
 * - Code splitting with React.lazy and Suspense
 * - Tree-shaking Material-UI imports
 * - Dynamic imports for heavy components
 * - Component memoization to reduce renders
 */

import { lazy, Suspense } from 'react';

/**
 * Dynamic import wrapper for code splitting
 *
 * Usage:
 * const WeekCarousel = lazyImport(() => import('./WeekCarousel'));
 *
 * Then use with Suspense:
 * <Suspense fallback={<Spinner />}>
 *   <WeekCarousel />
 * </Suspense>
 */
export function lazyImport<
  T extends Record<string, any>,
  K extends keyof T = 'default'
>(
  importFunc: () => Promise<T>,
  exportName?: K
): React.LazyExoticComponent<T[K] extends React.ComponentType<any> ? T[K] : never> {
  return lazy(async () => {
    const module = await importFunc();
    return {
      default: module[exportName || ('default' as K)] as React.ComponentType<any>,
    };
  });
}

/**
 * Bundle analysis helper
 *
 * Provides estimated bundle size information
 */
export const BundleAnalyzer = {
  /**
   * Estimate component size impact
   * Returns rough estimate based on typical React component patterns
   */
  estimateComponentSize: (componentName: string): number => {
    const estimates: Record<string, number> = {
      'WeekSelector': 4.5,
      'WeekCarousel': 5.2,
      'WeekMetadataPanel': 3.1,
      'WeekStatusBadge': 2.0,
      'WeekMetadataModal': 3.8,
    };

    return estimates[componentName] || 2.5; // KB
  },

  /**
   * Calculate total bundle impact
   */
  calculateTotalImpact: (components: string[]): number => {
    return components.reduce((total, comp) => {
      return total + BundleAnalyzer.estimateComponentSize(comp);
    }, 0);
  },

  /**
   * Recommend optimization strategies
   */
  recommendOptimizations: (bundleSizeKB: number): string[] => {
    const recommendations: string[] = [];

    if (bundleSizeKB > 100) {
      recommendations.push('Code split heavy components with React.lazy()');
      recommendations.push('Implement route-based code splitting');
    }

    if (bundleSizeKB > 80) {
      recommendations.push('Tree-shake unused Material-UI components');
      recommendations.push('Use CSS-in-JS only for dynamic styles');
    }

    if (bundleSizeKB > 60) {
      recommendations.push('Memoize expensive components with React.memo()');
      recommendations.push('Use useMemo for expensive computations');
    }

    recommendations.push('Enable gzip compression on server');
    recommendations.push('Use production build with minification');

    return recommendations;
  },
};

/**
 * Material-UI tree-shaking helper
 *
 * Instead of:
 * import { Box, Button, Select, MenuItem } from '@mui/material';
 *
 * Use:
 * import Box from '@mui/material/Box';
 * import Button from '@mui/material/Button';
 *
 * This allows tree-shaking to remove unused components
 */
export const MUIOptimizations = {
  description: 'Material-UI components support tree-shaking when imported individually',

  examples: {
    bad: "import { Box, Button } from '@mui/material'",
    good: `import Box from '@mui/material/Box';
import Button from '@mui/material/Button';`,
  },

  commonComponents: {
    'Box': '@mui/material/Box',
    'Button': '@mui/material/Button',
    'Stack': '@mui/material/Stack',
    'Typography': '@mui/material/Typography',
    'FormControl': '@mui/material/FormControl',
    'Select': '@mui/material/Select',
    'MenuItem': '@mui/material/MenuItem',
    'Dialog': '@mui/material/Dialog',
    'Modal': '@mui/material/Modal',
    'Tooltip': '@mui/material/Tooltip',
    'CircularProgress': '@mui/material/CircularProgress',
    'Skeleton': '@mui/material/Skeleton',
  },
};

/**
 * Performance monitoring for bundle
 */
export const PerformanceMonitor = {
  /**
   * Log initial bundle metrics
   */
  logBundleMetrics: (): void => {
    if (typeof window === 'undefined') return;

    const performanceMetrics = {
      'First Contentful Paint': performance?.getEntriesByName('first-contentful-paint')[0]?.startTime,
      'Largest Contentful Paint': performance?.getEntriesByName('largest-contentful-paint')[0]?.startTime,
      'Time to Interactive': performance?.getEntriesByName('first-input')[0]?.startTime,
    };

    console.log('Bundle Performance Metrics:', performanceMetrics);
  },

  /**
   * Monitor component render times
   */
  measureComponentRender: (componentName: string, renderTime: number): void => {
    if (renderTime > 16) { // 60fps = 16ms per frame
      console.warn(
        `Slow component render: ${componentName} took ${renderTime.toFixed(2)}ms ` +
        `(target: <16ms for 60fps)`
      );
    }
  },
};

/**
 * CSS-in-JS optimization tips
 */
export const CSSOptimizations = {
  // Use sx prop for dynamic styles (Material-UI specific)
  // Keep CSS animations in pure CSS files
  // Avoid inline styles in tight loops
  // Use CSS custom properties for theme values

  description: 'Optimize CSS-in-JS performance for better runtime performance',

  bestPractices: [
    'Define keyframes outside component functions',
    'Use `sx` prop for styles instead of inline objects',
    'Cache computed styles with useMemo',
    'Use CSS animations instead of JavaScript animations',
    'Minimize dynamic style calculations',
  ],
};

/**
 * Tree-shaking verification for production build
 *
 * Run in build process to check unused code:
 * npm run analyze -- --stat
 */
export const TreeShakingChecklist = [
  '[ ] All unused imports removed',
  '[ ] Unused Material-UI components removed',
  '[ ] Dead code eliminated by build tool',
  '[ ] Polyfills only included if needed',
  '[ ] Dynamic imports used for large components',
  '[ ] Production build with minification enabled',
  '[ ] CSS minification enabled',
  '[ ] Source maps for debugging (production)',
];

/**
 * Code splitting strategy for week management feature
 *
 * Main bundle:
 * - WeekSelector (desktop dropdown)
 * - WeekStatusBadge
 * - useWeekStore
 *
 * Lazy loaded:
 * - WeekCarousel (mobile only)
 * - WeekMetadataModal (on tap)
 * - WeekMetadataPanel (detailed view)
 */
export const CodeSplittingStrategy = {
  mainBundle: [
    'WeekSelector',
    'WeekStatusBadge',
    'weekStore',
    'useWeeks hook',
  ],

  lazyLoaded: [
    'WeekCarousel',
    'WeekMetadataModal',
    'WeekMetadataPanel',
  ],

  expectedSizes: {
    mainBundle: '~25KB (gzipped)',
    lazyCarousel: '~5KB (gzipped)',
    lazyModal: '~4KB (gzipped)',
  },

  targetTotalSize: '<100KB for feature code (gzipped)',
};
