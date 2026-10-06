from unittest import TestCase

from erpbrasil.edoc import mdfe


class TestMDFeServiceUrl(TestCase):
    def test_todas_as_ufs_na_svrs(self):
        for uf in mdfe.SIGLA_ESTADO:
            if uf == "AN":
                continue
            with self.subTest(uf=uf):
                self.assertEqual(
                    mdfe.get_service_url(uf, mdfe.WS_MDFE_STATUS_SERVICO, "1"),
                    "https://mdfe.svrs.rs.gov.br/ws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl",
                )
                self.assertTrue(
                    mdfe.get_service_url(uf, mdfe.WS_MDFE_STATUS_SERVICO, "2").startswith(
                        "https://mdfe-homologacao.svrs.rs.gov.br/"
                    )
                )

    def test_ufs_que_davam_erro(self):
        # MG, MS, MT e PR ficavam fora da lista e levantavam ValueError
        for uf in ("MG", "MS", "MT", "PR"):
            with self.subTest(uf=uf):
                self.assertIn(
                    "mdfe.svrs.rs.gov.br",
                    mdfe.get_service_url(uf, mdfe.WS_MDFE_RECEPCAO_SINC, 1),
                )

    def test_ambiente_nacional_nao_e_autorizadora(self):
        with self.assertRaises(ValueError):
            mdfe.get_service_url("AN", mdfe.WS_MDFE_STATUS_SERVICO, "1")
