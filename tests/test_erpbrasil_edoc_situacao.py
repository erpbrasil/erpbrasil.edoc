# coding=utf-8

import os
from unittest import TestCase

from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.edoc import NFe
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

VALID_CSTAT_LIST = ['107', '108', '109']


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
            versao='4.00', ambiente='1'
        )

    def test_status_servico(self):
        ret = self.nfe.status_servico()
        self.assertIn(ret.resposta.cStat, VALID_CSTAT_LIST)


t = Tests()
t.setUp()
t.test_status_servico()
