from types import SimpleNamespace
from unittest import TestCase

from lxml import etree

from erpbrasil.edoc.nfe import NFe
from erpbrasil.nfelib_legacy.v4_00 import retEnviNFe

from .test_certificate_mixin import TestCertificateMixin

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


class TestReassinatura(TestCertificateMixin, TestCase):
    def test_reassinar_descarta_a_signature_anterior(self):
        nfe = NFe(
            SimpleNamespace(certificado=self.certificate),
            "35",
            versao="4.00",
            ambiente="2",
        )
        chave = "NFe35260112345678000195550010000000011000000011"
        tnfe = _tnfe(True)
        tnfe.infNFe = retEnviNFe.infNFeType(versao="4.00", Id=chave)

        xml_assinado = nfe.assina_raiz(tnfe, chave)

        self.assertIsNone(tnfe.Signature)
        self.assertEqual(len(etree.fromstring(xml_assinado).findall(f".//{{{NS_DS}}}Signature")), 1)
        self.assertNotIn("YmJi", xml_assinado)  # SignatureValue da assinatura antiga
