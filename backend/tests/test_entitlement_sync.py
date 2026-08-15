"""
Regression tests for the payment -> entitlement path.

The bug these exist to prevent: entitlement checks read UserPlan.tier, but
UserPlan.tier was written in exactly one place — the moment a row is first
created — and never updated again. A UserPlan row is created the first time a
user touches any metered feature, which for a real customer happens long
before they pay. Payment webhooks wrote only to the Subscription table, so:

    sign up -> use a feature (UserPlan created as FREE) -> pay
    -> Subscription.plan = PRO, UserPlan.tier still FREE
    -> get_user_tier() returns FREE forever

Every paying customer received nothing they bought, and nothing failed loudly.

These tests are deliberately dependency-free where possible so they run in CI
without a database.
"""

import inspect

import pytest

import models as DBmodels
from tier_limits import plan_string_to_tier


class TestPlanStringToTier:
    """The two enums disagree on case, which is how lookups silently missed."""

    @pytest.mark.parametrize(
        "plan_str,expected",
        [
            ("pro", DBmodels.Tier.PRO),
            ("PRO", DBmodels.Tier.PRO),
            ("enterprise", DBmodels.Tier.ENTERPRISE),
            ("ENTERPRISE", DBmodels.Tier.ENTERPRISE),
            ("institutional", DBmodels.Tier.INSTITUTIONAL),
            ("api_metered", DBmodels.Tier.API_METERED),
            ("free", DBmodels.Tier.FREE),
        ],
    )
    def test_known_plans_map_case_insensitively(self, plan_str, expected):
        assert plan_string_to_tier(plan_str) is expected

    @pytest.mark.parametrize("bad", [None, "", "nonsense", "  "])
    def test_unknown_plans_fail_closed_to_free(self, bad):
        """An unrecognised plan must never grant paid access."""
        assert plan_string_to_tier(bad) is DBmodels.Tier.FREE

    def test_every_subscription_plan_value_is_mappable(self):
        """
        Guards against a new SubscriptionPlan member being added without a
        corresponding Tier mapping, which would silently downgrade buyers.
        """
        for plan in DBmodels.SubscriptionPlan:
            tier = plan_string_to_tier(plan.value)
            if plan is DBmodels.SubscriptionPlan.FREE:
                assert tier is DBmodels.Tier.FREE
            else:
                assert tier is not DBmodels.Tier.FREE, (
                    f"SubscriptionPlan.{plan.name} maps to FREE — paying customers "
                    f"on this plan would receive no entitlements."
                )


class TestBillingPathsSyncEntitlements:
    """
    Every code path that changes what a customer has paid for must call
    sync_user_plan_tier. Asserted by source inspection so the test does not
    need a database, Redis, or a live WarriorPlus IPN.
    """

    def test_warriorplus_ipn_syncs_user_plan(self):
        from routers import payment

        source = inspect.getsource(payment.warriorplus_ipn_handler)
        assert source.count("sync_user_plan_tier") >= 2, (
            "The IPN handler must sync entitlements on BOTH the sale path and "
            "the refund/cancel path. Writing only to the Subscription table "
            "leaves UserPlan.tier stale, which is the original bug."
        )

    def test_unmapped_product_does_not_grant_paid_tier(self):
        """
        _determine_tier_from_product used to default to PRO. Both product-ID
        settings default to "", so an unconfigured deployment granted Pro on
        every sale — including unrelated products sold from the same account.
        """
        from routers.payment import _determine_tier_from_product

        assert _determine_tier_from_product({}) is DBmodels.SubscriptionPlan.FREE
        assert (
            _determine_tier_from_product({"WP_ITEM_ID": "some-unrelated-offer"})
            is DBmodels.SubscriptionPlan.FREE
        )

    def test_ipn_uses_constant_time_key_comparison(self):
        from routers import payment

        source = inspect.getsource(payment.warriorplus_ipn_handler)
        assert "compare_digest" in source, (
            "The shared secret must be compared in constant time."
        )

    def test_mock_subscribe_is_disabled_in_production(self):
        """
        /api/billing/subscribe grants PRO to any authenticated caller. In
        production that is a self-serve free upgrade.
        """
        import billing

        source = inspect.getsource(billing.subscribe_plan)
        assert "is_production" in source, (
            "The mock checkout endpoint must be unreachable in production."
        )


class TestCbomEntitlement:
    """CBOM export is the Pro upgrade hook and must be quota-bounded."""

    def test_cbom_export_is_available_to_pro_not_only_enterprise(self):
        from routers import pqc

        source = inspect.getsource(pqc.perform_enterprise_pqc_scan_cyclonedx)
        assert 'tier == "FREE"' in source, (
            "CBOM export should gate on FREE, making it available to Pro and above."
        )

    def test_cbom_export_consumes_scan_quota(self):
        """
        Otherwise a Pro user bypasses the 50-scan monthly limit entirely by
        calling the CBOM route instead of the standard scan route.
        """
        from routers import pqc

        source = inspect.getsource(pqc.perform_enterprise_pqc_scan_cyclonedx)
        assert "monthly_pqc_scans" in source
        assert "with_for_update" in source, (
            "The quota increment must be row-locked to prevent concurrent bypass."
        )

    def test_cbom_is_returned_as_a_download(self):
        from routers.pqc import _cbom_download_response

        resp = _cbom_download_response({"bomFormat": "CycloneDX"}, "example.com")
        assert "attachment" in resp.headers["Content-Disposition"]
        assert "example.com" in resp.headers["Content-Disposition"]
        assert "cyclonedx" in resp.media_type

    def test_download_filename_is_sanitised(self):
        """A domain is user input and reaches a Content-Disposition header."""
        from routers.pqc import _cbom_download_response

        resp = _cbom_download_response({}, 'evil"\r\nX-Injected: 1')
        disposition = resp.headers["Content-Disposition"]
        assert '"' not in disposition.split("filename=")[1][1:-1]
        assert "\r" not in disposition and "\n" not in disposition
