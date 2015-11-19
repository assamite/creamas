from setuptools import setup, find_packages


setup(
    name='creamas',
    version='0.1.0',
    author='Simo Linkola',
    author_email='simo.linkola at cs.helsinki.fi',
    description=('A library for creative multi-agent systems, based on aiomas.'),
    long_description=(open('README.rst', encoding='utf-8').read()),
    url='',
    install_requires=[
        'aiomas>=0.6.0',
        'msgpack-python==0.4.6',
    ],
    extras_require={
    },
    packages=find_packages(exclude=['tests*', 'experiments']),
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
    ],
)