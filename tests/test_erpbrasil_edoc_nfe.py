from unittest import TestCase

from erpbrasil.edoc.nfe import NFe
from lxml import etree


class NFeTests(TestCase):
    def setUp(self):
        self.nfe = NFe(False, "35", versao="4.00", ambiente="1")
        nfe_xml_str = """
        <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
            <infNFe Id="NFe12345678901234567890123456789012345678901234" versao="4.00">
                <ide>
                    <cUF>35</cUF>
                    <cNF>1234567</cNF>
                    <natOp>Venda de mercadoria</natOp>
                    <!-- Outros campos da tag ide -->
                </ide>
                <emit>
                    <CNPJ>12345678000195</CNPJ>
                    <xNome>Empresa Exemplo</xNome>
                    <!-- Outros campos da tag emit -->
                </emit>
                <!-- Outras tags como det, total, transp, etc. -->
            </infNFe>
        </NFe>
        """
        prot_nfe_xml_str = """
        <protNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
            <infProt>
                <tpAmb>1</tpAmb>
                <verAplic>SP_NFE_PL_008i2</verAplic>
                <chNFe>12345678901234567890123456789012345678901234</chNFe>
                <dhRecbto>2024-01-16T14:00:00-03:00</dhRecbto>
                <nProt>13579024681112</nProt>
                <digVal>abcd1234abcd1234abcd1234abcd1234abcd1234=</digVal>
                <cStat>100</cStat>
                <xMotivo>Autorizado o uso da NF-e</xMotivo>
            </infProt>
        </protNFe>
        """
        self.nfe_element = etree.fromstring(nfe_xml_str)
        self.prot_nfe_element = etree.fromstring(prot_nfe_xml_str)

    def test_monta_nfe_proc(self):
        nfe_proc_bytes = self.nfe.monta_nfe_proc(
            self.nfe_element, self.prot_nfe_element
        )
        root = etree.fromstring(nfe_proc_bytes)
        self.assertIsInstance(nfe_proc_bytes, bytes)
        self.assertEqual(root.tag, "{http://www.portalfiscal.inf.br/nfe}nfeProc")
        children = list(root)
        self.assertEqual(len(children), 2)
        child_tags = [child.tag for child in children]
        self.assertIn("{http://www.portalfiscal.inf.br/nfe}NFe", child_tags)
        self.assertIn("{http://www.portalfiscal.inf.br/nfe}protNFe", child_tags)
