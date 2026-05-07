"""Stripe pricing tiers configuration."""

from dataclasses import dataclass


@dataclass
class PricingTier:
    """A subscription pricing tier."""

    id: str
    name: str
    price_monthly: int  # in cents
    price_yearly: int  # in cents
    description: str
    features: list[str]
    limits: dict
    stripe_price_id: str | None = None
    stripe_product_id: str | None = None


PRICING_TIERS = [
    PricingTier(
        id="free",
        name="Personal",
        price_monthly=0,
        price_yearly=0,
        description="Get started with basic AI features",
        features=[
            "100 queries/month",
            "Basic RAG memory (10 docs)",
            "Ollama local inference",
            "1 agent type",
            "Community support",
        ],
        limits={
            "queries_per_month": 100,
            "max_documents": 10,
            "max_agents": 1,
            "max_context_length": 2048,
            "rate_limit_per_minute": 10,
        },
    ),
    PricingTier(
        id="pro",
        name="Cyber Ops",
        price_monthly=2900,
        price_yearly=29000,
        description="Advanced AI with enhanced capabilities",
        features=[
            "5,000 queries/month",
            "Enhanced RAG memory (500 docs)",
            "Cloud + local inference (Groq)",
            "All agent types",
            "Priority support",
            "Custom model fine-tuning",
        ],
        limits={
            "queries_per_month": 5000,
            "max_documents": 500,
            "max_agents": 5,
            "max_context_length": 8192,
            "rate_limit_per_minute": 60,
        },
    ),
    PricingTier(
        id="enterprise",
        name="Enterprise",
        price_monthly=9900,
        price_yearly=99000,
        description="Full-scale AI infrastructure",
        features=[
            "Unlimited queries",
            "Unlimited RAG memory",
            "Dedicated inference instances",
            "Unlimited agents",
            "24/7 dedicated support",
            "Custom model training",
            "SSO & SAML",
            "Audit logging",
        ],
        limits={
            "queries_per_month": -1,  # unlimited
            "max_documents": -1,
            "max_agents": -1,
            "max_context_length": 32768,
            "rate_limit_per_minute": 300,
        },
    ),
    PricingTier(
        id="defense",
        name="Defense",
        price_monthly=0,
        price_yearly=0,
        description="Government and defense-grade AI (contact sales)",
        features=[
            "Everything in Enterprise",
            "Air-gapped deployment",
            "Classified data handling",
            "Custom security protocols",
            "On-premise deployment",
            "FedRAMP compliance",
        ],
        limits={
            "queries_per_month": -1,
            "max_documents": -1,
            "max_agents": -1,
            "max_context_length": -1,
            "rate_limit_per_minute": -1,
        },
    ),
]


def get_tier(tier_id: str) -> PricingTier | None:
    """Get a pricing tier by ID."""
    for tier in PRICING_TIERS:
        if tier.id == tier_id:
            return tier
    return None


def get_all_tiers() -> list[PricingTier]:
    """Get all pricing tiers."""
    return PRICING_TIERS
