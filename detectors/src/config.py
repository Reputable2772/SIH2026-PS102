"""
MPLADS Intelligence Engine — Configuration & Policy Parameters.

Encodes statutory MPLADS Guidelines 2023, ministerial monitoring rules,
and analytical baseline thresholds as specified in docs/Core.md (v0.6).
"""

from pathlib import Path
from dataclasses import dataclass

# Base directories
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class PolicyThresholds:
    """
    Statutory thresholds mandated by MPLADS Guidelines 2023 & Parliamentary monitoring.
    - SANCTION_SLA_DAYS: Para 3.2.4 (IDA mandate to issue sanction or rejection within 45 days)
    - EXECUTION_SLA_DAYS: Para 3.2.12 (Completion timeline generally not exceeding 1 year)
    - RS_POST_TENURE_SLA_DAYS: Administrative exception for Rajya Sabha post-tenure completion
    - DISBURSEMENT_STALL_DAYS: Ministerial 90-day post-sanction dormancy monitoring criterion
    """
    SANCTION_SLA_DAYS: int = 45          # Para 3.2.4: IDA mandate to sanction/reject within 45 days
    EXECUTION_SLA_DAYS: int = 365        # Para 3.2.12: General execution deadline not exceeding 1 year
    RS_POST_TENURE_SLA_DAYS: int = 540   # Rajya Sabha post-tenure completion window exception
    DISBURSEMENT_STALL_DAYS: int = 90    # Ministerial criterion: no payment within 3 months of sanction
    PROGRESS_STALL_DAYS: int = 180       # Observation window stall: no observed lifecycle event in 6 months


@dataclass(frozen=True)
class StatisticalThresholds:
    """Configurable baseline parameters for anomaly detection."""
    MIN_PEER_GROUP_SIZE: int = 10        # Minimum observations to compute confident peer baseline
    COST_OUTLIER_Z_SCORE: float = 2.5    # Z-score threshold for cost anomaly flagging
    COST_OUTLIER_IQR_FACTOR: float = 1.5 # IQR multiplier for Tukey outlier detection
    EXPENDITURE_OVERRUN_RATIO: float = 1.05  # Actual disbursement > 105% of sanctioned amount
    ROUND_NUMBER_VOUCHER_STEP: float = 10000.0  # Step for round voucher clustering analysis
    PENNY_DROP_MAX_AMOUNT: float = 10.0  # Threshold for account-validation test transactions (<= 10 INR)


@dataclass(frozen=True)
class NetworkThresholds:
    """Thresholds for entity relationship and concentration detection."""
    HHI_HIGH_CONCENTRATION: float = 2500.0  # DOJ / FTC threshold for highly concentrated markets
    HHI_MODERATE_CONCENTRATION: float = 1500.0
    TOP_ENTITY_SHARE_THRESHOLD: float = 0.40 # Entity capturing > 40% of district volume
    SIMILARITY_DUPLICATE_THRESHOLD: float = 0.82 # TF-IDF + metadata composite similarity threshold
    SIMILARITY_COST_WINDOW_RATIO: float = 0.20   # Cost difference within +/- 20%
    ENABLE_VENDOR_CONCENTRATION: bool = False    # Gated per Core.md FR-08 / AC-07 until entity disambiguation verified


@dataclass(frozen=True)
class RiskWeights:
    """Configurable weights for composite risk aggregation across detector families."""
    WEIGHT_COMPLIANCE: float = 0.30
    WEIGHT_FINANCIAL: float = 0.30
    WEIGHT_EXECUTION: float = 0.20
    WEIGHT_NETWORK_SIMILARITY: float = 0.20
    
    # Phase 4 ML supporting signal weights when integrated
    WEIGHT_ML_UNSUPERVISED: float = 0.10
    WEIGHT_ML_BREACH_PREDICTOR: float = 0.15


# Global singletons
POLICY = PolicyThresholds()
STATISTICS = StatisticalThresholds()
NETWORK = NetworkThresholds()
WEIGHTS = RiskWeights()
