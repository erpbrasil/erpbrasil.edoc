from types import SimpleNamespace
from unittest import TestCase

from erpbrasil.base import misc
from erpbrasil.edoc.provedores.cidades import NFSeFactory
from erpbrasil.edoc.provedores.paulistana import Paulistana
from erpbrasil.transmissao import TransmissaoSOAP
from nfselib.paulistana.v02.PedidoEnvioLoteRPS import (
    CabecalhoType,
    PedidoEnvioLoteRPS,
    tpChaveRPS,
    tpCPFCNPJ,
    tpEndereco,
    tpRPS,
)
from requests import Session

from .test_certificate_mixin import TestCertificateMixin


class AnalisaRetornoConsultaTests(TestCase):
    """`analisa_retorno_consulta` so depende do processo/XML, sem rede."""

    def setUp(self):
        self.nfse = Paulistana.__new__(Paulistana)

    def test_consulta_com_sucesso(self):
        xml = """<root>
  <CodigoVerificacao>ABC123</CodigoVerificacao>
  <NumeroNFe>001</NumeroNFe>
  <DataEmissaoNFe>2020-10-29</DataEmissaoNFe>
</root>"""
        processo = SimpleNamespace(
            resposta=SimpleNamespace(Cabecalho=SimpleNamespace(Sucesso=True)),
            retorno=xml,
        )
        resultado = self.nfse.analisa_retorno_consulta(processo)
        self.assertEqual(
            resultado,
            {
                "codigo_verificacao": "ABC123",
                "numero": "001",
                "data_emissao": "2020-10-29",
            },
        )

    def test_consulta_sem_sucesso(self):
        processo = SimpleNamespace(
            resposta=SimpleNamespace(Cabecalho=SimpleNamespace(Sucesso=False)),
            retorno="<root/>",
        )
        resultado = self.nfse.analisa_retorno_consulta(processo)
        self.assertEqual(resultado, "Error communicating with the webservice")


class AnalisaRetornoCancelamentoTests(TestCase):
    def setUp(self):
        self.nfse = Paulistana.__new__(Paulistana)

    def test_cancelamento_com_sucesso(self):
        processo = SimpleNamespace(
            resposta=SimpleNamespace(Cabecalho=SimpleNamespace(Sucesso=True), Erro=[])
        )
        status, mensagem = self.nfse.analisa_retorno_cancelamento_paulistana(processo)
        self.assertTrue(status)
        self.assertEqual(mensagem, "")

    def test_cancelamento_com_erro(self):
        erro = SimpleNamespace(
            Codigo=1306,
            Descricao=(
                "A NFS-e que se deseja cancelar não foi gerada via Web Service."
            ),
        )
        processo = SimpleNamespace(
            resposta=SimpleNamespace(
                Cabecalho=SimpleNamespace(Sucesso=False), Erro=[erro]
            )
        )
        status, mensagem = self.nfse.analisa_retorno_cancelamento_paulistana(processo)
        self.assertFalse(status)
        self.assertEqual(
            mensagem,
            "1306 - A NFS-e que se deseja cancelar não foi gerada via Web Service.\n",
        )


class PreparaDocumentosTests(TestCertificateMixin, TestCase):
    """Testa a montagem/assinatura do XML sem realizar nenhuma chamada de rede."""

    def setUp(self):
        super().setUp()
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(self.certificate, session)
        self.nfse = NFSeFactory(
            transmissao=transmissao,
            ambiente="2",
            cidade_ibge=3550308,  # Sao Paulo - SP
            cnpj_prestador=misc.punctuation_rm("07.865.699/0001-00"),
            im_prestador=misc.punctuation_rm("3.570.741-0"),
        )

    def test_prepara_envia_documento_assina_rps_e_xml(self):
        edoc = create_nfse_object()
        assinatura_original = edoc.RPS[0].Assinatura

        xml_assinado = self.nfse._prepara_envia_documento(edoc)

        # a assinatura do RPS foi trocada pelo resultado (base64) da assinatura
        self.assertNotEqual(edoc.RPS[0].Assinatura, assinatura_original)
        self.assertIn("07865699000100", xml_assinado)

    def test_prepara_consulta_recibo_le_numero_lote_e_cnpj_do_retorno(self):
        proc_envio = SimpleNamespace(
            retorno="<root><NumeroLote>123</NumeroLote>"
            "<CNPJ>07865699000100</CNPJ></root>"
        )
        xml = self.nfse._prepara_consulta_recibo(proc_envio)
        self.assertIn("123", xml)
        self.assertIn("07865699000100", xml)

    def test_prepara_consultar_nfse_rps(self):
        xml = self.nfse._prepara_consultar_nfse_rps(
            cnpj_prest="07865699000100",
            insc_prest="35707410",
            serie_rps="111",
            numero_rps="294",
        )
        self.assertIn("07865699000100", xml)
        self.assertIn("294", xml)

    def test_prepara_cancelar_nfse_envio_com_codigo_verificacao(self):
        xml = self.nfse._prepara_cancelar_nfse_envio(
            {"numero_nfse": "001", "codigo_verificacao": "0000"}
        )
        self.assertIn("07865699000100", xml)

    def test_prepara_cancelar_nfse_envio_sem_codigo_verificacao(self):
        # codigo_verificacao e opcional (usa "" como padrao)
        xml = self.nfse._prepara_cancelar_nfse_envio({"numero_nfse": "001"})
        self.assertIn("07865699000100", xml)

    def test_edoc_situacao_em_processamento_nao_implementado(self):
        # metodo comentado no codigo-fonte: nao retorna nada (None)
        self.assertIsNone(self.nfse._edoc_situacao_em_processamento(None))

    def test_ambiente_producao_usa_servicos_de_producao(self):
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(self.certificate, session)
        nfse_producao = NFSeFactory(
            transmissao=transmissao,
            ambiente="1",
            cidade_ibge=3550308,
            cnpj_prestador=misc.punctuation_rm("07.865.699/0001-00"),
            im_prestador=misc.punctuation_rm("3.570.741-0"),
        )
        self.assertIn("envia_documento", nfse_producao._servicos)


def create_nfse_object():
    return PedidoEnvioLoteRPS(
        Cabecalho=CabecalhoType(
            Versao=1,
            CPFCNPJRemetente=tpCPFCNPJ(CNPJ="07865699000100"),
            transacao=False,
            dtInicio="2020-10-29",
            dtFim="2020-10-29",
            QtdRPS=1,
            ValorTotalServicos=100.0,
            ValorTotalDeducoes=0.0,
        ),
        RPS=[
            tpRPS(
                Assinatura=(
                    "35707410111  0000000002942020102"
                    "9TNN00000000001000000000000000000002692262228384000151"
                ),
                ChaveRPS=tpChaveRPS(
                    InscricaoPrestador=35707410,
                    SerieRPS="111",
                    NumeroRPS=294,
                ),
                TipoRPS="RPS",
                DataEmissao="2020-10-29",
                StatusRPS="N",
                TributacaoRPS="T",
                ValorServicos=100.0,
                ValorDeducoes=0.0,
                ValorPIS=0.0,
                ValorCOFINS=0.0,
                ValorINSS=0.0,
                ValorIR=0.0,
                ValorCSLL=0.0,
                CodigoServico=2692,
                AliquotaServicos=0.0,
                ISSRetido=False,
                CPFCNPJTomador=tpCPFCNPJ(CNPJ="62228384000151"),
                InscricaoEstadualTomador=621240850633,
                RazaoSocialTomador="AMD South America Ltda",
                EnderecoTomador=tpEndereco(
                    Logradouro="Rua Samuel Morse",
                    NumeroEndereco="134",
                    Bairro="Brooklin",
                    Cidade=3550308,
                    UF="SP",
                    CEP=4576060,
                ),
                EmailTomador="teste@teste.com.br",
                Discriminacao="[ODOO_DEV] Customized Odoo Development",
                ValorCargaTributaria=0.0,
                FonteCargaTributaria="100.0",
            )
        ],
    )
