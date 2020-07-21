# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import abc
import time
from datetime import datetime
from .resposta import analisar_retorno_raw
from requests import Session

from lxml import etree
from lxml.etree import _Element
from erpbrasil.assinatura.assinatura import Assinatura

# Fix Python 2.x.
try:
    UNICODE_EXISTS = bool(type(unicode))
except NameError:
    unicode = str

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
    _consulta_servico_ao_enviar = False
    _consulta_documento_antes_de_enviar = False

    def __init__(self, transmissao):
        self._transmissao = transmissao

    def _generateds_to_string_etree(self, ds, pretty_print=False):

        if type(ds) == _Element:
            return etree.tostring(ds), ds
        if isinstance(ds, str):
            return ds, etree.fromstring(ds)
        # if isinstance(ds, unicode):
        #     return ds, etree.fromstring(ds)

        output = StringIO()
        namespace=False
        if self._namespace:
            namespace = 'xmlns="' + self._namespace + '"'

        if namespace:
            ds.export(
                output,
                0,
                pretty_print=pretty_print,
                namespacedef_=namespace
            )
        else:
            ds.export(
                output,
                0,
                pretty_print=pretty_print,
            )
        contents = output.getvalue()
        output.close()
        return contents, etree.fromstring(contents)

    def _post(self, raiz, url, operacao, classe):
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        with self._transmissao.cliente(url):
            retorno = self._transmissao.enviar(
                operacao, xml_etree
            )
            return analisar_retorno_raw(
                operacao, raiz, xml_string, retorno, classe
            )

    def processar_documento(self, edoc):
        """ Processar documento executa o envio do documento fiscal de forma
        completa ao serviço relacionado, esta é um método padrão que
        segue o seguinte workflow:

        1. Consulta o serviço;
        2. Verifica se o documento não foi emitido anteriormente;
        3. Envia o documento
        4. Caso o envio seja assincrono busca o resultado do processamento
            - Caso o processamento ainda não tenha sido efetuado,
            aguarda o tempo médio + 50% e tenta o máximo setado no atributo
            'maximo_tentativas_consulta_recibo'
        5. Retorna o resultado.

        Caro você queira armazenar todas as consultas em seu ERP segue o
        exemplo:
                for edoc in self.serialize():
                    nfe = NFe()
                    processo = None
                    for p in nfe.processar_documento(edoc):
                        # seu código aqui

        :param edoc:
        :return: Esta função retorna um yield, portanto ela retorna um iterator

        """
        if self._consulta_servico_ao_enviar:
            proc_servico = self.status_servico()
            yield proc_servico
            #
            # Se o serviço não estiver em operação
            #
            if not self._verifica_servico_em_operacao(proc_servico):
                #
                # Interrompe todo o processo
                #
                return
        #
        # Verificar se os documentos já não foram emitados antes
        #
        if self._consulta_documento_antes_de_enviar:
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
            if self._verifica_documento_ja_enviado(proc_consulta):
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
        if not proc_envio.resposta:
            return

        if not self._verifica_resposta_envio_sucesso(proc_envio):
            #
            # Interrompe o processo
            #
            return

        #
        # Aguarda o tempo do processamento antes da consulta
        #
        self._aguarda_tempo_medio(proc_envio)
        #
        # Consulta o recibo do lote, para ver o que aconteceu
        #
        proc_recibo = self.consulta_recibo(proc_envio=proc_envio)

        if not proc_recibo.resposta:
            return

        #
        # Tenta receber o resultado do processamento do lote, caso ainda
        # esteja em processamento
        #
        tentativa = 0
        while (self._edoc_situacao_em_processamento(proc_recibo) and
               tentativa < self._maximo_tentativas_consulta_recibo):
            self._aguarda_tempo_medio(proc_envio)
            tentativa += 1
            #
            # Consulta o recibo do lote, para ver o que aconteceu
            #
            proc_recibo = self.consulta_recibo(proc_envio=proc_envio)
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

    def _gera_numero_lote(self):
        return datetime.now().strftime('%Y%m%d%H%M%S')

    def _hora_agora(self):
        FORMAT = '%Y-%m-%dT%H:%M:%S'
        # return datetime.today().strftime(FORMAT) + '-00:00'
        return time.strftime(FORMAT, time.localtime()) + '-00:00'

    def assina_raiz(self, raiz, id, getchildren=False):
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        xml_assinado = Assinatura(self._transmissao.certificado).assina_xml2(
            xml_etree, id, getchildren
        )
        return xml_assinado
        return xml_assinado.replace('\n', '').replace('\r', '')

    def _verifica_servico_em_operacao(self, proc_servico):
        return True

    def _verifica_documento_ja_enviado(self, proc_consulta):
        return False
