from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

def export_csv(df: pd.DataFrame, filename: str):
    df.to_csv(filename, index=False)

def export_excel(df: pd.DataFrame, summary: pd.DataFrame, filename: str):
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)

def export_pdf(figures: dict, title: str, filename: str):
    """Save a sequence of matplotlib.Figure objects into a single PDF."""
    with PdfPages(filename) as pdf:
        # Cover page
        fig = figures.get("Cover")
        if fig:
            pdf.savefig(fig)
        for name, fig in figures.items():
            if name == "Cover":
                continue
            pdf.savefig(fig)
