from setuptools import setup
from os import getenv

setup(
    name="unifi_switch_client",
    version=getenv("RELEASE_VERSION", "0.0.2"),
    description="Unifi switch client",
    url="https://github.com/waggle-sensor/unifi_switch_client",
    install_requires=[
        "requests",
        "click",
    ],
    packages=[
        "unifi_switch_client",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'unifi-cli=unifi_cli:cli',
        ],
    },
)
