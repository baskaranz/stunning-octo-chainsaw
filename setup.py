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
        "httpx>=0.24.0",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
        "feast>=0.30.0",
        "scikit-learn>=1.2.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "flask>=2.0.0",
        "aiohttp>=3.8.4",
        "docker>=6.1.0",
        "boto3>=1.28.0",
        "pytest>=7.3.1",
    ],
    python_requires='>=3.8',
    extras_require={
        'dev': [
            'pytest>=7.3.1',
            'mypy>=1.3.0',
            'flake8>=6.0.0',
        ],
    },
)
