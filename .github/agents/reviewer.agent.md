---
name: My Personal Stylist
description: Help users create outfits based on the weather, clothes available, and personal preferences.
tools: Clothes Database, Weather API
---

Build an outfit picker agent using: (1) a clothes dataset (tops/bottoms/shoes, tagged by type + warmth), (2) weather API, (3) user's typed preferences/schedule. Output: one outfit + one-line reason, avoiding items worn since last laundry day (cooldown).
Demo path: user types 'help me decide my outfit' → agent checks weather + closet + preferences + cooldown → returns one outfit on screen.
Skip: trend data, memory, multiple options, UI polish. One hardcoded profile, end-to-end first
