# Using Code Carbon with prometheus

> [Prometheus](https://github.com/prometheus/prometheus) is a systems and service monitoring system. It collects metrics from configured targets at given intervals, evaluates rule expressions, displays the results, and can trigger alerts when specified conditions are observed.

Code Carbon exposes all its metrics with the suffix `codecarbon_`.

Current version uses pushgateway mode. If your pushgateway server needs auth, set your environment values `PROMETHEUS_USERNAME` and `PROMETHEUS_PASSWORD` so codecarbon is able to push the metrics.

# How to test in local

Deploy a local version of Prometheus + Prometheus Pushgateway + grafana (optional)

```sh
cd dev
docker-compose up
```

Run your EmissionTracker as usual, but with the parameter `save_to_prometheus` as True.
e.g.

```
...
tracker = OfflineEmissionsTracker(
            project_name=self.project_name,
            country_iso_code="USA",
            save_to_prometheus=True,
        )
tracker.start()
...
```

Go to [localhost:9090](localhost:9090). Search for `codecarbon_`. You will see all the metrics there.
