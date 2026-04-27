"""Package setup for cronwatch."""

from setuptools import setup, find_packages

setup(
    name="cronwatch",
    version="0.1.0",
    description="Lightweight daemon that monitors cron job execution times and sends alerts.",
    author="cronwatch contributors",
    python_requires=">= 3.9",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "croniter>=1.4",
        "requests>=2.28",
    ],
    extras_require={
        "dev": [
            "pytest>=7",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "cronwatch=cronwatch.cli:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Monitoring",
    ],
)
