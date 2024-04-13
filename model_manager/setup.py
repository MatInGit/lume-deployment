from setuptools import setup, find_packages

setup(
    name="model_manager",
    version="0.1",
    packages=find_packages(),
    entry_points={"console_scripts": ["model_manager=main:main"]},
    install_requires=["argparse"],
)
