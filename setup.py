# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


with open(os.path.join('flagging_site', '__init__.py'), encoding='utf8') as f:
    version = re.search(r"__version__ = '(.*?)'", f.read()).group(1)

with open('README.md', encoding='utf8') as f:
    readme = f.read()


setup(
    name='CRWA Flagging Website',
    version=version,
    packages=find_packages(),
    author='Code for Boston',
    python_requires='>=3.7.1',
    maintainer='Charles River Watershed Association',
    license='MIT',
    include_package_data=True,
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-cov'
    ],
    install_requires=[
        'pandas',
        'flask',
        'jinja2',
        'flasgger',
        'requests',
        'Flask-SQLAlchemy',
        'Flask-Admin',
        'Flask-BasicAuth',
        'py7zr'
    ],
    extras_require={
        'windows': ['psycopg2'],
        'osx': ['psycopg2-binary']
    },
    url='https://github.com/codeforboston/flagging',
    description='Flagging website for the CRWA',
    long_description=readme,
    long_description_content_type='text/markdown',
)
