from co2_tracker.config import AppConfig


def get_test_app_config() -> AppConfig:
    test_config = {
        "geo_js_url": "https://get.geojs.io/v1/ip/geo.json",
        "cloud_emissions_path": "data/cloud/impact.csv",
        "private_infra_us_path": "data/private_infra/2016/us_emissions.json",
        "private_infra_energy_mix_path": "data/private_infra/2016/energy_mix.json",
    }
    return AppConfig(test_config)
