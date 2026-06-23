"""
QuantCAI Enterprise — Dynamic Cost Estimator
==============================================
Calculates execution costs based on backend pricing model,
shot count, circuit complexity, and error mitigation overhead.
Validates against organization/project budget limits.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional
from decimal import Decimal

logger = logging.getLogger("quantcai.cost_estimator")


def estimate_cost(
    backend_id: str,
    shots: int,
    circuit_depth: int,
    gate_count: int,
    error_mitigation: dict[str, bool] | None = None,
    optimization_level: int = 1,
    org_budget_remaining: Optional[float] = None,
) -> dict[str, Any]:
    """
    Calculate the estimated cost for running a quantum job.

    Supports three pricing models:
      - per_shot: task fee + per-shot cost (Amazon Braket model)
      - duration: session time * per-minute rate (IBM Qiskit Runtime model)
      - per_minute: GPU simulator billing with minimum billing threshold

    Args:
        backend_id: Target backend
        shots: Number of measurement shots
        circuit_depth: Circuit depth after transpilation
        gate_count: Total gate count
        error_mitigation: {"zne": bool, "pec": bool, "cdr": bool, "readout": bool}
        optimization_level: Transpilation optimization level (0-3)
        org_budget_remaining: Remaining budget for budget validation

    Returns:
        {
            "estimatedCost": float,
            "breakdown": {...},
            "warning": str | None,
            "optimizationTip": str | None,
            "effectiveShots": int,
        }
    """
    from services.backend_configs import get_backend_config

    if error_mitigation is None:
        error_mitigation = {}

    config = get_backend_config(backend_id)

    # -----------------------------------------------------------------------
    # Calculate effective shots (error mitigation overhead)
    # -----------------------------------------------------------------------
    effective_shots = shots
    mitigation_multiplier = 1

    if error_mitigation.get("zne"):
        mitigation_multiplier *= 3  # 3 noise factors by default
    if error_mitigation.get("pec"):
        mitigation_multiplier *= 10  # ~10x sampling overhead
    if error_mitigation.get("cdr"):
        mitigation_multiplier *= 2  # Calibration circuits

    effective_shots = shots * mitigation_multiplier

    # -----------------------------------------------------------------------
    # Calculate cost based on pricing model
    # -----------------------------------------------------------------------
    pricing_model = config.get("pricing_model", "free")
    breakdown = {}
    total = 0.0

    if pricing_model == "per_shot":
        # Amazon Braket model: task fee + per-shot cost
        task_fee = config.get("task_fee", 0.30)
        per_shot = config.get("per_shot_cost", 0.01)
        shot_cost = per_shot * effective_shots
        total = task_fee + shot_cost

        breakdown = {
            "taskFee": round(task_fee, 4),
            "perShotCost": per_shot,
            "shotCount": effective_shots,
            "shotCostTotal": round(shot_cost, 4),
            "mitigationOverhead": f"{mitigation_multiplier}x" if mitigation_multiplier > 1 else "none",
        }

    elif pricing_model == "duration":
        # IBM Qiskit Runtime model: estimated duration * per-minute rate
        rate_per_min = config.get("session_cost_per_min", 1.60)

        # Estimate execution duration
        # Rough heuristic: circuit_depth * shots / throughput_factor
        throughput = 50_000  # shots per second (approximate)
        estimated_seconds = max(1, (circuit_depth * effective_shots) / throughput)
        estimated_minutes = estimated_seconds / 60.0
        total = rate_per_min * estimated_minutes

        # Also calculate per-shot cost component
        per_shot = config.get("per_shot_cost", 0.0)
        if per_shot > 0:
            total += per_shot * effective_shots

        breakdown = {
            "sessionRatePerMin": rate_per_min,
            "estimatedDurationSec": round(estimated_seconds, 1),
            "estimatedDurationMin": round(estimated_minutes, 3),
            "sessionCost": round(rate_per_min * estimated_minutes, 4),
            "perShotCost": per_shot,
            "shotCostTotal": round(per_shot * effective_shots, 4) if per_shot > 0 else 0,
            "mitigationOverhead": f"{mitigation_multiplier}x" if mitigation_multiplier > 1 else "none",
        }

    elif pricing_model == "per_minute":
        # GPU simulator billing
        rate_per_min = config.get("cost_per_minute", 0.12)
        min_billing = config.get("min_billing_seconds", 3)

        # Estimate simulation duration
        throughput = 100_000  # Higher for simulators
        estimated_seconds = max(
            min_billing,
            (circuit_depth * effective_shots) / throughput
        )
        estimated_minutes = estimated_seconds / 60.0
        total = rate_per_min * estimated_minutes

        breakdown = {
            "ratePerMinute": rate_per_min,
            "estimatedDurationSec": round(estimated_seconds, 1),
            "minBillingSec": min_billing,
            "simulatorCost": round(total, 4),
            "mitigationOverhead": f"{mitigation_multiplier}x" if mitigation_multiplier > 1 else "none",
        }

    elif pricing_model == "free":
        total = 0.0
        breakdown = {"note": "Free tier — no charges"}

    # -----------------------------------------------------------------------
    # Budget validation
    # -----------------------------------------------------------------------
    warning = None
    optimization_tip = None

    if org_budget_remaining is not None and total > org_budget_remaining:
        warning = (
            f"Estimated cost ${total:.2f} exceeds remaining budget "
            f"${org_budget_remaining:.2f}. Job will be rejected."
        )

    # Optimization tips
    if mitigation_multiplier > 1 and pricing_model == "per_shot":
        base_cost = config.get("task_fee", 0.30) + config.get("per_shot_cost", 0.01) * shots
        optimization_tip = (
            f"Error mitigation increases cost by {mitigation_multiplier}x "
            f"(from ${base_cost:.2f} to ${total:.2f}). "
            f"Consider disabling PEC for cost savings."
        )

    if effective_shots > 10_000 and pricing_model == "per_shot":
        # Program set optimization
        single_task_fees = math.ceil(effective_shots / config.get("max_shots", 10000)) * config.get("task_fee", 0.30)
        bundled_task_fee = config.get("task_fee", 0.30)
        if single_task_fees > bundled_task_fee * 2:
            optimization_tip = (
                f"Using Program Sets saves "
                f"${single_task_fees - bundled_task_fee:.2f} on task fees "
                f"({single_task_fees / bundled_task_fee:.0f}x reduction)."
            )

    result = {
        "estimatedCost": round(total, 4),
        "breakdown": breakdown,
        "warning": warning,
        "optimizationTip": optimization_tip,
        "effectiveShots": effective_shots,
        "pricingModel": pricing_model,
        "backendId": backend_id,
    }

    logger.info(
        f"Cost estimate for '{backend_id}': ${total:.4f} "
        f"(shots={shots}, effective={effective_shots}, "
        f"mitigation={mitigation_multiplier}x)"
    )

    return result


def validate_budget(
    estimated_cost: float,
    org_budget: float,
    org_spent: float,
    project_budget: Optional[float] = None,
    project_spent: Optional[float] = None,
) -> dict[str, Any]:
    """
    Validate that a job's estimated cost fits within budget limits.

    Returns:
        {
            "approved": bool,
            "reason": str | None,
            "org_remaining": float,
            "project_remaining": float | None,
            "budget_utilization_pct": float,
        }
    """
    org_remaining = org_budget - org_spent
    project_remaining = None

    if org_budget > 0 and estimated_cost > org_remaining:
        return {
            "approved": False,
            "reason": (
                f"Organization budget exceeded. "
                f"Remaining: ${org_remaining:.2f}, "
                f"Estimated: ${estimated_cost:.2f}"
            ),
            "org_remaining": org_remaining,
            "project_remaining": project_remaining,
            "budget_utilization_pct": round((org_spent / org_budget) * 100, 1) if org_budget > 0 else 0,
        }

    if project_budget is not None and project_spent is not None:
        project_remaining = project_budget - project_spent
        if project_budget > 0 and estimated_cost > project_remaining:
            return {
                "approved": False,
                "reason": (
                    f"Project budget exceeded. "
                    f"Remaining: ${project_remaining:.2f}, "
                    f"Estimated: ${estimated_cost:.2f}"
                ),
                "org_remaining": org_remaining,
                "project_remaining": project_remaining,
                "budget_utilization_pct": round((project_spent / project_budget) * 100, 1) if project_budget > 0 else 0,
            }

    utilization = round((org_spent / org_budget) * 100, 1) if org_budget > 0 else 0

    return {
        "approved": True,
        "reason": None,
        "org_remaining": org_remaining,
        "project_remaining": project_remaining,
        "budget_utilization_pct": utilization,
    }
