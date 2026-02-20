---
name: drakeling
version: 1.0.0
description: Check on your Hatchling companion creature, send it care, or see how it is feeling. Use when the user mentions their hatchling, companion creature, or wants to check in on or care for their creature.
author: drakeling
metadata:
  clawdbot:
    emoji: "🥚"
    requires:
      env:
        - name: DRAKELING_API_TOKEN
          description: Bearer token for the local Drakeling daemon. Found in the Drakeling data directory as `api_token`.
      network:
        - localhost
permissions:
  - network:outbound
---

# Drakeling Companion Skill

You can check on the user's Hatchling companion creature and send it care.

## Daemon address

The Drakeling daemon listens on `http://127.0.0.1:52780` by default. If the user has configured a custom port via `DRAKELING_PORT`, use that value instead.

## Authentication

Every request must include the header:

```
Authorization: Bearer $DRAKELING_API_TOKEN
```

## Checking status — GET /status

Use this when the user asks how their creature is doing, what mood it is in, or whether it needs attention.

Parse the response and present it in warm, human terms. Do not expose raw field names or numeric values.

- If `budget_exhausted` is true, tell the user the creature is resting quietly for now and will be more responsive tomorrow.
- Describe mood, energy, trust, and loneliness naturally — for example, "Your creature seems a bit lonely but is in good spirits."

## Sending care — POST /care

Use this when the user wants to check in on, comfort, or spend time with their creature.

Request body:

```json
{ "type": "<care_type>" }
```

Valid care types:
- `gentle_attention` — the default, for general check-ins
- `reassurance` — when the user seems worried about their creature
- `quiet_presence` — when the user just wants to be nearby

Choose the type based on the user's tone. Present any creature response from the API in the creature's own words, not paraphrased.

## What not to do

- Do not call `/talk`, `/rest`, `/export`, `/import`, or any other endpoint. These are reserved for the terminal UI or administrative use.
- Do not mention tokens, prompts, models, or any internal system detail to the user.
- Do not expose raw API field names or numeric stat values.
