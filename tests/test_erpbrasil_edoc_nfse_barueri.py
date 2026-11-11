from contextlib import contextmanager
from types import SimpleNamespace
from unittest import TestCase, skipUnless

from erpbrasil.edoc.provedores import barueri as provedor_barueri
from erpbrasil.edoc.provedores.barueri import Barueri
from erpbrasil.edoc.provedores.cidades import NFSeFactory

CNPJ = "12345678000195"
IM = "123456"


def _processo(resposta, webservice="NFeLoteStatusArquivo"):
    return SimpleNamespace(webservice=webservice, resposta=resposta)


class _Transmissao:
    """Registra as chamadas ao webservice em vez de transmitir."""

    def __init__(self):
        self.chamadas = []

    @contextmanager
    def cliente(self, url):
        transmissao = self

        class _Servico:
            def __getitem__(self, operacao):
                def chamar(*args):
                    transmissao.chamadas.append((url, operacao, args))
                    return "<retorno/>"

                return chamar

        yield SimpleNamespace(service=_Servico())


class TestBarueriRetornoConsulta(TestCase):
    """analisa_retorno_consulta só interpreta a resposta: não precisa de bindings
    nem de transmissão, por isso o provedor é criado sem o __init__."""

    def setUp(self):
        self.barueri = Barueri.__new__(Barueri)

    def test_retorno_com_erro_devolve_a_mensagem(self):
        resposta = SimpleNamespace(
            ListaMensagemRetorno=SimpleNamespace(Codigo="E001", Mensagem="Arquivo inválido", Correcao="Reenvie")
        )
        status, mensagem = self.barueri.analisa_retorno_consulta(_processo(resposta))
        self.assertIsNone(status)
        self.assertEqual(mensagem, "E001 - Arquivo inválido - Correção: Reenvie\n")

    def test_retorno_ok_devolve_a_situacao_do_arquivo(self):
        esperado = {
            "0": "Validated",
            "1": "Successfully Processed",
            "2": "Processed with Error",
            "-1": "Batch not yet processed",
        }
        for situacao, mensagem_esperada in esperado.items():
            with self.subTest(situacao=situacao):
                resposta = SimpleNamespace(
                    ListaMensagemRetorno=SimpleNamespace(Codigo="OK200"),
                    ListaNfeArquivosRPS=SimpleNamespace(SituacaoArq=situacao),
                )
                status, mensagem = self.barueri.analisa_retorno_consulta(_processo(resposta))
                self.assertEqual(status, int(situacao))
                self.assertEqual(mensagem, mensagem_esperada)

    def test_outro_servico_nao_e_interpretado(self):
        status, mensagem = self.barueri.analisa_retorno_consulta(
            _processo(SimpleNamespace(), webservice="NFeLoteEnviarArquivo")
        )
        self.assertIsNone(status)
        self.assertEqual(mensagem, "")


@skipUnless(provedor_barueri.barueri, "nfselib.barueri não instalada")
class TestBarueriServicos(TestCase):
    """Monta as mensagens e chama os serviços com uma transmissão falsa."""

    def setUp(self):
        self.transmissao = _Transmissao()
        self.nfse = NFSeFactory(
            transmissao=self.transmissao,
            ambiente="2",
            cidade_ibge=3505708,  # Barueri - SP
            cnpj_prestador=CNPJ,
            im_prestador=IM,
        )

    def test_ambiente_define_o_servidor(self):
        self.assertEqual(self.nfse._url, "https://testeeiss.barueri.sp.gov.br/")
        producao = NFSeFactory(
            transmissao=self.transmissao,
            ambiente="1",
            cidade_ibge=3505708,
            cnpj_prestador=CNPJ,
            im_prestador=IM,
        )
        self.assertEqual(producao._url, "https://www.barueri.sp.gov.br/")

    def test_consultas_levam_prestador_e_protocolo(self):
        proc_envio = SimpleNamespace(resposta=SimpleNamespace(ProtocoloRemessa="P1"))
        consultas = (
            (self.nfse._prepara_consulta_recibo(proc_envio), "P1"),
            (self.nfse._prepara_consultar_lote_rps("P2"), "P2"),
            (self.nfse._prepara_consultar_nfse_rps(lot_receipt_number="P3"), "P3"),
        )
        for raiz, protocolo in consultas:
            with self.subTest(protocolo=protocolo):
                self.assertEqual(raiz.CPFCNPJContrib, CNPJ)
                self.assertEqual(raiz.InscricaoMunicipal, IM)
                self.assertEqual(raiz.ProtocoloRemessa, protocolo)

    def test_baixar_lote_rps_envia_cabecalho_e_arquivo(self):
        processo = self.nfse.baixar_lote_rps("RETORNO.TXT")
        self.assertEqual(processo.webservice, "NFeLoteBaixarArquivo")
        self.assertEqual(processo.envio_raiz.NomeArqRetorno, "RETORNO.TXT")
        self.assertEqual(processo.resposta, "<retorno/>")
        url, operacao, args = self.transmissao.chamadas[0]
        self.assertEqual(url, "https://testeeiss.barueri.sp.gov.br/nfeservice/wsrps.asmx?WSDL")
        self.assertEqual(operacao, "NFeLoteBaixarArquivo")
        self.assertEqual(args[0], "1")
        self.assertIn("RETORNO.TXT", args[1])

    def test_consulta_nfse_rps_consulta_o_protocolo(self):
        processo = self.nfse.consulta_nfse_rps(lot_receipt_number="P9")
        self.assertEqual(processo.webservice, "NFeLoteStatusArquivo")
        self.assertIn("P9", self.transmissao.chamadas[0][2][1])

    def test_resposta_do_envio_e_situacao(self):
        self.assertTrue(
            self.nfse._verifica_resposta_envio_sucesso(SimpleNamespace(retorno=SimpleNamespace(ProtocoloRemessa="P1")))
        )
        self.assertFalse(
            self.nfse._verifica_resposta_envio_sucesso(SimpleNamespace(retorno=SimpleNamespace(ProtocoloRemessa="")))
        )
        recibo = SimpleNamespace(retorno=SimpleNamespace(ListaNfeArquivosRPS=SimpleNamespace(SituacaoArq=2)))
        self.assertTrue(self.nfse._edoc_situacao_em_processamento(recibo))
