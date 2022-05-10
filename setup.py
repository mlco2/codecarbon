import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

DEPENDENCIES = [
    "arrow",
    "pandas",
    "pynvml",
    "requests",
    "psutil",
    "py-cpuinfo",
    "fuzzywuzzy",
    "click",
]

TEST_DEPENDENCIES = ["mock", "pytest", "responses", "tox", "numpy", "requests-mock"]


setuptools.setup(
    name="codecarbon",
    version="2.1.2",
    author="Mila, DataForGood, BCG GAMMA, Comet.ml, Haverford College",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    install_requires=DEPENDENCIES,
    tests_require=TEST_DEPENDENCIES,
    extras_require={"viz": ["dash", "dash_bootstrap_components", "fire"]},
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    package_data={
        "codecarbon": [
            "data/cloud/impact.csv",
            "data/hardware/cpu_power.csv",
            "data/private_infra/2016/usa_emissions.json",
            "data/private_infra/2016/canada_energy_mix.json",
            "data/private_infra/carbon_intensity_per_source.json",
            "data/private_infra/global_energy_mix.json",
            "viz/assets/*.png",
        ],
    },
    python_requires=">3.6",
    entry_points={
        "console_scripts": [
            "carbonboard = codecarbon.viz.carbonboard:main",
            "codecarbon = codecarbon.cli.main:codecarbon",
        ]
    },
)
