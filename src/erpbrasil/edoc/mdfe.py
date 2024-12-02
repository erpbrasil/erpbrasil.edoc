# Copyright (C) 2019  Luis Felipe Mileo - KMEE
# Copyright (C) 2024  Marcel Savegnago - Escodoo


import base64
import gzip
from contextlib import suppress

from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.transmissao import TransmissaoSOAP

with suppress(ImportError):
    from nfelib.mdfe.bindings.v3_0 import (
        ConsSitMdfe,
        ConsStatServMdfe,
        EvCancMdfe,
        EvEncMdfe,
        EventoMdfe,
        RetConsSitMdfe,
        RetConsStatServMdfe,
        RetEventoMdfe,
        RetMdfe,
    )

AMBIENTE_PRODUCAO = 1
AMBIENTE_HOMOLOGACAO = 2

WS_MDFE_CONSULTA = "MDFeConsulta"
WS_MDFE_STATUS_SERVICO = "MDFeStatusServicoMDF"
WS_MDFE_CONSULTA_NAO_ENCERRADOS = "MDFeConsNaoEnc"
WS_MDFE_DISTRIBUICAO = "MDFeDistribuicaoDFe"

WS_MDFE_RECEPCAO = "MDFeRecepcao"
WS_MDFE_RECEPCAO_SINC = "MDFeRecepcaoSinc"
WS_MDFE_RET_RECEPCAO = "MDFeRetRecepcao"
WS_MDFE_RECEPCAO_EVENTO = "MDFeRecepcaoEvento"

QR_CODE_URL = "QRCode"

MDFE_MODELO = "58"

SIGLA_ESTADO = {
    "AC": 12,
    "AL": 27,
    "AM": 13,
    "AP": 16,
    "BA": 29,
    "CE": 23,
    "DF": 53,
    "ES": 32,
    "GO": 52,
    "MA": 21,
    "MG": 31,
    "MS": 50,
    "MT": 51,
    "PA": 15,
    "PB": 25,
    "PE": 26,
    "PI": 22,
    "PR": 41,
    "RJ": 33,
    "RN": 24,
    "RO": 11,
    "RR": 14,
    "RS": 43,
    "SC": 42,
    "SE": 28,
    "SP": 35,
    "TO": 17,
    "AN": 91,
}

SVRS_STATES = [
    "AC",
    "AL",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "PA",
    "PB",
    "PI",
    "RJ",
    "RN",
    "RO",
    "SC",
    "SE",
    "TO",
    "AP",
    "PE",
    "RR",
    "SP",
]

SVRS = {
    AMBIENTE_PRODUCAO: {
        "servidor": "mdfe.svrs.rs.gov.br",
        WS_MDFE_RET_RECEPCAO: "ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl",
        WS_MDFE_RECEPCAO_EVENTO: "ws/MDFeRecepcaoEvento/MDFeRecepcaoEvento.asmx?wsdl",
        WS_MDFE_CONSULTA: "ws/MDFeConsulta/MDFeConsulta.asmx?wsdl",
        WS_MDFE_STATUS_SERVICO: "ws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl",
        WS_MDFE_CONSULTA_NAO_ENCERRADOS: "ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl",
        WS_MDFE_DISTRIBUICAO: "ws/MDFeDistribuicaoDFe/MDFeDistribuicaoDFe.asmx?wsdl",
        WS_MDFE_RECEPCAO_SINC: "ws/MDFeRecepcaoSinc/MDFeRecepcaoSinc.asmx?wsdl",
        QR_CODE_URL: "https://dfe-portal.svrs.rs.gov.br/mdfe/qrCode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "mdfe-homologacao.svrs.rs.gov.br",
        WS_MDFE_RET_RECEPCAO: "ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl",
        WS_MDFE_RECEPCAO_EVENTO: "ws/MDFeRecepcaoEvento/MDFeRecepcaoEvento.asmx?wsdl",
        WS_MDFE_CONSULTA: "ws/MDFeConsulta/MDFeConsulta.asmx?wsdl",
        WS_MDFE_STATUS_SERVICO: "ws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl",
        WS_MDFE_CONSULTA_NAO_ENCERRADOS: "ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl",
        WS_MDFE_DISTRIBUICAO: "ws/MDFeDistribuicaoDFe/MDFeDistribuicaoDFe.asmx?wsdl",
        WS_MDFE_RECEPCAO_SINC: "ws/MDFeRecepcaoSinc/MDFeRecepcaoSinc.asmx?wsdl",
        QR_CODE_URL: "https://dfe-portal.svrs.rs.gov.br/mdfe/qrCode",
    },
}


def get_service_url(sigla_estado, service, ambiente):
    state_config = SVRS if sigla_estado in SVRS_STATES else sigla_estado

    if not state_config:
        raise ValueError(
            f"Estado {sigla_estado} não suportado ou configuração ausente."
        )

    environment = AMBIENTE_PRODUCAO if ambiente == 1 else AMBIENTE_HOMOLOGACAO
    if service == "QRCode":
        return state_config[environment][QR_CODE_URL]

    server = state_config[environment]["servidor"]
    service_path = state_config[environment][service]
    return f"https://{server}/{service_path}"


class MDFe(DocumentoEletronico):
    _namespace = "http://www.portalfiscal.inf.br/mdfe"

    _edoc_situacao_arquivo_recebido_com_sucesso = "103"
    _edoc_situacao_servico_em_operacao = "107"
    _edoc_situacao_ja_enviado = ("100", "101", "132")

    _consulta_servico_ao_enviar = True
    _maximo_tentativas_consulta_recibo = 5

    def __init__(self, transmissao, uf, versao="3.00", ambiente="2", mod="58"):
        super().__init__(transmissao)
        self.versao = str(versao)
        self.ambiente = str(ambiente)
        self.uf = int(uf)
        self.mod = str(mod)

    def _get_ws_endpoint(self, service):
        sigla = None
        for uf_code, ibge_code in SIGLA_ESTADO.items():
            if ibge_code == self.uf:
                sigla = uf_code
                break

        if not sigla:
            raise ValueError(f"UF {self.uf} não suportado ou configuração ausente.")

        return get_service_url(sigla, service, self.ambiente)

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return (
            proc_envio.resposta.cStat
            == self._edoc_situacao_arquivo_recebido_com_sucesso
        )

    def status_servico(self):
        raiz = ConsStatServMdfe(tpAmb=self.ambiente, versao=self.versao)
        return self._post(
            raiz=raiz,
            url=self._get_ws_endpoint(WS_MDFE_STATUS_SERVICO),
            operacao="mdfeStatusServicoMDF",
            classe=RetConsStatServMdfe,
        )

    def get_documento_id(self, edoc):
        return edoc.infMdfe.Id[:3], edoc.infMdfe.Id[3:]

    def monta_qrcode(self, chave):
        return (
            f"{self._get_ws_endpoint(QR_CODE_URL)}?chMDFe={chave}&tpAmb={self.ambiente}"
        )

    def consulta_documento(self, chave):
        raiz = ConsSitMdfe(tpAmb=self.ambiente, chMDFe=chave, versao=self.versao)
        return self._post(
            raiz=raiz,
            url=self._get_ws_endpoint(WS_MDFE_CONSULTA),
            operacao="mdfeConsulta",
            classe=RetConsSitMdfe,
        )

    def envia_documento(self, edoc):
        xml_assinado = self.assina_raiz(edoc, edoc.infMDFe.Id)

        # Compactar o XML assinado com GZip
        gzipped_xml = gzip.compress(xml_assinado.encode("utf-8"))

        # Codificar o XML compactado em Base64
        base64_gzipped_xml = base64.b64encode(gzipped_xml).decode("utf-8")

        return self._post(
            raiz=base64_gzipped_xml,
            url=self._get_ws_endpoint(WS_MDFE_RECEPCAO_SINC),
            operacao="mdfeRecepcao",
            classe=RetMdfe,
        )

    def monta_mdfe_proc(self, doc, prot):
        """
        Constrói e retorna o XML do processo da MDF-e,
        incorporando a MDF-e com o seu protocolo de autorização.
        """
        proc = etree.Element(
            f"{{{self._namespace}}}mdfeProc",
            versao=self.versao,
            nsmap={None: self._namespace},
        )
        proc.append(doc)
        proc.append(prot)
        return etree.tostring(proc)

    def envia_evento(self, evento, tipo, chave, sequencia="001", data_hora=False):
        inf_evento = EventoMdfe.InfEvento(
            Id="ID" + tipo + chave + sequencia.zfill(2),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chMDFe=chave,
            dhEvento=data_hora or self._hora_agora(),
            tpEvento=tipo,
            nSeqEvento=sequencia,
            detEvento=EventoMdfe.InfEvento.DetEvento(
                versaoEvento="3.00", any_element=evento
            ),
        )
        raiz = EventoMdfe(versao="3.00", infEvento=inf_evento)
        xml_assinado = etree.fromstring(self.assina_raiz(raiz, raiz.infEvento.Id))

        return self._post(
            xml_assinado,
            self._get_ws_endpoint(WS_MDFE_RECEPCAO_EVENTO),
            "mdfeRecepcaoEvento",
            RetEventoMdfe,
        )

    def cancela_documento(
        self, chave, protocolo_autorizacao, justificativa, data_hora_evento=False
    ):
        evento_canc = EvCancMdfe(
            descEvento="Cancelamento", nProt=protocolo_autorizacao, xJust=justificativa
        )
        return self.envia_evento(
            evento=evento_canc, tipo="110111", chave=chave, data_hora=data_hora_evento
        )

    def encerra_documento(
        self, chave, protocolo_autorizacao, estado, municipio, data_hora_evento=False
    ):
        encerramento = EvEncMdfe(
            descEvento="Encerramento",
            dtEnc=self._data_hoje(),
            nProt=protocolo_autorizacao,
            cUF=estado,
            cMun=municipio,
        )
        return self.envia_evento(
            evento=encerramento, tipo="110112", chave=chave, data_hora=data_hora_evento
        )

    def consulta_recibo(self):
        pass


class TransmissaoMDFE(TransmissaoSOAP):
    def interpretar_mensagem(self, mensagem, **kwargs):
        if isinstance(mensagem, str):
            try:
                return etree.fromstring(
                    mensagem, parser=etree.XMLParser(remove_blank_text=True)
                )
            except (etree.XMLSyntaxError, ValueError):
                # Retorna a string original se houver um erro na conversão
                return mensagem
        return mensagem
