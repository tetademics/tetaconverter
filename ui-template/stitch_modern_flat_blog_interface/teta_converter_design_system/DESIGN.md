---
name: Teta Converter Design System
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#464555'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#7e3000'
  on-tertiary: '#ffffff'
  tertiary-container: '#a44100'
  on-tertiary-container: '#ffd2be'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdbcc'
  tertiary-fixed-dim: '#ffb695'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7b2f00'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
  text-primary: '#1E293B'
  text-secondary: '#64748B'
  border-subtle: '#E2E8F0'
  surface-white: '#FFFFFF'
  error-red: '#EF4444'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
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
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
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
  container-max: 1200px
  article-max: 720px
  gutter: 1.5rem
  section-gap: 4rem
  element-gap: 1rem
  margin-mobile: 1rem
---

## Brand & Style

The design system is anchored in the concept of **Utilitarian Precision**. It aims to evoke a sense of speed, reliability, and technical sophistication through a "Flat-Plus" aesthetic—where minimalism meets functional depth. The UI prioritizes the user's task (conversion) by stripping away decorative elements in favor of high-contrast typography and intentional whitespace.

The visual direction combines **Minimalism** with **Corporate Modern** sensibilities. It avoids the heaviness of skeuomorphism, opting instead for crisp edges, subtle 1px borders, and a monochromatic foundation punctuated by a singular, vibrant accent color. The goal is to make the tool feel like a professional instrument rather than a casual utility.

## Colors

The palette is designed for maximum clarity and high legibility. 
- **Primary Indigo (#4F46E5):** Used for primary actions, active tab states, and focus indicators. It represents the "tech-forward" energy of the brand.
- **Surface & Background:** The system utilizes a pure White (#FFFFFF) for the main canvas and a "Very Light Gray" (#F8F9FA) for secondary surfaces like sidebar navigation, input backgrounds, and inactive tab states.
- **Typography:** We use a Slate scale. **Slate 800 (#1E293B)** provides high-contrast for headings and body text, while **Slate 500 (#64748B)** is reserved for meta-information and labels.
- **Success & Error:** Emerald Green is used strictly for successful conversion indicators, while a vibrant Red is used for validation errors and destructive actions.

## Typography

The design system uses **Inter** exclusively to ensure a systematic and utilitarian feel across all platforms. 

### Scale & Hierarchy
- **Headlines:** Use Bold (700) or Semi-Bold (600) weights with slightly tightened letter spacing to create a compact, authoritative look.
- **Body Text:** Standard body text is set to 16px for optimal readability. For article layouts, the `body-lg` (18px) size is used to reduce eye strain during long-form reading.
- **Technical Labels:** Small caps or medium-weight labels (12px-14px) are used for metadata like file sizes, bitrates, and timestamps.

### Readable Article Layouts
For the blog and article sections, the line length is strictly capped at **720px** to maintain a comfortable "words-per-line" ratio, with generous line heights (1.6x).

## Layout & Spacing

This design system employs a **Fixed Grid** approach for desktop views to ensure technical tools (like the converter dropzone) remain centered and focused.

- **Grid System:** A 12-column grid with a 24px gutter.
- **Desktop:** Elements are contained within a 1200px central wrapper.
- **Article View:** Content shifts to a single-column 720px centered layout.
- **Rhythm:** We use an 8px base unit. All margins and paddings must be multiples of 8 (e.g., 8, 16, 24, 32, 48, 64).
- **Responsive Behavior:** 
    - **Desktop (1024px+):** Full 12-column display.
    - **Tablet (768px - 1023px):** 12-column grid with 40px side margins.
    - **Mobile (<767px):** Single-column stack with 16px side margins. Horizontal tabs become a scrollable list.

## Elevation & Depth

To maintain a "flat" professional look, depth is communicated through **Tonal Layering** and **Low-Contrast Outlines** rather than heavy shadows.

1.  **Level 0 (Background):** #FFFFFF.
2.  **Level 1 (Surface):** #F8F9FA. Used for secondary containers or the background of the conversion tool area.
3.  **Outlines:** Most components (cards, inputs, dropzones) use a 1px border (#E2E8F0).
4.  **Shadows:** Shadows are used sparingly. Only "floating" elements like modals or dropdown menus receive a shadow: `0 10px 15px -3px rgba(0, 0, 0, 0.05)`. This is a soft, diffused "ambient" shadow that doesn't break the flat aesthetic.
5.  **Interactive States:** On hover, cards may transition from a 1px border to a slightly deeper 2px primary-colored border or a very subtle lift (y-2px).

## Shapes

The design system uses a **Rounded** shape language to soften the technical nature of the application and make it more approachable.

- **Standard Radius:** 8px (`0.5rem`) for buttons, input fields, and small cards.
- **Large Radius:** 16px (`1rem`) for the main converter container and large blog thumbnails.
- **Full Radius:** Used for status badges/chips and "Buy me a coffee" pill buttons to distinguish them as secondary or unique call-to-actions.

All borders are consistently 1px wide, except for focus states which increase to 2px.

## Components

### File Dropzone
The centerpiece of the system. It features a dashed 2px border (#CBD5E1), a large central icon in Primary Indigo, and a clear "Click to upload" instruction. On drag-over, the background shifts to a very light Primary tint (e.g., Indigo at 5% opacity).

### Tabs
Tabs are styled as a horizontal pill-group. The active tab has a solid Primary Indigo background with white text, while inactive tabs use a transparent background with Slate 600 text.

### Buttons
- **Primary:** Solid Indigo background, white text, 8px radius.
- **Secondary (Download):** Solid Emerald Green background, white text.
- **Tertiary (Skip):** Ghost style—outlined with Slate 300 or plain text with an underline.

### Blog Cards
Horizontal or vertical orientation. They feature a clean 1px border, a 16px rounded thumbnail, a `headline-md` title, and a `body-md` excerpt in Slate 500.

### Input Fields
Outlined style. 1px border (#E2E8F0) that turns Indigo on focus. Background is #FFFFFF. 

### Modals (Donation)
Centered, white background, high-level elevation shadow. The "Buy me a coffee" action should be the most prominent visual element, using a pill-shaped button.