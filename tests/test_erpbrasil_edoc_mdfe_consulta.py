from unittest import TestCase
from unittest.mock import patch

from erpbrasil.edoc import mdfe


class TestMDFeConsulta(TestCase):
    def test_operacao_da_consulta(self):
        processador = mdfe.MDFe(transmissao=None, uf=26, ambiente="2")
        chave = "26261109359574000125580010000000011776635741"
        with patch.object(mdfe.MDFe, "_post") as post:
            processador.consulta_documento(chave)
        self.assertEqual(post.call_args.kwargs["operacao"], "mdfeConsultaMDF")
