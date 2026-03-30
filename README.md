# crypto-project

A collection of interactive cryptography demos built with Python and tkinter.
Each demo visualises a specific attack or defense concept — no slides, no theory walls, just running code you can poke at.

**Zero external dependencies.** Everything uses Python's standard library.

---

## Project Structure

```
crypto-project/
├── config/
│   └── theme.py                    # shared UI theme (colours, fonts, widgets)
├── attack/
│   ├── seed_attack_simulator/      # Demo 1 — weak seeds
│   ├── randomness_visualizer/      # Demo 2 — random walk
│   ├── prng_vs_csprng/             # Demo 3 — sequence prediction
│   └── seed_image_generator/       # Demo 4 — Perlin noise images
└── defense/
    └── dashboard/                  # Demo 5 — defense techniques
```

---

## Requirements

- Python **3.10+** (uses `match` syntax and `int | None` type hints)
- `tkinter` — included with Python on Windows and macOS

**Linux only** — tkinter is a separate package:
```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

No `pip install` needed. All modules (`secrets`, `hashlib`, `random`, `math`, `threading`) are stdlib.

---

## Running the Demos

All commands are run from the **project root** (`crypto-project/`).

### Demo 1 — Seed Attack Simulator
> Shows how a predictable seed lets an attacker recover passwords, keys, and tokens.

```bash
python -m attack.seed_attack_simulator.main
```

Opens **3 windows**: Sender · Receiver · Attacker

| Window | What to do |
|--------|-----------|
| Sender | Tick "Use current time as seed" → click **GENERATE & TRANSMIT** |
| Receiver | Click **RECEIVE & VERIFY** → all fields match |
| Attacker | Click **INTERCEPT & ATTACK** → seed cracked in milliseconds |

---

### Demo 2 — Randomness Visualizer
> Three independent instances generate a random walk from the same seed. They always produce an identical path.

```bash
python -m attack.randomness_visualizer.main
```

Opens **4 windows**: Control panel + 3 walk windows (Instance A / B / C)

| Step | Action |
|------|--------|
| 1 | Type any seed in the control panel |
| 2 | Click **BROADCAST SEED →** |
| 3 | All three windows draw the same path - verified with |
| 4 | Click **ANIMATE** on any window to watch it draw step-by-step |
| 5 | Change seed → broadcast again - completely different but still identical across all three |

---

### Demo 3 — PRNG vs CSPRNG (Sequence Prediction)
> After observing 10 PRNG outputs, an attacker can predict every future value exactly.

```bash
python -m attack.prng_vs_csprng.main
```

Opens **2 windows**: Generator · Predictor

**PRNG attack:**
1. Generator is in PRNG mode (seed=42) by default
2. Click **▶ EMIT NEXT NUMBER** ~10 times in the Generator
3. Switch to Predictor → click **PREDICT NEXT**
4. Go back to Generator → click **EMIT NEXT NUMBER**
5. The prediction matches exactly - CORRECT every time

**CSPRNG comparison:**
1. In Generator, switch mode to **CSPRNG (secrets)**
2. Predictor's best guess is always - Wrong - no pattern to exploit

---

### Demo 4 - Seed-based Image Generator
> Same seed - identical Perlin noise image. Attacker brute-forces the seed from a fingerprint.

```bash
python -m attack.seed_image_generator.main
```

Opens **2 windows**: Generator · Attacker

| Step | Action |
|------|--------|
| 1 | Generator: type a seed (e.g. `42`) - click **GENERATE** |
| 2 | Try the quick-seed buttons (42, 43, 100…) — tiny seed change = completely different image |
| 3 | Attacker: set range `0 → 200` - click **ATTACK** |
| 4 | Attacker finds the seed in milliseconds and renders the exact same image |

---

### Demo 5 — Defense Dashboard
> Three defenses: secure seed generation, salting, and key stretching (PBKDF2).

```bash
python -m defense.dashboard.main
```

Opens **1 window** with three side-by-side panels:

| Panel | What to do |
|-------|-----------|
| ① Secure Seed | Click "Generate weak tokens" — identical within the same second. Then "Generate secure tokens" — different every time, 2²⁵⁶ possible seeds |
| ② Salt + Hashing | Type a password - "Hash ×3 (no salt)" — same hash every run. Then "Hash ×3 (with salt)" — different hash every run from the same password |
| ③ Key Stretching | Move the slider or use preset buttons (1k / 10k / 100k / 500k). Click **HASH & TIME IT** to see real ms/attempt. Watch the crack-time bar go from "days" to "years" |

---

## Concepts Covered

| Demo | Concept | Attack | Defense |
|------|---------|--------|---------|
| Seed Attack Simulator | PRNG determinism | Brute-force time-based seed | Use `secrets` / `os.urandom` |
| Randomness Visualizer | Seed reproducibility | Clone PRNG state | Never reuse seeds |
| PRNG vs CSPRNG | Sequence prediction | Shadow RNG prediction | Use CSPRNG for all tokens |
| Image Generator | Seed-to-output mapping | Fingerprint brute-force | Large keyspace |
| Defense Dashboard | Hardening techniques | — | `os.urandom`, salting, PBKDF2 |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'tkinter'`**
Install tkinter — see Linux instructions above. On Windows/macOS it ships with Python by default.

**Windows are opening off-screen**
Some multi-monitor setups place windows incorrectly. Resize or move the main window; child windows follow relative positioning.

**Attack doesn't find the seed**
The seed attack simulator and image generator attacker only search a fixed range. If the Generator used a manual seed outside the search range, widen the range or use the time-seed option.

**`SyntaxError` on Python 3.9 or older**
Update to Python 3.10+. The code uses `int | None` union type hints introduced in 3.10.
