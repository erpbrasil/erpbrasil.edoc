# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import abc
import time
from datetime import datetime
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

    def __init__(self, transmissao):
        self._transmissao = transmissao

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
        with self._transmissao.cliente(url):
            retorno = self._transmissao.enviar(
                operacao, xml_etree
            )
            return analisar_retorno(
                operacao, raiz, xml_string, retorno, classe
            )

    def processar_documento(self, edoc):
        """ Processar documento executa o envio do documento fiscal de forma
        completa ao serviço do sefaz relacionado, esta é um método padrão que
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

    def _gera_numero_lote(self):
        return datetime.now().strftime('%Y%m%d%H%M%S')

    def _hora_agora(self):
        FORMAT = '%Y-%m-%dT%H:%M:%S'
        # return datetime.today().strftime(FORMAT) + '-00:00'
        return time.strftime(FORMAT, time.localtime()) + '-00:00'


