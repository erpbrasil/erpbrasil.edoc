import logging.config
import os
from unittest import TestCase

import vcr
from erpbrasil.edoc.mde import MDe, TransmissaoMDE
from requests import Session

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

VALID_CSTAT_LIST = ["128"]


class Tests(TestCertificateMixin, TestCase):
    """Rodar este teste muitas vezes pode bloquear o seu IP"""

    def setUp(self):
        super().setUp()
        session = Session()
        session.verify = False

        transmissao = TransmissaoMDE(self.certificate, session)
        self.mde = MDe(transmissao, "35", versao="1.00", ambiente="1")

        self.chave = os.environ.get(
            "CHAVE_NFE", "35200309091076000144550010001807401003642343"
        )

    @vcr.use_cassette("tests/fixtures/vcr_cassettes/test_confirmacao_da_operacao.yaml")
    def test_confirmacao_da_operacao(self):
        ret = self.mde.confirmacao_da_operacao(
            chave=self.chave, cnpj_cpf=self.certificate.cnpj_cpf
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    @vcr.use_cassette("tests/fixtures/vcr_cassettes/test_ciencia_da_operacao.yaml")
    def test_ciencia_da_operacao(self):
        ret = self.mde.ciencia_da_operacao(
            chave=self.chave, cnpj_cpf=self.certificate.cnpj_cpf
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    @vcr.use_cassette(
        "tests/fixtures/vcr_cassettes/test_desconhecimento_da_operacao.yaml"
    )
    def test_desconhecimento_da_operacao(self):
        ret = self.mde.desconhecimento_da_operacao(
            chave=self.chave, cnpj_cpf=self.certificate.cnpj_cpf
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    @vcr.use_cassette("tests/fixtures/vcr_cassettes/test_operacao_nao_realizada.yaml")
    def test_operacao_nao_realizada(self):
        ret = self.mde.operacao_nao_realizada(
            chave=self.chave, cnpj_cpf=self.certificate.cnpj_cpf
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)
