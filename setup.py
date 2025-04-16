from setuptools import setup, find_packages
import os

# Read long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="orchestrator-api-service",
    version="0.1.0",
    author="Jaeger Team",
    author_email="example@example.com",
    description="A configurable API service that orchestrates data flows across multiple sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/orchestrator-api-service",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "orchestrator_api_service": ["py.typed"],
    },
    entry_points={
        "console_scripts": [
            "orchestrator-api=orchestrator_api_service.cli:main",
        ],
    },
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
    ],
    python_requires='>=3.8',
    extras_require={
        'dev': [
            'pytest>=7.3.1',
            'mypy>=1.3.0',
            'flake8>=6.0.0',
        ],
        'all': [
            'pytest>=7.3.1',
            'mypy>=1.3.0',
            'flake8>=6.0.0',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
)
