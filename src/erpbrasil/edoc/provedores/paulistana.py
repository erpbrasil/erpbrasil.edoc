# coding=utf-8
# Copyright (C) 2020 KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import xml.etree.ElementTree as ET

from erpbrasil.edoc.nfse import NFSe
from erpbrasil.edoc.nfse import ServicoNFSe

try:
    from erpbrasil.assinatura.assinatura import assina_tag
    from nfselib.paulistana.v02 import PedidoCancelamentoNFe
    from nfselib.paulistana.v02 import PedidoConsultaLote
    from nfselib.paulistana.v02 import PedidoConsultaNFe
    from nfselib.paulistana.v02 import RetornoCancelamentoNFe
    from nfselib.paulistana.v02 import RetornoConsulta
    from nfselib.paulistana.v02 import RetornoEnvioLoteRPS
    paulistana = True
except ImportError:
    paulistana = False

endpoint = 'ws/lotenfe.asmx?WSDL'

if paulistana:
    servicos_base = {
        'consulta_recibo': ServicoNFSe(
            'ConsultaLote',
            endpoint, RetornoConsulta, True),

        'consulta_nfse_rps': ServicoNFSe(
            'ConsultaNFe',
            endpoint, RetornoConsulta, True),

        'cancela_documento': ServicoNFSe(
            'CancelamentoNFe',
            endpoint, RetornoCancelamentoNFe, True),
    }

    servicos_hml = {
        'envia_documento': ServicoNFSe(
            'TesteEnvioLoteRPS',
            endpoint, RetornoEnvioLoteRPS, True),
    }
    servicos_hml.update(servicos_base.copy())

    servicos_prod = {}
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

        edoc = PedidoConsultaLote.PedidoConsultaLote(
            Cabecalho=PedidoConsultaLote.CabecalhoType(
                Versao=1,
                CPFCNPJRemetente=PedidoConsultaNFe.tpCPFCNPJ(CNPJ=cnpj),
                NumeroLote=numero_lote
            )
        )

        xml_assinado = self.assina_raiz(edoc, '', metodo='nfse')

        return xml_assinado

    def _prepara_consultar_nfse_rps(self, **kwargs):
        cnpj_prestador = kwargs.get("cnpj_prest")
        inscricao_prestador = kwargs.get("insc_prest")
        rps_serie = kwargs.get("serie_rps")
        rps_numero = kwargs.get("numero_rps")

        raiz = PedidoConsultaNFe.PedidoConsultaNFe(
            Cabecalho=PedidoConsultaNFe.CabecalhoType(
                Versao=1,
                CPFCNPJRemetente=PedidoConsultaNFe.tpCPFCNPJ(CNPJ=cnpj_prestador)
            ),
            Detalhe=[PedidoConsultaNFe.DetalheType(
                ChaveRPS=PedidoConsultaNFe.tpChaveRPS(
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

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        numero_nfse = doc_numero.get('numero_nfse')
        codigo_verificacao = doc_numero.get('codigo_verificacao') or ''

        assinatura = numero_nfse.zfill(8)
        assinatura += codigo_verificacao.zfill(12)

        raiz = PedidoCancelamentoNFe.PedidoCancelamentoNFe(
            Cabecalho=PedidoCancelamentoNFe.CabecalhoType(
                Versao=1,
                CPFCNPJRemetente=PedidoConsultaNFe.tpCPFCNPJ(CNPJ=self.cnpj_prestador),
            ),
            Detalhe=[PedidoCancelamentoNFe.DetalheType(
                ChaveNFe=PedidoCancelamentoNFe.tpChaveNFe(
                    InscricaoPrestador=int(self.im_prestador),
                    NumeroNFe=int(numero_nfse),
                    CodigoVerificacao=codigo_verificacao.zfill(8),
                ),
                AssinaturaCancelamento=assinatura,
            )],
        )

        for detalhe in raiz.Detalhe:
            detalhe.AssinaturaCancelamento = assina_tag(
                self._transmissao, detalhe.AssinaturaCancelamento)

        xml_assinado = self.assina_raiz(raiz, '', metodo='nfse')
        return xml_assinado

    def analisa_retorno_cancelamento_paulistana(self, processo):
        retorno_mensagem = ''
        status = True
        if not processo.resposta.Cabecalho.Sucesso:
            status = False
            for erro in processo.resposta.Erro:
                retorno_mensagem = \
                    str(erro.Codigo) + ' - ' + erro.Descricao + '\n'
        return status, retorno_mensagem
