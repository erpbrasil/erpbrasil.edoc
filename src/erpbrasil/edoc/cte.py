from contextlib import suppress

from lxml import etree

from erpbrasil.assinatura.assinatura import Assinatura
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.transmissao import TransmissaoSOAP

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

    def __init__(self, config, xml):
        self.config = config
        self._xml = xml
        self._ambiente = self.config  # tpAmb
        self._uf = self.config  # uf
        self._versao = 4.00
        self._chaveCte = self._gerar_chave(self.config)
        self.assinatura = Assinatura(self.config)  # self.config.certificado
        self.transmissao = TransmissaoSOAP(self.config)  # self.config.certificado
        super().__init__(self.transmissao)

    def status_servico(self):
        raiz = TconsStatServ(
            tpAmb=self._ambiente, cUF=SIGLA_ESTADO[self._uf], versao=self._versao
        )
        return self._post(
            raiz=raiz,
            url=self._search_url("CTeStatusServicoV4"),
            operacao="cteStatusServicoCT",
            classe=RetConsStatServCte,
        )

    def consulta_documento(self, chave):
        raiz = TconsSitCte(tpAmb=self._ambiente, chCTe=chave, versao=self._versao)
        return self._post(
            raiz=raiz,
            url=self._search_url("CTeConsultaV4"),
            operacao="cteConsultaCT",
            classe=RetConsSitCte,
        )

    def envia_documento(self, edoc):
        xml_assinado = self.assina_raiz(edoc, edoc.infCTe.Id)
        raiz = Tcte(infCte=edoc, signature=self.assinatura)
        xml_envio_string = raiz.to_xml()
        xml_envio_etree = xml_envio_string.from_xml()
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

    def _gerar_chave(self, edoc):
        """
            0  2    6             20  22  25        34 35      43  --> índice
            |  |    |              |  |   |         | |        |
            |  |    |              |  |   |         | |        |
        CTe  32 1712 32438772000104 57 001 000199075 1 39868226 3
        """
        cte = Cte(edoc)
        chave = ChaveEdoc()
        chave.cUF = cte.InfCte.Ide.cUF
        dhEmi = cte.InfCte.Ide.dhEmi
        chave.AAMM = dhEmi[2:4] + dhEmi[5:7]
        chave.CNPJ = cte.InfCte.Emit.CNPJ
        chave.mod = cte.InfCte.Ide.mod
        chave.serie = cte.InfCte.Ide.serie
        chave.nCT = cte.InfCte.Ide.nCT
        chave.tpEmis = cte.InfCte.Ide.tpEmis
        chave.cCT = cte.InfCte.Ide.cCT
        chave.cDV = cte.InfCte.Ide.cDV
        return chave

    def _search_url(self, service):
        if self._uf == "MG":
            if self._ambiente == 1:
                return MG_PRODUCAO[service]
            else:
                return MG_HOMOLOGACAO[service]
        elif self._uf == "MS":
            if self._ambiente == 1:
                return MS_PRODUCAO[service]
            else:
                return MS_HOMOLOGACAO[service]
        elif self._uf == "MT":
            if self._ambiente == 1:
                return MT_PRODUCAO[service]
            else:
                return MT_HOMOLOGACAO[service]
        elif self._uf == "PR":
            if self._ambiente == 1:
                return PR_PRODUCAO[service]
            else:
                return PR_HOMOLOGACAO[service]
        elif self._uf == "SVSP":
            if self._ambiente == 1:
                return SVSP_PRODUCAO[service]
            else:
                return SVSP_HOMOLOGACAO[service]
        elif self._uf == "SVRS":
            if self._ambiente == 1:
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
