# coding=utf-8
# Copyright (C) 2023  Luis Felipe Mileo - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import xml.etree.ElementTree as ET
from xml.dom import minidom
from lxml import etree
from datetime import datetime

from erpbrasil.base import misc

from base64 import b64encode
from erpbrasil.edoc.nfse import NFSe
from erpbrasil.edoc.nfse import ServicoNFSe

try:
    from nfselib.barueri import NFeLoteEnviarArquivo
    from nfselib.barueri import NFeLoteStatusArquivo
    from nfselib.barueri import ConsultarNFeRecebidaNumero
    barueri = True
except ImportError:
    barueri = False

endpoint = 'nfeservice/wsrps.asmx?WSDL'
nsmap = {'consulta': 'http://www.barueri.sp.gov.br/nfe/ConsultaNFeRecebidaNumero'
                             'ConsultaNFeRecebidaNumero.v1.xsd',
                 'tipo': 'https://servicos.barueri.sp.gov.br/nfewsxml/wsgeraxml.asmx?op=ConsultaNFeRecebidaCompetencia'}

if barueri:
    servicos = {
        'envia_documento': ServicoNFSe(
            'NFeLoteEnviarArquivo',
            endpoint, NFeLoteEnviarArquivo, True),
        'consulta_recibo': ServicoNFSe(
            'NFeLoteStatusArquivo',
            endpoint, NFeLoteStatusArquivo, True),
        'consultar_lote_rps': ServicoNFSe(
            'NFeLoteStatusArquivo',
            endpoint, NFeLoteStatusArquivo, True),
        'consulta_nfse_rps': ServicoNFSe(
            'ConsultarNFeRecebidaNumero',
            endpoint, ConsultarNFeRecebidaNumero, True),
    }
else:
    servicos = {}
    cabecalho = None


class Barueri(NFSe):
    
    def __init__(self, transmissao, ambiente, cidade_ibge, cnpj_prestador,
                 im_prestador):
        
        if ambiente == '2':
            self._url = 'https://testeeiss.barueri.sp.gov.br/'
        else:
            self._url = 'https://www.barueri.sp.gov.br/'
        self._servicos = servicos
        
        super(Barueri, self).__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)
        
    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.Id
        return edoc.LoteRps.Id, edoc.LoteRps.NumeroLote
        
    def _prepara_envia_documento(self, edoc):
        numero_lote = self._gera_numero_lote()
        xml_string, xml_etree = self._generateds_to_string_etree(edoc)
        root = etree.Element("NFeLoteEnviarArquivo", xmlns="http://www.barueri.sp.gov.br/nfe")
        versao_schema = etree.SubElement(root, "VersaoSchema")
        versao_schema.text = "1"
        mensagem_xml = etree.SubElement(root, "MensagemXML")
        mensagem_xml.text = etree.CDATA(xml_string)
        edoc.ApenasValidaArq = 'lote' + numero_lote
        return root

    def _prepara_consulta_recibo(self, proc_envio):
        raiz = NFeLoteStatusArquivo.ConsultarSituacaoLoteRpsEnvio(
            Prestador=NFeLoteStatusArquivo(
                CPFCNPJContrib=self.cnpj_prestador,
                InscricaoMunicipal=self.im_prestador
            ),
            ProtocoloRemessa=proc_envio.resposta.Protocolo
        )
        return self.assina_raiz(raiz, "")
    
    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = NFeLoteStatusArquivo(
            Prestador=NFeLoteStatusArquivo.tcIdentificacaoPrestador(
                CPFCNPJContrib=self.cnpj_prestador,
                InscricaoMunicipal=self.im_prestador
            ),
            ProtocoloRemessa=protocolo
        )
        xml_assinado = self.assina_raiz(raiz, raiz.Id)
        return xml_assinado
    
    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.Protocolo:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        return proc_recibo.resposta.Situacao == 2
    
    def _prepara_cancelar_nfse_envio(self, doc_numero):
        pass
    
    def _prepara_consultar_nfse_rps(self, **kwargs):
        rps_numero = kwargs.get('rps_number')
        raiz = ConsultarNFeRecebidaNumero(
            IdentificacaoRps=ConsultarNFeRecebidaNumero(
                NumeroNota=rps_numero,
            ),
            Prestador=ConsultarNFeRecebidaNumero(
                CPFCNPJPrestador=self.cnpj_prestador,
            ),
        )
        
        return self.assina_raiz(raiz, '')

    def analisa_retorno_consulta(self, processo, number, company_cnpj_cpf,
                                 company_legal_name):
        retorno = ET.fromstring(processo.retorno)
        mensagem = ''
        if processo.webservice == 'NFeRecebidaNumero':
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

                    variables_error = []

                    if numero_retorno != number:
                        variables_error.append('Número')
                    if cnpj_prestador_retorno != misc.punctuation_rm(
                            company_cnpj_cpf):
                        variables_error.append('CNPJ do prestador')
                    if razao_social_prestador_retorno != company_legal_name:
                        variables_error.append('Razão Social de prestador')

                    if variables_error:
                        mensagem = 'Os seguintes campos não condizem com' \
                                   ' o provedor NFS-e: \n'
                        mensagem += '\n'.join(variables_error)
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
        pass
    