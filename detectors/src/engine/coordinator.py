"""
MPLADS Intelligence Engine — High-Level Core Analytical Coordinator.

This module provides the decoupled, production-grade programmatic entry point (MPLADSEngine)
for the entire analytical pipeline. It coordinates Phase 0 (Data Foundation), Phase 1
(Baselines & Core Detectors), Phase 2 (Cross-Work Intelligence), Phase 3 (Composite Risk
& Dossiers), and Phase 4 (ML Models & Integration).

Any user interface, CLI, background job, or third-party service can import and interact
with this engine without depending on argparse, terminal formatters, or web servers.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import json
import pandas as pd

from src.config import PROCESSED_DIR, MODELS_DIR
from src.data.pipeline import DataPipeline
from src.engine.baselines import BaselineEngine
from src.engine.detectors import CoreDetectionEngine, AnomalyFinding
from src.engine.cross_work import CrossWorkIntelligenceEngine
from src.engine.risk.composite_scorer import CompositeRiskScorer, WorkRiskScore
from src.engine.risk.dossier import DossierBuilder, GovernanceDossier
from src.validation.injection import AnomalyInjectionTester
from src.validation.benchmark import HistoricalAuditBenchmark
from src.validation.coverage_bias import CoverageBiasAuditor
from src.engine.cross_work.trends import TrendAnalyzer
from src.engine.reporting.html_report import generate_audit_report_html, generate_dossier_html


@dataclass
class DetectionResultSet:
    """Encapsulates the complete results of an anomaly detection and risk scoring run."""
    works: pd.DataFrame
    scores: List[WorkRiskScore]
    findings: List[AnomalyFinding]
    ml_metadata: Optional[Dict[str, Any]] = None

    @property
    def priority_summary(self) -> Dict[str, int]:
        """Returns the distribution of works across review priority tiers."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NORMAL": 0}
        for s in self.scores:
            p = s.priority.value if hasattr(s.priority, "value") else str(s.priority)
            counts[p] = counts.get(p, 0) + 1
        return counts

    def top_cases(self, n: int = 15, priority: Optional[str] = None) -> List[WorkRiskScore]:
        """Returns the top N cases ordered by composite severity and confidence."""
        filtered = self.scores
        if priority:
            p_upper = priority.upper()
            filtered = [s for s in filtered if (s.priority.value if hasattr(s.priority, "value") else str(s.priority)).upper() == p_upper]
        else:
            # By default prioritize critical and high
            filtered = [s for s in filtered if (s.priority.value if hasattr(s.priority, "value") else str(s.priority)).upper() in {"CRITICAL", "HIGH", "MEDIUM"}]
            if not filtered:
                filtered = self.scores

        return sorted(
            filtered,
            key=lambda x: (
                x.composite_severity,
                x.composite_confidence,
                len(x.category_severities),
                x.findings_count
            ),
            reverse=True
        )[:n]

    def get_dossier(self, work_rec_id: Any) -> GovernanceDossier:
        """Constructs an explainable 5-question audit dossier for a work from scored results."""
        target_id = str(work_rec_id)
        for s in self.scores:
            if str(s.work_rec_id) == target_id:
                return DossierBuilder.build_dossier(s)
        raise ValueError(f"Work with recommendation ID '{target_id}' not found in detection results.")

    def to_dataframe(self) -> pd.DataFrame:
        """Converts scored results into a structured DataFrame for analysis."""
        rows = []
        for s in self.scores:
            f_codes = [f.detector_code for f in s.findings]
            action = s.findings[0].next_review_action if s.findings else "None"
            rows.append({
                "work_rec_id": s.work_rec_id,
                "work_id": s.work_id,
                "state_name": s.state_name,
                "ida_name": s.ida_name,
                "sanction_amount": s.sanction_amount,
                "priority": s.priority.value if hasattr(s.priority, "value") else str(s.priority),
                "composite_severity": s.composite_severity,
                "composite_confidence": s.composite_confidence,
                "findings_count": len(s.findings),
                "anomaly_codes": ",".join(f_codes),
                "next_review_action": action
            })
        return pd.DataFrame(rows)

    def to_dict(self) -> Dict[str, Any]:
        """Converts results to a serializable dictionary."""
        return {
            "total_works": len(self.works),
            "priority_summary": self.priority_summary,
            "total_findings": len(self.findings),
            "scores": [
                {
                    "work_rec_id": s.work_rec_id,
                    "work_id": s.work_id,
                    "state": s.state_name,
                    "district": s.ida_name,
                    "priority": s.priority.value if hasattr(s.priority, "value") else str(s.priority),
                    "composite_severity": s.composite_severity,
                    "composite_confidence": s.composite_confidence,
                    "findings": [f.to_dict() for f in s.findings]
                }
                for s in self.scores
            ]
        }

    def export_json(self, output_path: Union[str, Path]) -> str:
        """Exports results to a formatted JSON file."""
        data = self.to_dict()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return str(path)

    def export_html(self, output_path: Union[str, Path], title: Optional[str] = None) -> str:
        """Exports an interactive, self-contained HTML audit dashboard."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        html_content = generate_audit_report_html(self, title=title or "MPLADS Intelligence Engine — Audit Findings Report")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return str(path)


class MPLADSEngine:
    """
    Decoupled Autonomous Intelligence Engine for MPLADS / e-SAKSHI data.
    Provides unified programmatic API across all phases.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        models_dir: Optional[Path] = None,
        enable_vendor_concentration: Optional[bool] = None
    ):
        from src.ml.integration import MLIntegrationManager
        self.data_dir = data_dir or PROCESSED_DIR
        self.models_dir = models_dir or MODELS_DIR
        self.ml_manager = MLIntegrationManager(models_dir=self.models_dir)
        self.baseline_engine = BaselineEngine()
        self.core_detection_engine = CoreDetectionEngine(baseline_engine=self.baseline_engine)
        self.cross_work_engine = CrossWorkIntelligenceEngine(enable_vendor_concentration=enable_vendor_concentration)
        self.composite_scorer = CompositeRiskScorer()

    def load_data(self, sample_size: Optional[int] = None, force_reload: bool = False) -> pd.DataFrame:
        """Loads canonical normalized works data, running Phase 0 pipeline if missing."""
        parquet_path = self.data_dir / "canonical_works.parquet"
        csv_path = self.data_dir / "canonical_works.csv.gz"

        if not force_reload and parquet_path.exists():
            works = pd.read_parquet(parquet_path)
        elif not force_reload and csv_path.exists():
            works = pd.read_csv(csv_path, low_memory=False)
        else:
            pipeline = DataPipeline(processed_dir=self.data_dir)
            works, _ = pipeline.run(save_parquet=True)

        if sample_size and sample_size < len(works):
            works = works.sample(n=sample_size, random_state=42).reset_index(drop=True)

        return works

    def fit_baselines(self, works: pd.DataFrame) -> None:
        """Fits dynamic peer group statistical baselines."""
        self.core_detection_engine.fit_baselines(works)

    def detect(
        self,
        works: Optional[pd.DataFrame] = None,
        sample_size: Optional[int] = None,
        include_cross_work: bool = True,
        include_ml: bool = True
    ) -> DetectionResultSet:
        """
        Executes the full anomaly detection and risk scoring pipeline.
        Produces explainable, ranked review priorities adhering to SIH PS102.
        """
        if works is None:
            works = self.load_data(sample_size=sample_size)
        elif sample_size and sample_size < len(works):
            works = works.sample(n=sample_size, random_state=42).reset_index(drop=True)

        # 1. Fit Baselines & Run Phase 1 Core Detectors
        self.core_detection_engine.fit_baselines(works)
        rule_findings = self.core_detection_engine.run(works)

        all_findings = list(rule_findings)

        # 2. Run Phase 2 Cross-Work Intelligence
        if include_cross_work:
            cross_findings = self.cross_work_engine.run(works, prior_findings=rule_findings)
            all_findings.extend(cross_findings)

        # 3. Phase 4 ML Integration & Scoring
        ml_metadata = None
        if include_ml and self.ml_manager.load_models():
            ml_findings = self.ml_manager.generate_ml_findings(works)
            all_findings.extend(ml_findings)
            scores = self.ml_manager.score_works_integrated(works, all_findings, ml_findings)
            ml_metadata = self.ml_manager.metadata
        else:
            scores = self.composite_scorer.score_works(works, all_findings)

        return DetectionResultSet(
            works=works,
            scores=scores,
            findings=all_findings,
            ml_metadata=ml_metadata
        )

    def generate_dossier(
        self,
        work_rec_id: Any,
        works: Optional[pd.DataFrame] = None,
        include_ml: bool = True
    ) -> GovernanceDossier:
        """
        Synthesizes the complete 5-question audit dossier for a specific work.
        """
        rec_id_str = str(work_rec_id)
        if works is None:
            works = self.load_data()

        target_work = works[works["WORK_RECOMMENDATION_DTL_ID"].astype(str) == rec_id_str]
        if target_work.empty:
            raise ValueError(f"Work with recommendation ID '{rec_id_str}' not found in canonical dataset.")

        # Run detection specifically on target work
        self.core_detection_engine.fit_baselines(works)
        findings = self.core_detection_engine.run(target_work)

        cross_findings = self.cross_work_engine.run(target_work, prior_findings=findings)
        all_findings = list(findings) + list(cross_findings)

        if include_ml and self.ml_manager.load_models():
            ml_findings = self.ml_manager.generate_ml_findings(target_work)
            all_findings.extend(ml_findings)
            scores = self.ml_manager.score_works_integrated(target_work, all_findings, ml_findings)
        else:
            scores = self.composite_scorer.score_works(target_work, all_findings)

        return DossierBuilder.build_dossier(scores[0])

    def export_dossier(
        self,
        dossier: GovernanceDossier,
        format: str = "html",
        output_path: Optional[Union[str, Path]] = None
    ) -> str:
        """Exports an individual case dossier to HTML or JSON."""
        format_lower = format.lower()
        if format_lower == "html":
            content = generate_dossier_html(dossier)
        elif format_lower == "json":
            content = json.dumps(dossier.to_dict(), indent=2, default=str)
        else:
            raise ValueError(f"Unsupported dossier export format: {format}")

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
            return str(p)
        return content

    def train_ml_models(self, works: Optional[pd.DataFrame] = None, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Trains Phase 4 ML models on real MPLADS data and persists artifacts."""
        if works is None:
            works = self.load_data(sample_size=sample_size)
        elif sample_size and sample_size < len(works):
            works = works.sample(n=sample_size, random_state=42).reset_index(drop=True)

        return self.ml_manager.train_all(works)

    def run_validation_suite(self, works: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Executes complete mathematical and empirical validation suite:
        1. Monotonicity Injection Test (AC-13)
        2. Cost Sensitivity Injection Test (AC-13)
        3. Historical CAG Benchmark Recall (AC-16)
        4. State Coverage-Bias Audit (AC-17)
        """
        mono_res = AnomalyInjectionTester.test_monotonicity()
        cost_res = AnomalyInjectionTester.test_cost_sensitivity()
        bench_res = HistoricalAuditBenchmark.evaluate_benchmark()

        bias_res = {"status": "SKIPPED", "summary": "Requires scraped canonical data"}
        try:
            if works is None:
                works = self.load_data(sample_size=5000)
            else:
                works = works.head(5000)

            self.core_detection_engine.fit_baselines(works)
            sample_findings = self.core_detection_engine.run(works)
            bias_res = CoverageBiasAuditor.audit_coverage_bias(works, sample_findings)
        except Exception:
            pass

        all_passed = (
            mono_res.get("status") == "PASS" and
            cost_res.get("status") == "PASS" and
            bench_res.get("status") == "PASS" and
            bias_res.get("status") == "PASS"
        )

        return {
            "status": "PASS" if all_passed else "WARNING",
            "monotonicity_injection": mono_res,
            "cost_sensitivity_injection": cost_res,
            "historical_cag_benchmark": bench_res,
            "coverage_bias_audit": bias_res
        }

    def analyze_trends(self, works: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Analyzes national macro operational and financial trends over fiscal years."""
        if works is None:
            works = self.load_data()
        return TrendAnalyzer.compute_yearly_trends(works)
