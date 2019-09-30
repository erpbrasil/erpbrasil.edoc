# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import abc
import time
from .resposta import analisar_retorno
from requests import Session

from lxml import etree
from lxml.etree import _Element
from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.transmissao import TransmissaoSOAP

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

ABC = abc.ABCMeta('ABC', (object,), {})


class DocumentoEletronico(ABC):
    """
    Classe abstrata responsavel por definir os metodos e logica das classes
    de transmissao com os webservices.
    """

    consulta_servico_ao_enviar = True

    def _generateds_to_string_etree(self, ds):

        if type(ds) == _Element:
            return etree.tostring(ds), ds

        output = StringIO()
        ds.export(
            output,
            0,
            pretty_print=False,
            namespacedef_='xmlns="' + self._namespace + '"'
        )
        contents = output.getvalue()
        output.close()
        return contents, etree.fromstring(contents)

    def _post(self, raiz, url, operacao, classe):
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        with self.transmissao.cliente(url):
            retorno = self.transmissao.enviar(
                operacao, xml_etree
            )
            return analisar_retorno(
                operacao, raiz, xml_string, retorno, classe
            )

    def processar_documento(self, edoc):
        if self._consulta_servico_ao_enviar:
            proc_servico = self.status_servico()
            yield proc_servico
            #
            # Se o serviço não estiver em operação
            #
            if not proc_servico.resposta.cStat == \
                   self._edoc_situacao_servico_em_operacao:
                #
                # Interrompe todo o processo
                #
                return
        #
        # Verificar se os documentos já não foram emitados antes
        #
        documento, chave = self.get_documento_id(edoc)
        if not chave:
            #
            # Interrompe todo o processo se o documento nao tem chave
            #
            return

        proc_consulta = self.consulta_documento(chave)
        yield proc_consulta

        #
        # Se o documento já constar na SEFAZ (autorizada ou denegada)
        #
        if proc_consulta.resposta.cStat in self._edoc_situacao_ja_enviado:
            #
            # Interrompe todo o processo
            #
            return
        #
        # Documento nao foi enviado, entao vamos envia-lo
        #

        proc_envio = self.envia_documento(edoc)
        yield proc_envio

        #
        # Deu errado?
        #
        if proc_envio.resposta.cStat != \
            self._edoc_situacao_arquivo_recebido_com_sucesso:
            #
            # Interrompe o processo
            #
            return

        #
        # Aguarda o tempo do processamento antes da consulta
        #
        time.sleep(float(proc_envio.resposta.infRec.tMed) * 1.3)

        #
        # Consulta o recibo do lote, para ver o que aconteceu
        #
        proc_recibo = self.consulta_recibo(proc_envio.resposta.infRec.nRec)

        #
        # Tenta receber o resultado do processamento do lote, caso ainda
        # esteja em processamento
        #
        tentativa = 0
        while (proc_recibo.resposta.cStat ==
               self._edoc_situacao_em_processamento and
               tentativa < self.maximo_tentativas_consulta_recibo):
            time.sleep(proc_envio.resposta.infRec.tMed * 1.5)
            tentativa += 1
            #
            # Consulta o recibo do lote, para ver o que aconteceu
            #
            proc_recibo = self.consulta_recibo(
                proc_envio.resposta.infRec.nRec
            )
        yield proc_recibo


    @abc.abstractmethod
    def status_servico(self):
        pass

    @abc.abstractmethod
    def envia_documento(self):
        pass

    @abc.abstractmethod
    def cancela_documento(self):
        pass

    @abc.abstractmethod
    def consulta_documento(self):
        pass

    @abc.abstractmethod
    def consulta_recibo(self):
        pass
