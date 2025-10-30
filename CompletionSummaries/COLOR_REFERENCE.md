# Line Up Lab - Color Reference Guide

## Primary Colors

### Orange Accent (Primary)
- **Main**: `#ff6b35` - Used for buttons, links, highlights, active states
- **Light**: `#ff8c5e` - Used for hover states, lighter accents
- **Dark**: `#e65a2b` - Used for pressed states, darker accents

**Usage**: 
- Primary CTA buttons
- Active navigation items
- Focus states
- Icon accents
- Hover borders
- Current week indicator

---

## Background Colors

### Pure Black
- **Primary Background**: `#000000`
- **Usage**: Main app background, header background

### Near Black
- **Secondary Background**: `#0a0a0a`
- **Usage**: Cards, modals, dropdowns, input fields

---

## Text Colors

### White
- **Primary Text**: `#ffffff`
- **Usage**: Headings, body text, labels

### Gray Scale
- **Secondary Text**: `#a0a0a0`
- **Usage**: Descriptions, metadata, placeholder text

- **Disabled Text**: `#666666`
- **Usage**: Disabled states, locked items

---

## Border Colors

### Transparent Whites
- **Subtle**: `rgba(255, 255, 255, 0.1)`
  - Default borders, dividers
  
- **Default**: `rgba(255, 255, 255, 0.2)`
  - Input borders, card borders
  
- **Hover**: `rgba(255, 255, 255, 0.3)`
  - Hover state borders

- **Focus**: `#ff6b35`
  - Focus state borders (orange)

---

## Status Colors

### Error
- **Color**: `#f44336` (Red)
- **Background**: `rgba(244, 67, 54, 0.1)`
- **Border**: `rgba(244, 67, 54, 0.3)`

### Success
- **Color**: `#4caf50` (Green)
- **Background**: `rgba(76, 175, 80, 0.1)`
- **Border**: `rgba(76, 175, 80, 0.3)`

### Info
- **Color**: `#ff6b35` (Orange - same as primary)
- **Background**: `rgba(255, 107, 53, 0.1)`
- **Border**: `rgba(255, 107, 53, 0.3)`

---

## Interaction States

### Buttons (Primary)
```css
/* Default */
background: #ff6b35;
color: #ffffff;

/* Hover */
background: #e65a2b;
box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);

/* Active/Pressed */
background: #e65a2b;
box-shadow: none;
```

### Buttons (Text/Secondary)
```css
/* Default */
color: #ff6b35;

/* Hover */
background: rgba(255, 107, 53, 0.08);
```

### Cards
```css
/* Default */
background: #0a0a0a;
border: 1px solid rgba(255, 255, 255, 0.1);

/* Hover */
border-color: #ff6b35;
box-shadow: 0 8px 24px rgba(255, 107, 53, 0.15);
transform: translateY(-4px);
```

### Inputs/Selects
```css
/* Default */
background: #0a0a0a;
border: 1px solid rgba(255, 255, 255, 0.2);

/* Hover */
border-color: rgba(255, 255, 255, 0.3);

/* Focus */
border-color: #ff6b35;
```

---

## Typography

### Font Family
```css
font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
```

### Font Weights
- **Light**: 300
- **Regular**: 400
- **Medium**: 500
- **Semi-Bold**: 600
- **Bold**: 700
- **Extra-Bold**: 800

### Headings
```css
h1: 3rem, weight 700, letter-spacing -0.02em
h2: 2.5rem, weight 700, letter-spacing -0.01em
h3: 2rem, weight 600, letter-spacing -0.01em
h4: 1.75rem, weight 600, letter-spacing 0
h5: 1.5rem, weight 600, letter-spacing 0
h6: 1.25rem, weight 600, letter-spacing 0
```

### Body Text
```css
body1: 1rem, line-height 1.6
body2: 0.875rem, line-height 1.6
caption: 0.75rem
```

---

## Spacing Scale (8px base)

```
0.5 → 4px
1   → 8px
1.5 → 12px
2   → 16px
2.5 → 20px
3   → 24px
4   → 32px
5   → 40px
6   → 48px
8   → 64px
10  → 80px
```

---

## Border Radius

- **Small**: `4px` - Chips, badges
- **Medium**: `8px` - Buttons, inputs, selects
- **Large**: `12px` - Cards, modals
- **Circle**: `50%` - Avatar, icon containers

---

## Shadows

### Elevation Levels
```css
/* Level 1 - Subtle */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

/* Level 2 - Default */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

/* Level 3 - Hover */
box-shadow: 0 8px 24px rgba(255, 107, 53, 0.15);

/* Level 4 - Modal */
box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
```

---

## Animation Timing

### Transitions
```css
/* Fast - Micro-interactions */
transition: all 0.15s ease;

/* Medium - Default */
transition: all 0.2s ease;

/* Slow - Large movements */
transition: all 0.3s ease;
```

### Keyframes
```css
/* Glow Animation */
@keyframes glow {
  0% { box-shadow: 0 0 4px rgba(255, 107, 53, 0.3); }
  50% { box-shadow: 0 0 12px rgba(255, 107, 53, 0.6); }
  100% { box-shadow: 0 0 4px rgba(255, 107, 53, 0.3); }
}
```

---

## Breakpoints

```css
xs: 0px      (mobile)
sm: 600px    (tablet portrait)
md: 960px    (tablet landscape)
lg: 1280px   (desktop)
xl: 1920px   (large desktop)
```

---

## Design Tokens (CSS Variables)

You can optionally add these to your global CSS:

```css
:root {
  /* Primary */
  --color-primary: #ff6b35;
  --color-primary-light: #ff8c5e;
  --color-primary-dark: #e65a2b;
  
  /* Backgrounds */
  --bg-primary: #000000;
  --bg-secondary: #0a0a0a;
  
  /* Text */
  --text-primary: #ffffff;
  --text-secondary: #a0a0a0;
  --text-disabled: #666666;
  
  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.1);
  --border-default: rgba(255, 255, 255, 0.2);
  --border-hover: rgba(255, 255, 255, 0.3);
  
  /* Status */
  --color-error: #f44336;
  --color-success: #4caf50;
  
  /* Spacing */
  --spacing-unit: 8px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Typography */
  --font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
```

---

**Quick Reference**: When in doubt, use `#ff6b35` for interactive orange elements, `#0a0a0a` for surfaces, and `rgba(255, 255, 255, 0.1)` for subtle borders.

