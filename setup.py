from setuptools import setup, find_packages

setup(
    name="orchestrator-api-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "pydantic>=2.0.0",
        "uvicorn>=0.22.0",
        "requests>=2.31.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "feast>=0.30.0",
    ],
    python_requires='>=3.8',
)
