"""
Unified Data Foundation Pipeline.

Orchestrates raw dataset loading, normalization, relational lifecycle reconstruction,
and quality scoring into the canonical analytical DataFrame.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
import pandas as pd
from src.config import DATA_DIR, PROCESSED_DIR
from src.data.loader import DataLoader
from src.data.normalizer import DataNormalizer
from src.data.lifecycle import WorkLifecycleReconstructor
from src.data.quality import DataQualityAuditor


class DataPipeline:
    """End-to-end Phase 0 Data Foundation pipeline."""

    def __init__(self, data_dir: Path = DATA_DIR, processed_dir: Path = PROCESSED_DIR):
        self.loader = DataLoader(data_dir=data_dir)
        self.normalizer = DataNormalizer()
        self.reconstructor = WorkLifecycleReconstructor()
        self.auditor = DataQualityAuditor()
        self.processed_dir = processed_dir

    def run(self, save_parquet: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Executes full Phase 0 pipeline:
        1. Loads raw datasets for Lok Sabha and Rajya Sabha.
        2. Normalizes dates, financial amounts, strings, and keys.
        3. Reconstructs unified lifecycle work records.
        4. Computes DQI scores and State Coverage Matrix.
        5. Caches canonical outputs.
        """
        # Load Lok Sabha
        ls_raw = self.loader.load_house_datasets("lok_sabha")
        ls_norm = {k: self.normalizer.normalize_dataset(v) for k, v in ls_raw.items()}
        ls_works = self.reconstructor.reconstruct(
            df_recommended=ls_norm["recommended"],
            df_sanctioned=ls_norm["sanctioned"],
            df_expenditures=ls_norm["expenditures"],
            df_completed=ls_norm["completed"],
            house="LOK_SABHA"
        )

        # Load Rajya Sabha
        rs_raw = self.loader.load_house_datasets("rajya_sabha")
        rs_norm = {k: self.normalizer.normalize_dataset(v) for k, v in rs_raw.items()}
        rs_works = self.reconstructor.reconstruct(
            df_recommended=rs_norm["recommended"],
            df_sanctioned=rs_norm["sanctioned"],
            df_expenditures=rs_norm["expenditures"],
            df_completed=rs_norm["completed"],
            house="RAJYA_SABHA"
        )

        # Combine national dataset
        all_works = pd.concat([ls_works, rs_works], ignore_index=True)

        # Compute DQI
        all_works = self.auditor.compute_work_dqi(all_works)

        # Generate Coverage Matrix
        coverage_matrix = self.auditor.generate_coverage_matrix(all_works)

        # Save processed artifacts
        if save_parquet:
            self.processed_dir.mkdir(parents=True, exist_ok=True)
            try:
                all_works.to_parquet(self.processed_dir / "canonical_works.parquet", index=False)
            except Exception:
                all_works.to_csv(self.processed_dir / "canonical_works.csv.gz", index=False, compression="gzip")
            coverage_matrix.to_csv(self.processed_dir / "coverage_matrix.csv", index=False)

        return all_works, coverage_matrix
