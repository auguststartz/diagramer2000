# Build Plan - AWS Diagram Generator

## Current status

- Phase 1 scaffold started
- Backend API endpoint for PNG generation implemented
- Frontend form + preview implemented
- Docker configuration added (not executable in this environment because Docker is unavailable)

## Product increments

### Milestone 1: Phase 1 MVP (in progress)

Goal: input form + static layout renderer + PNG export in Docker.

Deliverables:

- `FastAPI` service with validation and endpoint contract
- Required inputs from PRD section 6.1 (Phase 1 subset)
- Static architecture layout with AZ distribution logic
- PNG export at 1920px width
- Basic browser UI for form input and export
- Containerization via `Dockerfile` + `docker-compose.yml`

Remaining tasks:

- Integrate official AWS icons instead of placeholders
- Add inline help text/tooltips for all fields
- Add API tests and renderer unit tests
- Validate image output dimensions and distribution edge cases

### Milestone 2: Service toggles + live preview

Goal: add optional service rendering and sub-2s preview updates.

Deliverables:

- Inputs for ALB, RDS, S3, CloudFront, WAF, Route 53, ElastiCache
- Diagram placement and connection rules for each service
- Debounced live preview updates without explicit download
- SVG export endpoint

### Milestone 3: Save/load + PDF export

Goal: improve consultant workflow persistence and deliverables.

Deliverables:

- JSON save/load for diagram configurations
- Diagram title override + date field
- PDF export (letter-size centered output)

### Milestone 4: hardening + distribution

Goal: production readiness.

Deliverables:

- UI polish and usability review
- ARM64 and AMD64 image validation
- Image size optimization (<500MB target)
- Browser compatibility test pass (Chrome/Firefox/Edge/Safari)

## Technical workstreams

1. Rendering engine
- Keep Pillow renderer for Phase 1 speed
- Evolve renderer abstraction so icon-based service layers can be added without rewrites

2. API and contracts
- Maintain a versioned API namespace (`/api/v1`)
- Add request/response examples and error model in docs

3. Frontend
- Keep a no-build static frontend during Phase 1
- Move to React/Vite only if preview interactions grow beyond simple form state

4. Quality
- Add unit tests for server distribution algorithm
- Add API tests for input validation and region handling
- Add snapshot-style image smoke test (dimensions + non-empty payload)

## Immediate next queue (recommended)

1. Replace placeholder EC2 boxes with official AWS icon assets bundled in repo
2. Add tests for `_distribute_servers` and payload validation
3. Add tooltips and inline help text to satisfy PRD usability requirement
4. Add endpoint for returning image metadata (dimensions, generation time)

## Risks and mitigations

- Risk: icon licensing/compliance drift
- Mitigation: bundle only official AWS Architecture icons and document source/version

- Risk: rendering complexity increases with service toggles
- Mitigation: introduce service-specific layout modules before Milestone 2

- Risk: export fidelity differences across formats
- Mitigation: define visual regression checks for PNG/SVG/PDF outputs
