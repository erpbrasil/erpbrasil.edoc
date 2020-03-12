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
            versao='1.00', ambiente='1'
        )

        self.chave = os.environ.get(
            'chNFe', '26180812984794000154550010000016871192213339'
        )

    def test_status_servico_manifestacao(self):
        ret = self.nfe.status_servico_manifestacao()

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

    def test_confirmacao_da_operacao(self):
        ret = self.nfe.confirmacao_da_operacao(
            chave=self.chave,
            cnpj_cpf=self.certificado.cnpj_cpf
        )

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

    def test_ciencia_da_operacao(self):
        ret = self.nfe.ciencia_da_operacao(
            chave=self.chave,
            cnpj_cpf=self.certificado.cnpj_cpf
        )

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

    def test_desconhecimento_da_operacao(self):
        ret = self.nfe.desconhecimento_da_operacao(
            chave=self.chave,
            cnpj_cpf=self.certificado.cnpj_cpf
        )

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

    def test_operacao_nao_realizada(self):
        ret = self.nfe.operacao_nao_realizada(
            chave=self.chave,
            cnpj_cpf=self.certificado.cnpj_cpf
        )

        # TODO: Assert
        print('XML Envio:\n{}\n\nXML Resposta:\n{}'.format(ret.envio_xml, ret.retorno.text))

t = Tests()
t.setUp()
t.test_status_servico_manifestacao()
t.test_confirmacao_da_operacao()
t.test_ciencia_da_operacao()
t.test_desconhecimento_da_operacao()
t.test_operacao_nao_realizada()
