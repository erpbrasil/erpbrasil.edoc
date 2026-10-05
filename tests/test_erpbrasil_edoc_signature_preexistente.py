from unittest import TestCase

from erpbrasil.edoc.nfe import NFe
from erpbrasil.nfelib_legacy.v4_00 import retEnviNFe
from lxml import etree

NS_DS = "http://www.w3.org/2000/09/xmldsig#"
SIGNATURE_XML = (
    f'<Signature xmlns="{NS_DS}"><SignedInfo>'
    '<CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>'
    f'<SignatureMethod Algorithm="{NS_DS}rsa-sha1"/>'
    f'<Reference URI="#x"><DigestMethod Algorithm="{NS_DS}sha1"/>'
    "<DigestValue>YWFh</DigestValue></Reference></SignedInfo>"
    "<SignatureValue>YmJi</SignatureValue>"
    "<KeyInfo><X509Data><X509Certificate>Y2Nj</X509Certificate></X509Data></KeyInfo>"
    "</Signature>"
)


def _tnfe(assinada):
    assinatura = None
    if assinada:
        assinatura = retEnviNFe.SignatureType.factory()
        assinatura.build(etree.fromstring(SIGNATURE_XML))
    tnfe = retEnviNFe.TNFe(infNFe=None, infNFeSupl=None, Signature=assinatura)
    tnfe.original_tagname_ = "NFe"
    return tnfe


class TestSignaturePreExistente(TestCase):
    """Os bindings legados exportam ds:Signature sem declarar xmlns:ds."""

    def setUp(self):
        self.nfe = NFe(False, "35", versao="4.00", ambiente="2")

    def test_export_com_signature_declara_xmlns_ds(self):
        xml_string, xml_etree = self.nfe._generateds_to_string_etree(_tnfe(True))
        self.assertIn(f'xmlns:ds="{NS_DS}"', xml_string)
        self.assertEqual(len(xml_etree.findall(f"{{{NS_DS}}}Signature")), 1)

    def test_export_sem_signature_nao_muda(self):
        xml_string, _ = self.nfe._generateds_to_string_etree(_tnfe(False))
        self.assertNotIn("xmlns:ds", xml_string)
