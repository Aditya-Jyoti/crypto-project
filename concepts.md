# How Every Attack and Defense Works

A plain-English walkthrough of the code behind each demo — what it does, why it works, what's wrong with the simulated victim, and how to fix it in real life.


## Attack 1 — Seed Attack Simulator

### What the victim does (Sender)

```python
seed = int(time.time())          # e.g. 1774728799
rng  = random.Random(seed)
password = "".join(rng.choice(charset) for _ in range(16))
token    = "".join(rng.choice(hexdigits) for _ in range(32))
key      = bytes(rng.randint(0, 255) for _ in range(16)).hex()
```

The sender uses the current Unix timestamp (seconds since 1970) as the seed for Python's `random` module, then generates a password, session token, and encryption key from it.

### Why this is bad

`random.Random(seed)` is a Mersenne Twister. It is **entirely deterministic** — the same seed always produces the same sequence of numbers. The timestamp seed is not secret: there are only ~86,400 possible values per day, and an attacker who intercepts any single output (the token, a password hash, anything) can recover every other value that was derived from the same seed.

The attacker only needs to know roughly *when* the token was generated, which is usually visible from network logs, HTTP response headers, or the token's own structure.

### What the attacker does

```python
candidates = range(now - window_seconds, now + 1)
for seed in candidates:
    if generate_session_token(seed) == intercepted_token:
        # seed found — derive password, key, everything
        return derive_all_from_seed(seed)
```

It iterates over every timestamp in the last N seconds, regenerates the token for each one, and compares. With a 60-second window that's at most 60 attempts. On a modern machine this takes under 1 millisecond. Once the seed is found, `derive_all_from_seed()` recovers the password, encryption key, and all other values that were generated from it — because they are all deterministic outputs of the same seed.

### What's wrong with the demo specifically

The demo uses `int(time.time())` which has second-level precision. Real applications sometimes use millisecond timestamps (e.g. `int(time.time() * 1000)`), which gives a 1000× larger search space but is still trivially brute-forceable. The XOR encryption used for the key is also intentionally broken — proper encryption is not the point here, the seed is.

### How to fix it in real code

```python
# Instead of:
seed = int(time.time())
rng  = random.Random(seed)
token = "".join(rng.choice(...) for _ in range(32))

# Do this:
token = secrets.token_hex(32)        # 256 bits of OS entropy
key   = secrets.token_bytes(32)      # same
```

The `secrets` module pulls randomness from the operating system's entropy pool (`/dev/urandom` on Linux/macOS, `CryptGenRandom` on Windows). There is no seed, no way to reproduce the output, and no relationship between outputs generated at different times.


## Attack 2 — Randomness Visualizer

### What the demo shows

Three completely independent `random.Random(seed)` instances — created separately, in different windows, knowing nothing about each other — all called with the same seed integer:

```python
def make_walk(seed: int) -> list:
    rng = random.Random(seed)          # fresh instance each time
    x, y = WALK_W // 2, WALK_H // 2
    pts = [(x, y)]
    for _ in range(500):
        x = max(4, min(WALK_W-4, x + rng.randint(-7, 7)))
        y = max(4, min(WALK_H-4, y + rng.randint(-7, 7)))
        pts.append((x, y))
    return pts
```

All three produce an identical list of 501 points. The ✅ confirmation comes from a direct list comparison: `all(o == my_pts for o in others)`.

### Why this matters

This demonstrates that **the seed is the only thing that matters** in a PRNG. It does not matter that you created a new instance. It does not matter that you are in a different process, machine, or language. Anyone who knows the seed can reproduce every output, in order, indefinitely.

This is the foundational problem. All the other attacks are just specific applications of it.

### What's wrong with the demo specifically

The demo uses a small integer seed (default `42`) to make the concept clear. In practice weak seeds often come from:

- `random.seed()` with no argument, which seeds from `time.time()` internally
- `random.seed(os.getpid())` — process IDs are sequential and public
- `random.seed(username)` — usernames are known
- `random.seed(hash(some_known_value))` — if the input is guessable, the seed is guessable

### How to fix it in real code

If you genuinely need a reproducible random sequence (procedural generation, simulations, testing), that's fine — but keep the seed secret, make it large, and generate it from `secrets`:

```python
seed = int.from_bytes(secrets.token_bytes(32), "big")  # 256-bit seed
rng  = random.Random(seed)
# Store seed securely if you need to reproduce the sequence later
```

For security-sensitive outputs (tokens, passwords, keys), never use `random` at all. There is no seed size that makes `random` safe for cryptographic use — the algorithm itself is not designed for it.


## Attack 3 — PRNG vs CSPRNG (Sequence Prediction)

### What the victim does (Generator)

```python
self._rng = random.Random(seed)   # seeded once at init

def _emit(self):
    value = self._rng.randint(0, 999999)
    self.shared["outputs"].append(value)
```

It initialises a `random.Random` instance with a known seed, then emits one integer at a time on demand.

### What the attacker does (Predictor)

```python
self._shadow = random.Random(seed)   # same seed — exact clone

def _on_emit(self):
    # Every time generator emits, shadow consumes the same call
    self._shadow.randint(0, 999999)

def _predict(self):
    predicted = self._shadow.randint(0, 999999)
    # generator will produce this exact value next
```

The predictor creates a shadow `random.Random` initialised with the same seed. Every time the generator emits a number, the shadow also calls `.randint()` to stay in sync. When the predictor wants to guess the next value, it simply calls `.randint()` on the shadow one step ahead of the generator. Because they share the same state, they produce the same output.

### Why this works

Python's `random` module uses the Mersenne Twister (MT19937). It is a finite state machine: given the same state, it always produces the same sequence. The seed fully determines the initial state. Once the attacker knows the seed, they own a perfect clone.

In this demo the attacker knows the seed directly (it is displayed). In a real attack the seed might be recovered by:
1. Brute-forcing (as in Demo 1)
2. Reconstructing the MT state from 624 consecutive 32-bit outputs (a well-known technique using the MT state inversion)
3. Side channels — reading logs, exploiting a weak seeding function, or timing attacks

### What happens with CSPRNG

When the generator switches to `secrets.randbelow(1000000)`, the predictor falls back to "guess the last seen value" — which is no better than random. The attacker scores 0/N in any reasonable run because `secrets` uses OS entropy with no repeating state to clone.

### What's wrong with the demo specifically

The demo simplifies the attack by giving the predictor the seed directly. A real MT state-reconstruction attack requires 624 outputs and knowledge of the output transformation, which is doable but more involved. The demo captures the concept cleanly without that complexity.

### How to fix it in real code

```python
# Never use this for tokens, sessions, OTPs, keys, nonces:
random.randint(0, 999999)

# Use this:
secrets.randbelow(1_000_000)
secrets.token_hex(32)
secrets.token_bytes(16)
```

The rule of thumb: if the value ever leaves your process (sent to a user, stored in a database, used to authenticate anything), it must come from `secrets` or `os.urandom`.


## Attack 4 — Seed-based Image Generator

### What the victim does (Generator)

```python
def make_perlin(seed: int):
    rng = random.Random(seed)
    p   = list(range(256))
    rng.shuffle(p)             # permutation table seeded from integer
    perm = (p + p) * 2
    ...
```

The Perlin noise algorithm needs a permutation table — a shuffled array of 0–255. Here it shuffles that table using `random.Random(seed)`. Every downstream noise value is determined entirely by the seed integer. The same seed → same shuffle → same gradients → same image, pixel for pixel.

The fingerprint is a 16-character SHA-256 hash of 16 probe values sampled from the noise field:

```python
def image_fingerprint(seed: int) -> str:
    noise  = make_perlin(seed)
    probes = [noise(x, y) for x in [0, 1.3, 2.7, 4.0]
                           for y in [0, 1.3, 2.7, 4.0]]
    raw = "".join(f"{v:.8f}" for v in probes) + str(seed)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
```

This fingerprint is what "leaks" — think of it as a hash of the image that someone could observe without seeing the full image, or a checksum transmitted alongside encrypted content.

### What the attacker does

```python
for seed in range(lo, hi + 1):
    if image_fingerprint(seed) == target_fp:
        grid = render_cells(seed, CELLS)
        # Render: identical image recovered
```

Sequential search across the seed space. Because the seed is a small integer (set to values like 42, 100, 999 in the demo), the full search space is tiny. Finding seed=42 in a range of 0–200 takes ~10ms and 42 attempts.

### Why this is bad

The seed encodes the entire output. A 32-bit integer seed has only ~4.3 billion possible values — less than an hour of brute-force on modern hardware. More critically, if the seed is a timestamp or a small number (as in this demo), the search space collapses to seconds.

This applies to any deterministic generation: procedurally generated game levels, "random" art, encryption keys, UUIDs (version 1 UUIDs embed a timestamp), OTP seeds.

### What's wrong with the demo specifically

The fingerprint function appends `str(seed)` to the probe values before hashing, which means the hash is technically dependent on the seed directly — a real fingerprint would only be the image data or a hash of it. Also, `hashlib.sha256(...).hexdigest()[:16]` truncates to 64 bits, which reduces collision resistance. For a demo this is fine; in production you would use the full 256-bit digest.

### How to fix it in real code

For procedural generation where reproducibility is desired, use a large random seed stored securely:

```python
seed = int.from_bytes(secrets.token_bytes(32), "big")
# Store seed in a secrets vault, not in the output or URL
```

For any output that must be unique and unpredictable (UUIDs, nonces, IVs):

```python
import uuid
unique_id = uuid.uuid4()           # uses os.urandom internally
nonce     = secrets.token_bytes(16)
```

Never use a sequential counter or timestamp as a seed for anything that needs to be unpredictable.


## Defense 1 — Secure Seed Generation

### What the weak version does

```python
def weak_token():
    rng = random.Random(int(time.time()))
    return "".join(rng.choice(string.hexdigits[:16]) for _ in range(16))
```

Seeds from the floor of the current timestamp in seconds. If two tokens are generated within the same second, they are identical. An attacker with a rough idea of when the token was created has a search space of a few thousand timestamps at most.

### What the secure version does

```python
def secure_token():
    return secrets.token_hex(8)   # 64 bits = 16 hex chars
```

`secrets.token_hex(n)` internally calls `os.urandom(n)`, which asks the OS kernel for bytes from its entropy pool. The kernel accumulates entropy from hardware events (disk timing, network interrupts, keyboard input, hardware RNG). There is no seed. There is no relationship between consecutive calls. The search space for 64 bits is 2⁶⁴ ≈ 18 quintillion.

### What's still weak about this demo

`secrets.token_hex(8)` produces 64 bits of entropy. For most tokens (session IDs, password reset links) you want at least 128 bits. Use `secrets.token_hex(16)` or `secrets.token_urlsafe(24)` in production.

### How to improve it

```python
session_token   = secrets.token_hex(32)       # 256 bits
password_reset  = secrets.token_urlsafe(32)   # URL-safe base64, 256 bits
api_key         = secrets.token_bytes(32)     # raw bytes
```


## Defense 2 — Salt + Hashing

### What the weak version does

```python
h = hashlib.sha256(pw.encode()).hexdigest()
```

Raw SHA-256 with no salt. SHA-256 is deterministic: the same password always produces the same hash. This means:

1. **Rainbow tables work.** Pre-computed tables mapping common passwords → SHA-256 hashes exist and are publicly available. An attacker who steals your database can look up `hunter2` in milliseconds.

2. **Duplicate passwords are visible.** If 1,000 users have the password `password123`, they all have the same hash. Crack one, crack all.

3. **SHA-256 is fast.** Modern GPUs can compute billions of SHA-256 hashes per second, making brute-force practical.

### What the secure version does

```python
salt = os.urandom(16)                                          # 128 bits, unique per user
h    = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 1)    # salt mixed in before hashing
```

The salt is a random value generated fresh for each password. It is stored alongside the hash (it is not secret — its job is to be unique, not secret). When the hash is computed, the salt is mixed into the input, so even if two users have the same password, their hashes are completely different. Rainbow tables must be rebuilt per-salt, which is computationally infeasible.

### What's still weak about this demo

The demo uses only 1 PBKDF2 iteration here — it is showing salting in isolation. In production you always combine salt with key stretching (see Defense 3). Also `hashlib.pbkdf2_hmac` with 1 iteration is barely better than raw SHA-256 in terms of speed.

### How to improve it

Use a purpose-built password hashing function that handles salt + stretching together:

```python
# Python 3.13+
import hashlib
dk = hashlib.scrypt(pw.encode(), salt=os.urandom(16), n=2**14, r=8, p=1)

# Or use the passlib or bcrypt library:
import bcrypt
hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12))
verified = bcrypt.checkpw(pw.encode(), hashed)
```

Argon2 is the current recommended standard (winner of the Password Hashing Competition). The `argon2-cffi` package wraps it for Python.


## Defense 3 — Key Stretching (PBKDF2)

### What it does

```python
dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, iters, dklen=32)
```

PBKDF2 (Password-Based Key Derivation Function 2) runs the password through a pseudorandom function (here HMAC-SHA256) `iters` times in a chain. Each iteration's output feeds into the next. The result is that one hash attempt costs `iters` times as long as a single SHA-256.

The demo runs this on your CPU and shows the real milliseconds. Then it estimates GPU crack time:

```python
gpu_pbkdf2_per_sec = 1_000_000_000 / iters
combinations       = 26**8               # 8-char lowercase: ~200 billion
seconds            = combinations / gpu_pbkdf2_per_sec
```

At 1,000 iterations: a GPU can do ~1,000,000 attempts/second → cracks 8-char lowercase in ~2 days.
At 100,000 iterations: ~10,000 attempts/second → ~8 months.
At 600,000 iterations: ~1,667 attempts/second → ~4 years.

### Why this works as a defense

An attacker cracking a stolen hash database must run the same expensive function for every guess. Increasing iterations multiplies their cost linearly while adding only one-time cost per legitimate login. The server runs PBKDF2 once per login attempt; the attacker must run it per guess across billions of attempts.

### What's wrong with the estimate

The GPU figure (10⁹ SHA-256/s) is a rough baseline and does not reflect actual PBKDF2 performance, which is lower due to sequential iteration dependencies. Real-world numbers vary by GPU and iteration count. The estimate is directionally correct but should not be taken as precise. More importantly, the estimate assumes only 8-char lowercase passwords — real passwords with mixed case, digits, and symbols have a vastly larger search space, making them far harder to crack even at low iteration counts.

### How to improve it

PBKDF2 with SHA-256 is acceptable but not the best choice today. Its weakness is that it is parallelisable on GPUs and FPGAs. Prefer:

- **Argon2id** — memory-hard, resistant to GPU and ASIC attacks. Use `argon2-cffi`.
- **bcrypt** — still widely used and well-audited. Use `bcrypt` package.
- **scrypt** — memory-hard, available in Python stdlib as `hashlib.scrypt`.

Minimum recommended settings as of 2024:
- PBKDF2-SHA256: 600,000 iterations (OWASP recommendation)
- bcrypt: cost factor 12
- Argon2id: m=64MB, t=3, p=4

Always re-hash stored passwords to stronger parameters when users log in, so your database gradually upgrades without forcing a password reset.


## Summary Table

| Demo | Vulnerable code | Why it fails | Real fix |
|------|----------------|-------------|----------|
| Seed Attack Simulator | `random.Random(int(time.time()))` | Timestamp has ~86,400 values/day; brute-forceable in < 1ms | `secrets.token_hex(32)` |
| Randomness Visualizer | `random.Random(seed).randint(...)` | Same seed → identical sequence across all instances forever | `secrets.randbelow()` for crypto; large secret seed for reproducible PRNG |
| PRNG Sequence Prediction | `random.Random(seed)` stream | Shadow clone predicts all future values after observing any output | `secrets.randbelow()` — no seed, no clone |
| Image Generator | `random.Random(seed)` permutation | Seed fully encodes the image; brute-force finds it in seconds | `secrets.token_bytes(32)` seed; never store seed in output |
| Defense — Secure Seed | `random.Random(int(time.time()))` | ~86,400 possible seeds per day | `secrets.token_hex(16)` minimum |
| Defense — Salt | `hashlib.sha256(pw)` | Rainbow tables; identical hashes for identical passwords | `os.urandom(16)` salt per user; store salt with hash |
| Defense — PBKDF2 | 1 iteration | Same speed as SHA-256; GPU cracks 8-char pw in hours | 600k+ iterations PBKDF2, or Argon2id |
