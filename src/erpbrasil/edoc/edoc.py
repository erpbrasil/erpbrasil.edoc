# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import abc
import warnings
from dataclasses import is_dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from lxml import etree
from lxml.etree import _Element

from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig

from .resposta import analisar_retorno_raw

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
        warnings.warn(
            "A função `_generateds_to_string_etree` está obsoleta e "
            "será removida em versões futuras. "
            "Por favor, substitua o uso desta função por `_render_edoc()`. ",
            DeprecationWarning
        )
        return self._render_edoc(ds, pretty_print)

    def _render_edoc(self, edoc, pretty_print=False):

        if type(edoc) == _Element:
            return etree.tostring(edoc), edoc
        if isinstance(edoc, str):
            return edoc, etree.fromstring(edoc)
        # if isinstance(edoc, unicode):
        #     return edoc, etree.fromstring(edoc)

        # XSDATA
        if is_dataclass(edoc):
            serializer = XmlSerializer(config=SerializerConfig(pretty_print=pretty_print))
            if self._namespace:
                ns_map = {None: self._namespace}
            else:
                ns_map = None
            xml_string = serializer.render(obj=edoc, ns_map=ns_map)
            return xml_string, etree.fromstring(xml_string.encode('utf-8'))

        # GenereteDS
        # ======= Aviso de Obsolescência =======
        # Este bloco de código será removido em uma versão futura.
        # Certifique-se de atualizar para as alternativas recomendadas.

        output = StringIO()
        namespace = False
        if self._namespace:
            namespace = 'xmlns="' + self._namespace + '"'

        if namespace:
            edoc.export(
                output,
                0,
                pretty_print=pretty_print,
                namespacedef_=namespace
            )
        else:
            edoc.export(
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
        self.monta_processo(edoc, proc_envio, proc_recibo)
        yield proc_recibo

    @abc.abstractmethod
    def status_servico(self):
        pass

    @abc.abstractmethod
    def envia_documento(self):
        pass

    @abc.abstractmethod
    def cancela_documento(self, doc_numero):
        proc_cancela = self.cancela_documento(doc_numero)
        yield proc_cancela

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
        return datetime.strftime(
            datetime.now(tz=timezone(timedelta(hours=-3))), FORMAT
        ) + str(timezone(timedelta(hours=-3)))[3:]

    def _data_hoje(self):
        return datetime.strftime(datetime.now(), "%Y-%m-%d")

    def assina_raiz(self, raiz, id, getchildren=False):
        xml_string, xml_etree = self._render_edoc(raiz)
        xml_assinado = Assinatura(self._transmissao.certificado).assina_xml2(
            xml_etree, id, getchildren
        )
        return xml_assinado.replace('\n', '').replace('\r', '')

    def _verifica_servico_em_operacao(self, proc_servico):
        return True

    def _verifica_documento_ja_enviado(self, proc_consulta):
        return False

    def monta_processo(self, edoc, proc_envio, proc_recibo):
        return True
