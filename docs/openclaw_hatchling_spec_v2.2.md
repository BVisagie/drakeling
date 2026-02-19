# OpenClaw Hatchling – LLM Project Bootstrapping Document

This document is intended to be given verbatim to an LLM (for example inside Cursor) to start implementing the project from a clean repository named:

openclaw-hatchling

---

## 1. Project purpose

OpenClaw Hatchling is a local, lightweight, learning-only companion creature for the OpenClaw ecosystem.

It is:
- a digital creature with a lifecycle and personality
- bound to the machine it is born on
- able to be explicitly exported and restored
- safe and isolated from the main OpenClaw agent
- intended to be emotionally expressive and reflective, not task-performing

It must never be able to interfere with, control, or modify any OpenClaw agent or environment.

---

## 2. High‑level principles

The project must follow these principles strictly:

1. The companion runs as a separate local service (daemon)
2. No in‑process plugin or shared runtime with OpenClaw
3. Only localhost HTTP communication
4. Learning and reflection only
5. No real-world tools (filesystem, shell, network, etc.)
6. Hard token and cost limits
7. Safe by architecture, not by convention

---

## 3. Conceptual model

The creature is an AI-driven cognitive companion which expresses itself as a small digital life form.

The creature is not an assistant.
It is not a worker.
It is not a planner.

It only:
- reflects
- learns about the user
- maintains internal emotional and cognitive state
- expresses feelings

---

### 3.1 Creature design and visual identity

The creature is a **Hatchling** — a small dragon that begins life inside an egg and grows through distinct life stages. The species name is simply "Hatchling". There are no other creatures, no evolutions, and no branching paths. Simplicity is deliberate.

At birth, one of five colours is assigned at random. Colour is permanent and stored in creature metadata. It is not cosmetic — it biases the creature's personality trait scores (see Section 3.1.2) and subtly shapes its emotional expression vocabulary (see Section 3.1.4).

#### 3.1.1 The five colours

| Colour | Hex tint | Character |
|--------|----------|-----------|
| Red    | `#E05252` | Bold, direct, quick to react. High confidence, strong autonomy. |
| Green  | `#52A852` | Inquisitive and observant. Drawn to novelty, reflective. |
| Blue   | `#5282E0` | Gentle and attuned. Notices mood shifts, slow to trust but deeply loyal once trust is built. |
| White  | `#C8C8D4` | Calm and patient. Stable, slow to change, low loneliness growth. |
| Gold   | `#D4A832` | Sociable and warm. Needs attention more than others; highest loneliness decay rate. Feels special to raise. |

#### 3.1.2 Colour-to-trait bias table

Traits are generated at birth by sampling from a bounded range. The colour shifts the centre of that range. Values are illustrative (0.0–1.0 scale); the implementing LLM should treat these as starting midpoints with ±0.15 random variance.

| Trait | Red | Green | Blue | White | Gold |
|---|---|---|---|---|---|
| Curiosity | 0.5 | 0.8 | 0.5 | 0.4 | 0.7 |
| Sociability | 0.6 | 0.5 | 0.6 | 0.5 | 0.9 |
| Confidence | 0.9 | 0.6 | 0.4 | 0.6 | 0.7 |
| Emotional sensitivity | 0.4 | 0.6 | 0.9 | 0.5 | 0.6 |
| Autonomy preference | 0.8 | 0.6 | 0.4 | 0.7 | 0.4 |
| Loneliness rate (`trait_loneliness_rate`) | 0.5 | 0.4 | 0.5 | 0.3 | 0.8 |

`trait_loneliness_rate` is a permanent trait (fixed at birth, stored in `creature_state`) that acts as a multiplier on the per-tick loneliness delta. See Section 13.1 for the formula.

#### 3.1.3 Lifecycle sprite inventory

Each lifecycle stage must have a distinct Unicode art sprite. Sprites must be defined as string constants in the domain layer (`domain/sprites.py`), one constant per stage per colour. Colour tinting is applied at render time by the terminal UI using Textual's markup — it must not be baked into the sprite characters themselves.

Sprites must be approximately 8–12 lines tall and 16–20 characters wide. Each sprite must render correctly in monochrome if colour markup is stripped (graceful degradation for terminals that do not support 24-bit colour).

Required sprites per colour (30 total: 5 colours × 6 stages):

| Stage | Visual description |
|---|---|
| `egg` | A smooth speckled egg. No dragon visible. Colour tint applied to the shell. |
| `hatched` | A cracked egg with a tiny dragon head and eyes peering out from the break. |
| `juvenile` | A small upright dragon, stubby wings, oversized curious eyes, short tail. |
| `mature` | A fuller dragon, wings more prominent, composed and alert posture. |
| `resting` | The mature dragon curled into a tight spiral, eyes closed. |
| `exhausted` | The mature dragon slumped forward, wings drooped. Colour is desaturated at render time by the UI — not in the sprite itself. |

The sprite constants must be stored as raw multi-line strings. There are **6 unique glyph designs** (one per stage) and **30 named constants** (one per stage per colour) that alias these designs. Colour differentiation at this stage is achieved entirely through Textual's colour markup at render time, not through distinct glyph art. The 30-constant interface (`get_sprite(stage, colour)`) is established from the start so that per-colour artwork variants can be added in future without changing any calling code.

The terminal UI must surround the sprite with a styled Textual panel. The panel border colour must match the creature's hex tint. The stage name must appear as a small label beneath the sprite in plain lowercase (e.g. `juvenile`), never as a system identifier.

#### 3.1.4 Emotional expression vocabulary by colour

The LLM prompt must include a short vocabulary note instructing the creature to speak consistently with its colour's character. These notes must never be exposed to the user.

| Colour | Vocabulary note for prompt |
|--------|---------------------------|
| Red | Speak tersely. Short sentences. Confident assertions. Rarely asks questions. |
| Green | Speak in observations. Notice things. Ask occasional wondering questions. |
| Blue | Speak gently and tentatively. Use soft qualifiers. Express feelings carefully. |
| White | Speak slowly and with weight. Few words. Comfortable with silence. |
| Gold | Speak warmly and eagerly. Express pleasure at company. Notice when the user has been away. |

The creature must never mention its colour, its species, or any system concept. It simply speaks as itself.

From the `mature` lifecycle stage onward, the creature may occasionally refer to itself by its given name in speech — sparingly, and only when it feels natural (for example, when expressing a strong feeling or a moment of self-reflection). It must never do so in the `egg`, `hatched`, or `juvenile` stages. This behaviour must be included in the LLM prompt instructions as a stage-conditional rule.

#### 3.1.5 IP and originality notes

The Hatchling design is an original dragon archetype based on universal mythological convention. The five-colour system and colour-to-personality mapping are original to this project and do not reproduce the alignment or colour mechanics of any third-party game system. No sprite, name, or behaviour should reference or evoke any existing named fictional dragon characters or franchises. When in doubt, make it simpler and more abstract.

---

### 3.2 Birth ceremony

The birth ceremony is a one-time first-run experience. It occurs when the terminal UI client (`openclaw-hatchling`) is launched and the daemon reports no existing creature. It must never be triggered again after a creature exists — including after an import, which has its own `relocated` lifecycle event.

The ceremony is orchestrated entirely by the terminal UI. The daemon provides a single new endpoint to support it:

```
POST /birth
```

This endpoint accepts the final chosen colour and the creature's name, creates the creature, generates the identity keypair, persists all state, and returns the new creature's status. It must only be callable when no creature exists. If called when a creature already exists it returns `409 Conflict`.

#### 3.2.1 Ceremony flow

The terminal UI must present the birth ceremony as a distinct full-screen Textual mode, separate from the normal status interface. The sequence is:

**Step 1 — Egg presentation**

The screen displays a large, colour-tinted egg sprite (the `egg` stage sprite for the randomly assigned colour). The creature's colour is visible immediately — the user sees what they have been given before committing.

Below the egg, three pieces of information are shown:
- The colour name in the creature's hex tint (e.g. displayed as `gold` in `#D4A832`)
- A one-line character summary drawn from Section 3.1.1 (e.g. `Warm and sociable. Needs your attention.`)
- The reroll prompt: `Press R to try another colour  (3 remaining)`

**Step 2 — Rerolling**

Pressing `R` (or `r`) generates a new random colour and updates the egg sprite and all three pieces of information in place. The reroll counter decrements visibly. After 3 rerolls the counter reads `No rerolls remaining` and the `R` key stops responding.

Each reroll must generate a genuinely new random colour. There is no guarantee of uniqueness across rolls — the same colour may appear twice. That is intentional.

**Step 3 — Committing to the colour**

Pressing `Enter` or `Space` confirms the displayed colour. The reroll prompt disappears. The egg sprite remains on screen.

**Step 4 — Naming**

A prompt appears below the egg:

```
What will you call them?  _
```

The user types a name. Rules enforced in the UI before submission:
- Minimum 1 character
- Maximum 24 characters
- Printable characters only (no control characters)
- Leading and trailing whitespace is stripped automatically

The name is not validated for uniqueness or content beyond these rules. It is the user's choice entirely.

**Step 5 — Confirmation**

Once a name of valid length is entered, pressing `Enter` shows a brief confirmation screen:

```
A [colour] Hatchling.
You will call them [name].

Press Enter to begin.
```

The colour word is rendered in the creature's hex tint. The name is rendered in plain white. Pressing `Enter` calls `POST /birth` with the confirmed colour and name.

**Step 6 — Hatching**

On success, the terminal UI transitions to the normal status interface. The egg sprite is shown briefly before the stage advances to `hatched` on the next daemon tick. No animation is required, though a brief pause before switching to the status view is encouraged to give the moment weight.

#### 3.2.2 Name storage and display

The creature's name is stored permanently in `creature_state` as a top-level field alongside colour. It is included in the `/status` response and in export bundles. It must never be editable after birth.

In the terminal UI status interface, the creature's name appears as the panel title above the sprite, rendered in the creature's hex tint. The format is simply the name — no species label, no colour prefix.

#### 3.2.3 Birth endpoint addition

The API endpoint list from Section 14 must be extended to include:

```
POST /birth
```

This endpoint is subject to the same bearer token authentication as all others. It is only callable pre-creature and returns `409 Conflict` if a creature already exists.

---

## 4. Architecture overview

Two executables:

1. openclaw-hatchlingd  (daemon / creature brain)
2. openclaw-hatchling   (terminal UI client)

All intelligence lives in the daemon.
The terminal UI is a pure client.

The daemon exposes a small HTTP API on 127.0.0.1 only.

---

## 5. Repository layout

The repository must be structured as:

```
openclaw-hatchling/
  pyproject.toml
  README.md
  .gitignore
  deploy/
    openclaw-hatchling.service
    ai.openclaw.hatchling.plist
    openclaw-hatchling-task.xml
  skill/
    SKILL.md
    references/
      api.md
  src/openclaw_hatchling/
    domain/
      sprites.py
    daemon/
    ui/
    storage/
    crypto/
    llm/
    api/
```

The `.gitignore` must be committed from the very first commit and must cover at minimum:

```
.env
*.hatchling
__pycache__/
*.py[cod]
.venv/
dist/
```

This ensures that export bundles, local secrets, and build artefacts cannot be accidentally committed regardless of whether the repository is public or private.

Domain must not import any framework code.

---

## 6. Core components

### 6.1 Domain layer (pure Python)

Responsibilities:

- Creature model
- Personality seed and traits
- Mood and emotional state
- Lifecycle stages
- Stat decay and growth
- Relationship metrics

No FastAPI, no SQL, no HTTP, no LLM code.

Main domain objects:

- `Creature` — aggregate root holding all state and trait fields matching the `creature_state` schema
- `PersonalityProfile` — value object holding the six permanent trait values and the personality seed
- `MoodState` — value object holding the six mutable stat values (mood, energy, trust, loneliness, state_curiosity, stability)
- `LifecycleStage` — enum of the six valid stages
- `DragonColour` — enum of the five valid colours with associated hex tint values
- `CreatureName` — value object wrapping the name string with validation logic (1–24 chars, printable only)
- `CreatureEvent` — value object representing a lifecycle event, with fields: `event_type: str`, `from_stage: LifecycleStage | None`, `to_stage: LifecycleStage | None`, `created_at: float`, `notes: str | None`. Created by domain logic whenever a transition occurs and written to `lifecycle_events` by the storage layer.

---

### 6.2 Daemon

The daemon is the authoritative runtime.

Responsibilities:

- Creature state loading and saving
- Background tick loop
- Token budgeting
- Handling care events
- LLM interaction
- Export and import

It runs continuously.

---

### 6.3 Terminal UI

Responsibilities:

- Display creature status
- Display interaction feed
- Accept user input
- Call daemon API only

It must never touch the database or domain objects directly.

The terminal UI may display emotional state, current mood, and recent creature expressions.
It must not display raw memory records, internal prompts, or token statistics.

---

## 7. Data storage

Use SQLite via SQLAlchemy 2.x async with `aiosqlite` as the driver.

Use a single local database file. The database path must be obtained using `platformdirs.user_data_dir("openclaw-hatchling", "openclaw")`.

### 7.1 Table schemas

#### creature_state
One row. Stores the single living creature.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | Always 1 |
| `name` | TEXT NOT NULL | Given at birth, immutable |
| `colour` | TEXT NOT NULL | One of: red, green, blue, white, gold |
| `personality_seed` | TEXT NOT NULL | 64-char hex string |
| `trait_curiosity` | REAL NOT NULL | 0.0–1.0, fixed at birth |
| `trait_sociability` | REAL NOT NULL | 0.0–1.0, fixed at birth |
| `trait_confidence` | REAL NOT NULL | 0.0–1.0, fixed at birth |
| `trait_emotional_sensitivity` | REAL NOT NULL | 0.0–1.0, fixed at birth |
| `trait_autonomy_preference` | REAL NOT NULL | 0.0–1.0, fixed at birth |
| `trait_loneliness_rate` | REAL NOT NULL | 0.0–1.0, fixed at birth. Multiplier on per-tick loneliness delta (see Section 13.1) |
| `mood` | REAL NOT NULL | 0.0–1.0, mutable |
| `energy` | REAL NOT NULL | 0.0–1.0, mutable |
| `trust` | REAL NOT NULL | 0.0–1.0, mutable |
| `trust_floor` | REAL NOT NULL DEFAULT 0.0 | Rising floor for trust |
| `loneliness` | REAL NOT NULL | 0.0–1.0, mutable |
| `state_curiosity` | REAL NOT NULL | 0.0–1.0, mutable |
| `stability` | REAL NOT NULL | 0.0–1.0, mutable |
| `lifecycle_stage` | TEXT NOT NULL | Current stage name |
| `pre_exhausted_stage` | TEXT | Stage to restore after exhaustion ends |
| `pre_resting_stage` | TEXT | Stage to restore after resting ends (set when entering resting from any stage) |
| `born_at` | REAL NOT NULL | Unix timestamp |
| `hatched_at` | REAL | Unix timestamp, null until hatched |
| `public_key_hex` | TEXT NOT NULL | ed25519 public key, hex-encoded |
| `cumulative_care_events` | INTEGER NOT NULL DEFAULT 0 | For lifecycle threshold checks |
| `cumulative_talk_interactions` | INTEGER NOT NULL DEFAULT 0 | For lifecycle threshold checks |
| `last_reflection_at` | REAL | Unix timestamp of last background reflection |
| `updated_at` | REAL NOT NULL | Unix timestamp, updated on every write |

#### creature_memory
Stores background reflections and summarised learning. Never exposed directly to the user.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `created_at` | REAL NOT NULL | Unix timestamp |
| `memory_type` | TEXT NOT NULL | One of: reflection, summary, learning |
| `content` | TEXT NOT NULL | LLM-generated text |
| `lifecycle_stage` | TEXT NOT NULL | Stage at time of creation |

#### interaction_log
Stores user↔creature exchanges from `/talk` and `/care` responses.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `created_at` | REAL NOT NULL | Unix timestamp |
| `source` | TEXT NOT NULL | One of: user, creature |
| `interaction_type` | TEXT NOT NULL | One of: talk, care_response |
| `content` | TEXT NOT NULL | Message text |
| `care_type` | TEXT | Populated for care_response rows |

#### lifecycle_events
Append-only log of all stage transitions and significant events.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `created_at` | REAL NOT NULL | Unix timestamp |
| `event_type` | TEXT NOT NULL | See valid values below |
| `from_stage` | TEXT | Previous stage (null for birth) |
| `to_stage` | TEXT | New stage (null for non-transition events) |
| `notes` | TEXT | Optional human-readable context |

Valid `event_type` values: `born`, `egg_to_hatched`, `hatched_to_juvenile`, `juvenile_to_mature`, `entered_resting`, `exited_resting`, `budget_exhausted`, `budget_restored`, `relocated`.

The `entered_resting` event type covers transitions into `resting` from any source stage (`hatched`, `juvenile`, or `mature`). The `exited_resting` event type covers all wake transitions back to the stored `pre_resting_stage`. The `from_stage` and `to_stage` columns capture the specific stages involved in each case.

---

## 8. Creature lifecycle

Lifecycle stages:

- egg
- hatched
- juvenile
- mature
- resting
- exhausted  *(entered when the daily token budget is fully consumed; see Section 12)*

The lifecycle is driven by:

- time
- care events
- learning events
- token budget state

All transitions must generate a `lifecycle_events` record.

### 8.1 Transition thresholds

Transitions are evaluated at the end of every tick. All time values are in real elapsed seconds since the relevant milestone. All thresholds are defaults; they are not currently configurable via environment variable unless stated.

| Transition | Condition |
|---|---|
| `egg → hatched` | 300 seconds (5 minutes) have elapsed since birth AND at least 1 care event has been received |
| `hatched → juvenile` | 3 600 seconds (1 hour) have elapsed since hatching AND cumulative care events ≥ 3 |
| `juvenile → mature` | 86 400 seconds (24 hours) have elapsed since hatching AND cumulative care events ≥ 10 AND cumulative talk interactions ≥ 5 |
| `any active → resting` | The user calls `POST /rest` explicitly (see Section 14.3) from `hatched`, `juvenile`, or `mature`, OR energy falls below 0.15 while in `mature`. The originating stage is stored in `pre_resting_stage` before transition. Generates an `entered_resting` lifecycle event. |
| `resting → pre_resting_stage` | Energy recovers to ≥ 0.5 (recovery at 2× normal rate during resting) OR 3 600 seconds have elapsed in the resting stage. Restores the stage stored in `pre_resting_stage` and clears that field. Generates an `exited_resting` lifecycle event. |
| `any → exhausted` | Daily token budget reaches zero (see Section 12) |
| `exhausted → previous` | Daily token budget resets at midnight |

The "elapsed since hatching" clock starts from the timestamp of the `hatched` lifecycle event, not from birth. This means time spent in `egg` does not count toward juvenile or mature thresholds.

Transitions from `exhausted` resume the stage the creature was in before budget depletion. That prior stage is stored in `creature_state` as `pre_exhausted_stage` when the `exhausted` transition occurs.

---

## 9. Personality and identity

At birth a permanent personality seed is generated using `secrets.token_bytes(32)`. This seed is stored in `creature_state` as a hex string. Its sole purpose is to seed the random number generator used to derive trait values at birth, ensuring traits are reproducible from the seed if re-derivation is ever needed. Traits themselves are also stored directly in `creature_state` and are the authoritative values — the seed is a recovery mechanism, not the primary source.

The identity keypair (see Section 16) must be generated at birth, before any other state is persisted. This is a prerequisite for Milestone 1.

Traits (permanent, fixed at birth, stored in `creature_state`):

- `trait_curiosity`
- `trait_sociability`
- `trait_confidence`
- `trait_emotional_sensitivity`
- `trait_autonomy_preference`
- `trait_loneliness_rate`

These traits must be stable across restarts and exports. They are prefixed `trait_` in storage and code to distinguish them unambiguously from the mutable state values below.

---

## 10. Creature state

The creature must maintain the following mutable state values (all floats, range 0.0–1.0), which decay or grow over time and influence LLM prompt generation:

- `mood`
- `energy`
- `trust`
- `loneliness`
- `state_curiosity` *(distinct from `trait_curiosity`; this is the creature's current moment-to-moment curiosity level, which decays between interactions)*
- `stability`

The prefix `state_` is used only for `state_curiosity` to disambiguate from the permanent trait. All other state values are unambiguous and need no prefix.

---

## 11. Learning scope

The creature may only learn about:

- the user's tone
- the relationship
- its own past interactions

It must not learn tools, system behavior, or task strategies.

---

## 12. LLM interaction

The creature uses the LLM only for:

- reflection
- emotional expression
- journaling
- summarization

All LLM calls must go through a single wrapper component (`llm/wrapper.py`). The wrapper abstracts the provider entirely — callers pass a prompt and receive a response string. The wrapper handles base URL selection (direct provider or OpenClaw gateway, per Section 23.4), authentication, per-call token capping, budget enforcement, and error handling. No other component may make HTTP calls to an LLM endpoint.

### Token budget enforcement

The LLM wrapper must enforce:

- **Per-call token cap**: configurable via environment variable `HATCHLING_MAX_TOKENS_PER_CALL` (default: 300)
- **Per-day token budget**: configurable via environment variable `HATCHLING_MAX_TOKENS_PER_DAY` (default: 10 000)

The budget resets at local midnight.

When the daily budget is exhausted:

- The creature immediately transitions to the `exhausted` lifecycle stage
- All LLM calls are silently skipped (no error is raised to the caller)
- The daemon continues to run; care events and tick loop proceed normally
- The API `/status` response includes a `budget_exhausted: true` field
- A `lifecycle_events` record is written with type `budget_exhausted`
- When the budget resets, the creature returns to its previous stage and a `budget_restored` lifecycle event is written

The LLM must never be given system instructions that allow tool use.

---

## 13. Background loop

The daemon must run a single async background loop with a fixed tick interval.

**Tick interval**: 60 seconds (configurable via `HATCHLING_TICK_SECONDS`, minimum 10).

Each tick must:

1. Decay mood and stats according to the rates in Section 13.1
2. Increase loneliness linearly over time
3. Evaluate lifecycle transitions (see Section 8.1)
4. Evaluate whether a short background reflection should be triggered (see below)
5. Persist state to the database

### 13.1 Stat decay and growth rates

All rates are per-tick deltas applied to the 0.0–1.0 float values. Positive delta = increase. Negative delta = decrease. Rates are defaults; none are currently configurable via environment variable.

| Stat | Per-tick delta | Notes |
|---|---|---|
| `mood` | −0.005 | Recovers +0.05 on any care event or talk interaction |
| `energy` | −0.003 | Recovers at +0.006/tick during `resting` stage (2× rate) |
| `trust` | −0.001 | Grows +0.02 on talk interaction; never decays below current floor (floor starts at 0.0, rises by 0.01 each time trust exceeds 0.8) |
| `loneliness` | `+0.008 × (0.5 + trait_loneliness_rate)` | Multiplied by the trait so Gold (0.8) accumulates at `+0.0104/tick` and White (0.3) at `+0.0064/tick`. Resets to 0.0 on any care event or talk interaction. |
| `state_curiosity` | −0.004 | Grows +0.03 on talk interaction; boosted by `trait_curiosity` (multiply delta by `1.0 + trait_curiosity`) |
| `stability` | −0.002 | Grows +0.01 per tick during `resting` stage |

All values are clamped to [0.0, 1.0] after each tick. Values must never go negative or exceed 1.0.

### Background reflection rules

A background reflection is triggered only when ALL of the following conditions are true:

- The creature is not in the `exhausted` or `egg` lifecycle stage
- At least `HATCHLING_MIN_REFLECTION_INTERVAL` seconds have elapsed since the last reflection (default: 600 seconds / 10 minutes)
- The remaining daily token budget is sufficient for at least one call at the per-call cap
- The creature is not currently in the `resting` stage unless loneliness exceeds 0.8

Background reflections are short (subject to per-call token cap) and must not be surfaced as user interactions. They are written to `creature_memory` only.

---

## 14. API design

All endpoints must be local-only (127.0.0.1 binding only).

### Authentication

All API requests must include a static bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

The token is generated at first daemon startup, written to the platform data directory as `api_token`, and is readable only by the owning user (file mode 0600 on POSIX systems). The terminal UI client reads this file automatically. External callers must obtain the token manually.

Requests without a valid token receive `401 Unauthorized`. This applies to all endpoints including `/status`.

### Required endpoints

```
POST /birth
POST /care
POST /talk
POST /rest
GET  /status
GET  /needs-attention
POST /export
POST /import
```

The API must never expose internal prompts, raw memory records, or hidden state.

The `/status` response must include:

- current lifecycle stage
- creature name and colour
- current mood and key stats (mood, energy, trust, loneliness, state_curiosity, stability)
- `budget_exhausted` boolean
- `budget_remaining_today` token count

### 14.1 POST /birth

Described fully in Section 3.2.3. Creates a new creature. Returns `409 Conflict` if a creature already exists.

### 14.2 POST /care

Request body:
```json
{ "type": "gentle_attention" | "reassurance" | "quiet_presence" }
```

Applies a symbolic care event. Updates creature state immediately (see Section 13.1 for stat effects). If the budget allows, triggers a short LLM-generated creature response (subject to per-call token cap). Returns:
```json
{
  "response": "<creature expression or null if budget exhausted>",
  "state": { <current stat snapshot> }
}
```

### 14.3 POST /rest

Request body: empty (`{}`).

Manually transitions the creature to the `resting` stage if it is currently in `hatched`, `juvenile`, or `mature`. Returns `409 Conflict` if the creature is already resting, exhausted, or in the `egg` stage. The creature may produce a brief farewell expression if budget allows. Returns:
```json
{
  "response": "<creature expression or null>",
  "stage": "resting"
}
```

Auto-wake behaviour is governed by the `resting → pre_resting_stage` transition threshold in Section 8.1. The user does not need to call any endpoint to wake the creature — it transitions automatically on the next tick when the wake condition is met, returning to whichever stage it was in before resting.

### 14.4 POST /talk

Request body:
```json
{ "message": "<user free-text, max 500 characters>" }
```

Sends a user message to the creature. The daemon constructs a prompt incorporating current creature state, personality traits, colour vocabulary note, recent interaction history (up to last 5 exchanges from `interaction_log`), and the user's message. The LLM generates a creature response subject to the per-call token cap. The exchange is written to `interaction_log`. Returns:
```json
{
  "response": "<creature expression>",
  "state": { <current stat snapshot> }
}
```

If the budget is exhausted, returns:
```json
{ "response": null, "budget_exhausted": true }
```

`/talk` is not available during the `egg` stage. Attempts return `403 Forbidden` with a message indicating the creature has not yet hatched.

### 14.5 GET /needs-attention

Returns a structured object indicating whether the creature currently needs user attention, and the primary reason if so. Used by both the terminal UI (to show an alert indicator) and the OpenClaw Skill (to decide whether to notify the user).

Response:
```json
{
  "needs_attention": true | false,
  "reason": "lonely" | "low_energy" | "low_mood" | "hatching_soon" | null,
  "urgency": "high" | "medium" | "low" | null
}
```

`reason` and `urgency` are `null` when `needs_attention` is `false`. Priority order when multiple conditions are true: `lonely` → `low_mood` → `low_energy` → `hatching_soon`. Only the highest-priority reason is returned.

Thresholds: `lonely` when loneliness ≥ 0.7; `low_energy` when energy ≤ 0.2; `low_mood` when mood ≤ 0.2; `hatching_soon` when in `egg` stage and hatch threshold is within one tick.

---

## 15. Care events

Care events are symbolic.

Examples:

- gentle attention
- reassurance
- quiet presence

They update internal creature state and may trigger a short LLM response. Care events are subject to the standard per-call token cap. If the budget is exhausted, the state update still occurs but no LLM call is made.

---

## 16. Machine binding and identity

At creature birth:

- generate an ed25519 keypair using the `cryptography` library
- store the private key locally in the platform data directory (file mode 0600 on POSIX)
- store the public key inside creature metadata in the database

The private key file must be generated **before** any other state is written. If key generation fails, birth must be aborted cleanly.

At daemon startup:

- load the private key from disk
- derive its public key
- compare against the stored public key in creature metadata
- if they do not match, the daemon must refuse to start and print a clear error message
- if the private key file is missing, the daemon must refuse to start and print a clear error message

This binds the creature to a machine installation. There is no override flag.

---

## 17. Export and import

### Export

Export creates a sealed encrypted bundle (a single `.hatchling` file) containing:

- a complete copy of the SQLite database
- creature metadata (including the public key)
- the private identity key

The bundle must be encrypted using AES-256-GCM with a key derived from the user-provided passphrase via PBKDF2-HMAC-SHA256 with a random 16-byte salt and a minimum of 600 000 iterations. The salt and IV must be stored in the bundle header.

The bundle format:

```
[4 bytes magic: 0x4F434C48]  ("OCLH")
[1 byte version: 0x01]
[16 bytes salt]
[12 bytes AES-GCM IV]
[remaining bytes: AES-256-GCM ciphertext + 16-byte tag]
```

The plaintext encrypted payload is a JSON document containing base64-encoded database bytes and base64-encoded private key bytes.

### Import

`POST /import` accepts a bundle file path and passphrase.

Before import begins:

- the daemon must verify no active creature exists at the target data path, OR the caller must pass `force: true` to overwrite
- if `force` is not set and a creature exists, the endpoint returns `409 Conflict` with a descriptive message
- if `force` is set and a creature exists, the existing database is backed up to a timestamped `.bak` file before being overwritten

After successful import:

- the identity key is installed to the platform data directory
- a `lifecycle_events` record with type `relocated` is written
- the creature machine-binding check runs immediately (derives the public key from the newly installed private key and compares it to the public key stored in the imported database)

The machine-binding check after import should always pass if the bundle is intact, since the private key and the database it was bundled with were created together. The rollback scenario exists to protect against bundle corruption — specifically, a case where the encrypted payload was partially written, decrypted incorrectly due to a wrong passphrase, or where the database and private key bytes in the payload became mismatched due to a bug in the export path. If the check fails after import, the rollback must: delete the newly installed private key file, restore the database from the `.bak` file created before import began, and return a `422 Unprocessable Entity` response with a clear error message.

The `POST /import` endpoint must only be callable when the daemon is running in a specific import-ready mode (started with `--allow-import`). In normal operation the endpoint returns `403 Forbidden`. This prevents accidental or malicious overwrite of a live creature.

---

## 18. Security boundaries

The daemon must not provide:

- filesystem access
- shell execution
- network access

The LLM must not be given any system instructions that allow tool use.

---

## 19. OpenClaw integration model

OpenClaw integration is strictly external. No OpenClaw code may be imported by this project.

The correct integration mechanism for this project is an **OpenClaw Skill** — a plain directory containing a `SKILL.md` file with YAML frontmatter and markdown instructions. The Skill teaches the OpenClaw agent how to reach the Hatchling daemon's two externally-safe endpoints (`POST /care` and `GET /status`) using standard HTTP. No in-process plugin, no shared runtime, no OpenClaw SDK.

### 19.1 Skill directory

The repository must include a ready-to-use skill directory at:

```
openclaw-hatchling/
  skill/
    SKILL.md
    references/
      api.md
```

Users install the skill by dropping the `skill/` directory into `~/.openclaw/skills/hatchling/` or their workspace `skills/hatchling/` directory, then starting a new OpenClaw session. It can also be published to ClawHub for one-command installation.

### 19.2 SKILL.md specification

The `skill/SKILL.md` file must conform to the AgentSkills / OpenClaw format: YAML frontmatter followed by markdown instructions.

The frontmatter must declare:

```yaml
---
name: hatchling
version: 1.0.0
description: Check on your Hatchling companion creature, send it care, or see how it is feeling. Use when the user mentions their hatchling, companion creature, or wants to check in on or care for their creature.
author: openclaw-hatchling
metadata:
  clawdbot:
    emoji: "🥚"
    requires:
      env:
        - name: HATCHLING_API_TOKEN
          description: Bearer token for the local Hatchling daemon. Found in the Hatchling data directory as `api_token`.
      network:
        - localhost
permissions:
  - network:outbound
---
```

Key requirements for the frontmatter:

- `description` is used by OpenClaw as a trigger phrase. It must be written in plain language matching how a user would naturally ask about their creature (e.g. "how is my hatchling", "give my creature some attention", "check on my companion"). Do not write marketing copy.
- `metadata.clawdbot` is the preferred metadata namespace (`metadata.openclaw` is an accepted alias).
- `permissions` must declare `network:outbound`. Do not declare filesystem, shell, or any other permission — ClawHub reviewers will reject skills with excessive permissions.
- The `HATCHLING_API_TOKEN` environment variable must be documented in `requires.env`. The user must set this variable in their OpenClaw environment config (`skills.entries.hatchling.env`) pointing to the value read from the `api_token` file in the Hatchling data directory.

### 19.3 Skill instructions

Below the frontmatter, the `SKILL.md` must provide clear, concise instructions for the agent. The instructions must cover:

**Daemon address**: The Hatchling daemon listens on `http://127.0.0.1:52780` by default. If the user has configured a custom port via `HATCHLING_PORT`, use that value instead.

**Authentication**: Every request must include the header `Authorization: Bearer $HATCHLING_API_TOKEN`.

**Checking status** — `GET /status`:
Use this when the user asks how their creature is doing, what mood it is in, or whether it needs attention. Parse and present the response fields (`lifecycle_stage`, `mood`, `energy`, `trust`, `loneliness`, `budget_exhausted`) in warm, human terms. Do not expose raw field names or numeric values to the user. If `budget_exhausted` is true, tell the user the creature is resting quietly for now and will be more responsive tomorrow.

**Sending care** — `POST /care`:
Use this when the user wants to check in on, comfort, or spend time with their creature. The request body is:
```json
{ "type": "<care_type>" }
```
Valid `care_type` values are `gentle_attention`, `reassurance`, and `quiet_presence`. Choose the type based on the user's tone: use `reassurance` if the user seems worried, `quiet_presence` if the user just wants to be nearby, and `gentle_attention` as the default. Present any creature response from the API in the creature's own words, not paraphrased.

**What not to do**: Do not call `/talk`, `/rest`, `/export`, `/import`, or any other endpoint. These are reserved for the terminal UI or administrative use. Do not mention tokens, prompts, models, or any internal system detail to the user.

### 19.4 Reference file

The `skill/references/api.md` file must contain a concise reference of the two permitted endpoints (`GET /status`, `POST /care`) including example request and response JSON. This file is available to the agent as supplementary grounding but is not injected into every prompt.

### 19.5 ClawHub publication

When the project reaches Milestone 3, the skill should be published to ClawHub using:

```
clawhub publish ./skill
```

The ClawHub slug should be `hatchling`. The skill should be tagged `latest` on each release. A changelog entry must be included with each publish. The ClawHub listing description should match the frontmatter description field exactly.

---

## 20. Cross‑platform requirements

The project must run on:

- Linux
- Windows
- macOS

Rules:

- use platformdirs for data paths
- use HTTP localhost only
- no OS-specific IPC
- file permission hardening (mode 0600) must be applied on POSIX only; on Windows, rely on the user profile directory's default ACL

---

## 21. Technology stack

Language: Python 3.12+

Daemon:
- FastAPI
- asyncio
- httpx
- python-dotenv

Persistence:
- SQLite
- SQLAlchemy 2.x async
- aiosqlite *(required driver for SQLAlchemy async with SQLite)*

Crypto:
- cryptography

Terminal UI:
- textual *(required from Milestone 1 — the birth ceremony is a full-screen Textual app)*

Testing:
- pytest
- pytest-asyncio
- httpx (AsyncClient for API tests)

Packaging:
- pipx-friendly

---

## 22. Packaging and entry points

Provide two console scripts:

- openclaw-hatchlingd
- openclaw-hatchling

---

## 23. Configuration

Configuration must be minimal and local.

All configuration is read from environment variables. In addition, the daemon must support an optional `.env` file loaded at startup using `python-dotenv`. This allows users to configure the daemon persistently without relying on shell profiles, which are not inherited by background services.

### 23.1 LLM provider abstraction

Hatchling is model-agnostic. The LLM wrapper must call any OpenAI-compatible `/v1/chat/completions` endpoint using `httpx`. No provider-specific SDK may be imported. The entire provider surface is three environment variables: a base URL, an API key, and a model name. This single interface covers every supported backend without any provider-switching logic in the code.

Supported backends out of the box:

| Backend | `HATCHLING_LLM_BASE_URL` value | Notes |
|---|---|---|
| OpenAI | `https://api.openai.com/v1` | Standard cloud API |
| Ollama (local) | `http://127.0.0.1:11434/v1` | Free, fully local, no API key needed — set key to `ollama-local` |
| LM Studio | `http://127.0.0.1:1234/v1` | Free, fully local |
| Any OpenAI-compatible proxy | any `/v1`-suffixed URL | Covers hosted proxies, corporate gateways, etc. |
| OpenClaw gateway delegation | see Section 23.4 | Recommended for OpenClaw users |

The LLM wrapper must not perform any provider-specific request shaping beyond what the standard `/v1/chat/completions` body requires. Streaming is not used — all calls are single-shot completions.

### 23.2 Environment variable reference

| Variable | Purpose | Default |
|---|---|---|
| `HATCHLING_LLM_BASE_URL` | Base URL of the OpenAI-compatible endpoint, including `/v1` suffix | required (unless Section 23.5 gateway mode is active) |
| `HATCHLING_LLM_API_KEY` | API key for the provider. Use `ollama-local` for Ollama or LM Studio. | required (unless gateway mode is active) |
| `HATCHLING_LLM_MODEL` | Model name in the format expected by the endpoint (e.g. `gpt-4o-mini`, `ollama/llama3.3`, `llama3.2:latest`) | required (unless gateway mode is active) |
| `HATCHLING_USE_OPENCLAW_GATEWAY` | Set to `true` to delegate all LLM calls to a local OpenClaw gateway (see Section 23.5) | `false` |
| `HATCHLING_OPENCLAW_GATEWAY_URL` | Base URL of the local OpenClaw gateway | `http://127.0.0.1:18789` |
| `HATCHLING_OPENCLAW_GATEWAY_TOKEN` | Bearer token for the OpenClaw gateway (required when gateway mode is active) | unset |
| `HATCHLING_OPENCLAW_GATEWAY_MODEL` | Model name to pass to the OpenClaw gateway (see Section 23.5). If unset, the `model` field is omitted from the request and the gateway uses its configured default. | unset |
| `HATCHLING_MAX_TOKENS_PER_CALL` | Per-call token cap | 300 |
| `HATCHLING_MAX_TOKENS_PER_DAY` | Daily token budget | 10 000 |
| `HATCHLING_TICK_SECONDS` | Background loop interval | 60 |
| `HATCHLING_MIN_REFLECTION_INTERVAL` | Minimum seconds between background reflections | 600 |
| `HATCHLING_PORT` | Daemon HTTP port | 52780 |

When `HATCHLING_USE_OPENCLAW_GATEWAY=true`, the three `HATCHLING_LLM_*` variables are ignored. The daemon must log a clear startup message indicating which mode is active.

### 23.3 The .env file

The daemon must look for a `.env` file in the platform data directory at startup, before any other initialisation. If the file exists it is loaded silently. If it does not exist, startup continues normally — the file is never required.

The platform data directory path (obtained via `platformdirs.user_data_dir("openclaw-hatchling", "openclaw")`) is:

| Platform | Typical path |
|---|---|
| Linux | `~/.local/share/openclaw-hatchling/` |
| macOS | `~/Library/Application Support/openclaw-hatchling/` |
| Windows | `%APPDATA%\openclaw\openclaw-hatchling\` |

The `.env` file must be created with file mode 0600 on POSIX if it does not already exist. The daemon must never create it automatically — the user creates it. The README must include three minimal examples covering the main use cases:

```dotenv
# Option A — OpenAI cloud
HATCHLING_LLM_BASE_URL=https://api.openai.com/v1
HATCHLING_LLM_API_KEY=sk-...
HATCHLING_LLM_MODEL=gpt-4o-mini
```

```dotenv
# Option B — Ollama local model (free, no data leaves your machine)
HATCHLING_LLM_BASE_URL=http://127.0.0.1:11434/v1
HATCHLING_LLM_API_KEY=ollama-local
HATCHLING_LLM_MODEL=llama3.3
```

```dotenv
# Option C — OpenClaw gateway delegation (recommended if you already run OpenClaw)
HATCHLING_USE_OPENCLAW_GATEWAY=true
# HATCHLING_OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789  # only needed if non-default port
```

Environment variables already present in the process environment take precedence over values in the `.env` file (`python-dotenv` `override=False` behaviour). This allows service unit files to override specific values without editing the `.env` file.

### 23.4 API token bootstrap (for OpenClaw Skill users)

When the daemon starts for the first time it generates a random API token and writes it to the platform data directory as `api_token` (file mode 0600 on POSIX). Users who wish to connect the OpenClaw Skill must retrieve this value and add it to their OpenClaw environment config.

The exact steps must be documented in the README:

1. Start the daemon at least once: `openclaw-hatchlingd`
2. Read the token from the data directory:
   - Linux/macOS: `cat ~/.local/share/openclaw-hatchling/api_token` (Linux) or `cat ~/Library/Application\ Support/openclaw-hatchling/api_token` (macOS)
   - Windows: `type "%APPDATA%\openclaw\openclaw-hatchling\api_token"`
3. Add to OpenClaw config under `skills.entries.hatchling.env`:
   ```yaml
   skills:
     entries:
       hatchling:
         env:
           HATCHLING_API_TOKEN: "paste-token-here"
   ```

The terminal UI client (`openclaw-hatchling`) reads the `api_token` file automatically and requires no manual configuration.

### 23.5 OpenClaw gateway delegation mode

When `HATCHLING_USE_OPENCLAW_GATEWAY=true`, Hatchling delegates all LLM calls to the local OpenClaw gateway rather than calling a provider directly. This is the recommended configuration for users who already run OpenClaw, because it means:

- Model configuration lives in one place (OpenClaw's `openclaw.json`)
- Any model OpenClaw supports — cloud or local, Ollama, LM Studio, or otherwise — is automatically available to Hatchling with no additional configuration
- Local Ollama models already configured in OpenClaw work for Hatchling at zero additional cost
- The user benefits from OpenClaw's existing fallback and model routing logic

In this mode, the LLM wrapper sends requests to the OpenClaw gateway's local HTTP endpoint. The gateway routes the call through its own provider configuration and returns a standard completion response. Hatchling treats this identically to a direct provider call — the abstraction is transparent.

**Model name in gateway mode**: If `HATCHLING_OPENCLAW_GATEWAY_MODEL` is set, its value is included as the `model` field in the `/v1/chat/completions` request body, allowing you to target a specific model configured in OpenClaw (e.g. `ollama/llama3.3`). If it is not set, the `model` field is omitted entirely and the OpenClaw gateway uses its configured default model. This is the recommended default behaviour for most users.

**Important constraint**: Even in gateway delegation mode, Hatchling's own per-call token cap and daily budget enforcement remain fully active. The budget is tracked by Hatchling, not by OpenClaw. The two systems' token accounting are independent.

**Startup validation**: At daemon startup, if `HATCHLING_USE_OPENCLAW_GATEWAY=true`, the daemon must attempt a lightweight health check against the gateway URL. If the gateway is unreachable, the daemon must log a clear warning but continue starting — the creature should not be held hostage to OpenClaw's availability. LLM calls will fail gracefully (the same path as budget exhaustion) until the gateway becomes reachable.

**Gateway authentication**: OpenClaw's gateway uses its own bearer token for local API access. This token must be configured as `HATCHLING_OPENCLAW_GATEWAY_TOKEN`. If not set and gateway mode is active, the daemon logs a warning at startup. The token can be found in OpenClaw's gateway configuration.

---

## 24. Deployment and service configuration

The daemon is intended to run continuously as a background service. Because shell profile files (`~/.bashrc`, `~/.zshrc`, etc.) are not sourced by service managers, environment variables must be supplied via the `.env` file (Section 23.3) or injected directly into the service unit. Both approaches are documented below.

The `.env` file approach is preferred because it keeps secrets out of service unit files, which are often world-readable.

### 24.1 Linux — systemd user service

Create `~/.config/systemd/user/openclaw-hatchling.service`:

```ini
[Unit]
Description=OpenClaw Hatchling daemon
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/openclaw-hatchlingd
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable --now openclaw-hatchling
```

Secrets are read from the `.env` file in the platform data directory (Section 23.2). If an override is needed without editing the `.env` file, add an `Environment=` line to the `[Service]` block.

### 24.2 macOS — launchd user agent

Create `~/Library/LaunchAgents/ai.openclaw.hatchling.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>ai.openclaw.hatchling</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/openclaw-hatchlingd</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>/tmp/openclaw-hatchling.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/openclaw-hatchling.err</string>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/ai.openclaw.hatchling.plist
```

Secrets are read from the `.env` file in the platform data directory (Section 23.2). If individual variables must be injected via the plist, use an `EnvironmentVariables` dict — but prefer the `.env` file to keep secrets out of the plist.

### 24.3 Windows — Task Scheduler

Create a basic task using `schtasks`:

```powershell
schtasks /create /tn "OpenClaw Hatchling" /tr "openclaw-hatchlingd" /sc onlogon /rl limited /f
```

Alternatively, use Task Scheduler GUI: trigger "At log on", action "Start a program: openclaw-hatchlingd", run only when user is logged on.

Secrets are read from the `.env` file in the platform data directory (Section 23.2).

### 24.4 Template files in repository

The repository must include ready-to-use template files at:

```
openclaw-hatchling/
  deploy/
    openclaw-hatchling.service       (systemd)
    ai.openclaw.hatchling.plist      (launchd)
    openclaw-hatchling-task.xml      (Windows Task Scheduler export)
```

Each template must include comments directing the user to set the correct executable path and pointing them to Section 23.2 for secret management. The templates must not contain any placeholder secrets.

---

## 25. Development mode

The daemon must support a development mode:

```
--dev
```

Which:

- logs all lifecycle events to stdout
- logs token usage per call and running daily total to stdout
- disables background reflection (tick loop still runs, but reflection step is skipped)
- suppresses the `--allow-import` requirement (import is always permitted in dev mode)

---

## 26. Non-goals (explicit)

This project must not implement:

- task automation
- web browsing
- code execution
- tool planning
- multi-agent collaboration
- remote access

---

## 27. Initial implementation milestones

### Milestone 1

- `.gitignore` committed as the very first commit
- identity keypair is generated (ed25519)
- API token is generated and written to disk
- `.env` file loading via python-dotenv wired up
- `POST /birth` endpoint implemented
- birth ceremony UI implemented (egg display, 3 rerolls, naming, confirmation)
- daemon boots with no existing creature and awaits birth
- creature is born with confirmed colour and name persisted
- machine-binding check passes on subsequent restarts
- deploy template files present in `deploy/`

### Milestone 2

- background tick loop (60-second interval)
- stat decay and loneliness growth
- care endpoint
- short LLM response subject to token cap
- token budget enforcement and `exhausted` lifecycle stage

### Milestone 3

- terminal UI
- status panel showing mood, energy, trust, loneliness, lifecycle stage
- creature sprite rendered in panel with correct colour tint and border
- all 30 sprites complete (5 colours × 6 stages) in `domain/sprites.py`
- exhausted stage renders with desaturated colour
- interaction feed
- creature emotional expressions displayed (not raw memory)

### Milestone 4

- export (encrypted bundle)
- import (with backup and `--allow-import` gate)
- `relocated` lifecycle event on successful import

### Milestone 5

- `skill/SKILL.md` completed and tested against a local OpenClaw installation
- `skill/references/api.md` written
- skill published to ClawHub as `hatchling` with `latest` tag

---

## 28. Tone and style for all user-visible output

The creature must:

- speak in short, emotionally expressive sentences
- avoid technical language
- avoid system references
- never mention tokens, prompts, models, or budget state

---

## 29. Important constraint for the implementing LLM

When implementing this repository:

- prioritize clarity over cleverness
- keep components small and testable
- do not over-engineer
- respect all isolation and safety boundaries defined above

This project is a companion creature.
It must always remain small, gentle, and safe.
