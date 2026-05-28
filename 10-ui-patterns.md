# UI Patterns, Accessibility & Component Guidance
**Estate Asset Manager — Product & Engineering Deliverable 10**

---

## Executive Summary
This document defines the UI patterns for bulk editing, inline validation, mobile-first layout, accessibility requirements, and component library guidance for the Estate Asset Manager. Wireframe snippets and copy-ready microcopy are included throughout.

---

## 1. How to Complete This Template

1. **Align with your component library** first: map every pattern below to an existing component (MUI, Radix, shadcn/ui, etc.) before building custom components.
2. **Validate microcopy with users**: run 3–5 usability tests on error messages and empty states before shipping.
3. **Run an accessibility audit** against WCAG 2.1 AA on every new screen using axe DevTools or Lighthouse before each release.
4. **Test on real devices**: iOS Safari and Android Chrome are the minimum mobile targets; test at 320 px, 375 px, and 768 px widths.
5. **Add new patterns to this doc** before implementing them — prevents duplication and keeps the system consistent.
6. **Review with design and engineering** at the start of each sprint that touches the UI.

> **References**
> - WCAG 2.1 AA: https://www.w3.org/TR/WCAG21/
> - ARIA Authoring Practices Guide: https://www.w3.org/WAI/ARIA/apg/
> - Google Material Design (patterns reference): https://m3.material.io/
> - Inclusive Components (Heydon Pickering): https://inclusive-components.design/
> - Search: `bulk edit UI pattern UX design enterprise data table`
> - Search: `inline validation best practices form design site:nngroup.com`

---

## 2. Bulk Edit Pattern

### 2.1 Behavior Specification

| Behavior | Specification |
|---|---|
| Selection mechanism | Checkbox in first column of data table; "Select all on page" in table header |
| Selection limit | Max 500 records per bulk operation (enforce server-side; warn at 490) |
| Bulk action trigger | "Edit selected (N)" button appears in floating action bar when ≥ 1 row selected |
| Editable fields | Status, Category, Estate assignment, Tags (not: ID, Created date, Audit fields) |
| Confirmation | Modal summarizing: "You are about to update N assets. This cannot be undone for Status changes." |
| Partial failure | Return per-record result: show success count + error details in dismissible banner |
| Undo | Not supported for bulk operations — confirmation modal serves as the gate |
| Keyboard shortcut | `Ctrl/Cmd + A` selects all visible rows; `Escape` clears selection |

### 2.2 Wireframe — Bulk Edit Table

```
┌────────────────────────────────────────────────────────────────────┐
│  Assets  ›  All Assets                                             │
│                                         [+ Add Asset]  [⬇ Export] │
├──┬─────────────────┬──────────┬───────────┬────────────┬───────────┤
│☑ │ Asset Name      │ Category │ Status    │ Value      │ Actions   │
├──┼─────────────────┼──────────┼───────────┼────────────┼───────────┤
│☑ │ 123 Main St     │ Property │ APPROVED  │ $950,000   │ [Edit]    │
│☑ │ Tesla Model 3   │ Vehicle  │ DRAFT     │ $38,000    │ [Edit]    │
│☐ │ Chase Checking  │ Account  │ APPROVED  │ $24,500    │ [Edit]    │
│☑ │ Art Collection  │ Collecti │ PENDING   │ $120,000   │ [Edit]    │
├──┴─────────────────┴──────────┴───────────┴────────────┴───────────┤
│  [Select all 42]    Showing 1–25 of 42                  [◀] [1] [▶]│
└────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ☑ 3 assets selected    [Edit selected (3) ▼]    [Clear selection]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2.3 Bulk Edit Modal Wireframe

```
┌────────────────────────────────────────────────────────┐
│  Edit 3 assets                                    [✕]  │
├────────────────────────────────────────────────────────┤
│  Only fields you change will be updated.               │
│  Leave a field blank to keep existing values.          │
│                                                        │
│  Category        [──── Select category ────────────▼]  │
│                                                        │
│  Tags            [──── Add tags ─────────────── ✕ ──]  │
│                                                        │
│  Assigned Estate [──── Select estate ──────────────▼]  │
│                                                        │
├────────────────────────────────────────────────────────┤
│                      [Cancel]   [Apply to 3 assets →]  │
└────────────────────────────────────────────────────────┘
```

### 2.4 Bulk Edit Microcopy

| Context | Copy |
|---|---|
| Action bar (1 selected) | "1 asset selected" |
| Action bar (N selected) | "N assets selected" |
| Action bar (at limit) | "500 assets selected (maximum)" |
| Button label | "Edit selected (N)" |
| Modal title | "Edit N assets" |
| Modal subtitle | "Only fields you change will be updated. Leave a field blank to keep existing values." |
| Confirm button | "Apply to N assets →" |
| Success banner | "N assets updated successfully." |
| Partial failure banner | "N of M assets updated. X could not be updated — see details." |
| Error detail link | "Show details" / "Hide details" |
| Near-limit warning | "You've selected 490 assets. The maximum is 500." |

---

## 3. Inline Validation Pattern

### 3.1 Validation Timing Rules

| Trigger | Behavior |
|---|---|
| On blur (field loses focus) | Validate field; show error if invalid; show success checkmark if valid |
| On input (while typing) | Clear error if it becomes valid; do NOT show new errors while typing |
| On form submit | Validate all fields; scroll to first error; set `aria-invalid="true"` |
| Server-side error (API response) | Display server error below field; map field path to form control |

### 3.2 Validation States

| State | Visual | Icon | Color Token |
|---|---|---|---|
| Default | Standard border | None | `--color-border-default` |
| Focused | Highlighted border | None | `--color-border-focus` (blue) |
| Valid | Standard border | ✅ checkmark | `--color-success` (green) |
| Error | Red border | ⚠ icon | `--color-error` (red) |
| Warning | Amber border | ⚠ icon | `--color-warning` (amber) |
| Disabled | Muted border | None | `--color-border-disabled` |

### 3.3 Inline Validation Wireframe

```
  Asset Name *
  ┌──────────────────────────────────────────────────────┐
  │ 123 Main Street                                   ✅  │
  └──────────────────────────────────────────────────────┘

  Valuation Amount *
  ┌──────────────────────────────────────────────────────┐
  │ -500                                              ⚠  │
  └──────────────────────────────────────────────────────┘
  ⚠ Amount must be greater than 0.

  Notes
  ┌──────────────────────────────────────────────────────┐
  │ Appraised by certified appraiser on 04/30/2026.      │
  │                                                      │
  └──────────────────────────────────────────────────────┘
  480 / 500 characters
```

### 3.4 Inline Validation Microcopy

| Error | User-Facing Message |
|---|---|
| Required field empty | "This field is required." |
| Value below minimum | "Amount must be greater than [min]." |
| Value above maximum | "Amount must be less than [max]." |
| Invalid date format | "Enter a date in MM/DD/YYYY format." |
| Future date required | "Valuation date cannot be in the past." |
| Text too long | "[Field] must be [N] characters or fewer." |
| Invalid email format | "Enter a valid email address (e.g., name@domain.com)." |
| Duplicate name | "An asset with this name already exists in this estate." |
| Server-side generic | "Something went wrong. Please try again or contact support." |

---

## 4. Mobile-First Considerations

### 4.1 Breakpoint System

| Breakpoint | Min Width | Layout |
|---|---|---|
| `xs` | 320 px | Single column; stacked form fields; bottom sheet for modals |
| `sm` | 375 px | Single column; card-based asset list |
| `md` | 768 px | 2-column layout; side-by-side form fields |
| `lg` | 1024 px | Full sidebar + content layout; data table visible |
| `xl` | 1280 px | Full dashboard; multi-panel layout |

### 4.2 Mobile UI Rules

| Rule | Implementation |
|---|---|
| Touch targets | Minimum 44 × 44 px (Apple HIG); 48 × 48 dp (Material Design) |
| Data tables on mobile | Replace table with card list on xs/sm; show 3–4 key fields per card |
| Bulk edit on mobile | Use long-press to enter selection mode; floating action button replaces action bar |
| Modals on mobile | Full-screen bottom sheet instead of centered modal on xs/sm |
| Navigation | Bottom tab bar on xs/sm; sidebar on md+ |
| Form fields | Full-width inputs on xs/sm; use native date/select pickers on mobile |
| Loading states | Skeleton screens preferred over spinners for content areas |

### 4.3 Mobile Asset Card Wireframe

```
┌──────────────────────────────────────────────┐
│  📦 123 Main Street          [APPROVED] ●    │
│  Property  ·  Maple Estate                   │
│                              $950,000 USD     │
│  Last synced: 2 hours ago          [Edit ▶]  │
└──────────────────────────────────────────────┘
┌──────────────────────────────────────────────┐
│  🚗 Tesla Model 3             [DRAFT] ○      │
│  Vehicle  ·  Maple Estate                    │
│                               $38,000 USD     │
│  Not yet synced                    [Edit ▶]  │
└──────────────────────────────────────────────┘
```

---

## 5. Accessibility Checklist (WCAG 2.1 AA)

### 5.1 Per-Screen Checklist

Run this before every screen ships to production:

| Category | Check | Pass? |
|---|---|---|
| **Perceivable** | All images have descriptive `alt` text (or `alt=""` for decorative) | `[ ]` |
| **Perceivable** | Color is never the sole means of conveying information (e.g., error also has icon + text) | `[ ]` |
| **Perceivable** | Minimum contrast ratio 4.5:1 for normal text; 3:1 for large text | `[ ]` |
| **Perceivable** | All video/audio has captions or transcripts (if applicable) | `[ ]` |
| **Operable** | All interactive elements are keyboard-focusable in logical order | `[ ]` |
| **Operable** | Focus indicator is visible on all interactive elements | `[ ]` |
| **Operable** | No keyboard traps (user can exit any modal/drawer with `Escape`) | `[ ]` |
| **Operable** | Skip-to-content link is the first focusable element on each page | `[ ]` |
| **Operable** | Touch targets ≥ 44 × 44 px on mobile | `[ ]` |
| **Understandable** | All form fields have visible `<label>` or `aria-label` | `[ ]` |
| **Understandable** | Error messages are descriptive and linked to the field via `aria-describedby` | `[ ]` |
| **Understandable** | Language is declared on `<html lang="en">` | `[ ]` |
| **Robust** | No ARIA roles conflict with native semantics | `[ ]` |
| **Robust** | Screen reader announces dynamic content changes via `aria-live` regions | `[ ]` |
| **Robust** | All status messages (toast, banner) use `role="status"` or `aria-live="polite"` | `[ ]` |
| **Robust** | Automated axe DevTools scan passes with 0 critical / 0 serious violations | `[ ]` |

### 5.2 Accessible ARIA Patterns

| Component | ARIA Pattern | Key Requirements |
|---|---|---|
| Data table with bulk select | `role="grid"` | `aria-multiselectable="true"`; row checkboxes have `aria-label="Select [asset name]"` |
| Confirmation modal | `role="dialog"` | `aria-modal="true"`; `aria-labelledby` → modal title; focus trapped inside; `Escape` closes |
| Inline error message | `role="alert"` or linked via `aria-describedby` | Error text ID matches `aria-describedby` on input |
| Status badge (Approved/Draft) | `<span>` with visible text | Do not use color alone; include text label |
| Loading skeleton | `aria-busy="true"` on container | Announce "Loading assets…" via `aria-live="polite"` region |
| Toast notifications | `role="status"` for info/success; `role="alert"` for errors | Auto-dismiss after 5 s; include close button |
| Dropdown / combobox | ARIA combobox pattern | Full keyboard nav; `aria-expanded`; `aria-activedescendant` |

---

## 6. Component Library Guidance

### 6.1 Recommended Component Mapping

| UI Pattern | Component (if using shadcn/ui) | Component (if using MUI) | Notes |
|---|---|---|---|
| Data table | `<DataTable>` + TanStack Table | `<DataGrid>` (MUI X) | Enable virtualization for > 500 rows |
| Bulk select | Custom `<Checkbox>` in table header + rows | `<DataGrid checkboxSelection>` | Keyboard: `Space` to toggle row |
| Inline validation | `<FormField>` + `<FormMessage>` | `<TextField error helperText>` | Drive from react-hook-form + Zod |
| Modal / dialog | `<Dialog>` (Radix UI) | `<Dialog>` (MUI) | Always trap focus; `Escape` to close |
| Bottom sheet (mobile) | `<Drawer direction="bottom">` | `<SwipeableDrawer anchor="bottom">` | Use for modals on xs/sm breakpoints |
| Toast notification | `<Sonner>` or `<Toast>` (Radix) | `<Snackbar>` (MUI) | Max 3 visible at once; auto-dismiss 5 s |
| Badge / status pill | `<Badge>` | `<Chip>` | Never color-only: always include text |
| Skeleton loader | `<Skeleton>` | `<Skeleton>` | Match exact shape of loaded content |
| Floating action bar | Custom `<div>` fixed to bottom | Custom `<Paper elevation>` | `z-index` above table; dismissible |

### 6.2 Design Token Naming Convention

```css
/* Status colors — always paired with text/icon, never color alone */
--color-status-draft:     #6b7280;  /* gray */
--color-status-pending:   #f59e0b;  /* amber */
--color-status-approved:  #10b981;  /* green */
--color-status-failed:    #ef4444;  /* red */
--color-status-archived:  #9ca3af;  /* light gray */
--color-status-locked:    #8b5cf6;  /* purple */

/* Feedback colors */
--color-error:    #ef4444;
--color-warning:  #f59e0b;
--color-success:  #10b981;
--color-info:     #3b82f6;

/* Borders */
--color-border-default:   #d1d5db;
--color-border-focus:     #3b82f6;
--color-border-error:     #ef4444;
--color-border-disabled:  #e5e7eb;
```

---

## 7. Empty States & Onboarding Microcopy

| Screen | Empty State Heading | Empty State Subtext | Primary CTA |
|---|---|---|---|
| Asset list (no assets yet) | "No assets yet" | "Add your first asset to start building your estate inventory." | "Add asset" |
| Asset list (filtered, no results) | "No assets match your filters" | "Try adjusting your search or removing a filter." | "Clear filters" |
| Connector list (none configured) | "No connectors configured" | "Connect your accounting system or IoT devices to keep your assets in sync." | "Add connector" |
| Reports (no data) | "No data to report" | "Reports will appear once assets are added and approved." | "Add asset" |
| Audit log (no events) | "No audit events" | "Audit events will appear as users take actions in the system." | — |
| Sync failed state | "Sync paused" | "We couldn't reach your accounting system. Check your connection settings or contact your admin." | "Review connector" |

---

## 8. Microcopy Style Guide

| Principle | Rule | Example |
|---|---|---|
| Active voice | Use subject-verb-object | "Save your changes" not "Changes will be saved" |
| Sentence case | Headlines and buttons in sentence case | "Edit asset" not "Edit Asset" |
| Contractions | Use them for friendliness | "We couldn't" not "We could not" |
| Error messages | Say what happened + what to do | "Name is required. Enter a name for this asset." |
| Destructive actions | Name the consequence | "Archive this asset?" not "Are you sure?" |
| Loading states | Be specific | "Loading assets…" not "Loading…" |
| Success states | Confirm what happened | "Asset approved and live." not "Success!" |
| Avoid jargon | Use plain English | "Connected accounts" not "OAuth provider integrations" |

---

*Last updated: 2026-05-28 | Owner: `[Design Lead / Frontend Engineering Lead]` | Review cycle: Each sprint that ships new UI screens*
