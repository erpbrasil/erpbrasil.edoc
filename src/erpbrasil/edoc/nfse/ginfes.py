# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_envio_v03 as consulta_situacao_lote
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_envio_v03 as servico_consultar_lote_rps_envio
from nfselib.ginfes.v3_01 import servico_enviar_lote_rps_resposta_v03 as servico_enviar_lote_rps_resposta
from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_resposta_v03 as servico_consultar_situacao_lote_rps_resposta
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_resposta_v03 as servico_consultar_lote_rps_resposta
from nfselib.ginfes.v3_01.cabecalho_v03 import cabecalho
from nfselib.ginfes.v3_01.tipos_v03 import tcIdentificacaoPrestador


endpoint = 'ServiceGinfesImpl?wsdl'

servicos = {
    'envia_documento': ServicoNFSe(
        'RecepcionarLoteRpsV3',
        endpoint, servico_enviar_lote_rps_resposta, True),
    'consulta_recibo': ServicoNFSe(
        'ConsultarSituacaoLoteRpsV3',
        endpoint, servico_consultar_situacao_lote_rps_resposta, True),
    'consultar_lote_rps': ServicoNFSe(
        'ConsultarLoteRpsV3',
        endpoint, servico_consultar_lote_rps_resposta, True),
}


class Ginfes(NFSe):

    _header = cabecalho(versao="3", versaoDados="3")

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):

        if ambiente == '2':
            self._url = 'https://homologacao.ginfes.com.br'
        else:
            self._url = 'https://producao.ginfes.com.br'
        self._servicos = servicos

        super(Ginfes, self).__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)

    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.Id
        return edoc.LoteRps.Id, edoc.LoteRps.NumeroLote

    def _prepara_envia_documento(self, edoc):
        numero_lote = self._gera_numero_lote()
        edoc.LoteRps.Id = 'lote' + numero_lote
        edoc.LoteRps.NumeroLote = numero_lote
        #
        # Assinamos todas as RPS e o Lote
        #
        xml_assinado = edoc
        # for rps in edoc.LoteRps.ListaRps.Rps:
        #     xml_assinado = self.assin a_raiz(xml_assinado, rps.InfRps.Id, getchildren=True)
        # Assinamos o lote
        # xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.Id)

        for rps in edoc.LoteRps.ListaRps.Rps:
            xml_assinado = self.assina_raiz(xml_assinado, rps.InfRps.Id)
        # Assinamos o lote
        # xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.Id)

        return xml_assinado

    def _prepara_consulta_recibo(self, proc_envio):

        raiz = consulta_situacao_lote.ConsultarSituacaoLoteRpsEnvio(
            # Id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                Cnpj=self.cnpj_prestador,
                InscricaoMunicipal=self.im_prestador
            ),
            Protocolo=proc_envio.resposta.Protocolo
        )
        xml_assinado = self.assina_raiz(raiz,"")
        return xml_assinado

    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = servico_consultar_lote_rps_envio.ConsultarLoteRpsEnvio(
            Id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                Cnpj=self.cnpj_prestador,
                InscricaoMunicipal=self.im_prestador
            ),
            Protocolo=protocolo
        )
        xml_assinado = self.assina_raiz(raiz, raiz.Id)
        return xml_assinado

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.Protocolo:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.Situacao == 2:
            return True
        return False

    # def processar_documento(self, edoc):
    #     processo = super(NFSe, self).processar_documento(edoc)
    #
    #     ultimo_processo = None
    #     for p in processo:
    #         ultimo_processo = p
    #
    #     if ultimo_processo.webservice == u'ConsultarSituacaoLoteRpsV3':
    #         if processo.resposta.Situacao == 1:
    #             print('Não Recebido')
    #
    #         elif ultimo_processo.resposta.Situacao == 2:
    #             print('Lote ainda não processado')
    #
    #         elif ultimo_processo.resposta.Situacao == 3:
    #             print('Procesado com Erro')
    #
    #         elif ultimo_processo.resposta.Situacao == 4:
    #             print('Procesado com Sucesso')
    #
