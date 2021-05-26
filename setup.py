#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

install_requires = [
    "erpbrasil.base>=2.0.0",
    "erpbrasil.assinatura>=1.2.0",
    "erpbrasil.transmissao>=1.0.0",
]

nfselib_ginfes_require = [
    "nfselib.ginfes",
]
nfselib_paulistana_require = [
    "nfselib.paulistana",
]
nfselib_dsf_require = [
    "nfselib.dsf",
]
nfselib_betha_require = [
    "nfselib.betha",
]
nfselib_issnet_require = [
    "nfselib.issnet",
]
nfelib_require = [
    "nfselib",
]
mdfelib_require = [
    "mdfelib",
]


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


setup(
    name='erpbrasil.edoc',
    version='2.2.0',
    license='MIT',
    description='Emissão de documentos fiscais e outras obrigações (NF-E, NFS-E, MDF-E, CT-E, REINF, E-SOCIAL)',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    author='Luis Felipe Mileo',
    author_email='mileo@kmee.com.br',
    url='https://github.com/erpbrasil/erpbrasil.edoc',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    namespace_packages=["erpbrasil", "erpbrasil.edoc"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://erpbrasiledoc.readthedocs.io/',
        'Changelog': 'https://erpbrasiledoc.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/erpbrasil/erpbrasil.edoc/issues',
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires='>=3.5, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=install_requires,
    extras_require={
        "nfselib.ginfes": nfselib_ginfes_require,
        "nfselib.paulistana": nfselib_paulistana_require,
        "nfselib.dsf": nfselib_dsf_require,
        "nfselib.betha": nfselib_betha_require,
        "nfselib.issnet": nfselib_issnet_require,
        "nfelib": nfelib_require,
        "mdfelib": mdfelib_require,
    },
    setup_requires=[
    ],
    entry_points={
        'console_scripts': [
            'erpbrasil.edoc = erpbrasil.edoc.cli:main',
        ]
    },
)
