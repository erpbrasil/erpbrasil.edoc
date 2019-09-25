# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

import re
import datetime
from lxml import etree

from mdfelib.v3_00 import consStatServMDFe
from mdfelib.v3_00 import consSitMDFe
from mdfelib.v3_00 import consMDFeNaoEnc
from mdfelib.v3_00 import enviMDFe
from mdfelib.v3_00 import consReciMDFe

from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.assinatura.assinatura import Assinatura

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class MDFe(DocumentoEletronico):
    _namespace = 'http://www.portalfiscal.inf.br/mdfe'

    _edoc_situacao_arquivo_recebido_com_sucesso = '103'
    _edoc_situacao_em_processamento = '105'
    _edoc_situacao_servico_em_operacao = '107'
    _edoc_situacao_ja_enviado = ('100', '101', '132')

    _consulta_servico_ao_enviar = True
    _maximo_tentativas_consulta_recibo = 5


    def get_documento_id(self, edoc):
        return edoc.infMDFe.Id[:3], edoc.infMDFe.Id[3:]

    def status_servico(self):
        raiz = consStatServMDFe.TConsStatServ(
            versao='4.00',
            tpAmb='2',
            cUF=35,
            xServ='STATUS',
        )
        raiz.original_tagname_ = 'consStatServMDFe'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/wws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl',
            'nfeStatusServicoNF',
            consStatServMDFe
        )

    def consulta_documento(self, chave):
        raiz = consSitMDFe.TConsSitMDFe(
            versao='4.00',
            tpAmb='2',
            xServ='CONSULTAR',
            chMDFe=chave,
        )
        raiz.original_tagname_ = 'consSitMDFe'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeConsulta/MDFeConsulta.asmx?wsdl',
            'MDFeConsultaNF',
            consSitMDFe
        )

    def consulta_nao_encerrados(self, cnpj):
        raiz = consMDFeNaoEnc.TConsMDFeNaoEnc(
            versao=self._versao,
            tpAmb=str(self._ambiente),
            xServ='CONSULTAR NÃO ENCERRADOS',
            CNPJ=cnpj,
        )
        raiz.original_tagname_ = 'consMDFeNaoEnc'

        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl',
            'mdfeConsNaoEnc',
            consMDFeNaoEnc,
        )

    def envia_documento(self, edoc):
        """

        Exportar o documento
        Assinar o documento
        Adicionar o mesmo ao envio

        :param edoc:
        :return:
        """
        xml_string, xml_etree = self._generateds_to_string_etree(edoc)
        xml_assinado = Assinatura(self.certificado).assina_xml2(
            xml_etree, edoc.infMDFe.Id
        )

        raiz = enviMDFe.TEnviMDFe(
            versao='4.00',
            idLote=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        )
        raiz.original_tagname_ = 'enviMDFe'
        xml_envio_string, xml_envio_etree = self._generateds_to_string_etree(
            raiz
        )
        xml_envio_etree.append(etree.fromstring(xml_assinado))

        return self._post(
            xml_envio_etree,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFerecepcao/MDFeRecepcao.asmx?wsdl',
            'mdfeRecepcaoLote',
            enviMDFe
        )

    def consulta_recibo(self, numero):
        raiz = consReciMDFe.TConsReciMDFe(
            versao='4.00',
            tpAmb='2',
            nRec=numero,
        )
        raiz.original_tagname_ = 'consReciMDFe'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl', #'ws/MDFeretautorizacao4.asmx'
            'mdfeRetRecepcao',
            consReciMDFe,
        )

    def cancela_documento(self):
        pass
