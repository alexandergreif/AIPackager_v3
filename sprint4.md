# Sprint 4 – AI Integration
**Duration:** 1 week  
**Goal:** GPT‑4o function‑call returns structured PSADT JSON and renders final script.

| ID | Task |
|----|------|
| SP4‑01 | Integrate OpenAI SDK, load key from env. |
| SP4‑02 | Define `PSADTScript` Pydantic schema for function call. |
| SP4‑03 | Implement `PSADTGenerator` service with retry/backoff. |
| SP4‑04 | Update `/api/packages/<id>/generate` to call AI, store JSON. |
| SP4‑05 | Unit test with mocked OpenAI response. |

**DoD** • Real call returns valid JSON → script rendered & saved; tests pass with mock.
