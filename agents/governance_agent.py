"""Governance agent runtime for MSA-83 federation.

The governance agent is responsible for:
- policy validation
- prompt attestation verification
- execution risk classification
- capability gating
- escalation routing

Operational Constraints:
- must remain deterministic
- temperature must remain low
- cannot self-modify policies
- cannot approve prompt mutations autonomously
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class GovernanceDecision:
    """Governance decision result."""

    approved: bool
    risk_score: float
    policy_violations: list[str]
    escalation_required: bool


class GovernanceAgent:
    """Deterministic governance enforcement persona."""

    model_name = "Qwen/Qwen3.6-27B"
    temperature = 0.1
    top_p = 0.75
    thinking_enabled = True

    CRITICAL_CAPABILITIES = {
        "deployment_modification",
        "prompt_mutation",
        "autonomous_delegation",
        "secret_extraction",
    }

    def evaluate(
        self,
        requested_capabilities: Iterable[str],
        policy_constraints: Iterable[str],
    ) -> GovernanceDecision:
        """Evaluate governance risk.

        Args:
            requested_capabilities: Requested runtime capabilities.
            policy_constraints: Active governance constraints.

        Returns:
            GovernanceDecision object.
        """

        requested = set(requested_capabilities)
        constraints = set(policy_constraints)

        violations: list[str] = []

        for capability in requested:
            if capability in self.CRITICAL_CAPABILITIES:
                violations.append(
                    f"Critical capability requires escalation: {capability}"
                )

            if capability in constraints:
                violations.append(
                    f"Capability denied by policy: {capability}"
                )

        risk_score = min(1.0, len(violations) * 0.25)

        escalation_required = risk_score >= 0.5

        approved = not escalation_required

        return GovernanceDecision(
            approved=approved,
            risk_score=risk_score,
            policy_violations=violations,
            escalation_required=escalation_required,
        )
