# Deep Research Prompt — QuantCAI Platform

Paste the section below into a deep-research tool. It is deliberately grounded
in the platform's *actual* implementation state (audited 2026-08-05) rather
than aspirational marketing copy, and it asks for evidence rather than
recommendations.

Context on why this framing matters: three prior strategy documents for this
platform confidently recommended features that were already shipped (CBOM
export, BYOK, fork-and-share permalinks, cold-outreach tooling) and cited
funnel benchmarks with no sources. Meanwhile the single most important
technical claim the product makes — that it detects post-quantum key exchange —
was broken for every TLS 1.3 server. The prompt is written to avoid repeating
that failure mode.

---

## PROMPT BEGINS

You are researching **QuantCAI**, a dual-audience deep-tech SaaS platform:

1. **A quantum circuit simulator** (B2D) — browser circuit builder, OpenQASM 3
   export, Qiskit Aer backend, BYOK execution against IBM Quantum / IonQ.
2. **A post-quantum cryptography (PQC) vulnerability scanner** (B2B) — external
   TLS scanning, NIST FIPS 203/204/205 posture assessment, CycloneDX CBOM
   export.

Stack: FastAPI + SQLAlchemy + Alembic + PostgreSQL + Redis + Celery backend;
React/Vite frontend; a separate Python marketing-automation service; deployed
on Render. Payments run through **WarriorPlus** (this is a fixed constraint —
do not recommend replacing it). Pricing: Free, Pro $27/mo ($18/mo annual),
Enterprise custom.

### Ground rules — these are not optional

1. **Cite everything.** Every factual claim, benchmark, statistic, standard,
   date, or byte-size must carry a source and its publication date. If you
   cannot source a number, say so explicitly instead of stating it. Prefer
   primary sources (NIST, NSA, IETF RFCs, OWASP/Ecma, vendor docs) over
   secondary summaries and blog aggregations.
2. **Distinguish evidence from inference.** Mark each conclusion as
   `[MEASURED]`, `[SOURCED]`, or `[INFERRED]`. Do not let an inference inherit
   the confidence of a source.
3. **Segment-match all benchmarks.** Generic "SaaS converts at X%" figures are
   not useful. Any conversion, pricing, or retention figure must state the
   segment it came from (ACV band, developer-tool vs security-tool, self-serve
   vs sales-assisted, geography) and how far that segment is from a
   sub-$500-ACV dual-audience deep-tech tool.
4. **Report disconfirming evidence.** Where the data contradicts a proposal,
   say so. A recommendation that survives contrary evidence is worth more than
   five that were never tested.
5. **Respect the constraints.** WarriorPlus stays. `quantc.info@gmail.com` is
   the correct support address. Do not spend effort re-litigating either.

### Research questions, in priority order

#### A. PQC scanner correctness and competitive defensibility (highest priority)

This is the enterprise revenue engine and it must be technically unimpeachable.

- **A1.** How do mature TLS scanners (Qualys SSL Labs, testssl.sh, sslyze,
  Hardenize/Red Sift, tls-scan) determine the negotiated TLS 1.3 key exchange
  group, and how do they *actively probe* for group support rather than
  observing a single negotiation? What exactly does each expose in output?
- **A2.** What is the current, sourced state of PQC group support in the
  ecosystem — OpenSSL 3.5+, BoringSSL, Go crypto/tls, rustls, NSS — and in
  Python's `ssl` module specifically (`SSLSocket.group()`,
  `SSLContext.set_groups()`): which Python and OpenSSL versions are required?
  Cite the CPython changelog and OpenSSL release notes with versions.
- **A3.** `X25519MLKEM768` (RFC 9370 / draft-kwiatkowski-tls-ecdhe-mlkem):
  what is its actual deployment share today across major CDNs, cloud load
  balancers, and the top 1M sites? Which measurement studies exist, and what
  are their methodologies and blind spots?
- **A4.** What must a CBOM satisfy to be *accepted* by an enterprise
  compliance workflow, beyond schema-validating against CycloneDX 1.6/1.7?
  Look for concrete evidence: what do auditors actually ask for, which fields
  do GRC platforms ingest, and what causes a CBOM to be rejected?
- **A5.** **Scanning ethics and legality.** An external TLS scanner and an
  automated cold-outreach pipeline that scans third-party domains without
  consent raise real exposure. Research: CFAA and equivalent statutes, India's
  DPDPA and CERT-In directions, GDPR implications of unsolicited security
  audits, and how existing vendors (SSL Labs, Shodan, Censys) structure
  consent, opt-out, and rate limiting. **What is the defensible operating
  model?** This is a live risk, not a hypothetical.
- **A6.** What does the CNSA 2.0 timeline actually mandate, by date and system
  class, from the primary NSA source — and what are the common
  misinterpretations that appear in vendor marketing?

#### B. Quantum simulation economics

- **B1.** Benchmark Qiskit Aer's methods (`statevector`, `density_matrix`,
  `stabilizer`, `matrix_product_state`, `extended_stabilizer`) on
  memory-vs-qubits and time-vs-depth. For which circuit classes does MPS
  genuinely beat statevector, and where does it degrade badly? Sourced
  benchmarks, not vendor claims.
- **B2.** Is browser-side WebAssembly statevector simulation actually viable?
  Find real measurements: what qubit count is usable in a browser tab, what is
  the WASM memory ceiling, how do SIMD and threads change it, and what do
  existing WASM quantum simulators achieve? Include the cost of the download.
- **B3.** What do comparable services charge for simulation compute, and what
  does the true marginal cost per simulation-second look like on Render, Fly,
  AWS, and Modal? Where is the actual gross-margin line for a $27/mo plan?
- **B4.** Qiskit 1.x → 2.0 migration: what specifically breaks? Enumerate
  removed/moved APIs relevant to a service using `qiskit.qasm3.loads`,
  `transpile`, `AerSimulator`, and `qiskit-qasm3-import`. Is `qiskit-qasm3-import`
  maintained for 2.x, and what is the migration cost?

#### C. Product-led growth for a genuinely dual-audience product

- **C1.** Find **documented case studies** of single companies successfully
  serving both a self-serve developer audience and an enterprise security
  buyer. How did they structure domain, navigation, pricing, and sales? Where
  did it fail, and what were the failure signatures?
- **C2.** For an ungated "scan any domain" lead magnet: what abuse, rate
  limiting, and cost-control architectures do comparable free security tools
  use? What conversion rates are documented, with segment context?
- **C3.** What is the minimum viable product-telemetry stack to operationalise
  product-qualified leads, and what does it genuinely cost at low volume?
  Compare self-hosted PostHog against hosted options on cost, data residency
  (relevant for Indian and EU enterprise buyers), and engineering time.
- **C4.** Given WarriorPlus as the payment rail: how do enterprise security
  buyers actually react to it, and what compensating trust signals (SOC 2,
  security.txt, DPA, pen-test attestation, status page, published SLA) most
  effectively offset an unfamiliar payment processor? Rank by evidence of
  impact on enterprise procurement, not by intuition.

#### D. Production hardening

- **D1.** For a small team on Render: what is the realistic minimum path to
  SOC 2 Type I, with actual cost and calendar time from published accounts?
  Which controls matter most to security buyers before certification exists?
- **D2.** Failure modes of Celery + Redis + FastAPI for CPU-bound work — what
  do postmortems and production write-ups identify as the common causes of
  worker starvation, memory exhaustion, and silent job loss, and what are the
  mitigations?
- **D3.** For a service whose core value is compliance assessment, what
  evidence and audit-trail properties must the scan pipeline have for a
  customer to rely on it in their own audit? Think reproducibility, scan
  provenance, versioned rule sets, and immutability of past results.

### Required output format

1. **Executive summary** — the five findings that would most change decisions,
   each with its confidence marker and strongest source.
2. **Per-question findings** — evidence first, then interpretation, then the
   specific implication for this platform.
3. **Contradictions table** — every place the evidence contradicts a common
   assumption or a prior recommendation, with the source on each side.
4. **Prioritised actions** — ranked by (evidence strength × revenue impact ÷
   engineering cost). State the assumptions behind each ranking so they can be
   challenged.
5. **Open questions** — what could not be resolved from public sources, and
   what experiment or measurement would resolve each.

### What NOT to produce

- Recommendations to adopt Stripe, Paddle, or any payment processor.
- Recommendations to change the support email address.
- Unsourced conversion or pricing benchmarks.
- Generic PLG advice that would apply unchanged to any SaaS company.
- Feature suggestions without a check on whether they already exist.

## PROMPT ENDS

---

## Verified platform state as of 2026-08-05

Supply this to the researcher so it does not recommend what already exists.

### Shipped and working

| Capability | Location |
|---|---|
| CycloneDX CBOM generation and export | `backend/models/cyclonedx_models.py`, `backend/services/pqc_scanner.py` |
| BYOK hardware provider credentials | `backend/services/backend_configs.py` |
| Circuit fork/share permalinks | `backend/routers/circuit.py` (`share_slug`), `frontend/src/pages/SharedCircuit.tsx` |
| Learn modules (qubits, gates, PQC) | `frontend/src/pages/Learn*.tsx` |
| Tiered limits with Redis rate limiting | `backend/tier_limits.py`, `backend/core/config.py` |
| Cold outbound audit tooling | `scripts/outbound_ciso_blitz.py` |
| Marketing automation service | `python_admin/` (6h campaign loop, 12h arXiv newsroom) |
| Annual pricing toggle | `frontend/src/components/landing/PricingSection.tsx` |

### Fixed recently — do not re-report as open

- TLS 1.3 key exchange detection. Suite-name matching meant ML-KEM was never
  detected and every TLS 1.3 host took a spurious +50 risk penalty. Now uses
  the negotiated group plus an active capability probe, with a tri-state
  result so "unmeasurable" is never reported as "vulnerable".
- Developer API tier limits. A key-name mismatch capped every plan at the free
  limit of 10 requests/day and started Pro overage billing at request 11
  instead of 501.
- A duplicate tier-limit table granting free users 20 qubits against a
  configured 3.
- Enterprise qubit ceiling of 29, which required 8 GB of statevector against a
  4 GB worker memory cap and therefore OOM'd rather than working.
- Simulation cost budget. `USE_CELERY` defaults to `False`, so jobs run inline
  in the web process where Celery's 30s limit never applies.
- CI ran a migration script importing modules deleted in a refactor, so it
  failed on every run and **pytest never executed**. No test in this repo had
  ever run in CI.

### Genuinely absent — open for research

- Ungated/anonymous PQC scanning. Every scan endpoint requires
  `get_current_user` (`backend/routers/pqc.py`).
- Client-side WebAssembly simulation. No WASM anywhere in the frontend.
- Product analytics of any kind. No PostHog/Mixpanel/Segment/Amplitude, so the
  entire product-qualified-lead concept is currently unimplementable.
- A reusable GitHub Action for CI/CD scanning.
- TLS handshake overhead forecasting (payload inflation, fragmentation,
  latency) for PQC migration planning.
- SOC 2 or any formal compliance attestation.

### Known open risks

- The marketing service depends on a Neon PostgreSQL instance that has
  exceeded its compute quota. Until that is restored the service runs degraded.
- `qiskit` is pinned `<2.0.0`; the codebase uses 1.x APIs.
- Legacy scripts (`backend/scripts/migrate_db.py`, `cleanup_user.py`,
  `create_root_user.py`, `update_to_root.py`) import modules that no longer
  exist and are dead code.
- The frontend hardcodes an `onrender.com` production API fallback
  (`frontend/src/lib/api.ts`, `axiosClient.ts`).
