import os
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requires = [l.strip() for l in f if l.strip() and not l.startswith("#")]

with open("README.md") as f:
    long_desc = f.read()

setup(
    name="agentworld",
    version="0.1.0",
    description="Declarative LLM agent simulation engine. 14 YAML slots, zero cognitive code.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/Asher0501/AgentWorld_Async",
    license="MIT",
    python_requires=">=3.10",
    install_requires=requires,
    packages=find_packages("src") + find_packages("dashboard") + find_packages("visual"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
