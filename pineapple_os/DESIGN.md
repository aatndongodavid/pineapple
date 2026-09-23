---
name: Pineapple OS
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#42474d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#73777e'
  outline-variant: '#c2c7ce'
  surface-tint: '#40627e'
  primary: '#001626'
  on-primary: '#ffffff'
  primary-container: '#002b45'
  on-primary-container: '#7293b2'
  inverse-primary: '#a8caeb'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#0c1800'
  on-tertiary: '#ffffff'
  tertiary-container: '#1c2e00'
  on-tertiary-container: '#6a9f00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cce5ff'
  primary-fixed-dim: '#a8caeb'
  on-primary-fixed: '#001d31'
  on-primary-fixed-variant: '#274a65'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#b2f746'
  tertiary-fixed-dim: '#98da27'
  on-tertiary-fixed: '#121f00'
  on-tertiary-fixed-variant: '#334f00'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  title-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding-desktop: 40px
  container-padding-mobile: 20px
  gutter: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The design system is a high-performance ecosystem built for the modern academic landscape. It merges the spatial depth and refined translucency of **Glassmorphism** with the rigorous functional clarity of premium **SaaS** platforms. 

The brand personality is **Visionary, Academic, and Vital**. It aims to evoke a sense of professional reliability (Trustworthy) while maintaining the high-energy pulse of a living campus community (Energetic). By utilizing light-refracting surfaces and deep chromatic contrast, the UI creates a "Smart Campus" atmosphere—one that feels like a physical space translated into a digital high-performance tool.

**Key Visual Principles:**
- **Atmospheric Depth:** Use of background blurs and layered transparency to indicate hierarchy.
- **Precision Engineering:** Sharp typography and intentional use of negative space to prevent information overload.
- **Vibrant Logic:** Color is used functionally to categorize user roles and system states, ensuring the interface is as intuitive as it is beautiful.

## Colors

This design system utilizes a high-contrast palette where the **Deep Pineapple Blue** serves as the grounding anchor for navigation and primary text, while the **Smart Green** and **Lime** accents inject energy and represent academic "growth."

### Color Application
- **Primary (#002B45):** Structural elements, headers, and high-emphasis typography.
- **Secondary (#10B981):** Success states, progress indicators, and "Teacher" role identifiers.
- **Accent (#A3E635):** High-visibility highlights, active election states, and call-to-action micro-elements.
- **Technology (#22D3EE):** Digital interactions, "Student" role identifiers, and connectivity status.

### Surface Tiers
To achieve the "visionOS" aesthetic, surfaces are defined by opacity levels rather than flat hex codes:
- **Bright:** Used for foreground cards and active modal content.
- **Dim:** Used for secondary sidebars or grouping elements.
- **Container:** Used for background canvas sections to provide subtle texture through backdrop filtering.

## Typography

The typographic scale emphasizes a strong vertical hierarchy. **Hanken Grotesk** is chosen for its sharp, contemporary geometry, providing a premium "tech-first" feel for headlines. **Inter** handles body copy to ensure maximum legibility across dense SaaS data views. **Geist** is used for labels and technical metadata, lending a precise, developer-centric aesthetic to status badges and roles.

**Usage Notes:**
- **High Contrast:** Always maintain a significant weight difference between titles (Bold/Black) and body text (Regular).
- **Type as UI:** Labels for user roles (e.g., "STUDENT") should always use the `label-sm` style with Geist to emphasize the "Smart Platform" identity.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** model with "Large Breathing Spaces." It uses a 12-column system for desktop and a 4-column system for mobile. 

The rhythm is based on a **4px baseline grid**. Components should prioritize generous internal padding (standardizing on 24px or 32px for cards) to maintain the premium, airy feel of the brand.

**Adaptive Rules:**
- **Desktop:** Floating panels with a max-width of 1440px, centered.
- **Tablet:** Sidebars collapse into a "compact" mode (icon only).
- **Mobile:** Margins reduce to 20px, and all floating cards become full-width with standard 16px horizontal safe-areas.

## Elevation & Depth

This design system uses **Glassmorphism** as its primary method of conveying depth. Visual hierarchy is achieved through cumulative backdrop blurs rather than heavy shadows.

- **Level 0 (Canvas):** Solid background or subtle mesh gradient using Primary and Secondary hues at 5% opacity.
- **Level 1 (Secondary Panels):** `backdrop-filter: blur(20px)`; `background: rgba(255, 255, 255, 0.4)`.
- **Level 2 (Floating Cards):** `backdrop-filter: blur(40px)`; `background: rgba(255, 255, 255, 0.8)`; `box-shadow: 0 10px 30px rgba(0, 43, 69, 0.05)`.
- **Level 3 (Modals/Popovers):** `backdrop-filter: blur(60px)`; `background: #FFFFFF`; `box-shadow: 0 20px 50px rgba(0, 43, 69, 0.1)`.

All elevated elements must feature a **1px semi-transparent border** (`rgba(255, 255, 255, 0.5)`) to act as a "specular highlight," mimicking the edge of a glass pane.

## Shapes

The shape language is **Rounded (Level 2)** to balance the professional nature of the platform with an approachable, friendly community vibe. 

- **Standard Elements (Buttons, Inputs):** 0.5rem (8px).
- **Standard Cards:** 1rem (16px).
- **Large Layout Containers (Main Dashboard Area):** 1.5rem (24px).
- **Avatars & Status Badges:** Circular (Full pill) to contrast against the geometric grid.

## Components

### Floating Cards
The signature component. Must include a `1px` border stroke and a `40px` backdrop blur. Content should have at least `24px` of internal padding.

### Status Badges
- **Verified Student:** Pill-shaped, Primary Blue background with Technology Cyan icon.
- **Active Election:** Pill-shaped, Accent Lime background with black text for maximum urgency.
- **Room Availability:** Small circular indicator. Green (#10B981) for "Available," Red for "Occupied."

### Buttons
- **Primary:** Solid Deep Pineapple Blue (#002B45) with white text. High-performance feel.
- **Secondary:** Ghost style with a Smart Green (#10B981) border and text.
- **Tertiary:** Glass-style with a subtle white semi-transparent fill and blur.

### Role Tags
Used to identify users in community feeds:
- **Admin:** Gold/Amber fill, Geist font.
- **Student:** Technology Cyan fill, Geist font.
- **Teacher:** Smart Green fill, Geist font.

### Input Fields
Soft white backgrounds (0.9 opacity) with a `2px` focus ring in Technology Cyan. Labels are always `label-sm` style positioned above the field.