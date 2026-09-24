"""
MPLADS Autonomous Audit & Intelligence Engine — Detectors Package.
"""

import sys
from pathlib import Path

# Ensure detectors directory and project root are in sys.path
_this_dir = Path(__file__).resolve().parent
_repo_root = _this_dir.parent
for _dir in [str(_this_dir), str(_repo_root)]:
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from src.engine.coordinator import DetectionResultSet, MPLADSEngine
from src.engine.detectors import AnomalyCategory, AnomalyFinding, CoreDetectionEngine

__all__ = [
    "MPLADSEngine",
    "DetectionResultSet",
    "CoreDetectionEngine",
    "AnomalyFinding",
    "AnomalyCategory",
]
