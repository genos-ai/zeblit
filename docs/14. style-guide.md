Style Guide for Replit App

## Brand Philosophy
**Core Concept**: "Out of the Ordinary" - Creating enduring worth through distinctive performance and client focus

## Key Design System Insights

Based on analysis of an actual website implementation:

1. **Icon System**: Custom Fontello icon font ('Zeblitcom') with 150+ banking-specific icons
2. **Typography**: Inter Variable Font for UI, Libre Caslon Text for elegant accents
3. **Colors**: Dark navy (#303849) primary, stone (#F4F4F2) backgrounds
4. **Framework**: Bootstrap-based responsive grid system
5. **Components**: Minimal border radius (2-4px), subtle shadows, hover state inversions
6. **Unique Elements**: SVG wave patterns between sections, "Out of the Ordinary" messaging
7. **Performance**: Font preloading, lazy loading, CSS minification

## Color Palette

### Primary Colors
```css
--Zeblit-dark-navy: #303849;    /* Primary dark color (from site) */
--Zeblit-navy-alt: #30384A;     /* Slight variant */
--Zeblit-stone: #F4F4F2;        /* Background stone color */
--Zeblit-white: #FFFFFF;        /* Pure white */
```

### UI Colors
```css
/* Form and Interactive Elements */
--form-focus-shadow: rgba(48, 56, 73, 0.1);
--text-primary: #303849;
--text-secondary: #6C757D;
--border-light: #E9ECEF;
--background-primary: #FFFFFF;
--background-secondary: #F4F4F2;
```

### Status Colors
```css
--success: #14A52C;
--error: #E74C3C;
--warning: #F39C12;
--info: #4A90E2;
```

## Typography

### Font Family
```css
/* Primary Fonts - Loaded from Zeblit */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter-VariableFont_slnt_wght.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;
}

@font-face {
  font-family: 'Libre Caslon Text';
  src: url('/fonts/LibreCaslonText-Regular.woff2') format('woff2');
  font-weight: 400;
  font-display: swap;
}

/* Font Stacks */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
--font-serif: 'Libre Caslon Text', Georgia, serif;
--font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
```

### Font Sizes (Mobile First)
```css
/* Typography Scale */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px - p-18 class */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */
--text-5xl: 3rem;       /* 48px */

/* Responsive Typography */
@media (min-width: 768px) {
  --text-3xl: 2rem;     /* 32px */
  --text-4xl: 2.5rem;   /* 40px */
  --text-5xl: 3.5rem;   /* 56px */
}
```

### Font Weights
```css
--font-light: 300;
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Line Heights
```css
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.6;
--leading-loose: 1.75;
```

## Spacing System
```css
/* Base spacing units */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-10: 2.5rem;   /* 40px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */
--space-20: 5rem;     /* 80px */

/* Component-specific spacing */
--component-padding: 2rem;
--component-padding-large: 3rem;
--component-padding-small: 1.5rem;
--section-spacing: 3rem 0;
```

## Layout System

### Container Widths
```css
--container-sm: 540px;
--container-md: 720px;
--container-lg: 960px;
--container-xl: 1140px;
--container-xxl: 1280px;
--container-fluid: 100%;
```

### Breakpoints (Bootstrap-based)
```css
--breakpoint-xs: 0;
--breakpoint-sm: 576px;
--breakpoint-md: 768px;
--breakpoint-lg: 992px;
--breakpoint-xl: 1200px;
--breakpoint-xxl: 1400px;
```

### Grid Gutters
```css
--grid-gutter: 1rem;    /* 16px between columns */
--grid-gutter-sm: 0.5rem;
--grid-gutter-lg: 1.5rem;
```

## Border & Radius
```css
/* Border Radius */
--radius-none: 0;
--radius-sm: 2px;        /* Zeblit uses minimal radius */
--radius-md: 4px;
--radius-lg: 8px;
--radius-full: 9999px;   /* For circular elements */

/* Borders */
--border-width: 1px;
--border-color: #E9ECEF;
--border-color-dark: rgba(48, 56, 73, 0.1);
```

## Shadows
```css
/* Subtle shadows aligned with Zeblit's clean aesthetic */
--shadow-sm: 0 1px 2px 0 rgba(48, 56, 73, 0.05);
--shadow-md: 0 4px 6px -1px rgba(48, 56, 73, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(48, 56, 73, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(48, 56, 73, 0.1);
--shadow-focus: 0 0 0 3px rgba(48, 56, 73, 0.1);
```

## Component Styles

### Buttons
```css
/* Primary Button (CTA Primary) */
.cta-primary {
  background-color: var(--Zeblit-dark-navy);
  color: white;
  padding: 0.75rem 2rem;
  border-radius: 2px;
  font-weight: 500;
  font-size: var(--text-base);
  border: 2px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
  text-transform: none;
  letter-spacing: normal;
}

.cta-primary:hover {
  background-color: transparent;
  color: var(--Zeblit-dark-navy);
  border-color: var(--Zeblit-dark-navy);
}

/* Secondary Button (Secondary CTA) */
.secondary-cta {
  background-color: transparent;
  color: var(--Zeblit-dark-navy);
  padding: 0.5rem 0;
  font-weight: 500;
  position: relative;
  display: inline-flex;
  align-items: center;
  transition: all 0.2s ease;
}

.secondary-cta::after {
  content: '→';
  margin-left: 0.5rem;
  transition: transform 0.2s ease;
}

.secondary-cta:hover::after {
  transform: translateX(4px);
}

/* Button Primary (Alternative Style) */
.button-primary {
  background-color: var(--Zeblit-dark-navy);
  color: white;
  padding: 0.875rem 2.5rem;
  border-radius: 2px;
  font-weight: 500;
  border: none;
  transition: all 0.2s ease;
}

/* Disabled State */
.cta-primary.disable {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### Forms
```css
/* Form Inputs */
.form__input,
.text-input__input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #E9ECEF;
  border-radius: 0;
  font-size: var(--text-base);
  transition: all 0.2s ease;
  background-color: white;
  font-family: var(--font-primary);
}

.form__input:focus,
.text-input__input:focus {
  outline: 1px solid transparent;
  border-color: var(--Zeblit-dark-navy);
  box-shadow: 0 0 0 3px var(--form-focus-shadow);
}

/* Form Labels */
.forms__label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
}

/* Select/Dropdown */
.forms__dropdown select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='24' height='25' viewBox='0 0 24 25' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M15 10.2456L12 7.24561L9 10.2456' stroke='%2330384A' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M9 14.2456L12 17.2456L15 14.2456' stroke='%2330384A' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 1rem center;
  padding-right: 3rem;
}
```

### Cards & Content Blocks
```css
/* Content Block */
.content-block {
  padding: 3rem 0;
}

.content-block__background {
  background-color: var(--Zeblit-stone);
  padding: 4rem 0;
}

/* Image Blocks */
.image-block {
  position: relative;
  min-height: 400px;
  background-size: cover;
  background-position: center;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.image-block:hover {
  transform: scale(1.02);
}

.image-block__details {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 2rem;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  color: white;
}

/* Cards with Borders */
.component-bordered {
  border: 1px solid #E9ECEF;
  border-radius: 4px;
  padding: 2rem;
}

.component-bordered--large {
  padding: 3rem;
}

.component-bordered--small {
  padding: 1.5rem;
}
```

## Animation & Transitions

### Timing Functions
```css
--transition-fast: 150ms;
--transition-base: 200ms;
--transition-slow: 300ms;
--transition-slower: 500ms;

/* Easing Functions */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-linear: linear;
```

### Standard Transitions
```css
/* Default transition for interactive elements */
.interactive-element {
  transition: all var(--transition-base) var(--ease-in-out);
}

/* Hover states */
a, button {
  transition: opacity var(--transition-base) ease,
              color var(--transition-base) ease,
              background-color var(--transition-base) ease,
              border-color var(--transition-base) ease,
              transform var(--transition-base) ease;
}

/* Focus transitions */
input, select, textarea {
  transition: border-color var(--transition-base) ease,
              box-shadow var(--transition-base) ease;
}
```

## Best Practices

### Mobile-First Responsive Design
- Start with mobile styles and enhance for larger screens
- Use the breakpoint system: 576px, 768px, 1024px, 1280px
- Test touch interactions on mobile devices

### Accessibility
- Include skip links for keyboard navigation
- Maintain WCAG 2.1 AA compliance (4.5:1 contrast ratio)
- Use semantic HTML5 elements
- Provide meaningful alt text for images
- Ensure all interactive elements are keyboard accessible
- Add proper ARIA labels where needed

### Performance
- Preload critical fonts
- Use responsive images with `<picture>` element
- Implement lazy loading for below-fold images
- Minimize CSS and JavaScript bundles
- Use CSS containment for complex components

### Content Strategy
- Follow the "Out of the Ordinary" messaging
- Use clear, concise copy
- Implement progressive disclosure for complex information
- Maintain consistent tone of voice

### Component Guidelines
- Keep components modular and reusable
- Follow BEM naming convention for CSS classes
- Document component variations and states
- Test components in isolation

## Design Principles

1. **Clarity Over Complexity**: Every element should serve a clear purpose
2. **Human-Centric**: Design for real people with real needs
3. **Trust Through Consistency**: Maintain visual and behavioral consistency
4. **Performance Matters**: Fast, responsive experiences build trust
5. **Accessible by Default**: Design for all users from the start
6. **Progressive Enhancement**: Start simple, enhance for capable browsers

This style guide provides a comprehensive foundation for creating an Zeblit-aligned Replit app while maintaining their distinctive brand identity and high standards for user experience.