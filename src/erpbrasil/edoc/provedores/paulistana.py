# Copyright (C) 2020 KMEE


import xml.etree.ElementTree as ET
from base64 import b64encode

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

try:
    from nfselib.paulistana.v02 import (
        PedidoCancelamentoNFe,
        PedidoConsultaLote,
        PedidoConsultaNFe,
        RetornoCancelamentoNFe,
        RetornoConsulta,
        RetornoEnvioLoteRPS,
    )

    from erpbrasil.assinatura.assinatura import Assinatura

    paulistana = True
except ImportError:
    paulistana = False

try:
    from nfselib.paulistana.v03 import PedidoCancelamentoNFe as PedidoCancelamentoNFeV3
    from nfselib.paulistana.v03 import PedidoConsultaLote as PedidoConsultaLoteV3
    from nfselib.paulistana.v03 import PedidoConsultaNFe as PedidoConsultaNFeV3
    from nfselib.paulistana.v03 import (
        RetornoCancelamentoNFe as RetornoCancelamentoNFeV3,
    )
    from nfselib.paulistana.v03 import RetornoConsulta as RetornoConsultaV3
    from nfselib.paulistana.v03 import RetornoEnvioLoteRPS as RetornoEnvioLoteRPSV3

    paulistana_v03 = True
except ImportError:
    paulistana_v03 = False

endpoint = "ws/lotenfe.asmx?WSDL"

if paulistana:
    # Versões do schema do WS LoteNFe:
    # - v02: schema *_v01.xsd (legado, fato gerador até 31/12/2025)
    # - v03: schema *_v02.xsd (Reforma Tributária 2026 / IBS-CBS)
    VERSOES_SCHEMA = {
        "v02": {
            "versao_cabecalho": 1,
            "url": "https://nfe.prefeitura.sp.gov.br",
            "endpoint": "ws/lotenfe.asmx?WSDL",
            "pedido_consulta_lote": PedidoConsultaLote,
            "pedido_consulta_nfe": PedidoConsultaNFe,
            "pedido_cancelamento_nfe": PedidoCancelamentoNFe,
            "retorno_envio_lote_rps": RetornoEnvioLoteRPS,
            "retorno_consulta": RetornoConsulta,
            "retorno_cancelamento_nfe": RetornoCancelamentoNFe,
            # tpAssinatura no schema v01 é exportado pelo generateDS como
            # string: o valor atribuído já deve estar codificado em base64
            "assinatura_em_bytes": False,
        },
    }
    if paulistana_v03:
        VERSOES_SCHEMA["v03"] = {
            "versao_cabecalho": 2,
            # WS da Reforma Tributária (Manual v3.3.7)
            "url": "https://nfews.prefeitura.sp.gov.br",
            "endpoint": "lotenfe.asmx?WSDL",
            "pedido_consulta_lote": PedidoConsultaLoteV3,
            "pedido_consulta_nfe": PedidoConsultaNFeV3,
            "pedido_cancelamento_nfe": PedidoCancelamentoNFeV3,
            "retorno_envio_lote_rps": RetornoEnvioLoteRPSV3,
            "retorno_consulta": RetornoConsultaV3,
            "retorno_cancelamento_nfe": RetornoCancelamentoNFeV3,
            # tpAssinatura no schema v02 é xs:base64Binary: o export do
            # generateDS aplica o base64, o valor atribuído deve ser bytes
            "assinatura_em_bytes": True,
        }

    def _montar_servicos(ambiente, schema):
        endpoint_ws = schema["endpoint"]
        servicos = {
            "consulta_recibo": ServicoNFSe(
                "ConsultaLote", endpoint_ws, schema["retorno_consulta"], True
            ),
            "consulta_nfse_rps": ServicoNFSe(
                "ConsultaNFe", endpoint_ws, schema["retorno_consulta"], True
            ),
            "cancela_documento": ServicoNFSe(
                "CancelamentoNFe", endpoint_ws, schema["retorno_cancelamento_nfe"], True
            ),
        }
        # Não tem URL de homologação mas tem método para testes
        # no mesmo webservice
        operacao_envio = "TesteEnvioLoteRPS" if ambiente == "2" else "EnvioLoteRPS"
        servicos["envia_documento"] = ServicoNFSe(
            operacao_envio, endpoint_ws, schema["retorno_envio_lote_rps"], True
        )
        return servicos


class Paulistana(NFSe):
    def __init__(
        self,
        transmissao,
        ambiente,
        cidade_ibge,
        cnpj_prestador,
        im_prestador,
        versao_schema="v02",
    ):
        if versao_schema not in VERSOES_SCHEMA:
            raise ValueError(
                "Versão de schema indisponível: %s (instale a nfselib.paulistana "
                "com suporte a ela). Disponíveis: %s"
                % (versao_schema, ", ".join(sorted(VERSOES_SCHEMA)))
            )
        self._versao_schema = versao_schema
        self._schema = VERSOES_SCHEMA[versao_schema]
        self._url = self._schema["url"]
        self._servicos = _montar_servicos(ambiente, self._schema)

        super().__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador
        )

    def _assina_paulistana(self, assinador, data):
        """Assina a cadeia de posições fixas do layout paulistano.

        Aceita str ou bytes; devolve no formato que o binding da versão
        de schema em uso espera no campo (str base64 no v02, bytes no v03).
        """
        if isinstance(data, str):
            data = data.encode("ascii")
        assinatura = assinador.sign_pkcs1v15_sha1(data)
        if self._schema["assinatura_em_bytes"]:
            return assinatura
        return b64encode(assinatura).decode()

    def _prepara_envia_documento(self, edoc):
        assinador = Assinatura(self._transmissao.certificado)
        for rps in edoc.RPS:
            rps.Assinatura = self._assina_paulistana(assinador, rps.Assinatura)
        xml_assinado = self.assina_raiz(edoc, "")
        return xml_assinado

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return proc_envio.resposta.Cabecalho.Sucesso

    def _edoc_situacao_em_processamento(self, proc_recibo):
        # if proc_recibo.resposta.Situacao == 2:
        #     return True
        # return False
        pass

    def _prepara_consulta_recibo(self, proc_envio):
        retorno = ET.fromstring(proc_envio.retorno)
        numero_lote = int(retorno.find(".//NumeroLote").text)
        cnpj = retorno.find(".//CNPJ").text

        consulta_lote = self._schema["pedido_consulta_lote"]
        consulta_nfe = self._schema["pedido_consulta_nfe"]
        edoc = consulta_lote.PedidoConsultaLote(
            Cabecalho=consulta_lote.CabecalhoType(
                Versao=self._schema["versao_cabecalho"],
                CPFCNPJRemetente=consulta_nfe.tpCPFCNPJ(CNPJ=cnpj),
                NumeroLote=numero_lote,
            )
        )

        xml_assinado = self.assina_raiz(edoc, "")

        return xml_assinado

    def _prepara_consultar_nfse_rps(self, **kwargs):
        cnpj_prestador = kwargs.get("cnpj_prest")
        inscricao_prestador = kwargs.get("insc_prest")
        rps_serie = kwargs.get("serie_rps")
        rps_numero = kwargs.get("numero_rps")

        consulta_nfe = self._schema["pedido_consulta_nfe"]
        raiz = consulta_nfe.PedidoConsultaNFe(
            Cabecalho=consulta_nfe.CabecalhoType(
                Versao=self._schema["versao_cabecalho"],
                CPFCNPJRemetente=consulta_nfe.tpCPFCNPJ(CNPJ=cnpj_prestador),
            ),
            Detalhe=[
                consulta_nfe.DetalheType(
                    ChaveRPS=consulta_nfe.tpChaveRPS(
                        InscricaoPrestador=int(inscricao_prestador),
                        SerieRPS=rps_serie,
                        NumeroRPS=int(rps_numero),
                    ),
                )
            ],
        )

        xml_assinado = self.assina_raiz(raiz, "")

        return xml_assinado

    def analisa_retorno_consulta(self, processo):
        retorno_mensagem = ""
        res = {}
        if processo.resposta.Cabecalho.Sucesso:
            retorno = ET.fromstring(processo.retorno)
            res["codigo_verificacao"] = retorno.find(".//CodigoVerificacao").text
            res["numero"] = retorno.find(".//NumeroNFe").text
            res["data_emissao"] = retorno.find(".//DataEmissaoNFe").text
            return res
        else:
            retorno_mensagem = "Error communicating with the webservice"
            return retorno_mensagem

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        numero_nfse = doc_numero.get("numero_nfse")
        codigo_verificacao = doc_numero.get("codigo_verificacao") or ""

        assinatura = self.im_prestador.zfill(8)
        assinatura += numero_nfse.zfill(12)

        cancelamento_nfe = self._schema["pedido_cancelamento_nfe"]
        consulta_nfe = self._schema["pedido_consulta_nfe"]
        raiz = cancelamento_nfe.PedidoCancelamentoNFe(
            Cabecalho=cancelamento_nfe.CabecalhoType(
                Versao=self._schema["versao_cabecalho"],
                CPFCNPJRemetente=consulta_nfe.tpCPFCNPJ(CNPJ=self.cnpj_prestador),
            ),
            Detalhe=[
                cancelamento_nfe.DetalheType(
                    ChaveNFe=cancelamento_nfe.tpChaveNFe(
                        InscricaoPrestador=int(self.im_prestador),
                        NumeroNFe=int(numero_nfse),
                        CodigoVerificacao=codigo_verificacao.zfill(8),
                    ),
                    AssinaturaCancelamento=assinatura,
                )
            ],
        )

        assinador = Assinatura(self._transmissao.certificado)
        for detalhe in raiz.Detalhe:
            detalhe.AssinaturaCancelamento = self._assina_paulistana(
                assinador, detalhe.AssinaturaCancelamento
            )
        xml_assinado = self.assina_raiz(raiz, "")
        return xml_assinado

    def analisa_retorno_cancelamento_paulistana(self, processo):
        retorno_mensagem = ""
        status = True
        if not processo.resposta.Cabecalho.Sucesso:
            status = False
            for erro in processo.resposta.Erro:
                retorno_mensagem = str(erro.Codigo) + " - " + erro.Descricao + "\n"
        return status, retorno_mensagem

    def assina_raiz(self, raiz, id, getchildren=False):
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        xml_assinado = Assinatura(self._transmissao.certificado).assina_nfse(xml_etree)
        return xml_assinado
