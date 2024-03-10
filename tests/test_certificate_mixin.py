# Copyright 2024 Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>

import os
import unittest

from erpbrasil.assinatura import misc
from erpbrasil.assinatura.certificado import Certificado


class TestCertificateMixin(unittest.TestCase):
    """
    Mixin para testes que requerem o carregamento de certificados,
    reais ou falsos, para testes de documentos eletrônicos.
    """

    def setUp(self):
        super().setUp()
        self.certificate = self._load_certificate()

    def _load_certificate(self):
        self._certificate_path = self._get_certificate_path()
        self._certificate_password = self._get_certificate_password()

        if self._should_load_real_certificate():
            return self._load_real_certificate()
        else:
            return self._load_fake_certificate()

    def _get_certificate_path(self):
        return os.environ.get("CERTIFICATE_PATH")

    def _get_certificate_password(self):
        return os.environ.get("CERTIFICATE_PASSWORD")

    def _should_load_real_certificate(self):
        return bool(self._certificate_path and self._certificate_password)

    def _load_real_certificate(self):
        return Certificado(self._certificate_path, self._certificate_password)

    def _load_fake_certificate(self):
        return Certificado(
            arquivo=misc.create_fake_certificate_file(
                valid=True,
                passwd="123456",
                issuer="EMISSOR A TESTE",
                country="BR",
                subject="CERTIFICADO VALIDO TESTE",
            ),
            senha="123456",
        )
