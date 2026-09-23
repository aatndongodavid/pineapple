---
name: Academic Excellence & Professionalism
colors:
  surface: '#f6fafe'
  surface-dim: '#d6dade'
  surface-bright: '#f6fafe'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f4f8'
  surface-container: '#eaeef2'
  surface-container-high: '#e4e9ed'
  surface-container-highest: '#dfe3e7'
  on-surface: '#171c1f'
  on-surface-variant: '#404944'
  inverse-surface: '#2c3134'
  inverse-on-surface: '#edf1f5'
  outline: '#707974'
  outline-variant: '#bfc9c3'
  surface-tint: '#2a6954'
  primary: '#003527'
  on-primary: '#ffffff'
  primary-container: '#044e3b'
  on-primary-container: '#7fbea6'
  inverse-primary: '#94d4ba'
  secondary: '#006c4b'
  on-secondary: '#ffffff'
  secondary-container: '#64f9bc'
  on-secondary-container: '#00714e'
  tertiary: '#00352d'
  on-tertiary: '#ffffff'
  tertiary-container: '#004e43'
  on-tertiary-container: '#5cc3af'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#aff0d6'
  primary-fixed-dim: '#94d4ba'
  on-primary-fixed: '#002117'
  on-primary-fixed-variant: '#09513e'
  secondary-fixed: '#68fcbf'
  secondary-fixed-dim: '#45dfa4'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#005137'
  tertiary-fixed: '#8ef5df'
  tertiary-fixed-dim: '#72d8c3'
  on-tertiary-fixed: '#00201b'
  on-tertiary-fixed-variant: '#005045'
  background: '#f6fafe'
  on-background: '#171c1f'
  surface-variant: '#dfe3e7'
  deep-pineapple-blue: '#011411'
  surface-white: '#FFFFFF'
  ink-dark: '#011411'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  title-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
  max-width: 1280px
---

## Brand & Style

The design system is engineered for high-achieving individuals within a university ecosystem, blending the prestige of institutional infrastructure with the distinctive flair of a personal brand. The aesthetic is **Modern Corporate**, characterized by precision, clarity, and structural integrity. 

The personality is authoritative yet approachable, utilizing a "High-End Editorial" approach to digital layouts. It avoids decorative clutter in favor of meaningful whitespace and rigorous grid alignment. The emotional response should be one of immediate trust, intellectual rigor, and sophisticated modernism. This is achieved through refined typography, a deep-toned color palette, and subtle, high-quality surface treatments.

## Colors

The palette is anchored by "Deep Pineapple Blue" (#011411) and "Pineapple Green" (#044E3B), creating a foundation of stability and growth. 

- **Primary & Secondary:** Use the Deep Green and Blue for structural elements, headers, and high-emphasis backgrounds. The "Smart Green" (#34D399) serves as a precision accent for interactive highlights and success states.
- **Surface Strategy:** The primary background is the near-white #F1F5F9, which provides a soft, paper-like quality that reduces eye strain compared to pure white.
- **Contrast:** High contrast is reserved for typography to ensure maximum readability. Use the Deep Blue for all primary text to maintain a premium "ink" feel.

## Typography

The design system utilizes **Hanken Grotesk** exclusively to maintain a sharp, technical, and contemporary feel. The type hierarchy is heavily influenced by modernist Swiss design.

- **Scale:** Large display sizes should use tighter letter spacing to create a cohesive visual block. 
- **Hierarchy:** Use the "Label-Caps" style for categories, breadcrumbs, and small metadata to distinguish them from the narrative flow of the body text.
- **Readability:** Body text is set with a generous line height (1.5x - 1.6x) to ensure academic papers or long-form portfolio descriptions remain legible.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy for desktop to maintain a premium "gallery" feel, transitioning to a fluid system for smaller viewports.

- **Grid:** A 12-column grid is used for desktop (1024px+). For portfolio showcases, elements should often span 6 or 8 columns to create intentional asymmetry and white space.
- **Rhythm:** An 8px linear scale (4px base) governs all padding and margins. 
- **Sectioning:** Vertical rhythm is aggressive; use large 80px - 120px gaps between major sections to allow the content to breathe and signify a change in context.

## Elevation & Depth

This design system eschews traditional shadows in favor of **Tonal Layers** and **Low-Contrast Outlines**.

- **Surfaces:** Depth is communicated by shifting background colors. A primary surface (#F1F5F9) may host a card with a pure white background to indicate elevation.
- **Borders:** Use subtle 1px borders in #0B8A78 at low opacity (10-15%) to define boundaries without adding visual weight.
- **Interactions:** On hover, elements should not "lift" with shadows but rather shift in tone or gain a slightly more defined border to maintain the flat, architectural aesthetic.

## Shapes

The shape language is "Soft" (0.25rem/4px). This minimal rounding removes the clinical harshness of sharp corners while maintaining a professional, structured appearance. 

- **Consistency:** All containers, buttons, and input fields must share the same base radius. 
- **Exceptions:** Icons and small tags may use a pill-shape (radius 999px) to contrast against the more rigid structural elements.

## Components

- **Buttons:** Primary buttons use the Deep Green background with white text. They should be rectangular with the system-standard 4px radius. Use a subtle "inset" border on hover rather than a shadow.
- **Input Fields:** Use a white background with a very light neutral border. On focus, the border transitions to the "Smart Green" accent.
- **Cards:** Cards should be "Ghost" style (no background, just a thin border) or "Surface" style (pure white background on the #F1F5F9 page background). No shadows are permitted.
- **Chips/Tags:** Used for skills or project categories. Use high-contrast combinations like the Deep Blue background with Smart Green text at small sizes.
- **Lists:** Use custom bullet points (small squares or dashes) in the Smart Green accent color to tie into the brand.
- **Portfolio Specifics:** Include a "Project Header" component that utilizes the Display-LG type and a full-bleed image container with minimal margins.