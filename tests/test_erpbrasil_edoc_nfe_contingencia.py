from unittest import TestCase

from erpbrasil.edoc import nfe

SERVICOS_SVC = (
    nfe.WS_NFE_CONSULTA,
    nfe.WS_NFE_SITUACAO,
    nfe.WS_NFE_RECEPCAO_EVENTO,
    nfe.WS_NFE_AUTORIZACAO,
    nfe.WS_NFE_RET_AUTORIZACAO,
)
# UFs cuja contingência é a SVC-RS (ESTADO_WS)
UFS_SVC_RS = ("13", "29", "52", "21", "50", "51", "26", "22", "41")


class TestContingenciaSvcRs(TestCase):
    def test_producao_usa_os_mesmos_caminhos_da_homologacao(self):
        for uf in UFS_SVC_RS:
            for servico in SERVICOS_SVC:
                with self.subTest(uf=uf, servico=servico):
                    producao = nfe.localizar_url(servico, uf, ambiente=1, contingencia=True)
                    homologacao = nfe.localizar_url(servico, uf, ambiente=2, contingencia=True)
                    self.assertTrue(producao.startswith("https://nfe.svrs.rs.gov.br/"))
                    self.assertEqual(producao.split("/", 3)[3], homologacao.split("/", 3)[3])

    def test_autorizacao_em_contingencia_na_producao(self):
        self.assertEqual(
            nfe.localizar_url(nfe.WS_NFE_AUTORIZACAO, "29", ambiente=1, contingencia=True),
            "https://nfe.svrs.rs.gov.br/ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl",
        )
