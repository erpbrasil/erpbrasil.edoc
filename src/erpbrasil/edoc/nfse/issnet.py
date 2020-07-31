# coding=utf-8
# Copyright (C) 2020 - TODAY, Marcel Savegnago - Escodoo

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

# from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_envio_v03 as consulta_situacao_lote
# from nfselib.issnet.v1_00 import servico_consultar_lote_rps_envio_v03 as servico_consultar_lote_rps_envio
# from nfselib.issnet.v1_00 import servico_enviar_lote_rps_resposta_v03 as servico_enviar_lote_rps_resposta
# from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_resposta_v03 as servico_consultar_situacao_lote_rps_resposta
# from nfselib.issnet.v1_00 import servico_consultar_lote_rps_resposta_v03 as servico_consultar_lote_rps_resposta
# from nfselib.issnet.v1_00.cabecalho_v03 import cabecalho
# from nfselib.issnet.v1_00.tipos_v03 import tcIdentificacaoPrestador

from nfselib.issnet.v1_00.nfse import ConsultarSituacaoLoteRpsEnvio as consultar_situacao_lote
from nfselib.issnet.v1_00.nfse import ConsultarLoteRpsEnvio as consultar_lote_rps_envio
from nfselib.issnet.v1_00.nfse import EnviarLoteRpsResposta as enviar_lote_rps_resposta
from nfselib.issnet.v1_00.nfse import ConsultarSituacaoLoteRpsResposta as consultar_situacao_lote_rps_resposta
from nfselib.issnet.v1_00.nfse import ConsultarLoteRpsResposta as consultar_lote_rps_resposta
from nfselib.issnet.v1_00.nfse import CancelarNfseEnvio as cancelar_nfse_envio
from nfselib.issnet.v1_00.nfse import cabecalho
from nfselib.issnet.v1_00.nfse import tcIdentificacaoPrestador
from nfselib.issnet.v1_00.nfse import tcPedidoCancelamento, tcInfPedidoCancelamento, tcIdentificacaoNfse


endpoint = '/webserviceabrasf/homologacao/servicos.asmx?WSDL'

servicos = {
    'envia_documento': ServicoNFSe(
        'RecepcionarLoteRps',
        endpoint, enviar_lote_rps_resposta, True),
    'consulta_recibo': ServicoNFSe(
        'ConsultarSituacaoLoteRps',
        endpoint, consultar_situacao_lote_rps_resposta, True),
    'consultar_lote_rps': ServicoNFSe(
        'ConsultarLoteRps',
        endpoint, consultar_lote_rps_resposta, True),
    'cancela_documento': ServicoNFSe(
        'CancelarNfse',
        endpoint, cancelar_nfse_envio, True),
}


class Issnet(NFSe):

    _header = cabecalho(versao="1", versaoDados="1")

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

        raiz = consultar_situacao_lote.ConsultarSituacaoLoteRpsEnvio(
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
        raiz = consultar_lote_rps_envio.ConsultarLoteRpsEnvio(
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


    def _prepara_cancelar_nfse_envio(self, doc_numero):
        raiz = cancelar_nfse_envio.CancelarNfseEnvio(
            Pedido=tcPedidoCancelamento(
                InfPedidoCancelamento=tcInfPedidoCancelamento(
                    Id=doc_numero,
                    IdentificacaoNfse=tcIdentificacaoNfse(
                        Numero=doc_numero,
                        Cnpj=self.cnpj_prestador,
                        InscricaoMunicipal=self.im_prestador,
                        CodigoMunicipio=self.cidade
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
    #     if ultimo_processo.webservice == u'ConsultarSituacaoLoteRps':
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
