import os
import json

G0 = 9.80665  # m/s²

CONFIG_PATH = os.path.expanduser("~/.cea_analyzer_config.json")
DEFAULT_CONFIG = {
    "heatmap_interp": "nearest",
    "regression_degree": 2,
    "pdf_report_title": "CEA Analysis Report"
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            return json.load(open(CONFIG_PATH))
        except Exception:
            pass
    json.dump(DEFAULT_CONFIG, open(CONFIG_PATH, "w"), indent=2)
    return DEFAULT_CONFIG

CONFIG = load_config()
