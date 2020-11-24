# coding=utf-8
# Copyright (C) 2020 - TODAY, Marcel Savegnago - Escodoo

from __future__ import division, print_function, unicode_literals
import xml.etree.ElementTree as ET
from datetime import datetime

from erpbrasil.base import misc
from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_envio as consulta_situacao_lote
from nfselib.issnet.v1_00 import servico_consultar_lote_rps_envio as servico_consultar_lote_rps_envio
from nfselib.issnet.v1_00 import servico_enviar_lote_rps_resposta as servico_enviar_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_consultar_situacao_lote_rps_resposta as servico_consultar_situacao_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_consultar_lote_rps_resposta as servico_consultar_lote_rps_resposta
from nfselib.issnet.v1_00 import servico_cancelar_nfse_envio as servico_cancelar_nfse_envio
from nfselib.issnet.v1_00 import servico_consultar_nfse_rps_envio as servico_consultar_nfse_rps_envio
from nfselib.issnet.v1_00.tipos_complexos import tcIdentificacaoPrestador
from nfselib.issnet.v1_00.tipos_complexos import tcIdentificacaoNfse, tcIdentificacaoRps, tcCpfCnpj, tcPedidoCancelamento, tcInfPedidoCancelamento
#from nfselib.issnet.v1_00.Servico_Cancelar_justificativa_tipo_complexos import tcPedidoCancelamento, tcInfPedidoCancelamento


cidade = {

    3543402: 'ribeiraopreto', # Ribeirão Preto - SP

}

endpoint = 'servicos.asmx?WSDL'

servicos = {
    'envia_documento': ServicoNFSe(
        'RecepcionarLoteRps',
        endpoint, servico_enviar_lote_rps_resposta, True),
    'consulta_recibo': ServicoNFSe(
        'ConsultarSituacaoLoteRPS',
        endpoint, servico_consultar_situacao_lote_rps_resposta, True),
    'consultar_lote_rps': ServicoNFSe(
        'ConsultarLoteRps',
        endpoint, servico_consultar_lote_rps_resposta, True),
    'cancela_documento': ServicoNFSe(
        'CancelarNfse',
        endpoint, servico_cancelar_nfse_envio, True),
    'consulta_nfse_rps': ServicoNFSe(
        'ConsultarNFSePorRPS',
        endpoint, servico_consultar_nfse_rps_envio, True),
}


class Issnet(NFSe):

    _header = None

    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):

        if ambiente == '2':
           self._url = 'https://www.issnetonline.com.br/webserviceabrasf/homologacao/'
        else:
            self._url = 'https://www.issnetonline.com.br/webserviceabrasf/' + cidade[int(cidade_ibge)] + '/'
        self._servicos = servicos

        super(Issnet, self).__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)

    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.id
        return edoc.LoteRps.id, edoc.LoteRps.NumeroLote

    def _prepara_envia_documento(self, edoc):
        numero_lote = self._gera_numero_lote()
        edoc.LoteRps.id = 'L' + numero_lote
        edoc.LoteRps.NumeroLote = numero_lote
        #
        # Assinamos o Lote
        #
        xml_assinado = edoc

        # for rps in edoc.LoteRps.ListaRps.Rps:
        #     xml_assinado = self.assina_raiz(xml_assinado, rps.InfRps.id)

        # Assinamos o lote
        xml_assinado = self.assina_raiz(xml_assinado, edoc.LoteRps.id)
        xml_assinado = '<?xml version="1.0"?>' + xml_assinado
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
        #xml_assinado = self.assina_raiz(raiz,"")
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        xml_string = '<?xml version="1.0"?>' + xml_string
        return xml_string

    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = servico_consultar_lote_rps_envio.ConsultarLoteRpsEnvio(
            # id=self._gera_numero_lote(),
            Prestador=tcIdentificacaoPrestador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.cnpj_prestador,
                ),
                InscricaoMunicipal=self.im_prestador
            ),
            Protocolo=protocolo
        )
        # xml_assinado = self.assina_raiz(raiz,"")
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        xml_string = '<?xml version="1.0"?>' + xml_string
        return xml_string

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.Protocolo:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.Situacao == 2:
            return True
        return False

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        Pedido = tcPedidoCancelamento(
            InfPedidoCancelamento=tcInfPedidoCancelamento(
                id=doc_numero,
                IdentificacaoNfse=tcIdentificacaoNfse(
                    Numero=doc_numero,
                    Cnpj=self.cnpj_prestador,
                    InscricaoMunicipal=self.im_prestador,
                    CodigoMunicipio=self.cidade
                ),
                CodigoCancelamento='0001',
                # MotivoCancelamentoNfse=self.'NFSe Cancelada pelo motivo XYZ', # TODO: Implementar
            )
        )

        # Foi codificado desta forma porque a assinatura fica dentro da tag Pedido. Acredito que de para melhorar.
        pedido = self.assina_raiz(Pedido, "")
        xml_assinado = '<?xml version="1.0"?>' \
                       '<p1:CancelarNfseEnvio ' \
                       'xmlns:p1="http://www.issnetonline.com.br/webserviceabrasf/vsd/servico_cancelar_nfse_envio.xsd" ' \
                       'xmlns:tc="http://www.issnetonline.com.br/webserviceabrasf/vsd/tipos_complexos.xsd" ' \
                       'xmlns:ts="http://www.issnetonline.com.br/webserviceabrasf/vsd/tipos_simples.xsd">' \
                       + pedido + '</p1:CancelarNfseEnvio>'

        return xml_assinado

    def _prepara_consultar_nfse_rps(self, rps_numero, rps_serie, rps_tipo):
        raiz = servico_consultar_nfse_rps_envio.ConsultarNfseRpsEnvio(
            IdentificacaoRps=tcIdentificacaoRps(
                Numero=rps_numero,
                Serie=rps_serie,
                Tipo=rps_tipo,
            ),
            Prestador=tcIdentificacaoPrestador(
                CpfCnpj=tcCpfCnpj(
                    Cnpj=self.cnpj_prestador,
                ),
                InscricaoMunicipal=self.im_prestador
            ),
        )
        xml_string, xml_etree = self._generateds_to_string_etree(raiz)
        xml_string = '<?xml version="1.0"?>' + xml_string
        return xml_string

    def analisa_retorno_consulta(self, processo, number, company_cnpj_cpf,
                        company_legal_name):
        retorno = ET.fromstring(processo.retorno)
        nsmap = {'consulta': 'http://www.issnetonline.com.br/webserviceabrasf/vsd/'
                             'servico_consultar_nfse_rps_resposta.xsd',
                 'tc': 'http://www.issnetonline.com.br/webserviceabrasf/vsd/'
                         'tipos_complexos.xsd'}

        mensagem = ''
        if processo.webservice == 'ConsultarNFSePorRPS':
            enviado = retorno.findall(
                ".//consulta:CompNfse", namespaces=nsmap)
            nao_encontrado = retorno.findall(
                ".//consulta:MensagemRetorno", namespaces=nsmap)

            if enviado:
                # NFS-e já foi enviada

                cancelada = retorno.findall(
                    ".//consulta:NfseCancelamento", namespaces=nsmap)

                if cancelada:
                    # NFS-e enviada foi cancelada

                    data = retorno.findall(
                        ".//consulta:DataHora", namespaces=nsmap)[0].text
                    data = datetime.strptime(data, '%Y-%m-%dT%H:%M:%S'). \
                        strftime("%m/%d/%Y")
                    mensagem = 'NFS-e cancelada em ' + data

                else:
                    numero_retorno = \
                        retorno.findall(".//tc:InfNfse/tc:Numero",
                                        namespaces=nsmap)[0].text
                    cnpj_prestador_retorno = retorno.findall(
                        ".//tc:IdentificacaoPrestador/tc:CpfCnpj/tc:Cnpj",
                        namespaces=nsmap)[0].text
                    razao_social_prestador_retorno = retorno.findall(
                        ".//tc:PrestadorServico/tc:RazaoSocial",
                        namespaces=nsmap)[0].text

                    variables_error = []

                    if numero_retorno != number:
                        variables_error.append('Número')
                    if cnpj_prestador_retorno != misc.punctuation_rm(
                        company_cnpj_cpf):
                        variables_error.append('CNPJ do prestador')

                    # TODO: A Razão Social pode ser alterada.
                    #  Vale a pena a comparação abaixo?

                    # if razao_social_prestador_retorno != company_legal_name:
                    #     variables_error.append('Razão Social de pestrador')

                    if variables_error:
                        mensagem = 'Os seguintes campos não condizem com' \
                                   ' o provedor NFS-e: \n'
                        mensagem += '\n'.join(variables_error)
                    else:
                        mensagem = "NFS-e enviada e corresponde com o provedor"

            elif nao_encontrado:
                # NFS-e não foi enviada

                mensagem_erro = retorno.findall(
                    ".//tc:Mensagem", namespaces=nsmap)[0].text
                correcao = retorno.findall(
                    ".//tc:Correcao", namespaces=nsmap)[0].text
                codigo = retorno.findall(
                    ".//tc:Codigo", namespaces=nsmap)[0].text
                mensagem = (codigo + ' - ' + mensagem_erro + ' - Correção: ' +
                            correcao + '\n')

            else:
                mensagem = 'Erro desconhecido.'

        return mensagem
