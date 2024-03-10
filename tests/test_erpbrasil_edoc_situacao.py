from unittest import TestCase

import vcr
from erpbrasil.edoc.nfe import NFe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from .test_certificate_mixin import TestCertificateMixin

VALID_CSTAT_LIST = ["107", "108", "109"]


class Tests(TestCertificateMixin, TestCase):
    """Rodar este teste muitas vezes pode bloquear o seu IP"""

    def setUp(self):
        super().setUp()
        session = Session()
        session.verify = False

        transmissao = TransmissaoSOAP(self.certificate, session)
        self.nfe = NFe(transmissao, "35", versao="4.00", ambiente="1")

    @vcr.use_cassette("tests/fixtures/vcr_cassettes/test_status_servico.yaml")
    def test_status_servico(self):
        ret = self.nfe.status_servico()
        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)
