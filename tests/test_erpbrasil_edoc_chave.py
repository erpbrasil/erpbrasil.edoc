import datetime
import hashlib
from types import SimpleNamespace
from unittest import TestCase

from erpbrasil.edoc.chave import ChaveNFSeDSF

# Chave de 94 posicoes valida, usada como ponto de partida para os testes:
# ela precisa ser valida pois o construtor da classe faz o parse completo
# (inclusive da data) assim que `chave=` e informado.
CHAVE_VALIDA = (
    "00000317330NF   00000003866320090905T N0000000000168600"
    "000000000000000008299799000008764130000"
)


def _item(valor_total):
    return SimpleNamespace(ValorTotal=valor_total)


def _deducao(valor_deduzir):
    return SimpleNamespace(ValorDeduzir=valor_deduzir)


class Tests(TestCase):
    def test_construtor_sem_chave_nem_rps_gera_excecao(self):
        with self.assertRaises(Exception):
            ChaveNFSeDSF()

    def test_construtor_com_chave_faz_parse_de_todos_os_campos(self):
        self.assertEqual(len(CHAVE_VALIDA), 94)
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        self.assertEqual(chave.inscricao_municipal, "00000317330")
        self.assertEqual(chave.serie, "NF   ")
        self.assertEqual(chave.numero, "000000038663")
        self.assertEqual(chave.data, "20090905")
        # o slice de tributacao tem largura 1: soma-se um espaco (ljust)
        self.assertEqual(chave.tributacao, "T ")
        self.assertEqual(chave.situacao, "N")
        self.assertEqual(chave.tipo_recolhimento, "0")
        self.assertEqual(chave.valor_servico, "000000000168600"[-15:])
        self.assertEqual(chave.valor_deducao, "0" * 15)
        self.assertEqual(chave.codigo_atividade, "0082997990")
        self.assertEqual(chave.cpf_cnpj, "00008764130000")
        # a property `chave` deve reconstruir exatamente a string original
        self.assertEqual(chave.chave, CHAVE_VALIDA)

    def test_setters_aplicam_padding_correto(self):
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        chave.inscricao_municipal = 317330
        self.assertEqual(chave.inscricao_municipal, "00000317330")

        chave.serie = "NF"
        self.assertEqual(chave.serie, "NF   ")

        chave.numero = 38663
        self.assertEqual(chave.numero, "000000038663")

        chave.tributacao = "T"
        self.assertEqual(chave.tributacao, "T ")

        chave.codigo_atividade = 82997990
        self.assertEqual(chave.codigo_atividade, "0082997990")

        chave.cpf_cnpj = "8764130000102"
        self.assertEqual(chave.cpf_cnpj, "08764130000102")

    def test_valor_servico_aceita_string_ou_float(self):
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        chave.valor_servico = "00000000168600"
        self.assertEqual(chave.valor_servico, "00000000168600")

        # float: o ponto decimal e apenas removido da representacao textual
        chave.valor_servico = 1686.00
        self.assertEqual(chave.valor_servico, "16860")

    def test_valor_deducao_aceita_string_float_ou_int(self):
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        chave.valor_deducao = "00000000000000"
        self.assertEqual(chave.valor_deducao, "00000000000000")

        chave.valor_deducao = 100.0
        self.assertEqual(chave.valor_deducao, "1000")

        chave.valor_deducao = 0
        self.assertEqual(chave.valor_deducao, "0")

    def test_data_aceita_string_e_datetime(self):
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        chave.data = "20090905"
        self.assertEqual(chave.data, "20090905")

        chave.data = datetime.datetime(2020, 11, 20)
        self.assertEqual(chave.data, "20201120")

    def test_rps_monta_chave_a_partir_de_objeto_rps(self):
        rps = SimpleNamespace(
            InscricaoMunicipalPrestador=317330,
            SerieRPS="NF",
            NumeroRPS=38663,
            DataEmissaoRPS="20090905",
            TipoRPS="TN",
            SituacaoRPS="N",
            TipoRecolhimento="0",
            Itens=[_item(1000.0), _item(686.0)],
            Deducoes=[_deducao(0.0)],
            CodigoAtividade=82997990,
            CPFCNPJTomador="8764130000102",
        )

        chave = ChaveNFSeDSF(rps=rps)

        self.assertEqual(chave.inscricao_municipal, "00000317330")
        self.assertEqual(chave.serie, "NF   ")
        self.assertEqual(chave.numero, "000000038663")
        self.assertEqual(chave.data, "20090905")
        self.assertEqual(chave.tributacao, "TN")
        self.assertEqual(chave.situacao, "N")
        self.assertEqual(chave.tipo_recolhimento, "0")
        # 1000.0 + 686.0 - 0.0 = 1686.0 -> "1686.0" sem o ponto
        self.assertEqual(chave.valor_servico, "16860")
        # 0.0 (float) -> "0.0" sem o ponto
        self.assertEqual(chave.valor_deducao, "00")
        self.assertEqual(chave.codigo_atividade, "0082997990")
        self.assertEqual(chave.cpf_cnpj, "08764130000102")

    def test_hash_e_sha1_da_chave(self):
        chave = ChaveNFSeDSF(chave=CHAVE_VALIDA)

        esperado = hashlib.sha1(chave.chave.encode()).hexdigest()
        self.assertEqual(chave.hash, esperado)
        self.assertEqual(len(chave.hash), 40)
