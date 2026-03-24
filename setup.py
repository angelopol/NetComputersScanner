from setuptools import setup, find_packages

setup(
    name="NetComScan",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "netcomscan=NetComScan.scanner:main",
        ],
    },
)
