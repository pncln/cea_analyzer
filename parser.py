#!/usr/bin/env python3
import re
import pandas as pd
from config import G0

def parse_cea_output(path, progress_cb=None):
    """
    Parse a NASA-CEA output file and return a DataFrame with one row per CASE.
    Columns:
        'O/F', 'Pc (bar)', 'P_throat (bar)', 'Pressure Ratio', 'Expansion Ratio',
        'T_chamber (K)', 'T_throat (K)', 'H_chamber (kJ/kg)', 'H_throat (kJ/kg)',
        'Delta_H (kJ/kg)', 'Isp (m/s)', 'Isp (s)'
    """
    # Read entire file
    text  = open(path, 'r', encoding='utf-8', errors='ignore').read()
    lines = text.splitlines()

    # Find indices of "CASE =" lines
    case_idxs = [i for i, L in enumerate(lines) if L.lstrip().startswith("CASE =")]
    case_idxs.append(len(lines))

    records = []
    total = len(case_idxs) - 1

    for idx, (start, end) in enumerate(zip(case_idxs, case_idxs[1:])):
        if progress_cb:
            progress_cb(int(100 * idx / total))
        block = "\n".join(lines[start:end])

        # 1) Expansion ratio (Ae/At) from PERFORMANCE PARAMETERS
        m_ar = re.search(r"Ae/At\s+([\d\.]+)", block, re.IGNORECASE)
        ar   = float(m_ar.group(1)) if m_ar else 1.0

        # 2) Core combustion data
        m_of  = re.search(r"O/F=\s*([\d\.]+)",                 block)
        m_p   = re.search(r"P,\s*BAR\s+([\d\.]+)\s+([\d\.]+)", block)
        m_t   = re.search(r"T,\s*K\s+([\d\.]+)\s+([\d\.]+)",   block)
        m_h   = re.search(r"H,\s*KJ/KG\s+([-\d\.]+)\s+([-\d\.]+)", block)
        m_isp = re.search(r"Isp,.*?M/SEC\s+([\d\.]+)",         block)

        # Skip if any required field is missing
        if not all([m_of, m_p, m_t, m_h, m_isp]):
            continue

        # 3) Extract numeric values
        of    = float(m_of.group(1))
        pc    = float(m_p.group(1))
        pt    = float(m_p.group(2))
        tch   = float(m_t.group(1))
        tth   = float(m_t.group(2))
        hch   = float(m_h.group(1))
        hth   = float(m_h.group(2))
        isp_m = float(m_isp.group(1))
        isp_s = isp_m / G0

        # 4) Append record
        records.append({
            "O/F":               of,
            "Pc (bar)":          pc,
            "P_throat (bar)":    pt,
            "Pressure Ratio":    pt/pc,
            "Expansion Ratio":   ar,
            "T_chamber (K)":     tch,
            "T_throat (K)":      tth,
            "H_chamber (kJ/kg)": hch,
            "H_throat (kJ/kg)":  hth,
            "Delta_H (kJ/kg)":   hch - hth,
            "Isp (m/s)":         isp_m,
            "Isp (s)":           isp_s
        })

    # 5) Build DataFrame
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # 6) Sort & reset index
    df.sort_values(["Pc (bar)", "O/F"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df
