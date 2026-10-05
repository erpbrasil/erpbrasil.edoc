from unittest import TestCase

from erpbrasil.edoc.nfe import WS_NFE_CADASTRO, NFe, localizar_url


class UrlConsultaCadastroTests(TestCase):
    """URLs da Relação de Serviços Web do Portal NF-e (produção e homologação)."""

    def test_am_usa_cad_consulta_cadastro_4(self):
        self.assertEqual(
            localizar_url(WS_NFE_CADASTRO, "13", "55", 1),
            "https://nfe.sefaz.am.gov.br/services2/services/CadConsultaCadastro4?wsdl",
        )
        self.assertEqual(
            localizar_url(WS_NFE_CADASTRO, "13", "55", 2),
            "https://homnfe.sefaz.am.gov.br/services2/services/CadConsultaCadastro4?wsdl",
        )

    def test_pe_usa_cad_consulta_cadastro_4(self):
        self.assertEqual(
            localizar_url(WS_NFE_CADASTRO, "26", "55", 1),
            "https://nfe.sefaz.pe.gov.br/nfe-service/services/CadConsultaCadastro4?wsdl",
        )
        self.assertEqual(
            localizar_url(WS_NFE_CADASTRO, "26", "55", 2),
            "https://nfehomolog.sefaz.pe.gov.br/nfe-service/services/CadConsultaCadastro4?wsdl",
        )

    def test_consultar_cadastro_chama_a_operacao_da_versao_4(self):
        chamadas = []
        nfe = NFe(False, "13", versao="4.00", ambiente="2")
        nfe._post = lambda raiz, url, operacao, classe: chamadas.append((url, operacao))

        nfe.consultar_cadastro("AM", cnpj="12345678000195")

        self.assertEqual(
            chamadas,
            [
                (
                    "https://homnfe.sefaz.am.gov.br/services2/services/"
                    "CadConsultaCadastro4?wsdl",
                    "consultaCadastro",
                )
            ],
        )
