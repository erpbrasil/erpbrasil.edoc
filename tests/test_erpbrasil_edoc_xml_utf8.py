# Copyright (C) 2026  KMEE
from unittest import TestCase

from lxml import etree

from erpbrasil.edoc.edoc import xml_bytes
from erpbrasil.edoc.nfe import NFe

NS = "http://www.portalfiscal.inf.br/nfe"
NFE = (
    f'<NFe xmlns="{NS}"><infNFe Id="NFe1"><emit>'
    "<xNome>Quick Manutenção de Aeronaves Ltda</xNome>"
    "<enderEmit><xMun>Goiânia</xMun></enderEmit></emit></infNFe></NFe>"
)
PROT = f'<protNFe xmlns="{NS}" versao="4.00"><infProt><cStat>100</cStat></infProt></protNFe>'


class TestXmlUtf8(TestCase):
    """O XML gravado sai em UTF-8, com os caracteres acentuados literais."""

    def setUp(self):
        self.nfe = etree.fromstring(NFE.encode("utf-8"))

    def assert_utf8_literal(self, xml):
        self.assertIsInstance(xml, bytes)
        texto = xml.decode("utf-8")
        self.assertIn("Manutenção", texto)
        self.assertIn("Goiânia", texto)
        self.assertNotIn("&#", texto)
        # sem declaração: quem grava o arquivo decide o cabeçalho
        self.assertFalse(texto.startswith("<?xml"))

    def test_elemento(self):
        self.assert_utf8_literal(xml_bytes(self.nfe))

    def test_mesmo_documento_e_mesmo_resumo(self):
        """A forma canônica, sobre a qual a assinatura é calculada, não muda."""
        antes = etree.tostring(self.nfe)
        self.assertIn(b"&#231;", antes)
        depois = xml_bytes(self.nfe)
        self.assertEqual(
            etree.tostring(etree.fromstring(antes), method="c14n"),
            etree.tostring(etree.fromstring(depois), method="c14n"),
        )

    def test_string_e_etree_de_um_elemento(self):
        processador = NFe.__new__(NFe)
        xml, arvore = processador._generateds_to_string_etree(self.nfe)
        self.assert_utf8_literal(xml)
        self.assertIs(arvore, self.nfe)

    def test_nfe_proc(self):
        processador = NFe.__new__(NFe)
        processador._namespace = NS
        processador.versao = "4.00"
        proc = processador.monta_nfe_proc(self.nfe, etree.fromstring(PROT.encode()))
        self.assert_utf8_literal(proc)
        raiz = etree.fromstring(proc)
        self.assertEqual(raiz.tag, f"{{{NS}}}nfeProc")
        self.assertEqual(len(raiz), 2)
