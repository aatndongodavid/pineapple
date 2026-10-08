# Task List — Master Prompt 07: Site Vitrine et Kit de Vente

- [ ] **Phase P0: Audit & Planning**
  - [x] Verify baseline environment (FastAPI, PostgreSQL, Redis, Alembic, React/Vite, Docker Compose)
  - [x] Create git branch `feature/site-vitrine-et-kit-de-vente` and tag `baseline-site-vitrine-et-kit-de-vente`
  - [x] Produce `ARCHITECTURE_WEBSITE.md`, `IMPLEMENTATION_PLAN.md`, `TASK_LIST.md`
  - [x] Produce Phase 0 artifact `phase0_audit_and_plan.md`

- [ ] **Phase P1: Website Foundation, Astro/Tailwind Setup, i18n & SEO**
  - [ ] Initialize `website/` project structure with Astro + TailwindCSS
  - [ ] Configure bilingual routing (`/fr`, `/en`), `hreflang` tags, `sitemap.xml`, `robots.txt`, and OpenGraph metadata
  - [ ] Configure `pricing.config.json` with XAF FCFA integer prices
  - [ ] **Validation Gate W6**: Verify bilingual parity and routing

- [ ] **Phase P2: Content Drafting & Sales Kit Production (`docs/sales/`)**
  - [ ] Write French and English content for 10 core pages (Home, Features, Security, Pricing, Demo, Students, About, FAQ >= 15 Qs, Legal, Blog >= 3 articles)
  - [ ] Produce `docs/sales/PITCH.md` (12-slide presentation deck)
  - [ ] Produce `docs/sales/ONE_PAGER.md` (commercial summary ready for PDF)
  - [ ] Produce `docs/sales/OBJECTIONS.md` (honest responses to school leader objections)
  - [ ] Produce `docs/sales/ONBOARDING_CHECKLIST.md` (signature to week 1 checklist)
  - [ ] Produce `docs/sales/EMAIL_TEMPLATES.md` (email templates for sales & onboarding)
  - [ ] Produce `docs/sales/TRAINING_OUTLINE.md` (admin 1h & delegate 30m training outlines)
  - [ ] Produce `docs/sales/ANNOUNCEMENT_KIT.md` (posters, social media & WhatsApp templates)
  - [ ] Produce `docs/sales/PRICING_SHEET.md` (internal discount & pricing sheet)
  - [ ] Produce `docs/sales/modele_import_registre.csv` & `modele_import_planning.csv`

- [ ] **Phase P3: Demo Request API & Super-Admin Console**
  - [ ] Create `DemoRequestModel` & migration `alembic/versions/0006_demo_requests.py`
  - [ ] Implement `POST /api/v1/public/demo-requests` with honeypot & IP rate limiting
  - [ ] Implement confirmation email + internal sales alert via `EmailGateway`
  - [ ] Implement Admin Console endpoints `GET /api/v1/admin/demo-requests` & CSV export
  - [ ] **Validation Gate W2 & W3**: Test demo request pipeline & honeypot anti-spam

- [ ] **Phase P4: Demo Environment, Nightly Auto-Reset & Safety Locks**
  - [ ] Seed fictional demo tenant "Établissement Démo Pineapple" (60 students, 4 classes, 8 rooms, 1 timetable, polls, delegate, visitor ads)
  - [ ] Implement nightly auto-reset script `scripts/reset_demo_tenant.py`
  - [ ] Implement demo account safety locks (prevent password changes, real payments, real SMS) and persistent floating banner
  - [ ] Write 10-minute demo script `docs/sales/DEMO_SCRIPT.md`
  - [ ] **Validation Gate W5**: Verify demo tenant isolation & auto-reset task

- [ ] **Phase P5: Real Product Screenshots & Social Proof Flag (Rule V3)**
  - [ ] Capture real screenshots of Pineapple OS web application
  - [ ] Implement `SocialProofPlaceholder.astro` with explicit config flag (`ENABLE_SOCIAL_PROOF = false` default)
  - [ ] **Validation Gate W4**: Confirm zero fake testimonials/logos present in codebase

- [ ] **Phase P6: Performance, Accessibility, Automated Scans & Deliverables**
  - [ ] Run Lighthouse audits on mobile profile (**Gate W1** score >= 95)
  - [ ] Conduct keyboard/screen-reader accessibility check (**Gate W7**)
  - [ ] Verify Slow 4G RTT loading time < 3s (**Gate W8**)
  - [ ] Run automated broken link scanner (**Gate W9**)
  - [ ] Deliver `docs/website/CONTENT_GUIDE.md` and completion report
