from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="liver_disease_mlops",
    version="0.1",
    author="htai",
    packages=find_packages(),
    install_requires = requirements,
)