import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

# TODO: Add co2-tracker-utils once it is published to PyPI here
DEPENDENCIES = [
    "APScheduler",
    "pandas",
    "requests",
    "dataclasses",
    "co2-tracker-utils",
    "dash",
    "fire",
    "dash_bootstrap_components",
]

TEST_DEPENDENCIES = ["responses", "tox", "mock", "pytest"]


setuptools.setup(
    name="co2_tracker",
    version="0.0.1",
    author="BCG GAMMA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    install_requires=DEPENDENCIES,
    tests_require=TEST_DEPENDENCIES,
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    package_data={
        "co2_tracker": [
            "data/cloud/impact.csv",
            "data/private_infra/2016/us_emissions.json",
            "data/private_infra/2016/global_energy_mix.json",
        ]
    },
    python_requires=">=3.6",
)
