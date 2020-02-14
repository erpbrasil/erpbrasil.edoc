# coding=utf-8
import logging.config

import collections
import os
from unittest import TestCase

from erpbrasil.assinatura.certificado import Certificado
from requests import Session

from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.edoc import NFe


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
            versao='1.01', ambiente='2'
        )

    def test_status_servico_manifestacao(self):
        ret = self.nfe.status_servico_manifestacao()

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

    def test_ciencia_da_operacao(self):
        ret = self.nfe.ciencia_da_operacao()

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

t = Tests()
t.setUp()
# t.test_status_servico_manifestacao()
t.test_ciencia_da_operacao()
