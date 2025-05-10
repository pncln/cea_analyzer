import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from config import CONFIG

def create_graphs(df):
    figs = {}
    pcs = sorted(df["Pc (bar)"].unique())

    # Isp vs O/F
    fig = Figure(figsize=(5,3))
    ax = fig.add_subplot(111)
    for pc in pcs:
        sub = df[df["Pc (bar)"] == pc]
        ax.plot(sub["O/F"], sub["Isp (s)"], 'o-', label=f'{pc} bar')
    ax.set(title="Isp vs O/F", xlabel="O/F", ylabel="Isp (s)")
    ax.legend(); ax.grid(True)
    figs["Isp"] = fig

    # T_chamber vs O/F
    fig = Figure(figsize=(5,3))
    ax = fig.add_subplot(111)
    for pc in pcs:
        sub = df[df["Pc (bar)"] == pc]
        ax.plot(sub["O/F"], sub["T_chamber (K)"], 's-', label=f'{pc} bar')
    ax.set(title="T_chamber vs O/F", xlabel="O/F", ylabel="T (K)")
    ax.legend(); ax.grid(True)
    figs["Temp"] = fig

    # Pressure Ratio vs O/F
    fig = Figure(figsize=(5,3))
    ax = fig.add_subplot(111)
    for pc in pcs:
        sub = df[df["Pc (bar)"] == pc]
        ax.plot(sub["O/F"], sub["Pressure Ratio"], '^-', label=f'{pc} bar')
    ax.set(title="Pressure Ratio vs O/F", xlabel="O/F", ylabel="P_throat/Pc")
    ax.legend(); ax.grid(True)
    figs["PressureRatio"] = fig

    # Enthalpy Drop vs O/F
    fig = Figure(figsize=(5,3))
    ax = fig.add_subplot(111)
    for pc in pcs:
        sub = df[df["Pc (bar)"] == pc]
        ax.plot(sub["O/F"], sub["Delta_H (kJ/kg)"], 'd-', label=f'{pc} bar')
    ax.set(title="Enthalpy Drop vs O/F", xlabel="O/F", ylabel="ΔH (kJ/kg)")
    ax.legend(); ax.grid(True)
    figs["Enthalpy"] = fig

    return figs

def create_heatmaps(df):
    """
    Returns {'Heatmaps': Figure} containing either:
      - two heatmaps (dIsp/dO/F and dIsp/dPc) when you have >1 Pc and >1 O/F, or
      - two line‐plots when you only have one axis varying.
    """
    interp = CONFIG.get("heatmap_interp", "nearest").lower()
    if interp == "linear":
        interp = "bilinear"
    valid = {
        'spline16','antialiased','catrom','mitchell','hermite','spline36',
        'hanning','bessel','hamming','none','quadric','lanczos','blackman',
        'sinc','bilinear','gaussian','nearest','kaiser','bicubic'
    }
    if interp not in valid:
        interp = "nearest"

    # compute gradients
    df1 = df.sort_values(['Pc (bar)', 'O/F']).copy()
    df1['dIsp_dO/F'] = (
        df1.groupby('Pc (bar)')['Isp (s)']
           .apply(lambda g: np.gradient(
               g.values,
               df1.loc[g.index, 'O/F'].values
           ))
           .reset_index(level=0, drop=True)
    )
    df2 = df.sort_values(['O/F', 'Pc (bar)']).copy()
    df2['dIsp_dPc'] = (
        df2.groupby('O/F')['Isp (s)']
           .apply(lambda g: np.gradient(
               g.values,
               df2.loc[g.index, 'Pc (bar)'].values
           ))
           .reset_index(level=0, drop=True)
    )

    piv1 = df1.pivot(index='Pc (bar)', columns='O/F', values='dIsp_dO/F')
    piv2 = df2.pivot(index='Pc (bar)', columns='O/F', values='dIsp_dPc')
    piv1 = piv1.apply(pd.to_numeric, errors='coerce')
    piv2 = piv2.apply(pd.to_numeric, errors='coerce')

    fig = Figure(figsize=(8, 4))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    # Check if we have a full 2D grid
    if piv1.shape[0] > 1 and piv1.shape[1] > 1:
        # true heatmaps
        X1, Y1 = np.meshgrid(piv1.columns.values, piv1.index.values)
        pcm1 = ax1.pcolormesh(X1, Y1, piv1.values.astype(float),
                              shading='auto', cmap='viridis')
        ax1.set(title='dIsp/dO/F', xlabel='O/F', ylabel='Pc (bar)')
        fig.colorbar(pcm1, ax=ax1)

        X2, Y2 = np.meshgrid(piv2.columns.values, piv2.index.values)
        pcm2 = ax2.pcolormesh(X2, Y2, piv2.values.astype(float),
                              shading='auto', cmap='viridis')
        ax2.set(title='dIsp/dPc', xlabel='O/F', ylabel='Pc (bar)')
        fig.colorbar(pcm2, ax=ax2)

    else:
        # fallback to 1D line plots
        # if only one Pc, plot dIsp/dO/F vs O/F
        ax1.plot(piv1.columns.values, piv1.values.flatten(), 'o-')
        ax1.set(title='dIsp/dO/F vs O/F', xlabel='O/F', ylabel='dIsp/dO/F')

        # if only one O/F, plot dIsp/dPc vs Pc
        ax2.plot(piv2.index.values, piv2.values.flatten(), 's-')
        ax2.set(title='dIsp/dPc vs Pc', xlabel='Pc (bar)', ylabel='dIsp/dPc')

    return {'Heatmaps': fig}