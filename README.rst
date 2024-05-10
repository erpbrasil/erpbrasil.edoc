========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - |codecov|
    * - package
      - |version| |wheel| |supported-versions| |supported-implementations|
        |commits-since|

.. |codecov| image:: https://codecov.io/github/erpbrasil/erpbrasil.edoc/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/erpbrasil/erpbrasil.edoc

.. |version| image:: https://img.shields.io/pypi/v/erpbrasil.edoc.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/erpbrasil.edoc

.. |commits-since| image:: https://img.shields.io/github/commits-since/erpbrasil/erpbrasil.edoc/v2.8.0.svg
    :alt: Commits since latest release
    :target: https://github.com/erpbrasil/erpbrasil.edoc/compare/v2.8.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/erpbrasil.edoc.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/erpbrasil.edoc

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/erpbrasil.edoc.svg
    :alt: Supported versions
    :target: https://pypi.org/project/erpbrasil.edoc

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/erpbrasil.edoc.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/erpbrasil.edoc


.. end-badges

Emissão de documentos fiscais e outras obrigações
(NF-E, NFS-E, MDF-E, CT-E, REINF, E-SOCIAL)


Documentação
============

https://erpbrasil.github.io/

Créditos
========

Esta é uma biblioteca criada através do esforço das empresas:

* Akretion https://akretion.com/pt-BR/
* KMEE https://www.kmee.com.br

Favor consultar a lista de contribuidores:

https://github.com/erpbrasil/erpbrasil.edoc/graphs/contributors

Licença
~~~~~~~

* Free software: MIT license

Instalação
==========

Para permitir que a instalação do seu ERP cresça somente com a necessidade
do cliente é possível instalar as dependências da biblioteca de forma opcional:

::

    pip install erpbrasil.edoc

    # Documentos do Sefaz

    pip install erpbrasil.edoc[nfelib] # Emissão de NF-e
    pip install erpbrasil.edoc[mdfelib] # Emissão de Manifesto de Carga - MD
    pip install erpbrasil.edoc[ctelib] # Emissão de CT-e
    pip install erpbrasil.edoc[gnrelib] # Emissão de GNRE

    # Notas de Serviço / Prefeituras

    pip install erpbrasil.edoc[nfselib.ginfes] # Emissão de NFS-E GINFES
    pip install erpbrasil.edoc[nfselib.betha] # Emissão de NFS-E Betha
    pip install erpbrasil.edoc[nfselib.dsf] # Emissão de NFS-E DSF
    pip install erpbrasil.edoc[nfselib.paulistana] # Emissão de NFS-E Paulistana
    pip install erpbrasil.edoc[nfselib.issnet] # Emissão de NFS-E ISSNET

Documentation
=============

https://erpbrasil.github.io/docs/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
