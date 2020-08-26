# coding=utf-8
# Copyright (C) 2020 KMEE

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe
from erpbrasil.assinatura.assinatura import assina_string

from nfselib.paulistana.v02 import RetornoEnvioLoteRPS_v01 as RetornoEnvioLoteRPS
from nfselib.paulistana.v02 import RetornoConsulta_v01 as RetornoConsulta

endpoint = 'ws/lotenfe.asmx?WSDL'

servicos_base = {

}

servicos_hml = {
    'envia_documento': ServicoNFSe(
        'TesteEnvioLoteRPS',
        endpoint, RetornoEnvioLoteRPS, True),

    'consulta_recibo': ServicoNFSe(
        'ConsultaLote',
        endpoint, RetornoConsulta, True),
}
servicos_hml.update(servicos_base.copy())

servicos_prod = {

}
servicos_prod.update(servicos_base.copy())

class Paulistana(NFSe):

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):

        self._url = 'https://nfe.prefeitura.sp.gov.br'

        # Não tem URL de homologação mas tem métodos para testes
        # no mesmo webservice

        if ambiente == '2':
            self._servicos = servicos_hml
        else:
            self._servicos = servicos_prod

        super(Paulistana, self).__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)

    def _prepara_envia_documento(self, edoc):
        for rps in edoc.RPS:
            rps.Assinatura = assina_string(self._transmissao, rps.Assinatura)
        xml_assinado = self.assina_raiz(edoc, '')

        return xml_assinado

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return not proc_envio.resposta.Cabecalho.Sucesso

    def _edoc_situacao_em_processamento(self, proc_recibo):
        # if proc_recibo.resposta.Situacao == 2:
        #     return True
        # return False
        pass

    def _prepara_consulta_recibo(self, proc_envio):

        pass

