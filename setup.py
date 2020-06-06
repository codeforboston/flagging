# -*- coding: utf-8 -*-
import io
from setuptools import setup, find_packages

with io.open('README.md', 'rt', encoding='utf8') as f:
    readme = f.read()

setup(
    name='CRWA Flagging Website',
    version='0.0.1',
    packages=find_packages(),
    author='Code for Boston',
    python_requires='>=3.7.1',
    maintainer='Charles River Watershed Association',
    include_package_data=True,
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
    ],
    install_requires=[
        'pyyaml',
        'pandas',
        'flask'
    ],
    url='https://github.com/codeforboston/flagging',
    description='Flagging website for the CRWA',
    long_description=readme
)
