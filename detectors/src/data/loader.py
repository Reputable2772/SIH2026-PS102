"""
MPLADS Data Ingestion Engine.

Loads the 15 raw CSV datasets from e-SAKSHI representing Lok Sabha, Rajya Sabha,
administrative masters, and financial allocations.
"""

from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.config import DATA_DIR


class DataLoader:
    """Manages raw CSV loading with type specifications and caching."""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    def load_masters(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads state, district, and tenure lookup tables."""
        states = pd.read_csv(self.data_dir / "master_states.csv")
        districts = pd.read_csv(self.data_dir / "master_districts.csv")
        tenures = pd.read_csv(self.data_dir / "master_tenures.csv")
        return states, districts, tenures

    def load_house_datasets(self, house: str = "lok_sabha") -> Dict[str, pd.DataFrame]:
        """Loads all datasets for a specific chamber (lok_sabha or rajya_sabha)."""
        prefix = f"mplads_{house}"
        return {
            "recommended": pd.read_csv(self.data_dir / f"{prefix}_recommended.csv", low_memory=False),
            "sanctioned": pd.read_csv(self.data_dir / f"{prefix}_sanctioned.csv", low_memory=False),
            "completed": pd.read_csv(self.data_dir / f"{prefix}_completed.csv", low_memory=False),
            "expenditures": pd.read_csv(self.data_dir / f"{prefix}_expenditures.csv", low_memory=False),
            "allocations": pd.read_csv(self.data_dir / f"{prefix}_allocations.csv", low_memory=False),
            "calamity": pd.read_csv(self.data_dir / f"{prefix}_calamity.csv", low_memory=False),
        }

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Loads all datasets across both houses and master tables."""
        states, districts, tenures = self.load_masters()
        ls = self.load_house_datasets("lok_sabha")
        rs = self.load_house_datasets("rajya_sabha")
        return {
            "master_states": states,
            "master_districts": districts,
            "master_tenures": tenures,
            "ls_recommended": ls["recommended"],
            "ls_sanctioned": ls["sanctioned"],
            "ls_completed": ls["completed"],
            "ls_expenditures": ls["expenditures"],
            "ls_allocations": ls["allocations"],
            "ls_calamity": ls["calamity"],
            "rs_recommended": rs["recommended"],
            "rs_sanctioned": rs["sanctioned"],
            "rs_completed": rs["completed"],
            "rs_expenditures": rs["expenditures"],
            "rs_allocations": rs["allocations"],
            "rs_calamity": rs["calamity"],
        }
