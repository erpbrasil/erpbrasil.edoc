from contextlib import suppress

from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico

from .resposta import analisar_retorno_raw

with suppress(ImportError):
    from nfelib.cte.bindings.v4_0 import (
        Cte,
        EvCancCte,
        RetConsSitCte,
        RetConsStatServCte,
        RetCte,
        RetEventoCte,
        TconsSitCte,
        TconsStatServ,
        Tcte,
    )


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

SVSP = ["AP", "PE", "RR", "SP"]
SVRS = [
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

SVSP_PRODUCAO = {
    "CTeConsultaV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeConsultaV4.asmx?wsdl",
    "CTeRecepcaoEventoV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
    "CTeRecepcaoGTVeV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
    "CTeRecepcaoOSV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
    "CTeRecepcaoSincV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
    "CTeStatusServicoV4": "https://nfe.fazenda.sp.gov.br/CTeWS/WS/CTeStatusServicoV4.asmx?wsdl",
}

SVSP_HOMOLOGACAO = {
    "CTeConsultaV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeConsultaV4.asmx?wsdl",
    "CTeRecepcaoEventoV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoEventoV4.asmx?wsdl",
    "CTeRecepcaoGTVeV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoGTVeV4.asmx?wsdl",
    "CTeRecepcaoOSV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoOSV4.asmx?wsdl",
    "CTeRecepcaoSincV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeRecepcaoSincV4.asmx?wsdl",
    "CTeStatusServicoV4": "https://homologacao.nfe.fazenda.sp.gov.br/CTeWS/WS/CTeStatusServicoV4.asmx?wsdl",
}

SVRS_PRODUCAO = {
    "CTeStatusServicoV4": "https://cte.svrs.rs.gov.br/ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
    "CTeConsultaV4": "https://cte.svrs.rs.gov.br/ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
    "CTeRecepcaoSincV4": "https://cte.svrs.rs.gov.br/ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
    "CTeRecepcaoOSV4": "https://cte.svrs.rs.gov.br/ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
    "CTeRecepcaoGTVeV4": "https://cte.svrs.rs.gov.br/ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
    "CTeRecepcaoEventoV4": "https://cte.svrs.rs.gov.br/ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
}

SVRS_HOMOLOGACAO = {
    "CTeStatusServicoV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeStatusServicoV4/CTeStatusServicoV4.asmx?wsdl",
    "CTeConsultaV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeConsultaV4/CTeConsultaV4.asmx?wsdl",
    "CTeRecepcaoSincV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeRecepcaoSincV4/CTeRecepcaoSincV4.asmx?wsdl",
    "CTeRecepcaoOSV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeRecepcaoOSV4/CTeRecepcaoOSV4.asmx?wsdl",
    "CTeRecepcaoGTVeV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeRecepcaoGTVeV4/CTeRecepcaoGTVeV4.asmx?wsdl",
    "CTeRecepcaoEventoV4": "https://cte-homologacao.svrs.rs.gov.br/ws/CTeRecepcaoEventoV4/CTeRecepcaoEventoV4.asmx?wsdl",
}

MT_PRODUCAO = {
    "CTeConsultaV4": "https://cte.sefaz.mt.gov.br/ctews2/services/CTeConsultaV4?wsdl",
    "CTeRecepcaoEventoV4": "https://cte.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoEventoV4?wsdl",
    "CTeStatusServicoV4": "https://cte.sefaz.mt.gov.br/ctews2/services/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoSincV4": "https://cte.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://cte.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoGTVeV4?wsdl",
    "CTeRecepcaoOSV4": "https://cte.sefaz.mt.gov.br/ctews/services/CTeRecepcaoOSV4?wsdl",
}

MT_HOMOLOGACAO = {
    "CTeStatusServicoV4": "https://homologacao.sefaz.mt.gov.br/ctews2/services/CTeStatusServicoV4?wsdl",
    "CTeConsultaV4": "https://homologacao.sefaz.mt.gov.br/ctews2/services/CTeConsultaV4?wsdl",
    "CTeRecepcaoSincV4": "https://homologacao.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://homologacao.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoGTVeV4?wsdl",
    "CTeRecepcaoEventoV4": "https://homologacao.sefaz.mt.gov.br/ctews2/services/CTeRecepcaoEventoV4?wsdl",
    "CTeRecepcaoOSV4": "https://homologacao.sefaz.mt.gov.br/ctews/services/CTeRecepcaoOSV4?wsdl",
}

MS_PRODUCAO = {
    "CTeRecepcaoSincV4": "https://producao.cte.ms.gov.br/ws/CTeRecepcaoSincV4?wsdl",
    "CTeStatusServicoV4": "https://producao.cte.ms.gov.br/ws/CTeStatusServicoV4?wsdl",
    "CTeConsultaV4": "https://producao.cte.ms.gov.br/ws/CTeConsultaV4?wsdl",
    "CTeRecepcaoEventoV4": "https://producao.cte.ms.gov.br/ws/CTeRecepcaoEventoV4?wsdl",
    "CTeRecepcaoOSV4": "https://producao.cte.ms.gov.br/ws/CTeRecepcaoOSV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://producao.cte.ms.gov.br/ws/CTeRecepcaoGTVeV4?wsdl",
}

MS_HOMOLOGACAO = {
    "CTeStatusServicoV4": "https://homologacao.cte.ms.gov.br/ws/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoEventoV4": "https://homologacao.cte.ms.gov.br/ws/CTeRecepcaoEventoV4?wsdl",
    "CTeConsultaV4": "https://homologacao.cte.ms.gov.br/ws/CTeConsultaV4?wsdl",
    "CTeRecepcaoSincV4": "https://homologacao.cte.ms.gov.br/ws/CTeRecepcaoSincV4?wsdl",
}

MG_PRODUCAO = {
    "CTeRecepcaoSincV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeRecepcaoGTVeV4?wsdl",
    "CTeRecepcaoOSV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeRecepcaoOSV4?wsdl",
    "CTeConsultaV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeConsultaV4?wsdl",
    "CTeStatusServicoV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoEventoV4": "https://cte.fazenda.mg.gov.br/cte/services/CTeRecepcaoEventoV4?wsdl",
}

MG_HOMOLOGACAO = {
    "CTeRecepcaoSincV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoOSV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeRecepcaoOSV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeRecepcaoGTVeV4?wsdl",
    "CTeConsultaV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeConsultaV4?wsdl",
    "CTeStatusServicoV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoEventoV4": "https://hcte.fazenda.mg.gov.br/cte/services/CTeRecepcaoEventoV4?wsdl",
}

PR_PRODUCAO = {
    "CTeRecepcaoSincV4": "https://cte.fazenda.pr.gov.br/cte4/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://cte.fazenda.pr.gov.br/cte4/CTeRecepcaoGTVeV4?wsdl",
    "CTeRecepcaoOSV4": "https://cte.fazenda.pr.gov.br/cte4/CTeRecepcaoOSV4?wsdl",
    "CTeConsultaV4": "https://cte.fazenda.pr.gov.br/cte4/CTeConsultaV4?wsdl",
    "CTeStatusServicoV4": "https://cte.fazenda.pr.gov.br/cte4/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoEventoV4": "https://cte.fazenda.pr.gov.br/cte4/CTeRecepcaoEventoV4?wsdl",
}

PR_HOMOLOGACAO = {
    "CTeConsultaV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeConsultaV4?wsdl",
    "CTeStatusServicoV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeStatusServicoV4?wsdl",
    "CTeRecepcaoSincV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeRecepcaoSincV4?wsdl",
    "CTeRecepcaoEventoV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeRecepcaoEventoV4?wsdl",
    "CTeRecepcaoGTVeV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeRecepcaoGTVeV4?wsdl",
    "CTeRecepcaoOSV4": "https://homologacao.cte.fazenda.pr.gov.br/cte4/CTeRecepcaoOSV4?wsdl",
}


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

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return (
            proc_envio.resposta.cStat
            == self._edoc_situacao_arquivo_recebido_com_sucesso
        )

    def status_servico(self):
        raiz = TconsStatServ(
            tpAmb=self.ambiente, cUF=self.uf, versao=self.versao
        )
        return self._post(
            raiz=raiz,
            url=self._search_url("CTeStatusServicoV4"),
            operacao="cteStatusServicoCT",
            classe=RetConsStatServCte,
        )

    def consulta_documento(self, chave):
        raiz = TconsSitCte(tpAmb=self.ambiente, chCTe=chave, versao=self.versao)
        return self._post(
            raiz=raiz,
            url=self._search_url("CTeConsultaV4"),
            operacao="cteConsultaCT",
            classe=RetConsSitCte,
        )

    def envia_documento(self, edoc):
        xml_assinado = self.assina_raiz(edoc, edoc.infCte.Id)
        raiz = Tcte(infCte=edoc, signature=None)
        xml_envio_string = raiz.to_xml()
        xml_envio_bytes = xml_envio_string.encode('utf-8')
        xml_envio_etree = etree.fromstring(xml_envio_bytes)
        xml_envio_etree.append(etree.fromstring(xml_assinado))
        return self._post(
            raiz=xml_envio_etree,
            url=self._search_url("CTeRecepcaoSincV4"),
            operacao="cteRecepcao",
            classe=RetCte,
        )

    def cancela_documento(self, doc_numero, justificativa):
        raiz = EvCancCte(
            descEvento="Cancelamento", nProt=doc_numero, xJust=justificativa
        )
        return self._post(
            raiz=raiz,
            url=self._search_url("CTeRecepcaoEventoV4"),
            operacao="cteRecepcaoEvento",
            classe=RetEventoCte,
        )

    def _search_url(self, service):
        sigla = ""
        for uf_code, ibge_code in SIGLA_ESTADO.items():
            if ibge_code == self.uf:
                sigla = uf_code

        if sigla == "MG":
            if self.ambiente == 1:
                return MG_PRODUCAO[service]
            else:
                return MG_HOMOLOGACAO[service]
        elif sigla == "MS":
            if self.ambiente == 1:
                return MS_PRODUCAO[service]
            else:
                return MS_HOMOLOGACAO[service]
        elif sigla == "MT":
            if self.ambiente == 1:
                return MT_PRODUCAO[service]
            else:
                return MT_HOMOLOGACAO[service]
        elif sigla == "PR":
            if self.ambiente == 1:
                return PR_PRODUCAO[service]
            else:
                return PR_HOMOLOGACAO[service]
        elif sigla in SVSP:
            if self.ambiente == 1:
                return SVSP_PRODUCAO[service]
            else:
                return SVSP_HOMOLOGACAO[service]
        elif sigla in SVRS:
            if self.ambiente == 1:
                return SVRS_PRODUCAO[service]
            else:
                return SVRS_HOMOLOGACAO[service]

    def consulta_recibo(self):
        pass

    def _post(self, raiz, url, operacao, classe):
        xml_string = raiz.to_xml()
        xml_etree = xml_string.from_xml()
        with self._transmissao.cliente(url):
            retorno = self._transmissao.enviar(operacao, xml_etree)
            return analisar_retorno_raw(operacao, raiz, xml_string, retorno, classe)

    def get_documento_id(self, edoc):
        return edoc.infCte.Id[:3], edoc.infCte.Id[3:]
