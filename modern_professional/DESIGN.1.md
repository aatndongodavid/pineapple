---
name: Modern Professional
colors:
  surface: '#f9f9ff'
  surface-dim: '#d7dae3'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f1f3fc'
  surface-container: '#ebedf7'
  surface-container-high: '#e6e8f1'
  surface-container-highest: '#e0e2eb'
  on-surface: '#181c22'
  on-surface-variant: '#414753'
  inverse-surface: '#2d3037'
  inverse-on-surface: '#eef0fa'
  outline: '#717785'
  outline-variant: '#c1c6d5'
  surface-tint: '#005db8'
  primary: '#005ab4'
  on-primary: '#ffffff'
  primary-container: '#0a73e0'
  on-primary-container: '#fefcff'
  inverse-primary: '#aac7ff'
  secondary: '#465f88'
  on-secondary: '#ffffff'
  secondary-container: '#b6d0ff'
  on-secondary-container: '#3f5881'
  tertiary: '#964400'
  on-tertiary: '#ffffff'
  tertiary-container: '#bd5700'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#aac7ff'
  on-primary-fixed: '#001b3e'
  on-primary-fixed-variant: '#00458d'
  secondary-fixed: '#d6e3ff'
  secondary-fixed-dim: '#aec7f7'
  on-secondary-fixed: '#001b3d'
  on-secondary-fixed-variant: '#2d476f'
  tertiary-fixed: '#ffdbc9'
  tertiary-fixed-dim: '#ffb68c'
  on-tertiary-fixed: '#321200'
  on-tertiary-fixed-variant: '#763400'
  background: '#f9f9ff'
  on-background: '#181c22'
  surface-variant: '#e0e2eb'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin: 24px
---

# Design System: Modern Professional

## Brand & Style
The brand identity has shifted from a warm, energetic orange palette to a cool, dependable, and professional blue aesthetic. The visual style is rooted in **Corporate / Modern** principles, emphasizing reliability, clarity, and precision. It leverages the "fidelity" color variant to ensure a high-quality, systematic appearance that feels balanced and trustworthy.

The target audience consists of professionals and enterprise users who value efficiency and clarity. The UI evokes a sense of calm intelligence and technical proficiency through its clean lines and cool tones.

## Colors
The color palette is led by a vibrant **Primary Blue (#1275e2)**, providing a modern and accessible foundation for action and focus. The **Secondary Muted Blue (#5f78a3)** adds professional depth without competing for attention, while the **Tertiary Rust/Orange (#c55b00)** serves as a high-contrast accent for specialized notifications or distinct UI elements.

Neutral tones are anchored by a **Cool Grey (#74777f)**, ensuring that backgrounds and structural elements remain sophisticated and recessive. This "fidelity" approach ensures that semantic meaning is preserved while maintaining a high aesthetic standard.

## Typography
The system has transitioned to **Inter** for all typographic roles. Inter provides exceptional legibility and a contemporary technical feel that complements the new blue-centric color palette. 

- **Headlines:** Use semi-bold weights to establish a clear hierarchy.
- **Body:** Uses standard weights with generous line heights to ensure readability in data-heavy views.
- **Labels:** Set in medium weights to maintain clarity at smaller scales.

The scale is designed to be responsive, with large headlines adjusting for mobile contexts to maintain accessibility.

## Layout & Spacing
The layout follows a **Fluid Grid** philosophy with a base 8px spatial rhythm. This ensures consistency across all components and page structures. 

- **Desktop:** 12-column grid with 24px margins.
- **Tablet:** 8-column grid with 16px margins.
- **Mobile:** 4-column grid with 16px margins.

Spacing increments are strictly adhered to, creating a predictable visual cadence that supports the professional brand personality.

## Elevation & Depth
Visual hierarchy is conveyed through **Tonal Layers** and subtle **Ambient Shadows**. Surfaces are tiered based on their proximity to the user, with higher elevation elements receiving softer, more diffused shadows. The cool neutral palette allows for "surface-container" tiers that create depth without relying on heavy borders, maintaining a modern and open feel.

## Shapes
The design system now utilizes a **Rounded (Level 2)** shape language. This introduces a 0.5rem (8px) base radius for standard components like buttons and input fields, moving away from the previous sharp-edged aesthetic.

- **Standard components:** 0.5rem (8px)
- **Large components (Cards):** 1rem (16px)
- **Extra-large (Dialogs):** 1.5rem (24px)

This change softens the professional aesthetic, making the interface feel more approachable and modern.

## Components
- **Buttons:** Feature the primary blue fill with 8px rounded corners. Primary actions use high-emphasis fills, while secondary actions use the secondary blue in an outlined or ghost format.
- **Input Fields:** Utilize the Inter font for labels and values, with a subtle 1px border in the neutral cool-grey tone and an 8px radius.
- **Cards:** Employ level 2 roundedness (16px) with very soft ambient shadows to define depth against the light background.
- **Chips & Labels:** Use the tertiary rust color sparingly for highlighting status or categories that need to stand out from the primary blue theme.