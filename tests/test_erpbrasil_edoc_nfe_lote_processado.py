from types import SimpleNamespace
from unittest import TestCase, mock

from lxml import etree

from erpbrasil.edoc.nfe import NFe
from erpbrasil.edoc.resposta import analisar_retorno_raw
from erpbrasil.nfelib_legacy.v4_00 import retEnviNFe

NS = "http://www.portalfiscal.inf.br/nfe"
CHAVE = "35260712345678000195550010000000011000000011"

ENVIO = (
    f'<enviNFe xmlns="{NS}" versao="4.00"><idLote>1</idLote><indSinc>0</indSinc>'
    f'<NFe xmlns="{NS}"><infNFe Id="NFe{CHAVE}" versao="4.00"/></NFe></enviNFe>'
)

ENVELOPE = (
    '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"><soap:Body>'
    '<nfeResultMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">'
    "{ret}</nfeResultMsg></soap:Body></soap:Envelope>"
)

RET_104 = (
    f'<retEnviNFe xmlns="{NS}" versao="4.00">'
    "<tpAmb>2</tpAmb><verAplic>SVRS2026</verAplic>"
    "<cStat>104</cStat><xMotivo>Lote processado</xMotivo><cUF>35</cUF>"
    "<dhRecbto>2026-07-27T10:00:00-03:00</dhRecbto>"
    '<protNFe versao="4.00"><infProt><tpAmb>2</tpAmb><verAplic>SVRS2026</verAplic>'
    f"<chNFe>{CHAVE}</chNFe>"
    "<dhRecbto>2026-07-27T10:00:00-03:00</dhRecbto><nProt>135260000000001</nProt>"
    "<digVal>YWJjZA==</digVal><cStat>100</cStat>"
    "<xMotivo>Autorizado o uso da NF-e</xMotivo>"
    "</infProt></protNFe></retEnviNFe>"
)

RET_103 = (
    f'<retEnviNFe xmlns="{NS}" versao="4.00">'
    "<tpAmb>2</tpAmb><verAplic>SVRS2026</verAplic>"
    "<cStat>103</cStat><xMotivo>Lote recebido com sucesso</xMotivo><cUF>35</cUF>"
    "<dhRecbto>2026-07-27T10:00:00-03:00</dhRecbto>"
    "<infRec><nRec>351000000000001</nRec><tMed>1</tMed></infRec></retEnviNFe>"
)


class _RespostaHttp:
    """O que o analisar_retorno_raw usa da resposta do requests."""

    def __init__(self, ret):
        self.text = ENVELOPE.format(ret=ret)

    def raise_for_status(self):
        return None


def _processo_envio(ret):
    return analisar_retorno_raw(
        "nfeAutorizacaoLote",
        etree.fromstring(ENVIO),
        ENVIO,
        _RespostaHttp(ret),
        retEnviNFe,
    )


class LoteProcessadoNoEnvioTests(TestCase):
    """A SEFAZ pode responder 104 (lote processado) a um envio assíncrono (#102)."""

    def _nfe(self, ret, envio_sincrono):
        nfe = NFe(False, "35", versao="4.00", ambiente="2", envio_sincrono=envio_sincrono)
        nfe.envia_documento = lambda edoc: _processo_envio(ret)
        nfe.consulta_recibo = mock.Mock()
        return nfe

    def test_104_em_envio_assincrono_monta_o_processo_sem_consultar_recibo(self):
        nfe = self._nfe(RET_104, envio_sincrono=False)
        with mock.patch("erpbrasil.edoc.nfe.time.sleep") as sleep:
            processos = list(nfe.processar_documento(object()))
        self.assertEqual(len(processos), 1)
        self.assertEqual(processos[0].resposta.cStat, "104")
        self.assertEqual(processos[0].protocolo.infProt.nProt, "135260000000001")
        self.assertIn(b"nfeProc", processos[0].processo_xml)
        sleep.assert_not_called()
        nfe.consulta_recibo.assert_not_called()

    def test_103_em_envio_assincrono_continua_consultando_o_recibo(self):
        nfe = self._nfe(RET_103, envio_sincrono=False)
        nfe.monta_processo = mock.Mock()
        nfe.consulta_recibo.return_value = SimpleNamespace(resposta=SimpleNamespace(cStat="104"))
        with mock.patch("erpbrasil.edoc.nfe.time.sleep") as sleep:
            processos = list(nfe.processar_documento(object()))
        self.assertEqual(len(processos), 2)
        sleep.assert_called_once_with(1.0)
        nfe.consulta_recibo.assert_called_once()

    def test_104_em_envio_sincrono_continua_igual(self):
        nfe = self._nfe(RET_104, envio_sincrono=True)
        processos = list(nfe.processar_documento(object()))
        self.assertEqual(len(processos), 1)
        self.assertIn(b"nfeProc", processos[0].processo_xml)
        nfe.consulta_recibo.assert_not_called()
