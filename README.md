# 3D Filament Scanner – Project Plan

Repo: `feedmetaco/3D-filament-scanner-`  
Goal: Local-first web app to catalog filament spools by **scanning box labels** and optionally **importing invoices** to track price & orders.

This document coordinates work between:

- **Sami** (you) – human operator, environment & infra.
- **Codx** – GitHub-connected code agent (repo-wide edits).
- **Cursor/Claude** – local dev assistant (workspace-aware refactors & debugging).
- **ChatGPT** – high-level planner/architect (this file’s author).

---

## 1. Product Overview

### 1.1 Core Use Case

You are stocking up on filament from a few main brands (Sunlu, eSUN, Bambu).  
You want:

- While shelving filament, to **take a photo of the box label** and have the app:
  - Extract **brand, material, color, diameter, etc.**
  - Store it as a **product + spool** entry.
- Later, when ordering:
  - Quickly check **what you already own** (by brand/material/color).

You **do not** care about:
- Exact weight remaining.
- Per-print consumption.

Each spool = one 1 kg unit. Inventory is count-based.

### 1.2 Versions

- **v1 – Local inventory**

  - Self-hosted on Synology via Docker + SQLite.
  - Add spools from:
    - Photo of label (with OCR + brand-specific parsing).
    - Manual form.
  - See inventory filtered by brand/material/color.
  - Mark spools as “used up”.

- **v1.1 – Orders & pricing**

  - Add **orders** with uploaded invoices (PDF/image).
  - Parse invoice → line items → map to products.
  - Auto-create spools with `price`, `order_date`, `vendor`.
  - Optional: attach label photos to newly created spools.

---

## 2. Architecture & Tech Stack

### 2.1 Target Stack (v1)

**Backend**

- Language: Python
- Framework: FastAPI
- DB: SQLite (file on mounted volume)
- ORM: SQLAlchemy or SQLModel
- OCR: Tesseract via `pytesseract`
- Media storage: local filesystem (`/media/labels`, `/media/invoices`)

**Frontend**

- SPA: React (Vite or CRA, up to the generator)
- UI: simple table/cards-based layout, mobile-friendly

**Deployment (v1)**

- Docker container running:
  - FastAPI backend
  - (Option A) React built into static files served by FastAPI
  - (Option B) Separate Nginx serving frontend; API at `/api`
- Hosted on Synology NAS, accessible over LAN.

> Future: If you move to cloud, DB schema should be compatible with Postgres (Supabase).

---

## 3. Data Model

### 3.1 v1 Entities

#### `Product`

Represents a **unique filament type** (e.g. “Sunlu PLA Yellow 1.75mm”).

- `id`
- `brand` – `Sunlu`, `eSUN`, `Bambu Lab`, …
- `line` – `PLA Basic`, `PLA+`, etc. (nullable)
- `material` – `PLA`, `PLA+`, `PETG`, `TPU`, …
- `color_name` – `Yellow`, `Blue`, `White`, …
- `diameter_mm` – usually 1.75
- `notes` – optional
- `barcode` – label barcode, if known
- `sku` – vendor/brand SKU, if known
- `created_at`
- `updated_at`

Weight is implicitly **1 kg**, not stored.

#### `Spool`

Represents one **physical box/spool** of a `Product`.

- `id`
- `product_id` – FK → `Product`
- `purchase_date`
- `vendor` – `Amazon`, `Bambu`, `Micro Center`, …
- `price` – per spool
- `storage_location` – `Shelf A2`, `Drybox 1`, …
- `photo_path` – local path to label image
- `status` – enum: `in_stock`, `used_up`, `donated`, `lost`
- (Optional for v1, required in v1.1) `order_id` – FK → `Order`
- `created_at`
- `updated_at`

---

### 3.2 v1.1 Entities

#### `Order`

- `id`
- `vendor`
- `order_number` – vendor-specific ID
- `order_date`
- `invoice_path` – PDF/image path
- `total_amount` – optional
- `currency` – e.g. `USD`
- `created_at`
- `updated_at`

#### `OrderItem`

- `id`
- `order_id` – FK → `Order`
- `product_id` – FK → `Product`, nullable until mapped
- `title_raw` – raw line string from invoice
- `quantity` – number of spools
- `unit_price`
- `currency`
- `status` – `pending_mapping`, `confirmed`
- `created_at`
- `updated_at`

Once an `OrderItem` is confirmed, **`quantity` spools** are created and linked.

---

## 4. Roles & Responsibilities

This section defines who does what so tools don’t step on each other.

### 4.1 Sami (You)

- Owns the **runtime environment**:
  - Synology configuration.
  - Docker installation / upgrades.
  - Volume mounts & backups.
- Runs and tests the app:
  - Uses UI to add real filaments.
  - Uploads label images / invoices.
  - Reports parsing failures as examples.
- Makes **product decisions**:
  - When to expand features (e.g., QR codes, PWA, cloud migration).

### 4.2 Codx (GitHub repo agent)

Codx is responsible for **repo-wide, spec-driven coding work**:

- Create and maintain:
  - Project structure (`backend/`, `frontend/`, `docker/`).
  - Backend models, schemas, routers, tests.
  - Frontend pages/components.
  - Dockerfile & docker-compose.
- Apply **structural changes**:
  - Add new entities (Orders, OrderItems).
  - Add new endpoints & flows.
  - Perform refactors that touch many files.
- Keep code consistent with this `PROJECT_PLAN.md`.

Codx should **always** treat `PROJECT_PLAN.md` as the source of truth.

### 4.3 Cursor + Claude (local dev assistant)

Cursor/Claude is best used for:

- **Local debugging**:
  - Reading error logs from your machine.
  - Suggesting fixes when the app doesn’t build/run.
- **Small/mid-sized refactors**:
  - Adjusting a function or component.
  - Reworking a parsing rule.
- **Environment-specific issues**:
  - Path/permissions problems on macOS/Windows before you push.
  - “Why is Docker not seeing Tesseract?” type issues.

Cursor sees your **local workspace**, Codx sees the **GitHub repo**.

### 4.4 ChatGPT (Planner/Architect)

This plan is produced here. Use ChatGPT for:

- High-level design changes:
  - New features & architecture.
  - Data model updates / migrations.
- Complex reasoning:
  - Trade-offs (SQLite vs Supabase, OCR options, etc.).
- Producing new project docs:
  - Updated `PROJECT_PLAN.md` sections.
  - Additional design docs if needed.

---

## 5. Implementation Phases

### Phase 0 – Repo Init & Ground Rules

**Owner: Sami + Codx**

**Goals:**

- Initialize repo structure.
- Commit this plan.
- Prepare Codx & Cursor for work.

**Tasks:**

- [ ] **Sami**: Clone `3D-filament-scanner-` locally.
- [ ] **Sami**: Create `PROJECT_PLAN.md` at repo root with this content.
- [ ] **Sami**: Commit & push initial plan to GitHub.
- [ ] **Codx**: Read `PROJECT_PLAN.md` and generate baseline project layout:
  - [ ] Create `backend/` with FastAPI skeleton.
  - [ ] Create `frontend/` with React skeleton.
  - [ ] Create `docker/` or top-level `Dockerfile` + `docker-compose.yml`.
- [ ] **Sami**: Review generated structure; adjust names/paths if needed.

---

### Phase 1 – v1 Backend (Products & Spools)

**Owner: Codx (with Cursor for debugging)**

**Goals:**

- Implement backend models & API for v1.
- Wire up SQLite + basic CRUD (no OCR yet).

**Tasks:**

- [ ] **Codx**: Add backend dependencies:
  - FastAPI, Uvicorn
  - SQLAlchemy or SQLModel
  - Pydantic
- [ ] **Codx**: Implement `Product` and `Spool` DB models per §3.1.
- [ ] **Codx**: Implement API endpoints:
  - [ ] `GET /api/products` (filter by brand/material/color).
  - [ ] `POST /api/products`.
  - [ ] `GET /api/products/{id}`.
  - [ ] `PATCH /api/products/{id}`.
  - [ ] `GET /api/spools` (filter by status/product props).
  - [ ] `POST /api/spools` (manual creation).
  - [ ] `GET /api/spools/{id}`.
  - [ ] `PATCH /api/spools/{id}`.
  - [ ] `POST /api/spools/{id}/mark-used` (status = `used_up`).
- [ ] **Codx**: Implement DB initialization & simple migration strategy (e.g., Alembic or manual).
- [ ] **Sami**: Run backend locally:
  - [ ] `uvicorn` or an equivalent dev server.
  - [ ] Create a few test products/spools manually.
  - [ ] Use **Cursor** if any errors arise.

---

### Phase 2 – v1 Frontend (Inventory UI)

**Owner: Codx + Cursor**

**Goals:**

- Build minimal UI to:
  - View inventory (grouped or flat).
  - Add/edit spools.
  - See product details.

**Tasks:**

- [ ] **Codx**: Scaffold React frontend with:
  - Routing (`/`, `/spools`, `/products/:id`).
  - Simple layout (header + main content).
- [ ] **Codx**: Add pages:
  - [ ] `InventoryPage`: list products + active spool counts with filters.
  - [ ] `SpoolListPage`: list spools with filters.
  - [ ] `ProductDetailPage`: show product details and its spools.
  - [ ] `AddSpoolPage`: manual creation form.
- [ ] **Codx**: Wire frontend to backend APIs.
- [ ] **Sami**: Run frontend locally, test basic workflows.
- [ ] **Cursor**: Adjust UI layout / forms as needed for better mobile use.

---

### Phase 3 – v1 Label Scanning (OCR + Parsing)

**Owner: Codx + Cursor**

**Goals:**

- Allow adding spools “from photo”.
- Implement brand-specific parsing for Sunlu, eSUN, Bambu.

**Tasks:**

- [ ] **Codx**: Add Tesseract & `pytesseract` to backend environment.
- [ ] **Codx**: Implement file storage for label images (`/media/labels`).
- [ ] **Codx**: Implement `POST /api/spools/from-photo`:
  - Accept multipart image file.
  - Store image.
  - Run OCR (Tesseract).
  - Run parsing pipeline:
    - Detect brand.
    - Parse material/color/diameter.
  - Try to match an existing `Product`.
  - Return:
    - `ocr_text`
    - `suggested_product`
    - `matched_product_id` (if any).
- [ ] **Codx**: Implement brand-specific parsers:
  - [ ] `parse_sunlu_label(text)`
  - [ ] `parse_bambu_label(text)`
  - [ ] `parse_esun_label(text)`
- [ ] **Codx**: Add unit tests with **sample OCR text** from your real labels.
- [ ] **Codx**: Update `AddSpoolPage` to:
  - Upload image.
  - Show suggested product mapping.
  - Allow selecting existing product OR creating new.
  - Then fill spool metadata.
- [ ] **Sami**: Capture real label photos and test.
- [ ] **Cursor**: Help debug OCR failures and refine parsing rules.

---

### Phase 4 – v1 Deployment to Synology

**Owner: Sami (with Cursor/ChatGPT for troubleshooting)**

**Goals:**

- Run v1 as a Docker stack on Synology, accessible from LAN.

**Tasks:**

- [ ] **Codx**: Finalize `Dockerfile` and `docker-compose.yml`:
  - Backend + frontend.
  - Volume mounts:
    - DB file (e.g., `/app/data/db.sqlite`).
    - Media directory (e.g., `/app/media`).
  - Expose HTTP port (e.g., `8000:8000` or `80:80`).
- [ ] **Sami**: Pull repo to Synology.
- [ ] **Sami**: Run `docker compose up -d`.
- [ ] **Sami**: Access app from phone via Synology IP.
- [ ] **Cursor/ChatGPT**: Assist with any container/build issues (logs pasted into them).

---

### Phase 5 – v1.1 Orders & Pricing

**Owner: Codx + Sami**

**Goals:**

- Add order & invoice support.
- Auto-create spools from invoice line items with price & vendor.

**Tasks:**

- [ ] **Codx**: Add `Order` and `OrderItem` models per §3.2.
- [ ] **Codx**: Add API endpoints:
  - [ ] `POST /api/orders` – create order metadata.
  - [ ] `POST /api/orders/{id}/invoice` – upload invoice (PDF/image) and trigger parsing.
  - [ ] `GET /api/orders/{id}` – view parsed order + items.
  - [ ] `POST /api/orders/{id}/confirm` – confirm mappings & create spools.
- [ ] **Codx**: Implement invoice parsing pipeline:
  - Extract text (PDF parsing or OCR).
  - Identify candidate line items (PLA/PETG/TPU/1.75mm/KG).
  - Parse `title_raw`, `quantity`, `unit_price`.
  - Attempt mapping to `Product` using same logic as label parsers.
- [ ] **Codx**: Update frontend:
  - [ ] `OrderListPage`.
  - [ ] `OrderDetailPage` with mapping UI.
  - [ ] “Add Order” wizard flow.
- [ ] **Sami**: Provide sample orders/invoices (Amazon/Bambu PDFs).
- [ ] **Cursor/ChatGPT**: Help refine parsing rules based on real invoice formats.

---

## 6. Prompts for Tools

### 6.1 Codx – Initial Onboarding Prompt

Use this (or a trimmed version) when you start Codx on the repo:

> You are Codx, the GitHub-aware code agent for the repository `feedmetaco/3D-filament-scanner-`.
>
> Your primary source of truth is the file `PROJECT_PLAN.md`.  
> Follow its architecture, data model, and phase breakdown exactly unless explicitly updated.
>
> High-level responsibilities:
> - Create and maintain a FastAPI + SQLite backend under `backend/`.
> - Create and maintain a React frontend under `frontend/`.
> - Implement v1 (products + spools, label photo OCR) and v1.1 (orders + invoice parsing) as described.
> - Manage Docker integration so the app can run as a single stack on Synology.
> - Keep code idiomatic, well-structured, and tested.
>
> Do not invent new requirements or features beyond what’s in `PROJECT_PLAN.md` without explicit instructions.
> When in doubt, add notes or TODO comments referencing the relevant section in `PROJECT_PLAN.md`.

---

### 6.2 Cursor + Claude – Local Dev Prompt

When working in Cursor, you can tell Claude something like:

> You are my local dev assistant for the `3D-filament-scanner-` project.  
> The authoritative spec is in `PROJECT_PLAN.md`.  
> Codx is responsible for large repo-wide changes via GitHub; you are responsible for:
> - Debugging build/runtime errors on my machine.
> - Refining specific functions (e.g., label parsing, invoice parsing).
> - Helping adjust UI components and layouts.
> - Suggesting fixes when Docker or environment paths break.
>
> Always read `PROJECT_PLAN.md` before making changes, and keep the implementation consistent with it.

---

### 6.3 ChatGPT – Planner Prompt (for future changes)

When you want to extend or refactor this plan:

> I have a project called 3D-filament-scanner-, with `PROJECT_PLAN.md` defining the architecture and phases.  
> I want to update the plan to add/modify these features: [describe].  
> Please produce an updated section or an add-on design that I can paste into the existing `PROJECT_PLAN.md`, keeping the same style and structure.

---

## 7. Progress Tracking

Use checkboxes in this file or open GitHub Issues for each task group.  
As you complete tasks, update the `[ ]` → `[x]` to keep Codx/Cursor aligned with reality.

This single document should be enough for:

- Codx to know what to build.
- Cursor/Claude to know what to debug/refine.
- You to know what to do on Synology.
- ChatGPT to keep the overall design coherent.


## 4. Roles & Responsibilities

This section defines who does what so tools don’t step on each other.

We assume you are using:

- **ChatGPT Codex** → ChatGPT with direct access to this GitHub repo (via the GitHub integration).
- **Cursor + Claude** → your local editor/agent running on your dev machine.
- **ChatGPT (regular)** → planning/architecture (this plan file).

### 4.1 Sami (You)

- Owns the **runtime environment**:
  - Synology configuration.
  - Docker installation / upgrades.
  - Volume mounts & backups.
- Runs and tests the app:
  - Uses UI to add real filaments.
  - Uploads label images / invoices.
  - Reports parsing failures and weird behavior.
- Makes **product/feature decisions**:
  - When to expand features (QR codes, PWA, cloud migration, etc.).

### 4.2 ChatGPT Codex (GitHub-connected ChatGPT)

ChatGPT Codex is your **repo-aware coding agent**. It sees the GitHub repo and can commit/PR.

It is responsible for **big, structured changes**:

- Creating and maintaining **project structure**:
  - `backend/` (FastAPI + SQLite + OCR).
  - `frontend/` (React).
  - Docker files (`Dockerfile`, `docker-compose.yml`).
- Implementing major features:
  - v1: `Product` + `Spool` models and CRUD.
  - v1: `/api/spools/from-photo` endpoint with label OCR + parsing.
  - v1.1: `Order` + `OrderItem` models and invoice parsing pipeline.
- Writing/maintaining:
  - API routes.
  - ORM models & schema changes.
  - Integration tests and unit tests for parsing logic.

**Important:**  
Whenever you start a “big change” session with ChatGPT Codex, tell it explicitly:

> “Use `PROJECT_PLAN.md` as the source of truth. Stay within v1/v1.1 scope unless I say otherwise.”

Codex should always respect `PROJECT_PLAN.md` as the spec.

### 4.3 Cursor + Claude (local dev assistant)

Cursor/Claude runs in your editor and has access to your **local workspace**, not GitHub directly.

Use Cursor/Claude for:

- **Local debugging**:
  - Build failures, runtime errors on your Mac/PC.
  - Path/permissions issues, missing libs, etc.
- **Targeted edits**:
  - Tweaking a single function (e.g., `parse_sunlu_label()`).
  - Adjusting React components and CSS/layout.
  - Small refactors that you want to see live while coding.
- **Bridging environment gaps**:
  - Helping adapt code from Codex to your local environment before you push.
  - Verifying Docker runs on your machine before you move to Synology.

Pattern to follow:

1. Let **ChatGPT Codex** do the “big sweep” changes in GitHub.
2. Pull changes locally.
3. Use **Cursor/Claude** to fix local issues and polish.
4. Commit/push back to GitHub.

### 4.4 ChatGPT (Planner/Architect – this file)

Use regular ChatGPT (no repo hookup) when you need:

- New design decisions:
  - Data model changes.
  - Architectural choices (e.g., “Should I move to Supabase?”).
- High-level plans:
  - New phases (v2, PWA, QR codes, etc.).
  - Updated implementation plans.
- New documentation:
  - Updated `PROJECT_PLAN.md`.
  - Additional design docs for future features.

When something big changes (e.g., you decide to add user auth, or cloud sync), come back here, ask ChatGPT to update the plan, then paste the new sections into `PROJECT_PLAN.md`. After that, **Codex and Cursor follow the updated spec.**


---
