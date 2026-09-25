export type PriorityTier = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NORMAL';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: 'CENTRAL_AUDITOR' | 'STATE_NODAL_OFFICER' | 'DISTRICT_AUTHORITY' | 'MP_USER' | 'CITIZEN';
  organization: string;
  state?: string | null;
  district?: string | null;
  constituency?: string | null;
  mp_name?: string | null;
  permissions: string[];
  strict_isolation?: boolean;
}

export interface PlatformOverview {
  total_works: number;
  total_sanctioned_cr: number;
  total_disbursed_cr: number;
  completed_works: number;
  overall_completion_pct: number;
  overall_utilization_pct: number;
  avg_dqi_score: number;
  priority_summary: {
    CRITICAL: number;
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  top_categories: { name: string; count: number }[];
  active_states_count: number;
  active_districts_count: number;
}

export interface MacroTrend {
  tenure_or_year: string;
  sanctioned_cr: number;
  disbursed_cr: number;
  works_count: number;
  completion_rate: number;
}

export interface StateMapMetric {
  state_name: string;
  total_works: number;
  sanctioned_amount_cr: number;
  disbursed_amount_cr: number;
  completed_works: number;
  critical_alerts: number;
  high_alerts: number;
  medium_alerts: number;
  total_alerts: number;
  avg_dqi: number;
  utilization_pct: number;
  completion_pct: number;
  district_count: number;
  mp_count: number;
}

export interface DistrictMetric {
  district_name: string;
  state_name: string;
  total_works: number;
  sanctioned_amount_cr: number;
  disbursed_amount_cr: number;
  completed_works: number;
  completion_pct: number;
  utilization_pct: number;
  critical_flags: number;
  high_flags: number;
  primary_ia: string;
  risk_tier: string;
}

export interface RiskSignal {
  weight: number;
  name: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  explanation: string;
  action: string;
}

export interface CanonicalWork {
  work_rec_id: string;
  work_id: string;
  description: string;
  category: string;
  state_name: string;
  ida_name: string;
  mp_name: string;
  sanction_amount: number;
  total_disbursed: number;
  priority: PriorityTier;
  lifecycle_stage: string;
  dqi_score: number;
  primary_vendor: string;
  days_rec_to_sanction: number;
  days_since_sanction: number;
  risk_score?: number;
  risk_signals?: RiskSignal[];
}

export interface GovernanceDossier {
  work_rec_id: string;
  work_id: string;
  description: string;
  category: string;
  state_name: string;
  ida_name: string;
  mp_name: string;
  priority: PriorityTier;
  sanction_amount: number;
  total_disbursed: number;
  risk_score?: number;
  risk_signals?: RiskSignal[];
  five_questions: {
    q1_what_happened: string;
    q2_why_unusual: string;
    q3_compared_with_what: string;
    q4_supporting_evidence: Record<string, any>;
    q5_limitations: string;
  };
  next_review_actions: string[];
}

export interface ReviewState {
  work_rec_id: string;
  status: 'UNDER_REVIEW' | 'DQM_DISPATCHED' | 'RESOLVED' | 'ESCALATED_TO_CAG';
  checked_actions: string[];
  auditor_notes: string;
  auditor_name: string;
  updated_at: string;
}

export interface DetectorDefinition {
  code: string;
  name: string;
  category: string;
  phase: string;
  legal_basis: string;
  threshold: string;
  formula: string;
  description: string;
  prescribed_action: string;
}

export interface MPProfile {
  mp_name: string;
  house: string;
  state_name: string;
  constituency: string;
  allocated_amount_cr: number;
  sanctioned_amount_cr: number;
  disbursed_amount_cr: number;
  utilization_pct: number;
  total_works: number;
  completed_works: number;
  critical_flags: number;
  high_flags: number;
  risk_tier: string;
}

export interface VendorProfile {
  vendor_name: string;
  total_disbursed_cr: number;
  total_works: number;
  district_count: number;
  state_count: number;
  critical_works: number;
  delayed_works: number;
  primary_state: string;
  primary_category: string;
  hhi_risk: 'CONCENTRATED' | 'COMPETITIVE';
  has_recurrence_flag: boolean;
}
