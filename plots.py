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
