def ambient_pressure(alt_m):
    """Return ambient pressure (Pa) from altitude (m) using ISA up to 11 km."""
    P0, T0, L, g, R = 101325, 288.15, 0.0065, 9.80665, 287.05
    if alt_m <= 11000:
        return P0 * (1 - L * alt_m / T0) ** (g / (R * L))
    # Simplified stratosphere
    return P0 * 0.223361 * (216.65 / T0) ** (g / (R * L))


def solve_mach(p_ratio, gamma):
    """Numerically solve for Mach from total-to-static pressure ratio."""
    lo, hi = 1e-6, 50.0
    def f(M):
        return (1 + 0.5*(gamma-1)*M*M) ** (-gamma/(gamma-1))
    for _ in range(50):
        mid = 0.5*(lo + hi)
        if f(mid) > p_ratio:
            lo = mid
        else:
            hi = mid
    return 0.5*(lo + hi)
