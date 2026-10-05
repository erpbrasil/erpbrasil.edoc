from types import SimpleNamespace
from unittest import TestCase

from erpbrasil.edoc.provedores.barueri import Barueri


def _processo(resposta, webservice="NFeLoteStatusArquivo"):
    return SimpleNamespace(webservice=webservice, resposta=resposta)


class TestBarueriRetornoConsulta(TestCase):
    """analisa_retorno_consulta só interpreta a resposta: não precisa de bindings
    nem de transmissão, por isso o provedor é criado sem o __init__."""

    def setUp(self):
        self.barueri = Barueri.__new__(Barueri)

    def test_retorno_com_erro_devolve_a_mensagem(self):
        resposta = SimpleNamespace(
            ListaMensagemRetorno=SimpleNamespace(
                Codigo="E001", Mensagem="Arquivo inválido", Correcao="Reenvie"
            )
        )
        status, mensagem = self.barueri.analisa_retorno_consulta(_processo(resposta))
        self.assertIsNone(status)
        self.assertEqual(mensagem, "E001 - Arquivo inválido - Correção: Reenvie\n")

    def test_retorno_ok_devolve_a_situacao_do_arquivo(self):
        resposta = SimpleNamespace(
            ListaMensagemRetorno=SimpleNamespace(Codigo="OK200"),
            ListaNfeArquivosRPS=SimpleNamespace(SituacaoArq="1"),
        )
        status, mensagem = self.barueri.analisa_retorno_consulta(_processo(resposta))
        self.assertEqual(status, 1)
        self.assertEqual(mensagem, "Successfully Processed")

    def test_outro_servico_nao_e_interpretado(self):
        status, mensagem = self.barueri.analisa_retorno_consulta(
            _processo(SimpleNamespace(), webservice="NFeLoteEnviarArquivo")
        )
        self.assertIsNone(status)
        self.assertEqual(mensagem, "")
