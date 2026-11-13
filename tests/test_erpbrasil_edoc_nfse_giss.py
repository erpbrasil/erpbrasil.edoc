# Copyright (C) 2026  KMEE
import base64
import datetime
import hashlib
import re
from html import escape
from types import SimpleNamespace
from unittest import TestCase

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree

from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.edoc.provedores.giss import (
    LOTE_PROCESSADO,
    NS_CABECALHO,
    NS_DS,
    NS_GISS,
    NS_SERVICO,
    NS_TIPOS,
    Giss,
)

NS_ENVIO = NS_GISS.format("enviar-lote-rps-envio")
CNPJ = "02244507000116"
IM = "217351"


def rps(numero):
    return (
        f'<t:Rps><t:InfDeclaracaoPrestacaoServico Id="rps{numero}">'
        f'<t:Rps Id="r{numero}"><t:IdentificacaoRps><t:Numero>{numero}</t:Numero>'
        "<t:Serie>1</t:Serie><t:Tipo>1</t:Tipo></t:IdentificacaoRps>"
        "<t:DataEmissao>2026-11-10</t:DataEmissao><t:Status>1</t:Status></t:Rps>"
        "<t:Competencia>2026-11-10</t:Competencia>"
        "</t:InfDeclaracaoPrestacaoServico></t:Rps>"
    )


def lote(numeros=(1,)):
    """Como o XmlSerializer do xsdata grava: o namespace dos tipos declarado
    de novo em cada filho do LoteRps."""
    t = f'xmlns:t="{NS_TIPOS}"'
    return (
        f'<e:EnviarLoteRpsEnvio xmlns:e="{NS_ENVIO}">'
        f'<e:LoteRps Id="lote7" versao="2.04"><t:NumeroLote {t}>7</t:NumeroLote>'
        f"<t:Prestador {t}><t:CpfCnpj><t:Cnpj>{CNPJ}</t:Cnpj></t:CpfCnpj>"
        f"<t:InscricaoMunicipal>{IM}</t:InscricaoMunicipal></t:Prestador>"
        f"<t:QuantidadeRps {t}>{len(numeros)}</t:QuantidadeRps>"
        f"<t:ListaRps {t}>{''.join(rps(n) for n in numeros)}</t:ListaRps>"
        "</e:LoteRps></e:EnviarLoteRpsEnvio>"
    )


def soap(operacao, corpo):
    return (
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        f'<soap:Body><ns2:{operacao}Response xmlns:ns2="{NS_SERVICO}">'
        f"<outputXML>{escape(corpo)}</outputXML>"
        f"</ns2:{operacao}Response></soap:Body></soap:Envelope>"
    )


RESPOSTA_PROTOCOLO = soap(
    "RecepcionarLoteRps",
    f'<?xml version="1.0" encoding="UTF-8"?>'
    f'<EnviarLoteRpsResposta xmlns="{NS_GISS.format("enviar-lote-rps-resposta")}">'
    "<NumeroLote>7</NumeroLote><DataRecebimento>2026-11-10T10:00:00</DataRecebimento>"
    "<Protocolo>PROT-123</Protocolo></EnviarLoteRpsResposta>",
)

RESPOSTA_LOTE_PROCESSADO = soap(
    "ConsultarLoteRps",
    f'<ConsultarLoteRpsResposta xmlns="{NS_GISS.format("consultar-lote-rps-resposta")}"'
    f' xmlns:t="{NS_TIPOS}"><Situacao>4</Situacao><ListaNfse><t:CompNfse>'
    '<t:Nfse versao="2.04"><t:InfNfse Id="nfse55"><t:Numero>55</t:Numero>'
    "<t:CodigoVerificacao>ABC123XYZ</t:CodigoVerificacao>"
    "<t:DataEmissao>2026-11-10T10:00:05</t:DataEmissao>"
    "<t:DeclaracaoPrestacaoServico><t:InfDeclaracaoPrestacaoServico>"
    "<t:Rps><t:IdentificacaoRps><t:Numero>1</t:Numero><t:Serie>1</t:Serie>"
    "<t:Tipo>1</t:Tipo></t:IdentificacaoRps></t:Rps>"
    "</t:InfDeclaracaoPrestacaoServico></t:DeclaracaoPrestacaoServico>"
    "</t:InfNfse></t:Nfse>"
    f"<t:ChaveNotaNacional>{'3' * 50}</t:ChaveNotaNacional>"
    "</t:CompNfse><t:ListaMensagemAlertaRetorno><t:MensagemRetorno>"
    "<t:Codigo>A14</t:Codigo><t:Mensagem>ISS calculado pela prefeitura</t:Mensagem>"
    "</t:MensagemRetorno></t:ListaMensagemAlertaRetorno></ListaNfse>"
    "</ConsultarLoteRpsResposta>",
)

NS_RESPOSTA_LOTE = NS_GISS.format("consultar-lote-rps-resposta")
RESPOSTA_LOTE_EM_FILA = soap(
    "ConsultarLoteRps",
    f'<ConsultarLoteRpsResposta xmlns="{NS_RESPOSTA_LOTE}"><Situacao>2</Situacao></ConsultarLoteRpsResposta>',
)

RESPOSTA_LOTE_COM_ERRO = soap(
    "ConsultarLoteRps",
    f'<ConsultarLoteRpsResposta xmlns="{NS_GISS.format("consultar-lote-rps-resposta")}"'
    f' xmlns:t="{NS_TIPOS}"><Situacao>3</Situacao>'
    "<t:ListaMensagemRetorno><t:MensagemRetorno><t:Codigo>E160</t:Codigo>"
    "<t:Mensagem>Arquivo em desacordo com o XML Schema</t:Mensagem>"
    "<t:Correcao>Confira o schema</t:Correcao></t:MensagemRetorno>"
    "</t:ListaMensagemRetorno><t:ListaMensagemRetornoLote><t:MensagemRetorno>"
    "<t:IdentificacaoRps><t:Numero>1</t:Numero><t:Serie>1</t:Serie>"
    "<t:Tipo>1</t:Tipo></t:IdentificacaoRps><t:Codigo>E174</t:Codigo>"
    "<t:Mensagem>RPS nao assinado</t:Mensagem></t:MensagemRetorno>"
    "</t:ListaMensagemRetornoLote></ConsultarLoteRpsResposta>",
)

RESPOSTA_CANCELADA = soap(
    "CancelarNfse",
    f'<CancelarNfseResposta xmlns="{NS_GISS.format("cancelar-nfse-resposta")}"'
    f' xmlns:t="{NS_TIPOS}"><RetCancelamento><t:NfseCancelamento versao="2.04">'
    "<t:Confirmacao><t:DataHora>2026-11-10T11:00:00</t:DataHora></t:Confirmacao>"
    "</t:NfseCancelamento></RetCancelamento></CancelarNfseResposta>",
)

FAULT = (
    '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
    "<soap:Body><soap:Fault><faultcode>soap:Client</faultcode>"
    "<faultstring>Error</faultstring></soap:Fault></soap:Body></soap:Envelope>"
)


def certificado_temporario():
    """Certificado autoassinado valido hoje."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"TESTE:{CNPJ}")])
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
    return Certificado(base64.b64encode(pfx), "teste")


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content.encode("utf-8")
        self.status_code = status_code


class FakeSession:
    def __init__(self, *respostas, status_code=200):
        self.respostas = list(respostas)
        self.status_code = status_code
        self.chamadas = []

    def post(self, url, data, headers, timeout):
        self.chamadas.append({"url": url, "data": data.decode(), "headers": headers})
        resposta = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        return FakeResponse(resposta, self.status_code)


def dados_da_chamada(chamada):
    """XML que foi dentro de nfseDadosMsg, ja sem o escape do envelope."""
    envelope = etree.fromstring(chamada["data"].encode())
    return etree.fromstring(envelope.find(".//nfseDadosMsg").text.encode())


def referencias(xml):
    return [ref.get("URI") for ref in xml.iter(f"{{{NS_DS}}}Reference")]


def declaracoes(xml):
    """Namespaces declarados no texto, um item por declaração."""
    return sorted(re.findall(r'xmlns(?::[\w.-]+)?="([^"]*)"', xml))


class TestGiss(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.transmissao = SimpleNamespace(certificado=certificado_temporario())

    def giss(self, *respostas, ambiente="1", cidade=3518800, **kwargs):
        self.session = FakeSession(*respostas, **kwargs)
        return Giss(self.transmissao, ambiente, cidade, CNPJ, IM, session=self.session)

    def test_url_por_municipio_e_homologacao_unica(self):
        self.assertEqual(
            self.giss("").url,
            "https://ws-guarulhos.giss.com.br/service-ws/nf/nfse-ws",
        )
        self.assertEqual(
            self.giss("", cidade=3549805).url,
            "https://ws-sjrp.giss.com.br/service-ws/nf/nfse-ws",
        )
        self.assertEqual(
            self.giss("", ambiente="2", cidade=1).url,
            "https://v2-ws-homologacao.giss.com.br/service-ws/nf/nfse-ws",
        )
        with self.assertRaises(ValueError):
            self.giss("", cidade=1).url  # noqa: B018
        fora = Giss(self.transmissao, "1", 1, CNPJ, IM, host="suzano")
        self.assertEqual(fora.url, "https://ws-suzano.giss.com.br/service-ws/nf/nfse-ws")

    def test_assina_cada_rps_e_depois_o_lote(self):
        assinado = etree.fromstring(self.giss("").assinar_lote(lote((1, 2))).encode())
        # uma assinatura por RPS, irma da InfDeclaracaoPrestacaoServico, e a
        # do lote por ultimo, irma do LoteRps e referenciando o Id dele
        self.assertEqual(referencias(assinado), ["#rps1", "#rps2", "#lote7"])
        for declaracao in assinado.iter(f"{{{NS_TIPOS}}}InfDeclaracaoPrestacaoServico"):
            self.assertEqual(declaracao.getnext().tag, f"{{{NS_DS}}}Signature")
        self.assertEqual(assinado[-1].tag, f"{{{NS_DS}}}Signature")
        metodo = assinado[-1].find(f".//{{{NS_DS}}}SignatureMethod").get("Algorithm")
        self.assertTrue(metodo.endswith("rsa-sha1"))
        # so o X509Certificate vai no KeyInfo
        for key_info in assinado.iter(f"{{{NS_DS}}}KeyInfo"):
            self.assertEqual(
                [etree.QName(e).localname for e in key_info.iter()][1:],
                ["X509Data", "X509Certificate"],
            )

    def test_assinaturas_validas_no_contexto_do_documento(self):
        """Resumo e assinatura RSA de cada assinatura, como o servidor confere.

        Um verificador rigoroso canonicaliza o ``SignedInfo`` no contexto do
        documento, com os prefixos de namespace herdados da raiz. As
        assinaturas dos RPS mudam de lugar depois de criadas: continuam
        validas porque os prefixos sao declarados na raiz e porque cada uma
        volta para junto do RPS antes de o lote ser assinado.
        """
        assinado = etree.fromstring(self.giss("").assinar_lote(lote((1, 2, 3))).encode())
        ds = f"{{{NS_DS}}}"
        assinaturas = list(assinado.iter(f"{ds}Signature"))
        self.assertEqual(len(assinaturas), 4)
        for assinatura in assinaturas:
            referencia = assinatura.find(f"{ds}SignedInfo/{ds}Reference")
            alvo = assinado.xpath("//*[@Id=$i]", i=referencia.get("URI")[1:])[0]
            resumo = base64.b64encode(
                hashlib.sha1(etree.tostring(alvo, method="c14n")).digest()  # noqa: S324
            ).decode()
            self.assertEqual(resumo, referencia.findtext(f"{ds}DigestValue"))
            # c14n inclusivo do SignedInfo em contexto: o lxml nao o faz certo
            # para um subelemento, entao os namespaces em escopo entram a mao
            signed_info = etree.tostring(assinatura.find(f"{ds}SignedInfo"), method="c14n", exclusive=True)
            em_escopo = "".join(
                f' xmlns:{prefixo}="{uri}"'
                for prefixo, uri in sorted((p, u) for p, u in assinatura.nsmap.items() if p is not None)
            )
            abertura = f'<SignedInfo xmlns="{NS_DS}"'.encode()
            signed_info = signed_info.replace(abertura, abertura + em_escopo.encode(), 1)
            certificado = x509.load_der_x509_certificate(
                base64.b64decode(assinatura.findtext(f".//{ds}X509Certificate"))
            )
            certificado.public_key().verify(
                base64.b64decode(assinatura.findtext(f"{ds}SignatureValue")),
                signed_info,
                padding.PKCS1v15(),
                hashes.SHA1(),  # noqa: S303
            )

    def test_namespaces_declarados_uma_vez_na_raiz(self):
        """Com o namespace dos tipos redeclarado nos filhos, o GissOnline
        recusa as assinaturas (E172)."""
        assinado = self.giss("").assinar_lote(lote((1, 2)))
        raiz = etree.fromstring(assinado.encode())
        self.assertEqual(raiz.nsmap, {None: NS_ENVIO, "tipos": NS_TIPOS})
        # fora da raiz, só cada Signature declara o namespace dela
        self.assertEqual(declaracoes(assinado), sorted([NS_ENVIO, NS_TIPOS] + [NS_DS] * 3))

    def test_lote_ja_assinado_e_reassinado_sem_duplicar(self):
        giss = self.giss("")
        duas_vezes = etree.fromstring(giss.assinar_lote(giss.assinar_lote(lote())).encode())
        self.assertEqual(referencias(duas_vezes), ["#rps1", "#lote7"])

    def test_lote_sem_id_nao_e_assinado(self):
        with self.assertRaises(ValueError):
            self.giss("").assinar_lote(lote().replace(' Id="lote7"', ""))
        with self.assertRaises(ValueError):
            self.giss("").assinar_lote(lote().replace(' Id="rps1"', ""))

    def test_envelope(self):
        giss = self.giss(RESPOSTA_PROTOCOLO)
        retorno = giss.recepcionar_lote_rps(lote())
        chamada = self.session.chamadas[0]
        self.assertEqual(chamada["headers"]["SOAPAction"], f"{NS_SERVICO}/RecepcionarLoteRps")
        envelope = etree.fromstring(chamada["data"].encode())
        pedido = envelope.find(f".//{{{NS_SERVICO}}}RecepcionarLoteRpsRequest")
        self.assertIsNotNone(pedido)
        cabecalho = etree.fromstring(pedido.find("nfseCabecMsg").text.encode())
        self.assertEqual(cabecalho.tag, f"{{{NS_CABECALHO}}}cabecalho")
        self.assertEqual(cabecalho.get("versao"), "2.04")
        self.assertEqual(cabecalho[0].text, "2.04")
        outra = Giss(self.transmissao, "1", 3518800, CNPJ, IM, versao_cabecalho="2.00")
        envelope = etree.fromstring(outra.envelope("RecepcionarLoteRps", lote()).encode())
        self.assertIn('versao="2.00"', envelope.find(".//nfseCabecMsg").text)
        self.assertEqual(dados_da_chamada(chamada).tag, f"{{{NS_ENVIO}}}EnviarLoteRpsEnvio")
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.protocolo, "PROT-123")
        self.assertEqual(retorno.numero_lote, "7")

    def test_consulta_do_lote_processado(self):
        retorno = self.giss(RESPOSTA_LOTE_PROCESSADO).consultar_lote_rps("PROT-123")
        dados = dados_da_chamada(self.session.chamadas[0])
        ns = NS_GISS.format("consultar-lote-rps-envio")
        self.assertEqual(dados.tag, f"{{{ns}}}ConsultarLoteRpsEnvio")
        self.assertEqual(dados.findtext(f"{{{ns}}}Protocolo"), "PROT-123")
        self.assertEqual(
            dados.findtext(f"{{{ns}}}Prestador/{{{NS_TIPOS}}}CpfCnpj/{{{NS_TIPOS}}}Cnpj"),
            CNPJ,
        )
        # a consulta leva uma assinatura na raiz, sobre o documento todo
        self.assertEqual(referencias(dados), [""])
        self.assertEqual(declaracoes(etree.tostring(dados, encoding=str)), sorted([ns, NS_TIPOS, NS_DS]))
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.situacao, LOTE_PROCESSADO)
        self.assertFalse(retorno.em_processamento)
        nfse = retorno.nfses[0]
        self.assertEqual(
            (nfse.numero, nfse.codigo_verificacao, nfse.numero_rps, nfse.serie_rps),
            ("55", "ABC123XYZ", "1", "1"),
        )
        self.assertEqual(nfse.chave_nacional, "3" * 50)
        self.assertFalse(nfse.cancelada)
        self.assertIn("InfNfse", nfse.xml)
        self.assertEqual([a.codigo for a in retorno.alertas], ["A14"])

    def test_lote_com_erro(self):
        retorno = self.giss(RESPOSTA_LOTE_COM_ERRO).consultar_lote_rps("PROT-123")
        self.assertFalse(retorno.sucesso)
        self.assertEqual([m.codigo for m in retorno.mensagens], ["E160", "E174"])
        self.assertEqual(retorno.mensagens[1].identificacao_rps, "1/1")
        self.assertIn("Confira o schema", retorno.mensagem)
        self.assertIn("[RPS 1/1] E174", retorno.mensagem)

    def test_aguarda_o_lote_sair_da_fila(self):
        giss = self.giss(RESPOSTA_LOTE_EM_FILA, RESPOSTA_LOTE_PROCESSADO)
        retorno = giss.aguardar_lote("PROT-123", espera=0)
        self.assertEqual(len(self.session.chamadas), 2)
        self.assertEqual(retorno.situacao, LOTE_PROCESSADO)
        ainda = self.giss(RESPOSTA_LOTE_EM_FILA).aguardar_lote("PROT-123", tentativas=2, espera=0)
        self.assertTrue(ainda.em_processamento)
        self.assertEqual(len(self.session.chamadas), 2)

    def test_consulta_por_rps(self):
        self.giss(RESPOSTA_LOTE_EM_FILA).consultar_nfse_rps(12, "A1")
        chamada = self.session.chamadas[0]
        self.assertEqual(chamada["headers"]["SOAPAction"], f"{NS_SERVICO}/ConsultarNfsePorRps")
        dados = dados_da_chamada(chamada)
        ns = NS_GISS.format("consultar-nfse-rps-envio")
        rps_id = dados.find(f"{{{ns}}}IdentificacaoRps")
        self.assertEqual([e.text for e in rps_id], ["12", "A1", "1"])

    def test_cancelamento(self):
        retorno = self.giss(RESPOSTA_CANCELADA).cancelar_nfse(55, "2")
        dados = dados_da_chamada(self.session.chamadas[0])
        ns = NS_GISS.format("cancelar-nfse-envio")
        pedido = dados.find(f"{{{ns}}}Pedido")
        inf = pedido.find(f"{{{NS_TIPOS}}}InfPedidoCancelamento")
        self.assertEqual(inf.get("Id"), "cancelamento55")
        self.assertEqual(inf.findtext(f"{{{NS_TIPOS}}}CodigoCancelamento"), "2")
        identificacao = inf.find(f"{{{NS_TIPOS}}}IdentificacaoNfse")
        self.assertEqual(identificacao.findtext(f"{{{NS_TIPOS}}}CodigoMunicipio"), "3518800")
        # a assinatura fica dentro do Pedido e referencia o InfPedidoCancelamento
        self.assertEqual(pedido[-1].tag, f"{{{NS_DS}}}Signature")
        self.assertEqual(referencias(dados), ["#cancelamento55"])
        self.assertEqual(declaracoes(etree.tostring(dados, encoding=str)), sorted([ns, NS_TIPOS, NS_DS]))
        self.assertTrue(retorno.sucesso)
        self.assertEqual(retorno.data_cancelamento, "2026-11-10T11:00:00")

    def test_cancelamento_so_com_os_codigos_do_contribuinte(self):
        for codigo in ("3", "5"):
            with self.assertRaises(ValueError):
                self.giss("").cancelar_nfse(55, codigo)

    def test_fault_resposta_invalida_e_erro_de_transporte(self):
        retorno = self.giss(FAULT).consultar_lote_rps("PROT-123")
        self.assertFalse(retorno.sucesso)
        self.assertEqual(retorno.mensagens[0].codigo, "soap:Client")
        retorno = self.giss("400 No required SSL certificate was sent", status_code=400)
        retorno = retorno.consultar_lote_rps("PROT-123")
        self.assertFalse(retorno.sucesso)
        self.assertEqual(retorno.mensagens[0].codigo, "HTTP")
        retorno = self.giss("<html/>", status_code=502).consultar_lote_rps("PROT-123")
        self.assertFalse(retorno.sucesso)
