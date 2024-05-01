from setuptools import setup, find_packages

setup(
    name="model_manager",
    version="0.1",
    maintainer="Mateusz Leputa",
    packages=find_packages(),
    entry_points={"console_scripts": ["model_manager=scripts.main:main"]},
    install_requires=["argparse"]  # wierd dep issue needs adressing
    # "botorch",
    # "tensorflow",
    # "lume-model@git+https://github.com/slaclab/lume-model.git@2921e6583a6cfd49285833eb851b361aacf65b4c",
    # "pandas>=2.0.1",
    # "numpy>=1.21.2",
    # "keras==3.1.1",
    # "mlflow==2.12.1",
    # "boto3==1.34.65",
    # "psycopg2-binary",
    # "k2eg==0.2.7",
    # "psutil==5.9.8",
    # "colorlog==6.8.2",
    # "p4p",
    # "pyepics"]
)
