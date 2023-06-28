# coding=utf-8
# Copyright (C) 2023  André Marcos Ferreira - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from erpbrasil.assinatura.assinatura import Assinatura
from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico

try:
    # Pedido de Consulta MDF-e Não Encerrados
    from nfelib.mdfe.bindings.v3_0 import TconsMdfeNaoEnc
    from nfelib.mdfe.bindings.v3_0 import TretConsMdfeNaoEnc

    # Pedido de Consulta do Recibo do MDF-e
    from nfelib.mdfe.bindings.v3_0 import TconsReciMdfe
    from nfelib.mdfe.bindings.v3_0 import TretConsReciMdfe

    # Pedido de Consulta da Situação Atual do MDF-e
    from nfelib.mdfe.bindings.v3_0 import TconsSitMdfe
    from nfelib.mdfe.bindings.v3_0 import TretConsSitMdfe

    # Consulta status do Serviço MDFe
    from nfelib.mdfe.bindings.v3_0 import TconsStatServ
    from nfelib.mdfe.bindings.v3_0 import TretConsStatServ

    # Pedido de Autorização Assíncrona de MDF-e
    from nfelib.mdfe.bindings.v3_0 import TenviMdfe
    from nfelib.mdfe.bindings.v3_0 import TretEnviMdfe
    
except ImportError:
    pass

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
        raiz = TconsStatServ(
            versao='4.00',
            tpAmb='2',
            xServ='STATUS',
        )
        raiz.original_tagname_ = 'TconsStatServ'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/wws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl',
            'nfeStatusServicoNF',
            TretConsStatServ
        )
    
    def consulta_documento(self, chave):
        raiz = TconsSitMdfe(
            versao='4.00',
            tpAmb='2',
            xServ='CONSULTAR',
            chMDFe=chave,
        )
        raiz.original_tagname_ = 'TconsSitMdfe'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeConsulta/MDFeConsulta.asmx?wsdl',
            'MDFeConsultaNF',
            TretConsSitMdfe
        )
    
    def consulta_nao_encerrados(self, cnpj):
        raiz = TconsMdfeNaoEnc(
            versao=self._versao,
            tpAmb=str(self._ambiente),
            xServ='CONSULTAR NÃO ENCERRADOS',
            CNPJ=cnpj,
        )
        raiz.original_tagname_ = 'TconsMdfeNaoEnc'

        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl',
            'mdfeConsNaoEnc',
            TretConsMdfeNaoEnc,
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

        raiz = TenviMdfe(
            versao='4.00',
            idLote=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
        )
        raiz.original_tagname_ = 'TenviMdfe'
        xml_envio_string, xml_envio_etree = self._generateds_to_string_etree(
            raiz
        )
        xml_envio_etree.append(etree.fromstring(xml_assinado))

        return self._post(
            xml_envio_etree,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFerecepcao/MDFeRecepcao.asmx?wsdl',
            'mdfeRecepcaoLote',
            TretEnviMdfe
        )
    
    def consulta_recibo(self, numero):
        raiz = TconsReciMdfe(
            versao='4.00',
            tpAmb='2',
            nRec=numero,
        )
        raiz.original_tagname_ = 'TconsReciMdfe'
        return self._post(
            raiz,
            'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl',  # 'ws/MDFeretautorizacao4.asmx'
            'mdfeRetRecepcao',
            TretConsReciMdfe,
        )

    def cancela_documento(self, numero, justificativa):
        pass
        #TODO não encontrado o link de cancelamento no https://dfe-portal.svrs.rs.gov.br/Mdfe/Servicos#topo
        # raiz  = EvCancMdfe(
        #     nProt=numero,
        #     xJust=justificativa
        # )
        # raiz.original_tagname_ = 'EvCancMdfe'
        # return self._post(
        #     raiz,
        #     'https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeRetRecepcao/.asmx?wsdl',  # 'ws/MDFeretautorizacao4.asmx'
        #     'mdfeRetRecepcao',
        #     TconsReciMdfe,
        # )
        