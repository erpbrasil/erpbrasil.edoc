# Copyright (C) 2026  KMEE
import base64
import datetime
from types import SimpleNamespace
from unittest import TestCase

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree

from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.edoc.provedores.cidades import NFSeFactory
from erpbrasil.edoc.provedores.notacontrol import (
    NS,
    NS_DS,
    NotaControl,
    dps_numero_serie,
)

DPS_ID = "DPS520870720224450700011600001000000000000001"
DPS = (
    f'<DPS xmlns="{NS}" versao="1.01"><infDPS Id="{DPS_ID}">'
    "<tpAmb>2</tpAmb><serie>1</serie><nDPS>1</nDPS></infDPS></DPS>"
)

RESPOSTA_AUTORIZADA = f"""<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><RecepcionarLoteDpsSincronoResponse xmlns="{NS}">
<RecepcionarLoteDpsSincronoResult>
<EnviarLoteDpsSincronoResposta xmlns="{NS}">
  <NumeroLote>7</NumeroLote><Protocolo>PROT-123</Protocolo>
  <ListaNfse><CompNfse><Nfse versao="1.01">
    <infNFSe Id="NFS52087072202244507000116000000000000126090000001">
      <nNFSe>1</nNFSe>
    </infNFSe>
  </Nfse></CompNfse>
  <ListaMensagemAlertaRetorno><MensagemRetorno><Codigo>A001</Codigo>
    <Mensagem>Alerta de teste</Mensagem></MensagemRetorno></ListaMensagemAlertaRetorno>
  </ListaNfse>
</EnviarLoteDpsSincronoResposta>
</RecepcionarLoteDpsSincronoResult></RecepcionarLoteDpsSincronoResponse></soap:Body>
</soap:Envelope>"""

RESPOSTA_REJEITADA = f"""<EnviarLoteDpsSincronoResposta xmlns="{NS}">
  <ListaMensagemRetorno><MensagemRetorno><Codigo>E160</Codigo>
    <Mensagem>Arquivo em desacordo com o XML Schema</Mensagem>
    <Correcao>Informe o cTribMun</Correcao></MensagemRetorno></ListaMensagemRetorno>
  <ListaMensagemRetornoLote><MensagemRetorno>
    <IdentificacaoDps><NumDPS>1</NumDPS><SerieDPS>1</SerieDPS></IdentificacaoDps>
    <Codigo>E0120</Codigo><Mensagem>Serie invalida</Mensagem>
  </MensagemRetorno></ListaMensagemRetornoLote>
</EnviarLoteDpsSincronoResposta>"""

FAULT = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body><soap:Fault><faultcode>soap:Client</faultcode>
<faultstring>Error</faultstring></soap:Fault></soap:Body></soap:Envelope>"""

SOAP = (
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body>'
    '<{op}Response xmlns="' + NS + '"><{resp}>{corpo}</{resp}></{op}Response></s:Body></s:Envelope>'
)
CHAVE = "52087071228222338000107000000000000226111794960947"
NFSE_REAL = (
    f'<CompNfse><NFSe versao="1.01"><infNFSe Id="NFS{CHAVE}"><nNFSe>2</nNFSe>'
    "<cStat>100</cStat></infNFSe></NFSe>{eventos}</CompNfse>"
)
EVENTO_CANCELAMENTO = (
    '<ListaEvento><evento versao="1.00"><infEvento Id="EVT1"><pedRegEvento versao="1.00">'
    f'<infPedReg Id="PRE1"><chNFSe>{CHAVE}</chNFSe><e101101><xDesc>Cancelamento de NFS-e</xDesc>'
    "<cMotivo>1</cMotivo><xMotivo>Erro na emissao</xMotivo></e101101></infPedReg>"
    "</pedRegEvento></infEvento></evento></ListaEvento>"
)


def certificado_temporario():
    """Certificado autoassinado valido hoje (o fixture do repo esta vencido)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "QUICK TESTE:02244507000116")])
    agora = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora - datetime.timedelta(days=1))
        .not_valid_after(agora + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    pfx = pkcs12.serialize_key_and_certificates(
        b"teste", key, cert, None, serialization.BestAvailableEncryption(b"teste")
    )
    # o Certificado recebe bytes em base64, como o Odoo guarda o arquivo
    return Certificado(base64.b64encode(pfx), "teste")


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content.encode("utf-8")
        self.status_code = status_code


class FakeSession:
    def __init__(self, resposta, status_code=200):
        self.resposta = resposta
        self.status_code = status_code
        self.chamadas = []

    def post(self, url, data, headers, timeout):
        self.chamadas.append({"url": url, "data": data.decode(), "headers": headers})
        return FakeResponse(self.resposta, self.status_code)


class TestNotaControl(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transmissao = SimpleNamespace(certificado=certificado_temporario())

    def _provedor(self, session=None, algoritmo="sha1", ambiente="2"):
        return NotaControl(
            self.transmissao,
            ambiente,
            5208707,
            "02.244.507/0001-16",
            "778151",
            algoritmo=algoritmo,
            session=session,
        )

    def test_factory_goiania(self):
        provedor = NFSeFactory(self.transmissao, "2", 5208707, "02244507000116", "778151")
        self.assertIsInstance(provedor, NotaControl)

    def test_url(self):
        self.assertIn("/homologacao/", self._provedor().url)
        self.assertIn("/goiania/", self._provedor(ambiente="1").url)
        outro = NotaControl(self.transmissao, "1", 3550308, "1", "1")
        with self.assertRaises(ValueError):
            outro.url  # noqa: B018

    def test_lote_com_duas_assinaturas(self):
        provedor = self._provedor(algoritmo="sha256")
        dps = provedor.assinar_dps(DPS)
        lote = etree.fromstring(provedor.assinar_lote(provedor.montar_lote([dps], 7), 7))

        lote_dps = lote.find(f"{{{NS}}}LoteDps")
        self.assertEqual(lote_dps.get("Id"), "Lote7")
        self.assertEqual(lote_dps.findtext(f"{{{NS}}}QuantidadeDps"), "1")
        self.assertEqual(lote_dps.findtext(f"{{{NS}}}Prestador/{{{NS}}}CNPJ"), "02244507000116")
        self.assertEqual(lote_dps.findtext(f"{{{NS}}}Prestador/{{{NS}}}IM"), "778151")

        # Signature da DPS irma da infDPS; a do lote irma do LoteDps
        sig_dps = lote.find(f".//{{{NS}}}DPS/{{{NS_DS}}}Signature")
        sig_lote = lote.find(f"{{{NS_DS}}}Signature")
        ref = f"{{{NS_DS}}}SignedInfo/{{{NS_DS}}}Reference"
        self.assertEqual(sig_dps.find(ref).get("URI"), f"#{DPS_ID}")
        self.assertEqual(sig_lote.find(ref).get("URI"), "#Lote7")
        metodo = sig_lote.find(f".//{{{NS_DS}}}SignatureMethod").get("Algorithm")
        self.assertTrue(metodo.endswith("rsa-sha256"))

    def test_dps_ja_assinada_e_reassinada(self):
        provedor = self._provedor()
        uma_vez = provedor.assinar_dps(DPS)
        duas_vezes = etree.fromstring(provedor.assinar_dps(uma_vez))
        self.assertEqual(len(duas_vezes.findall(f"{{{NS_DS}}}Signature")), 1)

    def test_envelope(self):
        env = NotaControl.envelope("RecepcionarLoteDpsSincrono", "<a/>")
        doc = etree.fromstring(env.encode())
        op = doc.find(f".//{{{NS}}}RecepcionarLoteDpsSincrono")
        self.assertIsNotNone(op.find(f"{{{NS}}}nfseCabecMsg/{{{NS}}}cabecalho"))
        self.assertIsNotNone(op.find(f"{{{NS}}}nfseDadosMsg/a"))

    def test_recepcionar_autorizada(self):
        session = FakeSession(RESPOSTA_AUTORIZADA)
        retorno = self._provedor(session=session).recepcionar_lote_dps_sincrono([DPS], 7)

        chamada = session.chamadas[0]
        self.assertEqual(chamada["headers"]["SOAPAction"], f"{NS}/RecepcionarLoteDpsSincrono")
        self.assertIn("<LoteDps", chamada["data"])
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.protocolo, "PROT-123")
        self.assertEqual(retorno.numeros_nfse, ["1"])
        self.assertEqual(retorno.chaves_acesso, ["52087072202244507000116000000000000126090000001"])
        self.assertEqual([a.codigo for a in retorno.alertas], ["A001"])

    def test_recepcionar_autorizada_nfse_maiusculo(self):
        # o ISSNet de Goiania (homologacao, 17/11/2026) devolve <NFSe>, nao <Nfse>
        resposta = RESPOSTA_AUTORIZADA.replace("<Nfse ", "<NFSe ").replace("</Nfse>", "</NFSe>")
        retorno = self._provedor(session=FakeSession(resposta)).recepcionar_lote_dps_sincrono([DPS], 7)
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.numeros_nfse, ["1"])
        self.assertEqual(retorno.chaves_acesso, ["52087072202244507000116000000000000126090000001"])

    def test_recepcionar_rejeitada(self):
        retorno = self._provedor(session=FakeSession(RESPOSTA_REJEITADA)).recepcionar_lote_dps_sincrono([DPS], 1)
        self.assertFalse(retorno.sucesso)
        self.assertEqual([m.codigo for m in retorno.mensagens], ["E160", "E0120"])
        self.assertIn("[DPS 1/1] E0120 - Serie invalida", retorno.mensagem)
        self.assertIn("(Informe o cTribMun)", retorno.mensagem)

    def test_fault_soap(self):
        retorno = self._provedor(session=FakeSession(FAULT, 500)).consultar_dps_disponivel()
        self.assertFalse(retorno.sucesso)
        self.assertEqual(retorno.mensagens[0].mensagem, "Error")

    def test_resposta_invalida(self):
        retorno = NotaControl.analisar_resposta("X", "<html>403</html", http_status=403)
        self.assertFalse(retorno.sucesso)
        self.assertIn("HTTP 403", retorno.mensagem)

    def test_consultar_url_sem_namespace(self):
        resposta = """<ConsultarUrlNfseResposta><ListaLinks><Links>
            <IdentificacaoNfse><nDFSe>1</nDFSe></IdentificacaoNfse>
            <UrlVisualizacaoNfse>https://exemplo/1</UrlVisualizacaoNfse>
            </Links></ListaLinks></ConsultarUrlNfseResposta>"""
        retorno = self._provedor(session=FakeSession(resposta)).consultar_url_nfse(1, "1")
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.urls[0]["visualizacao"], "https://exemplo/1")

    # as respostas reais do ISSNet vem como <XResponse><XResposta>, sem <XResult>

    def test_protocolo_do_envio_sincrono_na_forma_real(self):
        corpo = (
            "<NumeroLote>7</NumeroLote><Protocolo>CBE9D634-E5E2-F111-8CA6-005056992BC4</Protocolo>"
            "<ListaNfse>" + NFSE_REAL.format(eventos="") + "</ListaNfse>"
        )
        resposta = SOAP.format(op="RecepcionarLoteDpsSincrono", resp="EnviarLoteDpsSincronoResposta", corpo=corpo)
        retorno = self._provedor(session=FakeSession(resposta)).recepcionar_lote_dps_sincrono([DPS], 7)
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.protocolo, "CBE9D634-E5E2-F111-8CA6-005056992BC4")
        self.assertEqual(retorno.numero_lote, "7")
        self.assertEqual(retorno.chaves_acesso, [CHAVE])

    def test_erro_na_forma_real_nao_e_sucesso(self):
        corpo = (
            "<ListaMensagemRetorno><MensagemRetorno><Codigo>E212</Codigo>"
            "<Mensagem>NFS-e não encontrada.</Mensagem></MensagemRetorno></ListaMensagemRetorno>"
        )
        resposta = SOAP.format(op="ConsultarNfseDps", resp="ConsultarNfseDpsResposta", corpo=corpo)
        retorno = self._provedor(session=FakeSession(resposta)).consultar_nfse_dps(1, "8")
        self.assertFalse(retorno.sucesso)
        self.assertEqual([m.codigo for m in retorno.mensagens], ["E212"])

    def test_cancelamento_recusado_nao_e_sucesso(self):
        # sem descer ate a Resposta, o EM097 era ignorado e o cancelamento dava como feito
        corpo = (
            "<ListaMensagemRetorno><MensagemRetorno><Codigo>EM097</Codigo>"
            "<Mensagem>NFS-e já está cancelada.</Mensagem></MensagemRetorno>"
            "<MensagemRetorno><Codigo /></MensagemRetorno></ListaMensagemRetorno>"
        )
        resposta = SOAP.format(op="CancelarNfse", resp="CancelarNfseResposta", corpo=corpo)
        ped = (
            f'<pedRegEvento xmlns="{NS}" versao="1.00"><infPedReg Id="PRE1"><tpAmb>2</tpAmb></infPedReg></pedRegEvento>'
        )
        retorno = self._provedor(session=FakeSession(resposta)).cancelar_nfse(ped)
        self.assertFalse(retorno.sucesso)
        self.assertEqual([m.codigo for m in retorno.mensagens], ["EM097"])

    def test_consulta_devolve_eventos_da_nota_cancelada(self):
        corpo = "<ListaNfse>" + NFSE_REAL.format(eventos=EVENTO_CANCELAMENTO) + "<Pagina>1</Pagina></ListaNfse>"
        resposta = SOAP.format(
            op="ConsultarNfseServicoPrestado", resp="ConsultarNfseServicoPrestadoResposta", corpo=corpo
        )
        session = FakeSession(resposta)
        retorno = self._provedor(session=session).consultar_nfse_servico_prestado(numero=2)
        self.assertIn("<NumeroNfse>2</NumeroNfse><Pagina>1</Pagina>", session.chamadas[0]["data"])
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.numeros_nfse, ["2"])
        self.assertEqual(len(retorno.eventos), 1)
        self.assertEqual(retorno.eventos[0]["tipo"], "e101101")
        self.assertEqual(retorno.eventos[0]["chave"], CHAVE)
        self.assertEqual(retorno.eventos[0]["motivo"], "1")

    def test_consultar_servico_prestado_por_periodo(self):
        session = FakeSession(SOAP.format(op="X", resp="XResposta", corpo=""))
        provedor = self._provedor(session=session)
        provedor.consultar_nfse_servico_prestado(emissao=("2026-11-01", "2026-11-17"))
        provedor.consultar_nfse_servico_prestado(competencia=("2026-11-01", "2026-11-17"))
        self.assertIn("<PeriodoEmissao><DataInicial>2026-11-01</DataInicial>", session.chamadas[0]["data"])
        self.assertIn("<PeriodoCompetencia>", session.chamadas[1]["data"])
        with self.assertRaises(ValueError):
            provedor.consultar_nfse_servico_prestado()

    def test_consultar_dps_disponivel_envia_pagina(self):
        corpo = (
            "<ListaDpsDisponivel><Prestador><CNPJ>02244507000116</CNPJ><IM>778151</IM></Prestador>"
            "<DpsDisponivel><NumDPS>14</NumDPS><SerieDPS>8</SerieDPS></DpsDisponivel>"
            "<DpsDisponivel><NumDPS>15</NumDPS><SerieDPS>8</SerieDPS></DpsDisponivel>"
            "<Pagina>1</Pagina></ListaDpsDisponivel>"
        )
        session = FakeSession(
            SOAP.format(op="ConsultarDpsDisponivel", resp="ConsultarDpsDisponivelResposta", corpo=corpo)
        )
        retorno = self._provedor(session=session).consultar_dps_disponivel()
        # sem a Pagina o webservice responde E160
        self.assertIn("<Pagina>1</Pagina></ConsultarDpsDisponivelEnvio>", session.chamadas[0]["data"])
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.dps_disponiveis, [("14", "8"), ("15", "8")])

    def test_consultar_lote_dps_situacao(self):
        corpo = "<Situacao>4</Situacao><ListaNfse>" + NFSE_REAL.format(eventos="") + "</ListaNfse>"
        session = FakeSession(SOAP.format(op="ConsultarLoteDps", resp="ConsultarLoteDpsResposta", corpo=corpo))
        retorno = self._provedor(session=session).consultar_lote_dps("CBE9D634-E5E2-F111-8CA6-005056992BC4")
        self.assertIn("<Protocolo>CBE9D634-E5E2-F111-8CA6-005056992BC4</Protocolo>", session.chamadas[0]["data"])
        self.assertEqual(retorno.situacao, "4")
        self.assertEqual(retorno.numeros_nfse, ["2"])

    def test_consultar_faixa_e_dados_cadastrais(self):
        session = FakeSession(SOAP.format(op="X", resp="XResposta", corpo=""))
        provedor = self._provedor(session=session)
        provedor.consultar_nfse_faixa(1, 5)
        provedor.consultar_dados_cadastrais()
        self.assertIn(
            "<NumeroNfseInicial>1</NumeroNfseInicial><NumeroNfseFinal>5</NumeroNfseFinal>", session.chamadas[0]["data"]
        )
        self.assertIn("ConsultarDadosCadastraisEnvio", session.chamadas[1]["data"])

    def test_validar_xml(self):
        corpo = (
            "<ListaMensagemRetorno><MensagemRetorno><Codigo>S000</Codigo>"
            "<Mensagem>XML válido. Validação realizada com sucesso.</Mensagem></MensagemRetorno></ListaMensagemRetorno>"
        )
        resposta = SOAP.format(op="ValidarXml", resp="ValidarXmlResposta", corpo=corpo)
        self.assertTrue(self._provedor(session=FakeSession(resposta)).validar_xml("<GerarNfseEnvio/>").sucesso)
        corpo = (
            "<ListaMensagemRetorno><MensagemRetorno><Codigo>E160</Codigo>"
            "<Mensagem>Arquivo em desacordo</Mensagem></MensagemRetorno></ListaMensagemRetorno>"
        )
        resposta = SOAP.format(op="ValidarXml", resp="ValidarXmlResposta", corpo=corpo)
        self.assertFalse(self._provedor(session=FakeSession(resposta)).validar_xml("<GerarNfseEnvio/>").sucesso)

    def test_numero_serie(self):
        self.assertEqual(dps_numero_serie(DPS), ("1", "1"))
