
Changelog
=========

0.0.0 (2019-09-23)
~~~~~~~~~~~~~~~~~~

* First release on PyPI.

1.0.0 (2020-11-21)
~~~~~~~~~~~~~~~~~~

* NF-e - Nota fiscal eletrônica;
    * Status Serviço;
    * Emissão;
    * Cancelamento;
    * Carta de correção;
    * Consulta Chave;
    * Consulta Distribuição;
    * Manifestação do Destinatário;
        * Confirmação de Operação;
        * Ciência de Operação;
        * Desconhecimento da operação;
        * Operação não realizada;
* MDF-e - Manifesto Eletrônico de Documentos Fiscais (Transporte):
    * Status Serviço;
    * Consulta Documento;
    * Consulta Não Encerrados;
    * Emissão;
    * Cancelamento;
* NFS-E - Base para o desenvolvimento de provedores:
    * Status Serviço;
    * Consulta Documento;
    * Consulta NFS-e / RPS;
    * Consulta Lote RPS;
    * Emissão;
    * Cancelamento;
    * Suporte ao provedor:
        * GINFES:
* Implementação de testes automatizados;

2.0.0 (2021-04-09)
~~~~~~~~~~~~~~~~~~

* Refatoração do módulo de NF-e

2.1.0 (2021-05-01)
~~~~~~~~~~~~~~~~~~

- Manifestação do Destinatário
- Consulta Cadastro

2.2.0 (2021-05-26)
~~~~~~~~~~~~~~~~~~

- Nota Paulistana

2.9.0 (2024-05-15)
~~~~~~~~~~~~~~~~~~

- Suporte para emissão de NF-e utilizando as Sefaz autorizadoras de contingência.

2.10.0 (2024-07-25)
~~~~~~~~~~~~~~~~~~~

- Ceará passa a usar o webservice da SVRS.
- URLs e expressão regular do Ginfes corrigidas.
- Leitura do retorno SOAP com um padrão combinado de prefixos.
- Versão da nfelib travada e erpbrasil.transmissao no requirements.

2.10.1 (2024-10-10)
~~~~~~~~~~~~~~~~~~~

- URL da SEFAZ MG corrigida.

3.0.0 (2024-12-06)
~~~~~~~~~~~~~~~~~~

- CT-e: status do serviço, envio, cancelamento, carta de correção e cteProc.
- MDF-e refatorado.
- NF-e e NFC-e: ``monta_qrcode``.
- Busca das URLs dos webservices refatorada.

3.1.0 (2025-11-08)
~~~~~~~~~~~~~~~~~~

- Bindings generateDS legados de NF-e, NFC-e e eventos embutidos em
  ``erpbrasil.nfelib_legacy``.
- MDF-e: RS na SVRS e ``get_service_url`` levanta erro para UF sem configuração.
- Manifestação do destinatário: endpoint de homologação corrigido.

3.1.1 (2026-01-08)
~~~~~~~~~~~~~~~~~~

- digVal: ``gds_format_base64`` converte bytes para texto.

3.2.0 (2026-10-05)
~~~~~~~~~~~~~~~~~~

Novidades:

- NFS-e Paulistana: schema v03 (Reforma Tributária) opcional, com
  ``versao_schema="v03"``; o v02 continua padrão e gera o mesmo XML (#101).
- NFS-e Barueri: consulta pelo protocolo, download do arquivo do lote e retorno
  da consulta com a situação e a mensagem (#93).
- Novo extra ``nfselib.barueri``.

Correções:

- ``assina_raiz`` não altera mais o XML depois de assinado, o que evitava a
  rejeição 297 com texto que tem quebra de linha (#97). No Ginfes o XML assinado
  continua sem quebras de linha, como até a 3.1.1.
- Reassinatura descarta a Signature anterior e declara ``xmlns:ds`` na
  exportação dos bindings legados (#99).
- CT-e e MDF-e: ``get_service_url`` aceita o ambiente como texto (#109). Quem
  passa ``"1"`` em texto, como a localização OCA na 14.0, transmitia o MDF-e
  para a homologação e passa a transmitir para a produção.
- CT-e: PR, MT, MS e MG usam a autorizadora própria e RS a SVRS (#110).
- MDF-e: todas as UFs autorizam na SVRS; MG, MS, MT e PR levantavam ValueError
  (#100).
- NF-e: caminhos da contingência SVC-RS em produção, que estavam trocados entre
  os serviços (AM, BA, GO, MA, MS, MT, PE, PI e PR).
- NF-e: o lote que volta já processado a um envio assíncrono (cStat 104, sem
  infRec), comum na contingência, não quebra mais o ``processar_documento`` com
  AttributeError depois da autorização; o processo é montado como no envio
  síncrono (#102).
- NF-e: consulta de cadastro do AM e do PE pelo CadConsultaCadastro4, como
  publica o Portal NF-e; a versão 2 dava 404 (#87).
- Barueri: ``analisa_retorno_consulta`` não levanta mais UnboundLocalError em
  retorno com erro.
- Os extras ``nfelib`` e ``mdfelib`` instalam a nfelib (apontavam para pacotes
  inexistentes); sai o extra ``nfselib.betha``.

Outros:

- README reescrito; descrição e links do pacote no PyPI.
- CI: py37 removido; zeep e requests por versão do Python (alertas de
  segurança); testes de Paulistana, ISSNet, chave, CT-e, MDF-e, contingência
  SVC-RS, Barueri e reassinatura.
