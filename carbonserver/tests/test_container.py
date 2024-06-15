from container import ServerContainer


def test_container_exposes_correct_list_of_providers_at_initialisation():
    expected_providers = [
        "config",
        "db",
        "emission_repository",
        "experiment_repository",
        "project_global_sum_by_experiment_usecase",
        "project_repository",
        "organization_repository",
        "user_repository",
        "emission_service",
        "experiment_service",
        "project_service",
        "run_repository",
        "run_service",
        "organization_service",
        "user_service",
        "sign_up_service",
    ]

    actual_providers = ServerContainer().providers.keys()
    diff = set(expected_providers) ^ set(actual_providers)

    assert not diff
    assert len(expected_providers) == len(actual_providers)
