## Responsive design best practices

### General Principles
- **Mobile-First Development**: Start with mobile layout and progressively enhance for larger screens
- **Standard Breakpoints**: Use MUI's breakpoint system consistently (xs, sm, md, lg, xl)
- **Fluid Layouts**: Use percentage-based widths and flexible containers that adapt to screen size
- **Relative Units**: Prefer rem/em units over fixed pixels for better scalability and accessibility
- **Test Across Devices**: Test on actual devices (iPhone, iPad) and browser dev tools
- **Touch-Friendly Design**: Ensure tap targets are minimum 44x44px for mobile users
- **Performance on Mobile**: Optimize for mobile network conditions (lazy loading, image optimization)
- **Readable Typography**: Maintain readable font sizes across all breakpoints without requiring zoom
- **Content Priority**: Show the most important content first on smaller screens

### Cortex Breakpoints

**MUI Default Breakpoints:**
- **xs** (extra-small): 0px - 599px (mobile phones)
- **sm** (small): 600px - 899px (tablets portrait)
- **md** (medium): 900px - 1199px (tablets landscape, small laptops)
- **lg** (large): 1200px - 1535px (desktops)
- **xl** (extra-large): 1536px+ (large desktops)

**Cortex Target Devices:**
- **Mobile**: 390x844 (iPhone 15 Pro) - Primary mobile target
- **Tablet**: 1024x768 (iPad) - Secondary mobile target
- **Desktop**: 1920x1080 (standard desktop) - Primary desktop target

### Responsive Layout Patterns

#### Container Widths
```typescript
import { Container } from '@mui/material';

// Responsive container with max-width
<Container
  maxWidth="xl"  // xs, sm, md, lg, xl, or false for full width
  sx={{
    px: { xs: 2, sm: 3, md: 4 },  // Padding: 16px (mobile), 24px (tablet), 32px (desktop)
  }}
>
  {/* Content */}
</Container>
```

#### Grid Layouts
```typescript
import { Grid } from '@mui/material';

// Responsive grid: 1 column (mobile), 2 columns (tablet), 3 columns (desktop)
<Grid container spacing={{ xs: 2, md: 3 }}>
  <Grid item xs={12} sm={6} md={4}>
    <PlayerCard />
  </Grid>
  <Grid item xs={12} sm={6} md={4}>
    <PlayerCard />
  </Grid>
  <Grid item xs={12} sm={6} md={4}>
    <PlayerCard />
  </Grid>
</Grid>
```

#### Flexbox Layouts
```typescript
import { Box, Stack } from '@mui/material';

// Responsive flex direction
<Box
  sx={{
    display: 'flex',
    flexDirection: { xs: 'column', md: 'row' },  // Column on mobile, row on desktop
    gap: { xs: 2, md: 4 },
    alignItems: { xs: 'stretch', md: 'center' },
  }}
>
  <Box sx={{ flex: 1 }}>Left Panel</Box>
  <Box sx={{ flex: 2 }}>Right Panel</Box>
</Box>

// Stack component (simpler for common patterns)
<Stack
  direction={{ xs: 'column', md: 'row' }}
  spacing={{ xs: 2, md: 4 }}
  alignItems="center"
>
  <Button>Action 1</Button>
  <Button>Action 2</Button>
</Stack>
```

### Cortex-Specific Responsive Patterns

#### Dashboard Layout
```typescript
// Desktop: Sidebar + Main Content
// Mobile: Stacked layout with bottom navigation

<Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}>
  {/* Sidebar: Hidden on mobile, shown on desktop */}
  <Box
    sx={{
      display: { xs: 'none', md: 'block' },
      width: 240,
      flexShrink: 0,
      borderRight: 1,
      borderColor: 'divider',
    }}
  >
    <Sidebar />
  </Box>

  {/* Main Content */}
  <Box sx={{ flex: 1, p: { xs: 2, md: 4 } }}>
    <MainContent />
  </Box>

  {/* Bottom Navigation: Shown on mobile, hidden on desktop */}
  <Box
    sx={{
      display: { xs: 'block', md: 'none' },
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 1000,
    }}
  >
    <BottomNavigation />
  </Box>
</Box>
```

#### Player Pool Table
```typescript
// Desktop: Full table with all columns
// Mobile: Simplified table or card layout

// Option 1: Hide columns on mobile
<Table>
  <TableHead>
    <TableRow>
      <TableCell>Player</TableCell>
      <TableCell align="right">Salary</TableCell>
      <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>
        Ownership
      </TableCell>
      <TableCell align="right" sx={{ display: { xs: 'none', md: 'table-cell' } }}>
        Ceiling
      </TableCell>
      <TableCell align="right">Smart Score</TableCell>
    </TableRow>
  </TableHead>
  {/* ... */}
</Table>

// Option 2: Switch to card layout on mobile
const isMobile = useMediaQuery(theme.breakpoints.down('md'));

{isMobile ? (
  <Stack spacing={2}>
    {players.map(player => <PlayerCard key={player.id} player={player} />)}
  </Stack>
) : (
  <Table>{/* Full table */}</Table>
)}
```

#### Smart Score Configuration
```typescript
// Desktop: Sliders side-by-side
// Mobile: Stacked sliders

<Grid container spacing={3}>
  {weights.map((weight) => (
    <Grid item xs={12} sm={6} md={4} key={weight.id}>
      <Typography variant="body2">{weight.label}</Typography>
      <Slider
        value={weight.value}
        onChange={handleChange}
        min={0}
        max={2}
        step={0.1}
      />
    </Grid>
  ))}
</Grid>
```

#### Lineup Results
```typescript
// Desktop: 10 lineups in grid (2 rows x 5 columns)
// Mobile: Scrollable carousel or stacked cards

<Grid container spacing={2}>
  {lineups.map((lineup, index) => (
    <Grid item xs={12} sm={6} md={4} lg={2.4} key={index}>
      <LineupCard lineup={lineup} number={index + 1} />
    </Grid>
  ))}
</Grid>
```

### Typography Responsiveness
```typescript
// Responsive font sizes
<Typography
  variant="h1"
  sx={{
    fontSize: { xs: '2rem', sm: '2.5rem', md: '3rem' },  // 32px → 40px → 48px
    lineHeight: { xs: 1.2, md: 1.3 },
  }}
>
  Cortex
</Typography>

// Or use variant with responsive overrides
<Typography
  variant="h4"
  sx={{
    fontSize: { xs: '1.25rem', md: '1.5rem' },  // Smaller on mobile
  }}
>
  Player Pool
</Typography>
```

### Spacing Responsiveness
```typescript
// Responsive padding and margin
<Box
  sx={{
    p: { xs: 2, sm: 3, md: 4 },      // Padding: 16px → 24px → 32px
    mb: { xs: 2, md: 4 },            // Margin bottom: 16px → 32px
    gap: { xs: 1, sm: 2, md: 3 },    // Gap: 8px → 16px → 24px
  }}
>
  {/* Content */}
</Box>
```

### Touch Targets
```typescript
// Ensure minimum 44x44px tap targets on mobile
<Button
  sx={{
    minWidth: { xs: 44, md: 'auto' },
    minHeight: { xs: 44, md: 'auto' },
    p: { xs: 1.5, md: 1 },  // Larger padding on mobile
  }}
>
  Generate
</Button>

// Icon buttons
<IconButton
  sx={{
    width: { xs: 48, md: 40 },
    height: { xs: 48, md: 40 },
  }}
>
  <Settings />
</IconButton>
```

### Media Queries in Code
```typescript
import { useMediaQuery, useTheme } from '@mui/material';

function MyComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

  return (
    <Box>
      {isMobile && <MobileView />}
      {isTablet && <TabletView />}
      {isDesktop && <DesktopView />}
    </Box>
  );
}
```

### Performance Optimization

**Lazy Load Images:**
```typescript
<Box
  component="img"
  src={player.avatar}
  loading="lazy"  // Native lazy loading
  sx={{
    width: { xs: 40, md: 60 },
    height: { xs: 40, md: 60 },
  }}
/>
```

**Conditional Rendering:**
```typescript
// Don't render heavy components on mobile
const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

{isDesktop && <AdvancedAnalyticsPanel />}
```

**Virtualization for Long Lists:**
```typescript
// Use TanStack Table's virtualization for 200+ players on mobile
import { useVirtualizer } from '@tanstack/react-virtual';
```

### Testing Checklist

**Test on Real Devices:**
- ✅ iPhone 15 Pro (390x844) - Safari
- ✅ iPad (1024x768) - Safari
- ✅ Desktop (1920x1080) - Chrome

**Test Responsive Behaviors:**
- ✅ Navigation: Bottom nav on mobile, sidebar on desktop
- ✅ Tables: Simplified on mobile, full on desktop
- ✅ Forms: Stacked on mobile, side-by-side on desktop
- ✅ Buttons: Larger tap targets on mobile
- ✅ Typography: Readable sizes without zoom
- ✅ Spacing: Appropriate padding/margins for screen size

**Test Interactions:**
- ✅ Touch gestures work on mobile (tap, swipe, pinch-zoom)
- ✅ Keyboard navigation works on desktop
- ✅ Focus indicators visible on all devices
- ✅ Modals/dialogs fit on mobile screens
