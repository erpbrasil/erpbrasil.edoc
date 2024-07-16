import base64
import gzip
from contextlib import suppress

from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.transmissao import TransmissaoSOAP

with suppress(ImportError):
    from nfelib.cte.bindings.v4_0 import (
        ConsSitCte,
        ConsStatServCte,
        EvCancCte,
        EvCceCte,
        EventoCte,
        RetConsSitCte,
        RetConsStatServCte,
        RetCte,
        RetEventoCte,
    )

TEXTO_CARTA_CORRECAO = """A Carta de Correcao e disciplinada pelo Art. 58-B do \
CONVENIO/SINIEF 06/89: Fica permitida a utilizacao de carta de \
correcao, para regularizacao de erro ocorrido na emissao de \
documentos fiscais relativos a prestacao de servico de \
transporte, desde que o erro nao esteja relacionado com: \
I - as variaveis que determinam o valor do imposto tais como: \
base de calculo, aliquota, diferenca de preco, quantidade, \
valor da prestacao; II - a correcao de dados cadastrais que \
implique mudanca do emitente, tomador, remetente ou do \
destinatario; III - a data de emissao ou de saida."""

AMBIENTE_PRODUCAO = "producao"
AMBIENTE_HOMOLOGACAO = "homologacao"

WS_CTE_CONSULTA = "CTeConsultaV4"
WS_CTE_RECEPCAO_EVENTO = "CTeRecepcaoEventoV4"
WS_CTE_RECEPCAO_GT = "CTeRecepcaoGTVeV4"
WS_CTE_RECEPCAO_OS = "CTeRecepcaoOSV4"
WS_CTE_RECEPCAO_SINC = "CTeRecepcaoSincV4"
WS_CTE_STATUS_SERVICO = "CTeStatusServicoV4"
QR_CODE_URL = "QRCode"

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

SVSP_STATES = ["AP", "PE", "RR", "SP"]
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
]

SVSP = {
    AMBIENTE_PRODUCAO: {
        "servidor": "nfe.fazenda.sp.gov.br",
        WS_CTE_CONSULTA: "CTeWS/WS/CTeConsultaV4.asmx?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "CTeWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
        WS_CTE_RECEPCAO_GT: "CTeWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
        WS_CTE_RECEPCAO_OS: "CTeWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
        WS_CTE_RECEPCAO_SINC: "CTeWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
        WS_CTE_STATUS_SERVICO: "CTeWS/WS/CTeStatusServicoV4.asmx?wsdl",
        QR_CODE_URL: "https://nfe.fazenda.sp.gov.br/CTeConsulta/qrCode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "homologacao.nfe.fazenda.sp.gov.br",
        WS_CTE_CONSULTA: "CTeWS/WS/CTeConsultaV4.asmx?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "CTeWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
        WS_CTE_RECEPCAO_GT: "CTeWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
        WS_CTE_RECEPCAO_OS: "CTeWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
        WS_CTE_RECEPCAO_SINC: "CTeWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
        WS_CTE_STATUS_SERVICO: "CTeWS/WS/CTeStatusServicoV4.asmx?wsdl",
        QR_CODE_URL: "https://homologacao.nfe.fazenda.sp.gov.br/CTeConsulta/qrCode",
    },
}

SVRS = {
    AMBIENTE_PRODUCAO: {
        "servidor": "cte.svrs.rs.gov.br",
        WS_CTE_CONSULTA: "ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
        WS_CTE_RECEPCAO_GT: "ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
        WS_CTE_RECEPCAO_OS: "ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
        WS_CTE_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
        WS_CTE_STATUS_SERVICO: "ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
        QR_CODE_URL: "https://dfe-portal.svrs.rs.gov.br/cte/qrCode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "cte-homologacao.svrs.rs.gov.br",
        WS_CTE_CONSULTA: "ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
        WS_CTE_RECEPCAO_GT: "ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
        WS_CTE_RECEPCAO_OS: "ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
        WS_CTE_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
        WS_CTE_STATUS_SERVICO: "ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
        QR_CODE_URL: "https://dfe-portal.svrs.rs.gov.br/cte/qrCode",
    },
}

MT = {
    AMBIENTE_PRODUCAO: {
        "servidor": "cte.sefaz.mt.gov.br",
        WS_CTE_CONSULTA: "ctews2/services/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ctews2/services/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "ctews2/services/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "ctews/services/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "ctews2/services/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "ctews2/services/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "https://www.sefaz.mt.gov.br/cte/qrcode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "homologacao.sefaz.mt.gov.br",
        WS_CTE_CONSULTA: "ctews2/services/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ctews2/services/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "ctews2/services/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "ctews/services/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "ctews2/services/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "ctews2/services/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "https://homologacao.sefaz.mt.gov.br/cte/qrcode",
    },
}

MS = {
    AMBIENTE_PRODUCAO: {
        "servidor": "producao.cte.ms.gov.br",
        WS_CTE_CONSULTA: "ws/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "ws/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "ws/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "ws/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "http://www.dfe.ms.gov.br/cte/qrcode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "homologacao.cte.ms.gov.br",
        WS_CTE_CONSULTA: "ws/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "ws/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "ws/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "ws/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "ws/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "ws/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "http://www.dfe.ms.gov.br/cte/qrcode",
    },
}

MG = {
    AMBIENTE_PRODUCAO: {
        "servidor": "cte.fazenda.mg.gov.br",
        WS_CTE_CONSULTA: "cte/services/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "cte/services/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "cte/services/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "cte/services/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "cte/services/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "cte/services/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "https://cte.fazenda.mg.gov.br/portalcte/sistema/qrcode.xhtml",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "hcte.fazenda.mg.gov.br",
        WS_CTE_CONSULTA: "cte/services/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "cte/services/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "cte/services/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "cte/services/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "cte/services/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "cte/services/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "https://cte.fazenda.mg.gov.br/portalcte/sistema/qrcode.xhtml",
    },
}

PR = {
    AMBIENTE_PRODUCAO: {
        "servidor": "cte.fazenda.pr.gov.br",
        WS_CTE_CONSULTA: "cte4/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "cte4/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "cte4/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "cte4/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "cte4/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "cte4/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "http://www.fazenda.pr.gov.br/cte/qrcode",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "homologacao.cte.fazenda.pr.gov.br",
        WS_CTE_CONSULTA: "cte4/CTeConsultaV4?wsdl",
        WS_CTE_RECEPCAO_EVENTO: "cte4/CTeRecepcaoEventoV4?wsdl",
        WS_CTE_RECEPCAO_GT: "cte4/CTeRecepcaoGTVeV4?wsdl",
        WS_CTE_RECEPCAO_OS: "cte4/CTeRecepcaoOSV4?wsdl",
        WS_CTE_RECEPCAO_SINC: "cte4/CTeRecepcaoSincV4?wsdl",
        WS_CTE_STATUS_SERVICO: "cte4/CTeStatusServicoV4?wsdl",
        QR_CODE_URL: "http://www.fazenda.pr.gov.br/cte/qrcode",
    },
}


def get_service_url(sigla_estado, service, ambiente):
    if sigla_estado in SVSP_STATES:
        state_config = SVSP
    elif sigla_estado in SVRS_STATES:
        state_config = SVRS
    else:
        state_config = sigla_estado

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


class CTe(DocumentoEletronico):
    _namespace = "http://www.portalfiscal.inf.br/cte"
    _edoc_situacao_arquivo_recebido_com_sucesso = "103"
    _edoc_situacao_servico_em_operacao = "107"
    _consulta_servico_ao_enviar = True
    _consulta_documento_antes_de_enviar = True
    _maximo_tentativas_consulta_recibo = 5

    def __init__(self, transmissao, uf, versao="4.00", ambiente="1", mod="57"):
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
        raiz = ConsStatServCte(tpAmb=self.ambiente, cUF=self.uf, versao=self.versao)
        return self._post(
            raiz=raiz,
            url=self._get_ws_endpoint(WS_CTE_STATUS_SERVICO),
            operacao="cteStatusServicoCT",
            classe=RetConsStatServCte,
        )

    def consulta_documento(self, chave):
        raiz = ConsSitCte(tpAmb=self.ambiente, chCTe=chave, versao=self.versao)
        return self._post(
            raiz=raiz,
            url=self._get_ws_endpoint(WS_CTE_CONSULTA),
            operacao="cteConsultaCT",
            classe=RetConsSitCte,
        )

    def envia_documento(self, edoc):
        xml_assinado = self.assina_raiz(edoc, edoc.infCte.Id)

        # Compactar o XML assinado com GZip
        gzipped_xml = gzip.compress(xml_assinado.encode("utf-8"))

        # Codificar o XML compactado em Base64
        base64_gzipped_xml = base64.b64encode(gzipped_xml).decode("utf-8")

        return self._post(
            raiz=base64_gzipped_xml,
            url=self._get_ws_endpoint(WS_CTE_RECEPCAO_SINC),
            operacao="cteRecepcao",
            classe=RetCte,
        )

    def enviar_lote_evento(self, lista_eventos, numero_lote=False):
        for raiz_evento in lista_eventos:
            evento = EventoCte(
                versao="4.00",
                infEvento=raiz_evento,
            )
            xml_assinado = self.assina_raiz(evento, evento.infEvento.Id)

        return self._post(
            xml_assinado,
            self._get_ws_endpoint(WS_CTE_RECEPCAO_EVENTO),
            "cteRecepcaoEvento",
            RetEventoCte,
        )

    def cancela_documento(
        self, chave, protocolo_autorizacao, justificativa, data_hora_evento=False
    ):
        tipo_evento = "110111"
        sequencia = "1"
        raiz = EventoCte.InfEvento(
            Id="ID" + tipo_evento + chave + sequencia.zfill(3),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chCTe=chave,
            dhEvento=data_hora_evento or self._hora_agora(),
            tpEvento=tipo_evento,
            nSeqEvento=sequencia,
            detEvento=EventoCte.InfEvento.DetEvento(
                EvCancCte(
                    descEvento="Cancelamento",
                    nProt=protocolo_autorizacao,
                    xJust=justificativa,
                ),
                versaoEvento="4.00",
            ),
        )
        return raiz

    def carta_correcao(
        self,
        chave,
        protocolo_autorizacao,
        justificativa,
        sequencia,
        data_hora_evento=False,
    ):
        tipo_evento = "110110"

        temp_string = justificativa.replace("\\n", "TEMP_NEW_LINE")

        # Separar a string pelo separador
        lista = temp_string.split(";")

        # Dividir a lista em sublistas usando o separador temporário
        result = []
        sublist = []

        for item in lista:
            if "TEMP_NEW_LINE" in item:
                parts = item.split("TEMP_NEW_LINE")
                sublist.append(parts[0])
                result.append(sublist)
                sublist = [parts[1]]
            else:
                sublist.append(item)

        # Adicionar a última sublista
        result.append(sublist)
        correcoes = []
        nro_item = 1  # Inicia a sequência de itens alterados

        for linha in result:
            grupo, campo, valor = linha
            correcao = EvCceCte.InfCorrecao(
                grupoAlterado=grupo,
                campoAlterado=campo,
                valorAlterado=valor,
                nroItemAlterado=str(
                    nro_item
                ),  # Adiciona a sequência de itens alterados
            )
            correcoes.append(correcao)
            nro_item += 1  # Incrementa a sequência

        raiz = EventoCte.InfEvento(
            Id="ID" + tipo_evento + chave + sequencia.zfill(3),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chCTe=chave,
            dhEvento=data_hora_evento or self._hora_agora(),
            tpEvento=tipo_evento,
            nSeqEvento=sequencia,
            detEvento=EventoCte.InfEvento.DetEvento(
                EvCceCte(
                    descEvento="Carta de Correcao",
                    infCorrecao=correcoes,  # Lista de correções
                    xCondUso=TEXTO_CARTA_CORRECAO,
                ),
                versaoEvento="4.00",
            ),
        )
        return raiz

    def consulta_recibo(self):
        pass

    def get_documento_id(self, edoc):
        return edoc.infCte.Id[:3], edoc.infCte.Id[3:]

    def monta_qrcode(self, chave):
        return (
            f"{self._get_ws_endpoint(QR_CODE_URL)}?chCTe={chave}&tpAmb={self.ambiente}"
        )


class TransmissaoCTE(TransmissaoSOAP):
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
