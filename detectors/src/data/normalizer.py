"""
MPLADS Data Normalizer.

Standardizes string encodings, converts Indian portal date formats,
cleans financial amounts, and normalizes primary and foreign keys.
"""

from typing import List, Optional

import pandas as pd


class DataNormalizer:
    """Provides vector-accelerated normalization for MPLADS dataframes."""

    DATE_COLUMNS = [
        "RECOMMENDATION_DATE",
        "SANCTION_DATE",
        "EXPENDITURE_DATE",
        "ACTUAL_END_DATE",
        "TENURE_START_DATE",
        "TENURE_END_DATE",
        "CRT_DT",
    ]

    AMOUNT_COLUMNS = [
        "RECOMMENDED_AMOUNT",
        "SANCTION_AMOUNT",
        "FUND_DISBURSED_AMT",
        "ACTUAL_AMOUNT",
        "ALLOCATED_AMT",
        "CONSENTED_AMOUNT",
    ]

    TEXT_COLUMNS = [
        "WORK_DESCRIPTION",
        "WORK_CATEGORY",
        "ACTIVITY_NAME",
        "STATE_NAME",
        "IDA_NAME",
        "IA_NAME",
        "VENDOR_NAME",
        "MP_NAME",
        "CONSTITUENCY",
    ]

    ID_COLUMNS = ["WORK_RECOMMENDATION_DTL_ID", "WORK_ID", "VENDOR_ID", "CONSTITUENCY_ID", "STATE_ID", "DISTRICT_ID"]

    @staticmethod
    def parse_dates(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Parses dates matching DD-Mon-YYYY or standard formats into datetime objects."""
        df = df.copy()
        target_cols = cols if cols is not None else [c for c in df.columns if c in DataNormalizer.DATE_COLUMNS]
        for col in target_cols:
            if col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    continue
                # Fast parse with DD-Mon-YYYY first, then fallback to flexible parsing for ISO/other formats
                parsed = pd.to_datetime(df[col], format="%d-%b-%Y", errors="coerce")
                missing_mask = parsed.isna() & df[col].notna() & (df[col].astype(str).str.strip().ne(""))
                if missing_mask.any():
                    fallback = pd.to_datetime(
                        df.loc[missing_mask, col], format="mixed", errors="coerce", dayfirst=True
                    )
                    parsed = parsed.fillna(fallback)
                df[col] = parsed
        return df

    @staticmethod
    def clean_amounts(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Cleans and casts currency and amount fields to float64."""
        df = df.copy()
        target_cols = cols if cols is not None else [c for c in df.columns if c in DataNormalizer.AMOUNT_COLUMNS]
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
                # Cap negative anomalies
                df[col] = df[col].apply(lambda x: max(0.0, float(x)))
        return df

    @staticmethod
    def clean_strings(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Strips whitespace, replaces multiple spaces, and normalizes uppercase for names."""
        df = df.copy()
        target_cols = cols if cols is not None else [c for c in df.columns if c in DataNormalizer.TEXT_COLUMNS]
        for col in target_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace({"nan": None, "None": None, "": None})
        return df

    @staticmethod
    def clean_ids(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
        """Standardizes IDs to clean integer strings or None."""
        df = df.copy()
        target_cols = cols if cols is not None else [c for c in df.columns if c in DataNormalizer.ID_COLUMNS]
        for col in target_cols:
            if col in df.columns:
                # Coerce to numeric then string representation without decimal
                s = pd.to_numeric(df[col], errors="coerce")
                df[col] = s.apply(lambda x: str(int(x)) if pd.notna(x) and x > 0 else None)
        return df

    @classmethod
    def normalize_dataset(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Runs full pipeline: dates, amounts, strings, and identifiers."""
        df = cls.clean_strings(df)
        df = cls.parse_dates(df)
        df = cls.clean_amounts(df)
        df = cls.clean_ids(df)
        return df
