from setuptools import setup, find_packages

setup(
    name="pocketclaw",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["httpx>=0.27.0", "pyyaml>=6.0"],
    entry_points={"console_scripts": ["pocket=pocketclaw.cli:main"]},
    python_requires=">=3.10",
)
