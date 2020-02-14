# coding=utf-8
import logging.config

import collections
import os
from unittest import TestCase

from erpbrasil.assinatura.certificado import Certificado
from requests import Session

from erpbrasil.transmissao import TransmissaoSOAP
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
        session = Session()
        session.verify = False

        transmissao = TransmissaoSOAP(self.certificado, session)
        self.nfe = NFe(
            transmissao, '35',
            versao='1.01', ambiente='1'
        )

    def test_status_servico(self):
        ret = self.nfe.status_servico()

        # TODO: assert
        print(ret)

    def test_ultimo_nsu(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf='27469611000130',
            ultimo_nsu='1'.zfill(15),
        )

        # TODO: Assert
        print(ret)

    def test_nsu_especifico(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf='27469611000130',
            nsu_especifico='1'.zfill(15),
        )

        # TODO: Assert
        print(ret)

    def test_chave(self):

        ret = self.nfe.consultar_distribuicao(
            cnpj_cpf='27469611000130',
            chave='42200231865792000190550010000017641557307490'
        )

        # TODO: Assert
        print(ret)


t = Tests()
t.setUp()
# t.test_status_servico()
t.test_ultimo_nsu()
# t.test_nsu_especifico()
# t.test_chave()
