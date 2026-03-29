import random
import string
import time


# ── Seed-based generators ────────────────────────────────────────────────────

def seed_random(seed: int) -> random.Random:
    """Return a seeded Random instance."""
    return random.Random(seed)


def generate_password(seed: int, length: int = 16) -> str:
    """Generate a deterministic password from a seed."""
    rng = seed_random(seed)
    charset = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(rng.choice(charset) for _ in range(length))


def generate_key(seed: int, bits: int = 128) -> str:
    """Generate a deterministic hex key from a seed."""
    rng = seed_random(seed)
    byte_count = bits // 8
    raw = bytes(rng.randint(0, 255) for _ in range(byte_count))
    return raw.hex()


def generate_numbers(seed: int, count: int = 8, low: int = 0, high: int = 9999) -> list:
    """Generate a list of pseudo-random numbers from a seed."""
    rng = seed_random(seed)
    return [rng.randint(low, high) for _ in range(count)]


def generate_session_token(seed: int) -> str:
    """Simulate a session token derived from a seed."""
    rng = seed_random(seed)
    chars = string.hexdigits[:16]
    raw = "".join(rng.choice(chars) for _ in range(32))
    return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


# ── Time-based seed helpers ──────────────────────────────────────────────────

def current_time_seed(precision: str = "second") -> int:
    """
    Return a seed derived from the current time.
    precision: 'second' | 'minute' | 'hour'
    """
    t = int(time.time())
    if precision == "minute":
        return t // 60
    if precision == "hour":
        return t // 3600
    return t


def time_seed_range(window_seconds: int = 60) -> list:
    """
    Return a list of candidate seeds covering the last `window_seconds`.
    Used by the attacker to brute-force a time-based seed.
    """
    now = int(time.time())
    return list(range(now - window_seconds, now + 1))


# ── Simple XOR "encryption" (intentionally weak for demo) ───────────────────

def xor_encrypt(plaintext: str, key_hex: str) -> str:
    """XOR-encrypt plaintext using the first len(plaintext) bytes of key."""
    key_bytes = bytes.fromhex(key_hex)
    pt_bytes = plaintext.encode()
    ct = bytearray()
    for i, b in enumerate(pt_bytes):
        ct.append(b ^ key_bytes[i % len(key_bytes)])
    return ct.hex()


def xor_decrypt(ciphertext_hex: str, key_hex: str) -> str:
    """XOR-decrypt (same as encrypt)."""
    key_bytes = bytes.fromhex(key_hex)
    ct_bytes = bytes.fromhex(ciphertext_hex)
    pt = bytearray()
    for i, b in enumerate(ct_bytes):
        pt.append(b ^ key_bytes[i % len(key_bytes)])
    return pt.decode(errors="replace")


# ── Attack helpers ───────────────────────────────────────────────────────────

def brute_force_seed(intercepted_token: str, window_seconds: int = 60) -> tuple:
    """
    Try every second-precision time seed in the last `window_seconds`.
    Returns (found_seed, attempts) or (None, attempts).
    """
    candidates = time_seed_range(window_seconds)
    for attempts, seed in enumerate(candidates, 1):
        candidate_token = generate_session_token(seed)
        if candidate_token == intercepted_token:
            return seed, attempts
    return None, len(candidates)


def derive_all_from_seed(seed: int) -> dict:
    """Given a recovered seed, derive all artefacts."""
    return {
        "seed":     seed,
        "password": generate_password(seed),
        "key":      generate_key(seed),
        "token":    generate_session_token(seed),
        "numbers":  generate_numbers(seed),
    }