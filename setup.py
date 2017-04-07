from setuptools import setup, find_packages

setup(
    name='creamas',
    version='0.1.5',
    author='Simo Linkola',
    author_email='simo.linkola at gmail.com',
    description=('A library for creative MAS build on top of aiomas.'),
    long_description=('See https://assamite.github.io/creamas/'),
    url='https://assamite.github.io/creamas/',
    license='GNU General Public License v2 (GPLv2)',
    install_requires=[
        'aiomas>=1.0.3',
        'msgpack-python>=0.4.6',
        'numpy>=1.10.1',
    ],
    extras_require={
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
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering',
    ],
)
