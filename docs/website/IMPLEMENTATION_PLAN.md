# Implementation Plan — Master Prompt 07: Site Vitrine et Kit de Vente

**Document Ref:** `docs/website/IMPLEMENTATION_PLAN.md`  
**Target Completion:** Master Prompt 07  
**Status:** In Progress (Phase P0)  

---

## 1. Validation Gates (W1 to W9)

| Gate # | Target & Description | Validation Phase |
|---|---|---|
| **W1** | **Lighthouse Mobile Score $\ge 95$** across 5 main pages (Home, Features, Security, Pricing, Demo). | Phase P6 |
| **W2** | **Demo Request Pipeline**: Valid submission saved to DB, notification email sent, visible in Admin Console. | Phase P3 |
| **W3** | **Anti-Spam Filter**: Honeypot & rate-limiting block automated bot submissions. | Phase P3 |
| **W4** | **Rule V3 Zero Fake Proof**: 0 fake logos/testimonials; social proof sections hidden in prod unless toggled. | Phase P5 |
| **W5** | **Demo Environment Isolation**: Nightly auto-reset, floating banner, restricted demo permissions. | Phase P4 |
| **W6** | **Bilingual i18n Parity**: 100% content parity in French (`/fr`) and English (`/en`) with `hreflang`. | Phase P1 |
| **W7** | **Accessibility Audit**: Zero critical AA violations under keyboard and screen-reader navigation. | Phase P6 |
| **W8** | **Slow 4G Loading**: Main above-the-fold content visible in < 3s on simulated mobile network. | Phase P6 |
| **W9** | **Zero Broken Links**: Automated link crawler & screenshot freshness check passed. | Phase P6 |

---

## 2. Phase-by-Phase Roadmap

### Phase P0: Audit & Planning
- [x] Baseline check & git branch `feature/site-vitrine-et-kit-de-vente` with tag `baseline-site-vitrine-et-kit-de-vente`.
- [x] Produce `ARCHITECTURE_WEBSITE.md`, `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`.
- [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`.

### Phase P1: Website Foundation, Astro/Tailwind Setup, i18n & SEO
- [ ] Initialize `website/` with Astro + TailwindCSS design system.
- [ ] Configure bilingual routing (`/fr`, `/en`), `hreflang` tags, `sitemap.xml`, `robots.txt`, and OpenGraph metadata.
- [ ] **Validation Gate W6**: Verify bilingual parity and routing.

### Phase P2: Content Drafting & Sales Kit Production (`docs/sales/`)
- [ ] Write 10 core pages in French and English (Home, Features by profile, Security, Pricing, Demo, Students/Families, About/Contact, FAQ $\ge 15$ Qs, Legal, Blog $\ge 3$ articles).
- [ ] Draft complete sales kit in `docs/sales/`: `PITCH.md` (12 slides), `ONE_PAGER.md`, `OBJECTIONS.md`, `ONBOARDING_CHECKLIST.md`, `EMAIL_TEMPLATES.md`, `TRAINING_OUTLINE.md`, `ANNOUNCEMENT_KIT.md`, `PRICING_SHEET.md`, `modele_import_registre.csv`, `modele_import_planning.csv`.

### Phase P3: Demo Request API & Super-Admin Console
- [ ] Create `DemoRequestModel` & migration `alembic/versions/0006_demo_requests.py`.
- [ ] Implement `POST /api/v1/public/demo-requests` with honeypot & IP rate-limiting (**Gate W3**).
- [ ] Implement confirmation email + internal sales alert via `EmailGateway`.
- [ ] Implement Admin Console endpoints `GET /api/v1/admin/demo-requests` and CSV export.
- [ ] **Validation Gate W2 & W3**: Test demo request pipeline & honeypot anti-spam.

### Phase P4: Demo Environment, Nightly Auto-Reset & Safety Locks
- [ ] Seed fictional demo tenant "Établissement Démo Pineapple" (60 students, 4 classes, 8 rooms, 1 timetable, polls, delegate, visitor ads).
- [ ] Implement nightly auto-reset script `scripts/reset_demo_tenant.py`.
- [ ] Implement demo account safety locks (prevent password changes, real payments, real SMS) and persistent floating banner.
- [ ] Write 10-minute demo script `docs/sales/DEMO_SCRIPT.md`.
- [ ] **Validation Gate W5**: Verify demo tenant isolation & auto-reset task.

### Phase P5: Real Product Screenshots & Social Proof Flag (Rule V3)
- [ ] Capture real screenshots of Pineapple OS web application.
- [ ] Implement `SocialProofPlaceholder.astro` with explicit config flag (`ENABLE_SOCIAL_PROOF = false` default).
- [ ] **Validation Gate W4**: Confirm zero fake testimonials/logos present in codebase (**Gate W4**).

### Phase P6: Performance, Accessibility, Automated Scans & Deliverables
- [ ] Run Lighthouse audits on mobile profile (**Gate W1** score $\ge 95$).
- [ ] Conduct keyboard/screen-reader accessibility check (**Gate W7**).
- [ ] Verify Slow 4G RTT loading time < 3s (**Gate W8**).
- [ ] Run automated broken link scanner (**Gate W9**).
- [ ] Deliver `docs/website/CONTENT_GUIDE.md` and completion report.
