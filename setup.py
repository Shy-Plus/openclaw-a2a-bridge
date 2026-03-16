"""Setup script for openclaw-a2a-bridge."""

from setuptools import setup, find_packages

setup(
    name="openclaw-a2a-bridge",
    version="1.0.0",
    description="Cross-device Agent-to-Agent communication bridge for OpenClaw",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Shy's Lab",
    url="https://github.com/Shy-Plus/openclaw-a2a-bridge",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "a2a-sdk[http-server]>=0.3.25",
        "httpx>=0.28.1",
        "uvicorn>=0.42.0",
    ],
    entry_points={
        "console_scripts": [
            "a2a-server=src.server:main",
            "a2a-client=src.client:main",
            "a2a-health=src.health_check:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Networking",
    ],
)
