import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

DEPENDENCIES = [
    "APScheduler",
    "co2-tracker-utils",
    "dash",
    "dash_bootstrap_components",
    "dataclasses",
    "fire",
    "pandas",
    "pynvml",
    "requests",
]

TEST_DEPENDENCIES = ["mock", "pytest", "responses", "tox"]


setuptools.setup(
    name="code-carbon",
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
        "codecarbon": [
            "data/cloud/impact.csv",
            "data/private_infra/2016/usa_emissions.json",
            "data/private_infra/2016/global_energy_mix.json",
        ]
    },
    python_requires=">=3.6",
    entry_points={"console_scripts": ["carbonboard = codecarbon.viz.dashboard:main"]},
)
