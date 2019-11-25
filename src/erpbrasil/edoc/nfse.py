# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.edoc import DocumentoEletronico
from nfselib.v3_01 import servico_enviar_lote_rps_resposta_v03
from nfselib.v3_01.cabecalho_v03 import cabecalho


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class NFSe(DocumentoEletronico):
    _namespace = "TODO"
    _edoc_situacao_arquivo_recebido_com_sucesso = "TODO"
    _edoc_situacao_em_processamento = "TODO"
    _edoc_situacao_servico_em_operacao = "TODO"
    _consulta_servico_ao_enviar = False
    _maximo_tentativas_consulta_recibo = 5
    _header = cabecalho(versao="3", versaoDados="3")

    def _edoc_situacao_ja_enviado(self, proc_consulta):
        _edoc_situacao_ja_enviado = "TODO"
        return False

    def _verifica_servico_em_operacao(self, proc_servico):
        return True

    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.Id
        return edoc.LoteRps.Id, edoc.LoteRps.NumeroLote

    def status_servico(self):
        pass

    def envia_documento(self, edoc):
        numero_lote = self._gera_numero_lote()

        edoc.LoteRps.Id = numero_lote
        edoc.LoteRps.NumeroLote = numero_lote

        xml_assinado = self.assina_raiz(edoc, edoc.LoteRps.Id)

        header_string, header_etree = self._generateds_to_string_etree(
            self._header
        )

        return self._post(
            xml_assinado,
            'https://homologacao.ginfes.com.br/ServiceGinfesImpl?wsdl',
            'RecepcionarLoteRpsV3',
            servico_enviar_lote_rps_resposta_v03,
        )

    def cancela_documento(self):
        pass

    def consulta_documento(self, chave):
        pass

    def consulta_recibo(self):
        pass
