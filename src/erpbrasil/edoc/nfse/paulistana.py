# coding=utf-8
# Copyright (C) 2020 KMEE

from __future__ import division, print_function, unicode_literals
import xml.etree.ElementTree as ET

from erpbrasil.edoc.nfse import NFSe, ServicoNFSe
from erpbrasil.assinatura.assinatura import assina_tag

from nfselib.paulistana.v02 import RetornoEnvioLoteRPS
from nfselib.paulistana.v02 import RetornoConsulta

from nfselib.paulistana.v02.PedidoConsultaLote import(
    PedidoConsultaLote,
    CabecalhoType as CabecalhoLote,
    tpCPFCNPJ,
)

from nfselib.paulistana.v02.PedidoConsultaNFe import(
    PedidoConsultaNFe,
    CabecalhoType,
    DetalheType,
    tpCPFCNPJ,
    tpChaveRPS
)


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

    'consulta_nfse_rps': ServicoNFSe(
        'ConsultaNFe',
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
            rps.Assinatura = assina_tag(self._transmissao, rps.Assinatura)
        xml_assinado = self.assina_raiz(edoc, '', metodo='nfse')

        return xml_assinado

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return proc_envio.resposta.Cabecalho.Sucesso

    def _edoc_situacao_em_processamento(self, proc_recibo):
        # if proc_recibo.resposta.Situacao == 2:
        #     return True
        # return False
        pass

    def _prepara_consulta_recibo(self, proc_envio):

        retorno = ET.fromstring(proc_envio.retorno)
        numero_lote = int(retorno.find('.//NumeroLote').text)
        cnpj = retorno.find('.//CNPJ').text

        edoc = PedidoConsultaLote(
            Cabecalho=CabecalhoLote(
                Versao=1,
                CPFCNPJRemetente=tpCPFCNPJ(CNPJ=cnpj),
                NumeroLote=numero_lote
            )
        )

        xml_assinado = self.assina_raiz(edoc, '', metodo='nfse')

        return xml_assinado

    def _prepara_consultar_nfse_rps(
            self, rps_numero, rps_serie, inscricao_prestador, cnpj_prestador):

        raiz = PedidoConsultaNFe(
            Cabecalho=CabecalhoType(
                Versao=1,
                CPFCNPJRemetente=tpCPFCNPJ(CNPJ=cnpj_prestador)
            ),
            Detalhe=[DetalheType(
                ChaveRPS=tpChaveRPS(
                    InscricaoPrestador=int(inscricao_prestador),
                    SerieRPS=rps_serie,
                    NumeroRPS=int(rps_numero),
                ),
            )],
        )

        xml_assinado = self.assina_raiz(raiz, '', metodo='nfse')

        return xml_assinado

    def analisa_retorno_consulta(self, processo):
        retorno_mensagem = ''
        if processo.resposta.Cabecalho.Sucesso:
            retorno = ET.fromstring(processo.retorno)
            codigo = retorno.find('.//Codigo').text
            descricao = retorno.find('.//Descricao').text
            retorno_mensagem = codigo + ' - ' + descricao
        else:
            retorno_mensagem = 'Error communicating with the webservice'
        return retorno_mensagem
