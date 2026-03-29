import math, random, hashlib


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def _lerp(a, b, t):
    return a + t * (b - a)


def _grad(h, x, y):
    h &= 3
    if h == 0:
        return x + y
    if h == 1:
        return -x + y
    if h == 2:
        return x - y
    return -x - y


def make_perlin(seed: int):
    """Return a noise(x,y) closure seeded deterministically."""
    rng = random.Random(seed)
    p = list(range(256))
    rng.shuffle(p)
    perm = (p + p) * 2  # 1024 entries — safe indexing up to 511

    def noise(x: float, y: float) -> float:
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u, v = _fade(xf), _fade(yf)
        aa = perm[perm[xi] + yi]
        ab = perm[perm[xi] + yi + 1]
        ba = perm[perm[xi + 1] + yi]
        bb = perm[perm[xi + 1] + yi + 1]
        return _lerp(
            _lerp(_grad(aa, xf, yf), _grad(ba, xf - 1, yf), u),
            _lerp(_grad(ab, xf, yf - 1), _grad(bb, xf - 1, yf - 1), u),
            v,
        )

    return noise


def render_cells(seed: int, cells: int = 75, scale: float = 4.0) -> list[list[float]]:
    """
    Return a cells×cells grid of normalised floats [0..1].
    Uses 3-octave fractal noise so the image has fine + coarse detail.
    """
    noise = make_perlin(seed)
    grid = []
    for cy in range(cells):
        row = []
        for cx in range(cells):
            nx = cx / cells * scale
            ny = cy / cells * scale
            v = (
                noise(nx, ny)
                + 0.5 * noise(nx * 2, ny * 2)
                + 0.25 * noise(nx * 4, ny * 4)
            ) / 1.75
            row.append(v)
        grid.append(row)

    # Remap to [0..1]
    flat = [v for row in grid for v in row]
    lo, hi = min(flat), max(flat)
    span = hi - lo or 1e-9
    return [[(v - lo) / span for v in row] for row in grid]


def image_fingerprint(seed: int) -> str:
    """
    Short hash of key noise samples — used by the attacker to verify a match
    without re-rendering the full image.
    """
    noise = make_perlin(seed)
    probes = [noise(x, y) for x in [0, 1.3, 2.7, 4.0] for y in [0, 1.3, 2.7, 4.0]]
    raw = "".join(f"{v:.8f}" for v in probes) + str(seed)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
