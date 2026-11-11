from types import SimpleNamespace
from unittest import TestCase

from erpbrasil.edoc import cte, mdfe

CHAVE = "1" * 44


def _transmissao():
    return SimpleNamespace()


class TestAmbienteCTe(TestCase):
    def test_get_service_url_aceita_int_e_texto(self):
        for uf in ("SP", "BA"):
            for servico in (cte.WS_CTE_STATUS_SERVICO, "QRCode"):
                prod = cte.get_service_url(uf, servico, 1)
                homolog = cte.get_service_url(uf, servico, 2)
                self.assertEqual(prod, cte.get_service_url(uf, servico, "1"))
                self.assertEqual(homolog, cte.get_service_url(uf, servico, "2"))
        # SVSP tem URL distinta por ambiente, inclusive a do QR Code
        for servico in (cte.WS_CTE_STATUS_SERVICO, "QRCode"):
            self.assertNotEqual(
                cte.get_service_url("SP", servico, "1"),
                cte.get_service_url("SP", servico, "2"),
            )

    def test_qrcode_url_por_ambiente(self):
        self.assertEqual(
            cte.get_service_url("SP", "QRCode", "1"),
            cte.SVSP[cte.AMBIENTE_PRODUCAO][cte.QR_CODE_URL],
        )
        self.assertEqual(
            cte.get_service_url("SP", "QRCode", "2"),
            cte.SVSP[cte.AMBIENTE_HOMOLOGACAO][cte.QR_CODE_URL],
        )

    def test_processador_com_ambiente_texto_usa_producao(self):
        proc = cte.CTe(_transmissao(), uf=35, ambiente="1")
        self.assertEqual(
            proc._get_ws_endpoint(cte.WS_CTE_STATUS_SERVICO),
            cte.get_service_url("SP", cte.WS_CTE_STATUS_SERVICO, 1),
        )
        self.assertEqual(
            proc.monta_qrcode(CHAVE),
            cte.SVSP[cte.AMBIENTE_PRODUCAO][cte.QR_CODE_URL] + f"?chCTe={CHAVE}&tpAmb=1",
        )

    def test_processador_com_ambiente_int_ou_texto_homologacao(self):
        for ambiente in (2, "2"):
            proc = cte.CTe(_transmissao(), uf=35, ambiente=ambiente)
            self.assertEqual(
                proc._get_ws_endpoint(cte.WS_CTE_STATUS_SERVICO),
                cte.get_service_url("SP", cte.WS_CTE_STATUS_SERVICO, 2),
            )
            self.assertEqual(
                proc.monta_qrcode(CHAVE),
                cte.SVSP[cte.AMBIENTE_HOMOLOGACAO][cte.QR_CODE_URL] + f"?chCTe={CHAVE}&tpAmb=2",
            )

    def test_processador_com_ambiente_int_producao(self):
        proc = cte.CTe(_transmissao(), uf=35, ambiente=1)
        self.assertIn(
            cte.SVSP[cte.AMBIENTE_PRODUCAO]["servidor"],
            proc._get_ws_endpoint(cte.WS_CTE_STATUS_SERVICO),
        )


class TestAmbienteMDFe(TestCase):
    def test_get_service_url_aceita_int_e_texto(self):
        for servico in (mdfe.WS_MDFE_STATUS_SERVICO,):
            prod = mdfe.get_service_url("SP", servico, 1)
            homolog = mdfe.get_service_url("SP", servico, 2)
            self.assertNotEqual(prod, homolog)
            self.assertEqual(prod, mdfe.get_service_url("SP", servico, "1"))
            self.assertEqual(homolog, mdfe.get_service_url("SP", servico, "2"))

    def test_processador_com_ambiente_texto_usa_producao(self):
        proc = mdfe.MDFe(_transmissao(), uf=35, ambiente="1")
        self.assertEqual(
            proc.monta_qrcode(CHAVE),
            mdfe.SVRS[mdfe.AMBIENTE_PRODUCAO][mdfe.QR_CODE_URL] + f"?chMDFe={CHAVE}&tpAmb=1",
        )
        self.assertEqual(
            proc._get_ws_endpoint(mdfe.WS_MDFE_STATUS_SERVICO),
            mdfe.get_service_url("SP", mdfe.WS_MDFE_STATUS_SERVICO, 1),
        )

    def test_processador_com_ambiente_homologacao(self):
        for ambiente in (2, "2"):
            proc = mdfe.MDFe(_transmissao(), uf=35, ambiente=ambiente)
            self.assertEqual(
                proc.monta_qrcode(CHAVE),
                mdfe.SVRS[mdfe.AMBIENTE_HOMOLOGACAO][mdfe.QR_CODE_URL] + f"?chMDFe={CHAVE}&tpAmb=2",
            )
