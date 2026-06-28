# ASV benchmarks

These benchmarks measure `codecarbon` performance across git commits.

Run a local smoke check:

```bash
uvx asv --config benchmarks/asv.conf.json run --quick --show-stderr
```


Run across releases:

```bash
# Get the commits of the releases
./benchmarks/get_release_hashes.sh
# Run only against those commits
uvx asv --config benchmarks/asv.conf.json run HASHFILE:release_hashes.txt --show-stderr
```

Then when you see a big jump between releases, go and run the intermediate commits to see the diff:

```bash
# Imagine the jump is between 3.2.1 and 3.2.2
uvx asv --config benchmarks/asv.conf.json run v3.2.1..3.2.2 --show-stderr
```

Build and preview the report:

```bash
uvx asv --config benchmarks/asv.conf.json publish
uvx asv --config benchmarks/asv.conf.json preview
```

Generated ASV environments, results, and HTML are written under `benchmarks/`.
