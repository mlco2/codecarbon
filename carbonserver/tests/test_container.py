from container import ServerContainer


def test_container_exposes_correct_list_of_providers_at_initialisation():
    expected_providers = [
        "config",
        "db",
        "user_repository",
        "user_service",
        "organization_service",
        "organization_repository",
        "sign_up",
        "team_repository",
    ]

    actual_providers = ServerContainer().providers.keys()
    diff = set(expected_providers) ^ set(actual_providers)

    # Then
    assert not diff
    assert len(expected_providers) == len(actual_providers)
