# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import time

from erpbrasil.edoc.edoc import DocumentoEletronico
from erpbrasil.edoc.resposta import analisar_retorno

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


ServicoNFSe = collections.namedtuple(
    'ServicoNFSe', ['operacao', 'endpoint', 'classe_retorno', 'assinar']
)


class NFSe(DocumentoEletronico):
    _consulta_servico_ao_enviar = False
    _maximo_tentativas_consulta_recibo = 10
    _tempo_medio = 1
    _header = False
    _namespace = False

    _edoc_situacao_arquivo_recebido_com_sucesso = "TODO"
    _edoc_situacao_em_processamento = "TODO"
    _edoc_situacao_servico_em_operacao = "TODO"

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):
        self.ambiente = ambiente
        self.cidade = cidade_ibge
        self.cnpj_prestador = cnpj_prestador
        self.im_prestador = im_prestador
        super(NFSe, self).__init__(transmissao)

    def _post(self, body, servico):
        header_string = None
        if self._header:
            header_string, header_etree = self._generateds_to_string_etree(
                self._header
            )

        body_string, body_etree = self._generateds_to_string_etree(body)

        # TODO: Verificar impacto para outros provedores
        header = body_etree.find("Cabecalho")

        if header and header.attrib:
            header_string = header.attrib.get('Versao')

        if header_string:
            with self._transmissao.cliente(
                    urljoin(self._url, servico.endpoint)) as cliente:
                resposta = cliente.service[servico.operacao](
                    header_string,
                    body_string,
                )
        else:
            with self._transmissao.cliente(
                    urljoin(self._url, servico.endpoint)) as cliente:
                resposta = cliente.service[servico.operacao](
                    body_string,
                )

        return analisar_retorno(
            servico.operacao,
            body,
            body_string,
            resposta,
            servico.classe_retorno
        )

    def _aguarda_tempo_medio(self, proc_envio):
        time.sleep(self._tempo_medio)

    def envia_documento(self, edoc):
        return self._post(
            body=self._prepara_envia_documento(edoc),
            servico=self._servicos[self.envia_documento.__name__]
        )

    def consulta_recibo(self, proc_envio):
        return self._post(
            body=self._prepara_consulta_recibo(proc_envio),
            servico=self._servicos[self.consulta_recibo.__name__],
        )

    def consultar_lote_rps(self, protocolo):
        return self._post(
            body=self._prepara_consultar_lote_rps(protocolo),
            servico=self._servicos[self.consultar_lote_rps.__name__],
        )

    def cancela_documento(self, doc_numero):
        return self._post(
            body=self._prepara_cancelar_nfse_envio(doc_numero),
            servico=self._servicos[self.cancela_documento.__name__],
        )

    def _edoc_situacao_ja_enviado(self, proc_consulta):
        return False

    def _verifica_servico_em_operacao(self, proc_servico):
        return True

    def status_servico(self):
        pass

    def consulta_documento(self, chave):
        pass

    def consulta_nfse_rps(self, **kwargs):
        return self._post(
            body=self._prepara_consultar_nfse_rps(**kwargs),
            servico=self._servicos[self.consulta_nfse_rps.__name__],
        )
