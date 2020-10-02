# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals
import xml.etree.ElementTree as ET
from datetime import datetime

from erpbrasil.base import misc
from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_envio_v03 as consulta_situacao_lote
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_envio_v03 as servico_consultar_lote_rps_envio
from nfselib.ginfes.v3_01 import servico_enviar_lote_rps_resposta_v03 as servico_enviar_lote_rps_resposta
from nfselib.ginfes.v3_01 import servico_consultar_situacao_lote_rps_resposta_v03 as servico_consultar_situacao_lote_rps_resposta
from nfselib.ginfes.v3_01 import servico_consultar_lote_rps_resposta_v03 as servico_consultar_lote_rps_resposta
from nfselib.ginfes.v3_01 import servico_cancelar_nfse_envio_v03 as servico_cancelar_nfse_envio
from nfselib.ginfes.v3_01 import servico_consultar_nfse_rps_envio_v03 as servico_consultar_nfse_rps_envio
from nfselib.ginfes.v3_01.cabecalho_v03 import cabecalho
from nfselib.ginfes.v3_01.tipos_v03 import tcIdentificacaoPrestador
from nfselib.ginfes.v3_01.tipos_v03 import tcPedidoCancelamento, tcInfPedidoCancelamento, tcIdentificacaoNfse, tcIdentificacaoRps


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
    'cancela_documento': ServicoNFSe(
        'CancelarNfseV3',
        endpoint, servico_cancelar_nfse_envio, True),
    'consulta_nfse_rps': ServicoNFSe(
        'ConsultarNfsePorRpsV3',
        endpoint, servico_cancelar_nfse_envio, True),
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

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        raiz = servico_cancelar_nfse_envio.CancelarNfseEnvio(
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

    def _prepara_consultar_nfse_rps(self, rps_numero, rps_serie, rps_tipo):
        raiz = servico_consultar_nfse_rps_envio.ConsultarNfseRpsEnvio(
            IdentificacaoRps=tcIdentificacaoRps(
                Numero=rps_numero,
                Serie=rps_serie,
                Tipo=rps_tipo,
            ),
            Prestador=tcIdentificacaoPrestador(
                Cnpj=self.cnpj_prestador,
                InscricaoMunicipal=self.im_prestador
            ),
        )
        xml_assinado = self.assina_raiz(raiz, '')

        return xml_assinado

    def analisa_retorno_consulta(self, processo, number, company_cnpj_cpf,
                        company_legal_name):
        retorno = ET.fromstring(processo.retorno)
        nsmap = {'consulta': 'http://www.ginfes.com.br/servico_consultar_'
                             'nfse_rps_resposta_v03.xsd',
                 'tipo': 'http://www.ginfes.com.br/tipos_v03.xsd'}

        mensagem = ''
        if processo.webservice == 'ConsultarNfsePorRpsV3':
            enviado = retorno.findall(
                ".//consulta:CompNfse", namespaces=nsmap)
            nao_encontrado = retorno.findall(
                ".//tipo:MensagemRetorno", namespaces=nsmap)

            if enviado:
                # NFS-e já foi enviada

                cancelada = retorno.findall(
                    ".//tipo:NfseCancelamento", namespaces=nsmap)

                if cancelada:
                    # NFS-e enviada foi cancelada

                    data = retorno.findall(
                        ".//tipo:DataHora", namespaces=nsmap)[0].text
                    data = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S'). \
                        strftime("%m/%d/%Y")
                    mensagem = 'NFS-e cancelada em ' + data

                else:
                    numero_retorno = \
                        retorno.findall(".//tipo:InfNfse/tipo:Numero",
                                        namespaces=nsmap)[0].text
                    cnpj_prestador_retorno = retorno.findall(
                        ".//tipo:IdentificacaoPrestador/tipo:Cnpj",
                        namespaces=nsmap)[0].text
                    razao_social_prestador_retorno = retorno.findall(
                        ".//tipo:PrestadorServico/tipo:RazaoSocial",
                        namespaces=nsmap)[0].text

                    varibles_error = []

                    if numero_retorno != number:
                        varibles_error.append('Número')
                    if cnpj_prestador_retorno != misc.punctuation_rm(
                        company_cnpj_cpf):
                        varibles_error.append('CNPJ do prestador')
                    if razao_social_prestador_retorno != company_legal_name:
                        varibles_error.append('Razão Social de pestrador')

                    if varibles_error:
                        mensagem = 'Os seguintes campos não condizem com' \
                                   ' o provedor NFS-e: \n'
                        mensagem += '\n'.join(varibles_error)
                    else:
                        mensagem = "NFS-e enviada e corresponde com o provedor"

            elif nao_encontrado:
                # NFS-e não foi enviada

                mensagem_erro = retorno.findall(
                    ".//tipo:Mensagem", namespaces=nsmap)[0].text
                correcao = retorno.findall(
                    ".//tipo:Correcao", namespaces=nsmap)[0].text
                codigo = retorno.findall(
                    ".//tipo:Codigo", namespaces=nsmap)[0].text
                mensagem = (codigo + ' - ' + mensagem_erro + ' - Correção: ' +
                            correcao + '\n')

            else:
                mensagem = 'Erro desconhecido.'

        return mensagem

    def analisa_retorno_cancelamento(self, processo):
        if processo.webservice in ['CancelarNfseV3', 'CancelarNfse']:
            mensagem_completa = ''
            situacao = True
            retorno = ET.fromstring(processo.retorno)
            nsmap = {'tipo': 'http://www.ginfes.com.br/tipos_v03.xsd'}

            sucesso = retorno.findall(".//tipo:Sucesso", namespaces=nsmap)
            if not sucesso:
                mensagem_erro = retorno.findall(
                    ".//tipo:Mensagem", namespaces=nsmap)[0].text
                correcao = retorno.findall(
                    ".//tipo:Correcao", namespaces=nsmap)[0].text
                codigo = retorno.findall(
                    ".//tipo:Codigo", namespaces=nsmap)[0].text
                mensagem_completa += (
                    codigo + ' - ' + mensagem_erro +
                    ' - Correção: ' + correcao + '\n')
                situacao = False

            return situacao, mensagem_completa
