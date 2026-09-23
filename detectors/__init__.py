"""
MPLADS Autonomous Audit & Intelligence Engine — Detectors Package.
"""

import sys
from pathlib import Path

# Ensure project root and detectors directory are in sys.path
_base = Path.cwd()
for _dir in [str(_base / "detectors"), str(_base)]:
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from src.engine.coordinator import MPLADSEngine, DetectionResultSet
from src.engine.detectors import CoreDetectionEngine, AnomalyFinding, AnomalyCategory

__all__ = [
    "MPLADSEngine",
    "DetectionResultSet",
    "CoreDetectionEngine",
    "AnomalyFinding",
    "AnomalyCategory",
]
