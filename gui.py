import sys
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QWidget, QDockWidget,
    QVBoxLayout, QAction, QTabWidget, QTableView, QTextEdit,
    QStatusBar, QProgressBar, QFormLayout, QLineEdit, QPushButton, QSizePolicy, QInputDialog
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from parser import parse_cea_output
from models import PandasModel
from threads import ParserThread
from plots import create_graphs, create_heatmaps
from analysis import compute_system
from exporter import export_csv, export_excel, export_pdf
from config import CONFIG, CONFIG_PATH
from analysis import compute_system
from moc import generate_moc_contour

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEA Analyzer")
        self.resize(1000, 700)

        # Menu
        men = self.menuBar().addMenu("File")
        act_open = QAction("Open", self)
        # ignore the 'checked' bool and always call open_file() with no args
        act_open.triggered.connect(lambda checked=False: self.open_file())
        act_open.triggered.connect(self.open_file)
        men.addAction(act_open)

        # Tabs
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        # Data table
        self.tbl = QTableView(); self.tabs.addTab(self.tbl, "Data")
        # Graphs
        # Graphs (start with empty canvases; real plots come after loading data)
        self.graphTabs = QTabWidget(); self.figures, self.canvases = {}, {}
        for name in ["Isp","Temp","PressureRatio","Enthalpy"]:
            fig = Figure(figsize=(5,3))
            can = FigureCanvas(fig)
            w = QWidget(); l = QVBoxLayout(w); l.addWidget(can)
            self.graphTabs.addTab(w, name)
            self.figures[name] = fig
            self.canvases[name] = can
        self.tabs.addTab(self.graphTabs, "Graphs")

        # Summary & Optimization & Nozzle/System & Recommendations
        self.sum_text = QTextEdit(); self.sum_text.setReadOnly(True); self.tabs.addTab(self.sum_text, "Summary")
        self.opt_canvas = FigureCanvas(Figure(figsize=(8,4)))
        self.opt_text = QTextEdit(); self.opt_text.setReadOnly(True)
        wopt=QWidget(); lopt=QVBoxLayout(wopt); lopt.addWidget(self.opt_canvas); lopt.addWidget(self.opt_text)
        self.tabs.addTab(wopt, "Optimization")
        self.sys_canvas = FigureCanvas(self.figures["Isp"])  # placeholder
        self.sys_text = QTextEdit(); self.sys_text.setReadOnly(True)
        wsys=QWidget(); lsys=QVBoxLayout(wsys); lsys.addWidget(self.sys_canvas); lsys.addWidget(self.sys_text)
        self.tabs.addTab(wsys, "Nozzle/System")
        self.reco = QTextEdit(); self.reco.setReadOnly(True); self.tabs.addTab(self.reco, "Recommendations")

        # ─── MOC (Method of Characteristics) ───

        self.moc_canvas = FigureCanvas(Figure(tight_layout=True))
        self.moc_text   = QTextEdit()
        self.moc_text.setReadOnly(True)

        # Force the canvas to expand both horizontally & vertically,
        # and the text box to expand only horizontally.
        self.moc_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.moc_text.setSizePolicy(  QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Container for the MOC tab
        moc_widget = QWidget()
        moc_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        moc_layout = QVBoxLayout()
        moc_layout.setContentsMargins(0, 0, 0, 0)
        moc_layout.setSpacing(0)

        # Stretch=1 gives all extra space to the canvas; stretch=0 leaves
        # the text box at its preferred height.
        moc_layout.addWidget(self.moc_canvas, 1)
        moc_layout.addWidget(self.moc_text,   0)

        moc_widget.setLayout(moc_layout)
        self.tabs.addTab(moc_widget, "MOC")

        # Filters dock
        dock = QDockWidget("Filters", self)
        fw = QWidget(); fl = QFormLayout(fw)
        self.filters = {}
        for col in ["O/F","Pc (bar)","Isp (s)"]:
            mn, mx = QLineEdit(), QLineEdit()
            fl.addRow(f"{col} min:", mn); fl.addRow(f"{col} max:", mx)
            self.filters[col] = (mn, mx)
        btnA = QPushButton("Apply"); btnR = QPushButton("Reset")
        btnA.clicked.connect(self.apply_filters); btnR.clicked.connect(self.reset_filters)
        fl.addRow(btnA, btnR)
        dock.setWidget(fw); self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # Status bar
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.pbar = QProgressBar(); self.status.addPermanentWidget(self.pbar)

        # Export actions
        exp = men.addMenu("Export")
        act_csv = QAction("CSV", self); act_csv.triggered.connect(self.export_csv)
        act_xlsx = QAction("Excel", self); act_xlsx.triggered.connect(self.export_excel)
        act_pdf = QAction("PDF", self); act_pdf.triggered.connect(self.export_pdf)
        exp.addAction(act_csv); exp.addAction(act_xlsx); exp.addAction(act_pdf)

        # Data holders
        self.df_full = self.df = None

    def open_file(self, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Open CEA Output", "", "Text Files (*.txt *.out);;All Files (*)")
        if not path:
            return
        self.thread = ParserThread(path)
        self.thread.progress.connect(self.pbar.setValue)
        self.thread.finished.connect(self._on_parsed)
        self.thread.error.connect(lambda e: self.status.showMessage(f"Error: {e}", 5000))
        self.status.showMessage("Parsing...", 2000)
        self.thread.start()

    def _on_parsed(self, df):
        self.df_full = df.copy(); self.df = df
        self.update_all()
        self.status.showMessage("Done", 2000)

    def apply_filters(self):
        df = self.df_full.copy()
        for col, (mn, mx) in self.filters.items():
            try:
                lo = float(mn.text()) if mn.text() else None
                hi = float(mx.text()) if mx.text() else None
                if lo is not None: df = df[df[col] >= lo]
                if hi is not None: df = df[df[col] <= hi]
            except ValueError:
                pass
        self.df = df; self.update_all()

    def reset_filters(self):
        for mn, mx in self.filters.values():
            mn.clear(); mx.clear()
        self.df = self.df_full.copy(); self.update_all()

    def update_all(self):
        if self.df is None or self.df.empty:
            return
        self.update_table()
        self.update_graphs()
        self.update_summary()
        self.update_optimization()
        self.update_system()
        self.update_moc()
        self.update_recommendations()

    def update_table(self):
        self.tbl.setModel(PandasModel(self.df))

    def update_graphs(self):
        # build brand‐new figures
        new_figs = create_graphs(self.df)
        for name, new_fig in new_figs.items():
            canvas = self.canvases[name]
            # swap out the old Figure for the new one
            canvas.figure = new_fig
            canvas.draw()
            self.figures[name] = new_fig

    def update_summary(self):
        best = self.df.loc[self.df["Isp (s)"].idxmax()]
        html = (
            f"<h2>Summary</h2>"
            f"<p>Max Isp: <b>{best['Isp (s)']:.2f} s</b><br>"
            f"at O/F = <b>{best['O/F']:.2f}</b>, Pc = <b>{best['Pc (bar)']} bar</b></p>"
        )
        self.sum_text.setHtml(html)

    def update_optimization(self):
        # rebuild the heatmap figure
        hm = create_heatmaps(self.df)["Heatmaps"]
        # swap into the canvas
        self.opt_canvas.figure = hm
        self.opt_canvas.draw()
        # update the description
        self.opt_text.setHtml(f"<h2>Optimization (degree = {CONFIG['regression_degree']})</h2>")

    def update_moc(self):
        """
        Compute and plot the MOC nozzle wall from the ‘best’ case in self.df.
        """
        # 1) Find the best‐Isp row
        best = self.df.loc[self.df["Isp (s)"].idxmax()]

        # 2) Recompute system quantities (so we get At and Ae from compute_system)
        from analysis import compute_system
        res = compute_system(self.df)
        At = res["At"]       # throat area [m²]
        Ae = res["Ae"]       # exit  area [m²]

        # 3) Expansion ratio and throat radius
        area_ratio = Ae / At
        R_throat   = (At / np.pi) ** 0.5

        # 4) Generate the MOC contour (using your moc.py routine)
        from moc import generate_moc_contour
        gamma = 1.2    # or pull from config if you make it dynamic
        N     = 30     # number of characteristic lines
        x_wall, r_wall = generate_moc_contour(
            area_ratio=area_ratio,
            gamma=gamma,
            N=N,
            R_throat=R_throat
        )

        # 5) Clear & redraw the figure
        fig = self.moc_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        ax.plot(x_wall,  r_wall, lw=2, label="Upper contour")
        ax.plot(x_wall, -r_wall, lw=2, label="Lower contour")

        # 6) Autoscale + padding so lines never butt the edges
        ax.relim()
        ax.autoscale_view()
        ax.margins(x=0, y=0.05)

        ax.set_title("MOC Nozzle Contour")
        ax.set_xlabel("Axial (m)")
        ax.set_ylabel("Radius (m)")
        ax.legend(loc="best", frameon=False)

        # 7) Kill widget padding so the plot fills horizontally
        fig.tight_layout(pad=0)

        # 8) Render
        self.moc_canvas.draw()

        # 9) Update the explanatory text with the actual parameters
        self.moc_text.setHtml(
            "<h2>Method of Characteristics</h2>"
            "<p>Best case parameters:<br>"
            f"O/F = <b>{best['O/F']:.2f}</b>, "
            f"Pc = <b>{best['Pc (bar)']} bar</b><br>"
            f"Throat radius = <b>{R_throat:.3f} m</b><br>"
            f"Expansion ratio (Aₑ/A*) = <b>{area_ratio:.2f}</b></p>"
        )

    def update_system(self):
        """
        Compute & display nozzle sketch, thrust vs. altitude,
        prompting once if Expansion Ratio is missing.
        """
        # 1) Find the index of the best‐Isp row
        best_idx = self.df["Isp (s)"].idxmax()

        # 2) Pull that row
        best = self.df.loc[best_idx]

        # 3) Get (or prompt for) Expansion Ratio
        ar = best["Expansion Ratio"]
        if ar is None:
            ar, ok = QInputDialog.getDouble(
                self,
                "Missing Expansion Ratio",
                "Enter nozzle expansion ratio Aₑ/A*:",
                10.0,   # default
                1.0,    # min
                1e4,    # max
                2       # decimals
            )
            if not ok:
                return
            # Write it back into the one row
            self.df.at[best_idx, "Expansion Ratio"] = ar
            best = self.df.loc[best_idx]  # re‐fetch with updated ar

        # 4) Now call compute_system (which will use that ar)
        res = compute_system(self.df)
        At = res["At"]
        Ae = res["Ae"]

        # 5) Plot your nozzle sketch & thrust vs altitude (unchanged)
        fig = self.sys_canvas.figure
        fig.clear()

        ax1 = fig.add_subplot(121)
        x = [0.0, 0.2, 0.5, 1.0, 1.2]
        y = [0.0, 0.6, 1.0, 0.8, 0.8]
        ax1.plot(x, y, lw=2)
        ax1.plot(x, [-yy for yy in y], lw=2)
        ax1.set(aspect='equal', title='Nozzle Sketch', xlabel='Axial', ylabel='Radius')

        ax2 = fig.add_subplot(122)
        alts = res["alts"]
        Fs   = res["Fs"]
        ax2.plot(alts, Fs)
        ax2.set(title='Thrust vs Altitude', xlabel='Altitude (m)', ylabel='Thrust (N)')

        self.sys_canvas.draw()

        # 6) Show key numbers
        html = (
            f"<h2>Nozzle & System</h2>"
            f"<p>At = {At:.6f} m²<br>"
            f"Ae = {Ae:.6f} m²<br>"
            f"Expansion ratio = {ar:.2f}</p>"
        )
        self.sys_text.setHtml(html)


    def update_recommendations(self):
        b = self.df.loc[self.df["Isp (s)"].idxmax()]
        rec = (
            f"<h2>Recommendation</h2>"
            f"<p>Use O/F = {b['O/F']:.2f} at Pc = {b['Pc (bar)']} bar for max Isp.</p>"
        )
        self.reco.setHtml(rec)

    def export_csv(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if fn:
            export_csv(self.df, fn)

    def export_excel(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save Excel", "", "Excel Files (*.xlsx)")
        if fn:
            # summary as small DataFrame
            summary = pd.DataFrame([self.df.loc[self.df["Isp (s)"].idxmax()]])
            export_excel(self.df, summary, fn)

    def export_pdf(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if fn:
            figs = {"Cover": self.figures["Isp"]}
            figs.update(create_graphs(self.df))
            export_pdf(figs, CONFIG["pdf_report_title"], fn)
