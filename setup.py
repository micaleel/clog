from setuptools import setup, find_packages
from pathlib import Path

setup(
    name="clog-cli",
    version="0.0.1-dev",
    description="Clog",
    long_description=Path("README.md").read_text(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: Proprietary and Confidential",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="clog",
    url="https://github.com/micaleel/clog",
    author="Khalil Muhammad",
    author_email="micaleel@gmail.com",
    license="Proprietary and Confidential",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["click"],
    test_suite="pytest",
    tests_require=["pytest"],
    zip_safe=False,
    py_modules=["cli"],
    entry_points={"console_scripts": ["clog=clog.cli:main"]},
)
