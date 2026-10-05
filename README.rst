==============
erpbrasil.edoc
==============

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/erpbrasil/erpbrasil.edoc/v3.1.1.svg
    :alt: Commits since latest release
    :target: https://github.com/erpbrasil/erpbrasil.edoc/compare/v3.1.1...master

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

Biblioteca Python para transmitir documentos fiscais eletrônicos brasileiros aos
webservices das SEFAZ e das prefeituras: monta a mensagem, assina, envia, consulta e
interpreta o retorno de NF-e, NFC-e, CT-e, MDF-e, manifestação do destinatário e NFS-e.

É a camada de transmissão da localização brasileira do Odoo
(`OCA/l10n-brazil <https://github.com/OCA/l10n-brazil>`_), e pode ser usada em qualquer
projeto Python. A assinatura digital vem da
`erpbrasil.assinatura <https://github.com/erpbrasil/erpbrasil.assinatura>`_ e o
transporte SOAP da `erpbrasil.transmissao <https://github.com/erpbrasil/erpbrasil.transmissao>`_.

O que a biblioteca faz
======================

.. list-table::
    :header-rows: 1
    :widths: 22 28 50

    * - Documento
      - Classe
      - Serviços
    * - NF-e (modelo 55)
      - ``erpbrasil.edoc.nfe.NFe``
      - status do serviço, autorização (síncrona e assíncrona) e consulta do recibo,
        consulta por chave, cancelamento, carta de correção, inutilização, consulta de
        cadastro, distribuição de DF-e
    * - NFC-e (modelo 65)
      - ``erpbrasil.edoc.nfce.NFCe``
      - os serviços da NF-e, autorização síncrona e QR Code
    * - Manifestação do destinatário
      - ``erpbrasil.edoc.mde.MDe``
      - ciência, confirmação, desconhecimento e operação não realizada
    * - CT-e
      - ``erpbrasil.edoc.cte.CTe``
      - status do serviço, autorização e consulta do recibo, consulta por chave,
        cancelamento, carta de correção, QR Code
    * - MDF-e
      - ``erpbrasil.edoc.mdfe.MDFe``
      - status do serviço, autorização e consulta do recibo, consulta por chave,
        cancelamento, encerramento, QR Code
    * - NFS-e
      - ``erpbrasil.edoc.provedores.cidades.NFSeFactory``
      - envio do lote de RPS, consulta do lote e da NFS-e, cancelamento (os serviços
        variam por provedor)

O endereço do webservice é escolhido pela UF (ou pela cidade, na NFS-e) e pelo ambiente:
``1`` produção e ``2`` homologação.

Provedores de NFS-e
~~~~~~~~~~~~~~~~~~~

A ``NFSeFactory`` escolhe o provedor pelo código IBGE da cidade do prestador.

.. list-table::
    :header-rows: 1
    :widths: 18 52 30

    * - Provedor
      - Cidades (código IBGE)
      - Bindings
    * - DSF
      - Belém-PA (1501402), Teresina-PI (2211001), Uberlândia-MG (3170206),
        Nova Iguaçu-RJ (3303500), Campinas-SP (3509502), Campo Grande-MS (5002704)
      - ``erpbrasil.edoc[nfselib.dsf]``
    * - Ginfes
      - Itajubá-MG (3132404), Franca-SP (3516200)
      - ``erpbrasil.edoc[nfselib.ginfes]``
    * - Paulistana
      - São Paulo-SP (3550308)
      - ``erpbrasil.edoc[nfselib.paulistana]``
    * - ISSNet
      - Ribeirão Preto-SP (3543402), Duque de Caxias-RJ (3301702)
      - ``erpbrasil.edoc[nfselib.issnet]``
    * - Barueri
      - Barueri-SP (3505708)
      - ``erpbrasil.edoc[nfselib.barueri]``

Instalação
==========

.. code:: bash

    pip install erpbrasil.edoc

NF-e, NFC-e e manifestação do destinatário já funcionam com a instalação básica: as
bindings que elas usam vêm embutidas no pacote (``erpbrasil.nfelib_legacy``). Os demais
documentos pedem bindings externas, instaladas por extras:

.. code:: bash

    pip install "erpbrasil.edoc[nfelib]"              # CT-e e MDF-e
    pip install "erpbrasil.edoc[nfselib.paulistana]"  # NFS-e de São Paulo

Os extras de NFS-e seguem a tabela de provedores acima.

Como usar
=========

Status do serviço da NF-e em homologação, em São Paulo (código IBGE da UF ``35``):

.. code:: python

    from erpbrasil.assinatura.certificado import Certificado
    from erpbrasil.edoc.nfe import NFe
    from erpbrasil.transmissao import TransmissaoSOAP
    from requests import Session

    certificado = Certificado("certificado-a1.pfx", "senha-do-certificado")
    transmissao = TransmissaoSOAP(certificado, Session())
    nfe = NFe(transmissao, "35", versao="4.00", ambiente="2")

    processo = nfe.status_servico()
    print(processo.resposta.cStat, processo.resposta.xMotivo)

NFS-e pela fábrica de provedores:

.. code:: python

    from erpbrasil.edoc.provedores.cidades import NFSeFactory

    nfse = NFSeFactory(
        transmissao=transmissao,
        ambiente="2",
        cidade_ibge=3550308,
        cnpj_prestador="12345678000195",
        im_prestador="12345678",
    )
    processo = nfse.envia_documento(lote_rps)

``lote_rps`` é o objeto montado com as bindings do provedor (por exemplo,
``nfselib.paulistana``).

Quem monta a NF-e, a NFC-e, o CT-e ou o MDF-e com as bindings da
`nfelib <https://github.com/akretion/nfelib>`_ (xsdata) deve usar os adaptadores de
``nfelib.nfe.ws.edoc_legacy`` (``NFeAdapter``, ``NFCeAdapter``, ``CTeAdapter``,
``MDFeAdapter``, ``MDeAdapter``), que embrulham as classes desta biblioteca. É o caminho
usado pela localização OCA.

Desenvolvimento
===============

.. code:: bash

    pip install tox pre-commit
    pre-commit install
    tox -e py310   # testes (também py38 e py39)
    tox -e check   # metadados do pacote e o RST deste arquivo
    tox -e docs    # documentação, inclusive a verificação de links

Os testes que falam com webservices reproduzem respostas gravadas com o
`vcrpy <https://vcrpy.readthedocs.io/>`_ (``tests/fixtures/vcr_cassettes``). O ``tox``
fixa o ``vcrpy`` e o ``urllib3`` em versões que reproduzem esses cassetes: rodar o
``pytest`` fora do ``tox``, com versões mais novas, faz esses testes falharem com
``Invalid XML content received``.

Para combinar a cobertura de todos os ambientes do ``tox`` no Linux e no macOS:

.. code:: bash

    PYTEST_ADDOPTS=--cov-append tox

No Windows:

.. code:: bat

    set PYTEST_ADDOPTS=--cov-append
    tox

Publicação de uma versão
~~~~~~~~~~~~~~~~~~~~~~~~

1. Atualizar o ``CHANGELOG.rst``.
2. ``bump2version --no-tag patch`` (ou ``minor`` ou ``major``): atualiza a versão
   no ``setup.py``, neste arquivo, em ``docs/conf.py`` e em
   ``src/erpbrasil/edoc/__init__.py``.
3. Abrir o PR com o bump e mesclar com o CI verde.
4. Criar a Release ``vX.Y.Z`` no GitHub sobre o commit mesclado (ela cria a tag).
5. ``python -m build``, ``twine check dist/*`` e ``twine upload dist/*``.

Para testar antes de anunciar, publique um release candidate (``X.Y.Zrc1``): o
``pip`` só instala pré-releases quando pedido com ``--pre`` ou com a versão exata.

Créditos
========

Biblioteca criada pela `Akretion <https://akretion.com/>`_ e pela
`KMEE <https://www.kmee.com.br>`_, mantida com a comunidade da localização brasileira.
Veja a `lista de contribuidores <https://github.com/erpbrasil/erpbrasil.edoc/graphs/contributors>`_.

Licença
=======

MIT, veja o arquivo ``LICENSE``.
