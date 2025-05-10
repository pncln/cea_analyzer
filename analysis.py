import numpy as np
from config import G0
from util import ambient_pressure

# universal gas constant
R_univ = 8.31446261815324  # J/(mol·K)

def compute_system(df):
    """
    Compute nozzle/system parameters from the DataFrame.
    Returns a dict with keys:
      'best', 'At', 'Ae', 'alts', 'Fs', 'mdot', 'dv', 'tb'
    """
    # 1) Best‐Isp row
    best = df.loc[df["Isp (s)"].idxmax()]

    # 2) Extract core parameters
    Isp_s = best["Isp (s)"]               # Isp in seconds
    Pc    = best["Pc (bar)"] * 1e5        # chamber pressure in Pa
    Tch   = best["T_chamber (K)"]         # chamber temperature in K
    ar    = best["Expansion Ratio"]       # A_e/A*
    if ar is None:
        raise ValueError("Expansion Ratio is missing")

    # 3) System assumptions
    mveh    = 1000.0    # vehicle mass [kg]
    mprop   = 100.0     # propellant mass [kg]
    m0      = 200.0     # initial mass for Δv calc [kg]
    gamma   = 1.2       # specific heat ratio
    MW      = 0.022     # molecular weight [kg/mol]
    R       = R_univ / MW  # specific gas constant [J/(kg·K)]

    # 4) Thrust & mass flow
    F     = mveh * G0            # assume hover thrust [N]
    mdot  = F / (Isp_s * G0)     # mass flow [kg/s]

    # 5) Choked‐flow throat area A* from mdot equation:
    #    mdot = A* · Pc/√Tch · √(γ/R) · (2/(γ+1))^((γ+1)/(2(γ−1)))
    choke = (2.0/(gamma+1.0))**((gamma+1.0)/(2.0*(gamma-1.0)))
    At    = mdot * np.sqrt(Tch) / (Pc * np.sqrt(gamma/R) * choke)

    # 6) Exit area
    Ae = At * ar

    # 7) Altitude sweep
    alt_max = 10000.0  # meters
    alts    = np.linspace(0, alt_max, 20)
    Fs, Is  = [], []
    for a in alts:
        pa = ambient_pressure(a)
        # nozzle thrust: mdot·Isp·g0 + pressure thrust
        Fe = mdot * Isp_s * G0 + (Pc - pa) * Ae
        Fs.append(Fe)
        Is.append(Fe / (mdot * G0))

    # 8) Burn time and delta‐V
    tb = mprop / mdot
    dv = Isp_s * G0 * np.log(m0 / (m0 - mprop))

    return {
        "best": best,
        "At": At,
        "Ae": Ae,
        "alts": alts,
        "Fs": Fs,
        "mdot": mdot,
        "dv": dv,
        "tb": tb
    }
