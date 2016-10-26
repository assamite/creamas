from setuptools import setup, find_packages

setup(
    name='creamas',
    version='0.1.0',
    author='Simo Linkola',
    author_email='simo.linkola at cs.helsinki.fi',
    description=('library for creative multi-agent systems'),
    long_description=('See http://assamite.github.io/creamas/'),
    url='',
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
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering',
    ],
)
