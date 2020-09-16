# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


with open(os.path.join('flagging_site', '__init__.py'), encoding='utf8') as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)

with open('README.md', encoding='utf8') as f:
    readme = f.read()


setup(
    name='CRWA Flagging Website',
    version='0.3.0',
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
        'pytest-cov'
    ],
    install_requires=[
        'pyyaml',
        'pandas',
        'flask',
        'flasgger',
        'psycopg2',
        'Flask-SQLAlchemy'
    ],
    url='https://github.com/codeforboston/flagging',
    description='Flagging website for the CRWA',
    long_description=readme
)
