# coding=utf-8
# Copyright (C) 2020 - TODAY, Marcel Savegnago - Escodoo

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_envio as consulta_situacao_lote
from nfselib.issnet.v1_00 import servico_consultar_lote_rps_envio as servico_consultar_lote_rps_envio
from nfselib.issnet.v1_00 import servico_enviar_lote_rps_resposta as servico_enviar_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_resposta as servico_consultar_situacao_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_consultar_lote_rps_resposta as servico_consultar_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_cancelar_nfse_envio as servico_cancelar_nfse_envio
# from nfselib.issnet.v1_00.cabecalho import cabecalho
from nfselib.issnet.v1_00.tipos_complexos import tcIdentificacaoPrestador
from nfselib.issnet.v1_00.tipos_complexos import tcPedidoCancelamento, tcInfPedidoCancelamento, tcIdentificacaoNfse, tcCpfCnpj


endpoint = '/webserviceabrasf/homologacao/servicos.asmx?WSDL'

servicos = {
    'envia_documento': ServicoNFSe(
        'RecepcionarLoteRps',
        endpoint, servico_enviar_lote_rps_resposta, True),
    'consulta_recibo': ServicoNFSe(
        'ConsultarSituacaoLoteRps',
        endpoint, servico_consultar_situacao_lote_rps_resposta, True),
    'consultar_lote_rps': ServicoNFSe(
        'ConsultarLoteRps',
        endpoint, servico_consultar_lote_rps_resposta, True),
    'cancela_documento': ServicoNFSe(
        'CancelarNfse',
        endpoint, servico_cancelar_nfse_envio, True),
}


class Issnet(NFSe):

    #_header = cabecalho(versao="1", versaoDados="1")
    _header = None

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):

        if ambiente == '2':
            self._url = 'http://www.issnetonline.com.br'
        else:
            self._url = 'http://www.issnetonline.com.br'
        self._servicos = servicos

        super(Issnet, self).__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)

    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.id
        return edoc.LoteRps.id, edoc.LoteRps.NumeroLote

    def _prepara_envia_documento(self, edoc):
        numero_lote = '202000000000001' #self._gera_numero_lote()
        edoc.LoteRps.id = 'L' + numero_lote
        edoc.LoteRps.NumeroLote = numero_lote
        #
        # Assinamos todas as RPS e o Lote
        #
        xml_assinado = edoc
        # for rps in edoc.LoteRps.ListaRps.Rps:
        #     xml_assinado = self.assin a_raiz(xml_assinado, rps.InfRps.id, getchildren=True)
        # Assinamos o lote
        # xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.id)

        for rps in edoc.LoteRps.ListaRps.Rps:
            xml_assinado = self.assina_raiz(xml_assinado, rps.InfRps.id)
        # Assinamos o lote
        xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.id, getchildren=True)

        return xml_assinado

    def _prepara_consulta_recibo(self, proc_envio):
        raiz = consulta_situacao_lote.ConsultarSituacaoLoteRpsEnvio(
            # id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.cnpj_prestador,
                ),
                InscricaoMunicipal=self.im_prestador
            ),
            Protocolo=proc_envio.resposta.Protocolo
        )
        xml_assinado = self.assina_raiz(raiz,"")
        return xml_assinado

    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = servico_consultar_lote_rps_envio.ConsultarLoteRpsEnvio(
            id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.cnpj_prestador,
                ),
                InscricaoMunicipal=self.im_prestador
            ),
            Protocolo=protocolo
        )
        xml_assinado = self.assina_raiz(raiz, raiz.id)
        return xml_assinado

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.Protocolo:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.Situacao == 2:
            return True
        return False

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        raiz = servico_cancelar_nfse_envio.CancelarNfseEnvio(
            Pedido=tcPedidoCancelamento(
                InfPedidoCancelamento=tcInfPedidoCancelamento(
                    id=doc_numero,
                    IdentificacaoNfse=tcIdentificacaoNfse(
                        Numero=doc_numero,
                        CpfCnpj=tcCpfCnpj(
                            Cnpj=self.cnpj_prestador,
                        ),
                        InscricaoMunicipal=self.im_prestador,
                        Cidade=self.cidade
                    ),
                    CodigoCancelamento='0001'
                )
            )
        )
        xml_assinado = self.assina_raiz(raiz, '')

        return xml_assinado

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
