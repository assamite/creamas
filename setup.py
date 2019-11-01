from setuptools import setup, find_packages
import re

# Parse version number from creamas/__init__.py to keep it in one place.
__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    open('creamas/__init__.py').read()).group(1)

setup(
    name='creamas',
    version=__version__,
    author='Simo Linkola',
    author_email='simo.linkola@gmail.com',
    description='A library for creative MAS build on top of aiomas.',
    long_description='See https://creamas.readthedocs.io/',
    url='https://creamas.readthedocs.io/',
    license='GNU General Public License v2 (GPLv2)',
    install_requires=[
        'aiomas==2.0.1',
        'msgpack-python>=0.4.6',
        'numpy>=1.17.3',
    ],
    extras_require={
        'extras': ['deap>=1.3.0', 'opencv-python>=4.1.0', 'noise>=1.2.2', 'scipy>=1.3.1', 'networkx>=2.4'],
        'docs': ['Sphinx>=2.2.0', 'sphinx-rtd-theme>=0.4.3']
    },
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering',
    ],
)
