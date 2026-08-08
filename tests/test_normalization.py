from decimal import Decimal

from secure_cloud_platform import CloudProvider, normalize_request


def test_normalization_is_provider_resolved_and_deterministic(
    active_profile, request_model
) -> None:
    first = normalize_request(active_profile, request_model)
    second = normalize_request(active_profile, request_model)
    assert first == second
    assert first.provider.value == "aws"
    assert first.region == "eu-west-1"
    assert str(first.network_cidr) == "10.42.0.0/16"
    assert first.monthly_budget == Decimal("250.00")
    assert first.request_id == f"env-{first.fingerprint[:16]}"
    assert first.canonical_json == first.canonical_json.strip()


def test_normalization_changes_identity_when_provider_changes(
    active_profile, request_model, profile_factory
) -> None:
    aws = normalize_request(active_profile, request_model)
    azure_profile = profile_factory(CloudProvider.AZURE)
    azure = normalize_request(azure_profile, request_model)
    assert aws.fingerprint != azure.fingerprint
    assert aws.request_id != azure.request_id
