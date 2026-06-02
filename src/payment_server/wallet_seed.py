"""
Wallet Seed -- Phase 13a

Seeds buyer and seller wallets at server startup.
Called from server.py alongside seed_dnsid_registry().

In production, wallets are provisioned once during merchant/buyer onboarding
via a LoginID biometric ceremony. The operator_id field records who authorized
the wallet creation -- the audit hook for regulatory KYC requirements.
"""

from src.payment_server.wallet import provision_wallet, WALLETS

BUYER_ID  = "did:web:localhost:8090"
SELLER_ID = "did:web:localhost:8080"

BUYER_DNSID  = "dnsid://supplymind.localhost/agents/procurement-001"
SELLER_DNSID = "dnsid://supplymind.localhost/agents/seller-001"


def seed() -> dict[str, str]:
    """
    Provision the three wallets needed for the SupplyMind demo.
    Returns a dict of role -> wallet_id for easy lookup.
    Idempotent: skips wallets already provisioned for an owner.
    """
    existing_owners = {w["owner_id"] for w in WALLETS.values()}
    handles = {}

    if BUYER_ID not in existing_owners or not any(
        w["wallet_type"] == "coinbase_usdc" for w in WALLETS.values() if w["owner_id"] == BUYER_ID
    ):
        w = provision_wallet(
            owner_id        = BUYER_ID,
            wallet_type     = "coinbase_usdc",
            initial_balance = 1000.00,
            owner_dnsid     = BUYER_DNSID,
            operator_id     = "cfo@supplymind.localhost",
        )
        handles["buyer_usdc"] = w["wallet_id"]

    if BUYER_ID not in existing_owners or not any(
        w["wallet_type"] == "stripe_link" for w in WALLETS.values() if w["owner_id"] == BUYER_ID
    ):
        w = provision_wallet(
            owner_id        = BUYER_ID,
            wallet_type     = "stripe_link",
            initial_balance = 5000.00,
            owner_dnsid     = BUYER_DNSID,
            operator_id     = "cfo@supplymind.localhost",
        )
        handles["buyer_fiat"] = w["wallet_id"]

    if SELLER_ID not in existing_owners or not any(
        w["wallet_type"] == "coinbase_usdc" for w in WALLETS.values() if w["owner_id"] == SELLER_ID
    ):
        w = provision_wallet(
            owner_id        = SELLER_ID,
            wallet_type     = "coinbase_usdc",
            initial_balance = 0.00,
            owner_dnsid     = SELLER_DNSID,
            operator_id     = "ops@supplymind.localhost",
        )
        handles["seller_usdc"] = w["wallet_id"]

    return handles
