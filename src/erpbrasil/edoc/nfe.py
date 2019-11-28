# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

import re
from datetime import datetime
import time
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
from nfelib.v4_00 import leiauteEvento
from nfelib.v4_00 import leiauteEventoCancNFe
from nfelib.v4_00 import leiauteCCe
from nfelib.v4_00 import retEnvEvento
from erpbrasil.edoc.edoc import DocumentoEletronico

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

TEXTO_CARTA_CORRECAO = """A Carta de Correcao e disciplinada pelo paragrafo \
1o-A do art. 7o do Convenio S/N, de 15 de dezembro de 1970 e \
pode ser utilizada para regularizacao de erro ocorrido na \
emissao de documento fiscal, desde que o erro nao esteja \
relacionado com: I - as variaveis que determinam o valor do \
imposto tais como: base de calculo, aliquota, diferenca de \
preco, quantidade, valor da operacao ou da prestacao; II - \
a correcao de dados cadastrais que implique mudanca do \
remetente ou do destinatario; III - a data de emissao \
ou de saida."""


class NFe(DocumentoEletronico):
    _namespace = 'http://www.portalfiscal.inf.br/nfe'
    _edoc_situacao_arquivo_recebido_com_sucesso = '103'
    _edoc_situacao_servico_em_operacao = '107'
    _consulta_servico_ao_enviar = True
    _consulta_documento_antes_de_enviar = True
    _maximo_tentativas_consulta_recibo = 5

    def __init__(self, transmissao, uf, versao='4.00', ambiente='2'):
        super(NFe, self).__init__(transmissao)
        self.versao = str(versao)
        self.ambiente = str(ambiente)
        self.uf = int(uf)

    def _edoc_situacao_ja_enviado(self, proc_consulta):
        if proc_consulta.resposta.cStat in ('100', '110', '150', '301', '302'):
            return True
        return False

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
        xml_assinado = self.assina_raiz(edoc, edoc.infNFe.Id)

        raiz = enviNFe.TEnviNFe(
            versao='4.00',
            idLote=datetime.now().strftime('%Y%m%d%H%M%S'),
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

    def consulta_recibo(self, numero=False, proc_envio=False):
        if proc_envio:
            numero = proc_envio.resposta.infRec.nRec

        if not numero:
            return

        raiz = consReciNFe.TConsReciNFe(
            versao='4.00',
            tpAmb='2',
            nRec=numero,
        )
        raiz.original_tagname_ = 'consReciNFe'
        return self._post(
            raiz,
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nferetautorizacao4.asmx?wsdl',
            # 'ws/nferetautorizacao4.asmx'
            'nfeRetAutorizacaoLote',
            retConsReciNFe,
        )

    def enviar_lote_evento(self, lista_eventos, numero_lote=False):
        if not numero_lote:
            numero_lote = self._gera_numero_lote()

        raiz = leiauteEvento.TEnvEvento(versao="1.00",idLote=numero_lote)
        raiz.original_tagname_ = 'envEvento'
        xml_envio_string, xml_envio_etree = self._generateds_to_string_etree(
            raiz
        )

        for raiz_evento in lista_eventos:
            evento = leiauteEventoCancNFe.TEvento(
                versao="1.00", infEvento=raiz_evento,
            )
            evento.original_tagname_ = 'evento'
            xml_assinado = self.assina_raiz(evento, evento.infEvento.Id)
            xml_envio_etree.append(etree.fromstring(xml_assinado))

        return self._post(
            xml_envio_etree,
            'https://homologacao.nfe.fazenda.sp.gov.br/ws/nferecepcaoevento4.asmx?WSDL',
            'nfeRecepcaoEvento',
            retEnvEvento
        )

    def cancela_documento(self, chave, protocolo_autorizacao, justificativa,
                          data_hora_evento=False):
        tipo_evento = '110111'
        sequencia = '1'
        raiz = leiauteEventoCancNFe.infEventoType(
            Id='ID' + tipo_evento + chave + sequencia.zfill(2),
            cOrgao=35,
            tpAmb='2',
            CNPJ=chave[6:20],
            chNFe=chave,
            dhEvento=data_hora_evento or self._hora_agora(),
            tpEvento='110111',
            nSeqEvento='1',
            verEvento='1.00',
            detEvento=leiauteEventoCancNFe.detEventoType(
                versao="1.00",
                descEvento='Cancelamento',
                nProt=protocolo_autorizacao,
                xJust=justificativa
            ),
        )
        raiz.original_tagname_ = 'infEvento'
        return raiz

    def carta_correcao(self, chave, sequencia, justificativa,
                       data_hora_evento=False):
        tipo_evento = '110110'
        raiz = leiauteCCe.infEventoType(
            Id='ID' + tipo_evento + chave + sequencia.zfill(2),
            cOrgao=35,
            tpAmb='2',
            CNPJ=chave[6:20],
            # CPF=None,
            chNFe=chave,
            dhEvento=data_hora_evento or self._hora_agora(),
            tpEvento=tipo_evento,
            nSeqEvento=sequencia,
            verEvento='1.00',
            detEvento=leiauteCCe.detEventoType(
                versao="1.00",
                descEvento='Carta de Correcao',
                xCorrecao=justificativa,
                xCondUso=TEXTO_CARTA_CORRECAO,
            ),
        )
        raiz.original_tagname_ = 'infEvento'
        return raiz

    def _verifica_servico_em_operacao(self, proc_servico):
        if proc_servico.resposta.cStat == \
                self._edoc_situacao_servico_em_operacao:
            return True
        return False

    def _verifica_documento_ja_enviado(self, proc_consulta):
        if proc_consulta.resposta.cStat in ('100', '110', '150', '301', '302'):
            return True
        return False

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.cStat == \
                self._edoc_situacao_arquivo_recebido_com_sucesso:
            return True
        return False

    def _aguarda_tempo_medio(self, proc_envio):
        time.sleep(float(proc_envio.resposta.infRec.tMed) * 1.3)

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.cStat == '105':
            return True
        return False
