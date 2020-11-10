# coding=utf-8
import logging.config
import os
from unittest import TestCase

from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

from erpbrasil.edoc import NFe

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            'level': 'DEBUG',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})

VALID_CSTAT_LIST = ['137', '138']


class Tests(TestCase):
    """ Rodar este teste muitas vezes pode bloquear o seu IP"""

    def setUp(self):
        certificado_nfe_caminho = os.environ.get(
            'certificado_nfe_caminho',
            'tests/teste.pfx'
        )
        certificado_nfe_senha = os.environ.get(
            'certificado_nfe_senha', 'teste'
        )
        self.certificado = Certificado(
            certificado_nfe_caminho,
            certificado_nfe_senha
        )

        self.chave = os.environ.get(
            'chNFe', '26180812984794000154550010000016871192213339'
        )

        session = Session()
        session.verify = False

        transmissao = TransmissaoSOAP(self.certificado, session)
        self.nfe = NFe(
            transmissao, '35',
            versao='1.01', ambiente='1'
        )

    def test_ultimo_nsu(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf=self.certificado.cnpj_cpf,
            ultimo_nsu='1'.zfill(15),
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    def test_nsu_especifico(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf=self.certificado.cnpj_cpf,
            nsu_especifico='1'.zfill(15),
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)

    def test_chave(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf=self.certificado.cnpj_cpf,
            chave=self.chave
        )

        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)


t = Tests()
t.setUp()
t.test_ultimo_nsu()
t.test_nsu_especifico()
t.test_chave()
