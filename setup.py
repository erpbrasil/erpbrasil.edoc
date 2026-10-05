#!/usr/bin/env python

import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup

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
nfselib_issnet_require = [
    "nfselib.issnet",
]
nfselib_barueri_require = [
    "nfselib.barueri",
]
# CT-e e MDF-e usam as bindings da nfelib; NF-e, NFC-e e manifestação usam as
# bindings embutidas em erpbrasil.nfelib_legacy
nfelib_require = [
    "nfelib",
]


def read(*names, **kwargs):
    with open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="erpbrasil.edoc",
    version="3.1.1",
    license="MIT",
    description=(
        "Transmissão de documentos fiscais eletrônicos brasileiros"
        " (NF-e, NFC-e, CT-e, MDF-e, manifestação do destinatário e NFS-e)"
    ),
    long_description="{}\n{}".format(
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    author="Luis Felipe Mileo",
    author_email="mileo@kmee.com.br",
    url="https://github.com/erpbrasil/erpbrasil.edoc",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    namespace_packages=["erpbrasil", "erpbrasil.edoc"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        "Topic :: Utilities",
    ],
    project_urls={
        "Documentation": "https://github.com/erpbrasil/erpbrasil.edoc#readme",
        "Changelog": "https://github.com/erpbrasil/erpbrasil.edoc/blob/master/CHANGELOG.rst",
        "Issue Tracker": "https://github.com/erpbrasil/erpbrasil.edoc/issues",
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.5, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    install_requires=install_requires,
    extras_require={
        "nfselib.ginfes": nfselib_ginfes_require,
        "nfselib.paulistana": nfselib_paulistana_require,
        "nfselib.dsf": nfselib_dsf_require,
        "nfselib.issnet": nfselib_issnet_require,
        "nfselib.barueri": nfselib_barueri_require,
        "nfelib": nfelib_require,
        # nome mantido para quem já instala com ele; o MDF-e usa a nfelib
        "mdfelib": nfelib_require,
    },
    setup_requires=[],
    entry_points={
        "console_scripts": [
            "erpbrasil.edoc = erpbrasil.edoc.cli:main",
        ]
    },
)
