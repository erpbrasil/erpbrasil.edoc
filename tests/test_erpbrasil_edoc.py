import logging.config
import os
from unittest import TestCase

import vcr
from requests import Session

from erpbrasil.edoc.mde import MDe, TransmissaoMDE

from .test_certificate_mixin import TestCertificateMixin

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {"verbose": {"format": "%(name)s: %(message)s"}},
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "zeep.transports": {
                "level": "DEBUG",
                "propagate": True,
                "handlers": ["console"],
            },
        },
    }
)

# Os cassetes guardam o corpo gzip como foi recebido; com urllib3 2 o playback
# precisa descomprimir, senao o zeep recebe bytes gzip no lugar do WSDL.
gravador = vcr.VCR(decode_compressed_response=True)

VALID_CSTAT_LIST = ["137", "138"]


class Tests(TestCertificateMixin, TestCase):
    """Rodar este teste muitas vezes pode bloquear o seu IP"""

    def setUp(self):
        super().setUp()
        self.chave = os.environ.get("CHAVE_NFE", "35200309091076000144550010001807401003642343")
        session = Session()
        session.verify = False

        transmissao = TransmissaoMDE(self.certificate, session)
        self.mde = MDe(transmissao, "35", versao="1.01", ambiente="1")

    @gravador.use_cassette(
        "tests/fixtures/vcr_cassettes/test_nsu_especifico.yaml",
    )
    def test_nsu_especifico(self):
        ret = self.mde.consultar_distribuicao(
            cnpj_cpf=self.certificate.cnpj_cpf,
            nsu_especifico="16172".zfill(15),
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    @gravador.use_cassette(
        "tests/fixtures/vcr_cassettes/test_ultimo_nsu.yaml",
    )
    def test_ultimo_nsu(self):
        ret = self.mde.consultar_distribuicao(
            cnpj_cpf=self.certificate.cnpj_cpf,
            ultimo_nsu="0".zfill(15),
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    @gravador.use_cassette("tests/fixtures/vcr_cassettes/test_chave.yaml")
    def test_chave(self):
        ret = self.mde.consultar_distribuicao(cnpj_cpf=self.certificate.cnpj_cpf, chave=self.chave)

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)
