import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

DEPENDENCIES = [
    "uvicorn[standard] >= 0.13.0, < 0.14.0",
    "dependency-injector >= 4.3.2",
    "fastapi >= 0.65.0, < 0.66.0",
    "sqlalchemy",
    "psycopg2-binary",
    "pydantic[email]",
]

TEST_DEPENDENCIES = [
    "dependency-injector",
    "mock",
    "pytest",
    "requests",
    "responses",
    "tox",
    "alembic",
]


setuptools.setup(
    name="carbonserver",
    version="0.1.0",
    author="BCG GAMMA, Comet.ml, Haverford College, MILA, DataForGood France",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    install_requires=DEPENDENCIES,
    tests_require=TEST_DEPENDENCIES,
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["carbonserver = main:app"]},
)
