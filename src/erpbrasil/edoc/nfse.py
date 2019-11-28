# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

import time

from erpbrasil.edoc.edoc import DocumentoEletronico
from nfselib.ginfes.v3_01 import servico_enviar_lote_rps_resposta_v03
from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_resposta_v03
from nfselib.ginfes.v3_01.cabecalho_v03 import cabecalho
from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_envio_v03 as consulta_situacao_lote
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_envio_v03 as servico_consultar_lote_rps_envio
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_resposta_v03 as servico_consultar_lote_rps_resposta
from nfselib.ginfes.v3_01.tipos_v03 import tcIdentificacaoPrestador
from .resposta import analisar_retorno


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
        edoc.LoteRps.Id = 'lote' + numero_lote
        edoc.LoteRps.NumeroLote = numero_lote
        #
        # Assinamos todas as RPS e o Lote
        #
        xml_assinado = edoc
        for rps in edoc.LoteRps.ListaRps.Rps:
            xml_assinado = self.assina_raiz(xml_assinado, rps.InfRps.Id)
        # Assinamos o lote
        xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.Id)

        return self._post(
            body=xml_assinado,
            url='https://homologacao.ginfes.com.br/ServiceGinfesImpl?wsdl',
            operacao='RecepcionarLoteRpsV3',
            classe_retorno=servico_enviar_lote_rps_resposta_v03,
            header=self._header
        )

    def cancela_documento(self):
        pass

    def consulta_documento(self, chave):
        pass

    def consulta_recibo(self):
        pass

    def _post(self, url, operacao, classe_retorno, body, header):

        body_string, body_etree = self._generateds_to_string_etree(body)
        header_string, header_etree = self._generateds_to_string_etree(header)

        with self._transmissao.cliente(url)as cliente:
            resposta = cliente.service[operacao](
                header_string,
                body_string,
            )
        return analisar_retorno(
            operacao, body, body_string, resposta, classe_retorno
        )

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.Protocolo:
            return True
        return False

    def _aguarda_tempo_medio(self, proc_envio):
        time.sleep(1)

    def consulta_recibo(self, proc_envio):
        raiz = consulta_situacao_lote.ConsultarSituacaoLoteRpsEnvio(
            Id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                Cnpj='23130935000198',
                InscricaoMunicipal='35172'
            ),
            Protocolo=proc_envio.resposta.Protocolo
        )
        xml_assinado = self.assina_raiz(raiz,raiz.Id)
        return self._post(
            body=xml_assinado,
            url='https://homologacao.ginfes.com.br/ServiceGinfesImpl?wsdl',
            operacao='ConsultarSituacaoLoteRpsV3',
            classe_retorno=servico_consultar_situacao_lote_rps_resposta_v03,
            header=self._header
        )

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.Situacao == 2:
            return True
        return False

    def consultar_lote_rps(self, protocolo):
        raiz = servico_consultar_lote_rps_envio.ConsultarLoteRpsEnvio(
            Id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                Cnpj='23130935000198',
                InscricaoMunicipal='35172'
            ),
            Protocolo=protocolo
        )
        xml_assinado = self.assina_raiz(raiz, raiz.Id)
        return self._post(
            body=xml_assinado,
            url='https://homologacao.ginfes.com.br/ServiceGinfesImpl?wsdl',
            operacao='ConsultarLoteRpsV3',
            classe_retorno=servico_consultar_lote_rps_resposta,
            header=self._header
        )
