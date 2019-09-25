# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

import re
import datetime
from lxml import etree

from nfelib.v4_00 import leiauteNFe
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub
from nfelib.v4_00 import consStatServ
from nfelib.v4_00 import retConsStatServ
from nfelib.v4_00 import consSitNFe
from nfelib.v4_00 import retConsSitNFe
from nfelib.v4_00 import enviNFe
from nfelib.v4_00 import retEnviNFe
from nfelib.v4_00 import consReciNFe
from nfelib.v4_00 import retConsReciNFe
from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.assinatura.assinatura import Assinatura

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class NFe(DocumentoEletronico):
    _namespace = 'http://www.portalfiscal.inf.br/nfe'
    _edoc_situacao_arquivo_recebido_com_sucesso = '103'
    _edoc_situacao_em_processamento = '105'
    _edoc_situacao_servico_em_operacao = '107'
    _consulta_servico_ao_enviar = True
    _maximo_tentativas_consulta_recibo = 5
    _edoc_situacao_ja_enviado = ('100', '110', '150', '301', '302')

    def get_documento_id(self, edoc):
        return edoc.infNFe.Id[:3], edoc.infNFe.Id[3:]

    def status_servico(self):
        raiz = consStatServ.TConsStatServ(
            versao='4.00',
            tpAmb='2',
            cUF=35,
            xServ='STATUS',
        )
        raiz.original_tagname_ = 'consStatServ'
        return self._post(
            raiz,
            # 'https://hom.sefazvirtual.fazenda.gov.br/NFeStatusServico4/NFeStatusServico4.asmx?wsdl',
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx?wsdl',
            'nfeStatusServicoNF',
            retConsStatServ
        )

    def consulta_documento(self, chave):
        raiz = consSitNFe.TConsSitNFe(
            versao='4.00',
            tpAmb='2',
            xServ='CONSULTAR',
            chNFe=chave,
        )
        raiz.original_tagname_ = 'consSitNFe'
        return self._post(
            raiz,
            # 'https://hom.sefazvirtual.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx?wsdl',
            'nfeConsultaNF',
            retConsSitNFe
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
            xml_etree, edoc.infNFe.Id
        )

        raiz = enviNFe.TEnviNFe(
            versao='4.00',
            idLote=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            indSinc='0'
        )
        raiz.original_tagname_ = 'enviNFe'
        xml_envio_string, xml_envio_etree = self._generateds_to_string_etree(
            raiz
        )
        xml_envio_etree.append(etree.fromstring(xml_assinado))

        # teste_string, teste_etree = self._generateds_to_string_etree(xml_envio_etree)

        return self._post(
            xml_envio_etree,
            # 'https://hom.sefazvirtual.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx?wsdl',
            'nfeAutorizacaoLote',
            retEnviNFe
        )

    def consulta_recibo(self, numero):
        raiz = consReciNFe.TConsReciNFe(
            versao='4.00',
            tpAmb='2',
            nRec=numero,
        )
        raiz.original_tagname_ = 'consReciNFe'
        return self._post(
            raiz,
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx?wsdl', #'ws/nferetautorizacao4.asmx'
            'nfeRetAutorizacaoLote',
            retConsReciNFe,
        )

    def cancela_documento(self):
        pass
