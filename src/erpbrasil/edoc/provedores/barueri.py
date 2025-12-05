# Copyright (C) 2023  Luis Felipe Mileo - KMEE


import xml.etree.ElementTree as ET
from datetime import datetime

from lxml import etree

from erpbrasil.base import misc
from erpbrasil.edoc.nfse import NFSe, ServicoNFSe
from erpbrasil.edoc.resposta import RetornoSoap
from zeep.helpers import serialize_object

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    from nfselib.barueri import (
        ConsultarNFeRecebidaNumero,
        NFeLoteEnviarArquivo,
        NFeLoteStatusArquivo,
        NFeLoteBaixarArquivo,
    )

    barueri = True
except ImportError:
    barueri = False

endpoint = "nfeservice/wsrps.asmx?WSDL"
nsmap = {
    "consulta": "http://www.barueri.sp.gov.br/nfe/ConsultaNFeRecebidaNumero"
    "ConsultaNFeRecebidaNumero.v1.xsd",
    "tipo": "https://servicos.barueri.sp.gov.br/nfewsxml/wsgeraxml.asmx?op=ConsultaNFeRecebidaNumero",
}

if barueri:
    servicos = {
        "envia_documento": ServicoNFSe(
            "NFeLoteEnviarArquivo", endpoint, NFeLoteEnviarArquivo, True
        ),
        "consulta_recibo": ServicoNFSe(
            "NFeLoteStatusArquivo", endpoint, NFeLoteStatusArquivo, True
        ),
        "consultar_lote_rps": ServicoNFSe(
            "NFeLoteStatusArquivo", endpoint, NFeLoteStatusArquivo, True
        ),
        "baixar_lote_rps": ServicoNFSe(
            "NFeLoteBaixarArquivo", endpoint, NFeLoteBaixarArquivo, True
        ),
        "consulta_nfse_rps": ServicoNFSe(
            "ConsultaNFeRecebidaNumero", 'nfewsxml/wsgeraxml.asmx?WSDL', ConsultarNFeRecebidaNumero, True
        ),
    }
else:
    servicos = {}
    cabecalho = None


class Barueri(NFSe):
    def __init__(
        self, transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador
    ):
        if ambiente == "2":
            self._url = "https://testeeiss.barueri.sp.gov.br/"
        else:
            self._url = "https://www.barueri.sp.gov.br/"
        self._servicos = servicos

        super().__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador
        )

    def get_documento_id(self, edoc):
        # edoc.LoteRps.ListaRps.Rps[0].InfRps.Id
        return edoc.LoteRps.Id, edoc.LoteRps.NumeroLote

    def _prepara_envia_documento(self, edoc):
        xml_string, xml_etree = self._generateds_to_string_etree(edoc)
        return xml_string

    def _prepara_consulta_recibo(self, proc_envio):
        raiz = NFeLoteStatusArquivo.NFeLoteStatusArquivo(
                CPFCNPJContrib=self.cnpj_prestador, InscricaoMunicipal=self.im_prestador
            ,
            ProtocoloRemessa=proc_envio.resposta.ProtocoloRemessa,
        )
        return raiz

    def _prepara_consultar_lote_rps(self, protocolo):
        raiz = NFeLoteStatusArquivo.NFeLoteStatusArquivo(
                CPFCNPJContrib=self.cnpj_prestador, InscricaoMunicipal=self.im_prestador
            ,
            ProtocoloRemessa=protocolo,
        )
        return raiz

    def _prepara_baixar_lote_rps(self, nome_arq_retorno):
        raiz = NFeLoteBaixarArquivo.NFeLoteBaixarArquivo(
                CPFCNPJContrib=self.cnpj_prestador, InscricaoMunicipal=self.im_prestador, NomeArqRetorno=nome_arq_retorno,)
        return raiz

    def baixar_lote_rps(self, protocolo=None):
        return self._post(
            body=self._prepara_baixar_lote_rps(protocolo),
            servico=self._servicos[self.baixar_lote_rps.__name__],
        )

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.retorno.ProtocoloRemessa:
            return True
        return False

    def _edoc_situacao_em_processamento(self, proc_recibo):
        return proc_recibo.retorno.ListaNfeArquivosRPS.SituacaoArq == 2

    def _prepara_cancelar_nfse_envio(self, doc_numero):
        pass

    def _prepara_consultar_nfse_rps(self, **kwargs):
        rps_numero = kwargs.get("rps_number")
        raiz = ConsultarNFeRecebidaNumero.NFeRecebidaNumero(
            CPFCNPJTomador=self.cnpj_prestador,
            CPFCNPJPrestador=self.cnpj_prestador,
            NumeroNota=rps_numero,
        )
        return raiz

    def analisa_retorno_consulta(
        self, processo, number, company_cnpj_cpf, company_legal_name
    ):
        data = serialize_object(processo.resposta, target_cls=dict)
        root = etree.Element("ConsultarNfeResposta")

        if processo.webservice == "ConsultaNFeRecebidaNumero":
            # if "ListaNfe" in data:
            #     lista = etree.SubElement(root, "ListaNfe")
            #     for nfe in data["ListaNfe"]:
            #         item = etree.SubElement(lista, "CompNfe")
            #         for k, v in nfe.items():
            #             etree.SubElement(item, k).text = str(v)

            if "ListaMensagemRetorno" in data:
                msgs = etree.SubElement(root, "ListaMensagemRetorno")
                for msg in data["ListaMensagemRetorno"]:
                    item = etree.SubElement(msgs, "MensagemRetorno")
                    for k, v in msg.items():
                        etree.SubElement(item, k).text = str(v)
                mensagem = ""

            retorno = root
            enviado = retorno.findall(".//CompNfe")
            nao_encontrado = retorno.findall(".//MensagemRetorno")
            # TODO: PAREI AQUI

            if enviado:
                # NFS-e já foi enviada

                cancelada = retorno.findall(
                    ".//tipo:NfseCancelamento", namespaces=nsmap
                )

                if cancelada:
                    # NFS-e enviada foi cancelada

                    data = retorno.findall(".//tipo:DataHora", namespaces=nsmap)[0].text
                    data = datetime.strptime(data, "%Y-%m-%dT%H:%M:%S").strftime(
                        "%m/%d/%Y"
                    )
                    mensagem = "NFS-e cancelada em " + data

                else:
                    numero_retorno = retorno.findall(
                        ".//tipo:InfNfse/tipo:Numero", namespaces=nsmap
                    )[0].text
                    cnpj_prestador_retorno = retorno.findall(
                        ".//tipo:IdentificacaoPrestador/tipo:Cnpj", namespaces=nsmap
                    )[0].text
                    razao_social_prestador_retorno = retorno.findall(
                        ".//tipo:PrestadorServico/tipo:RazaoSocial", namespaces=nsmap
                    )[0].text

                    variables_error = []

                    if numero_retorno != number:
                        variables_error.append("Número")
                    if cnpj_prestador_retorno != misc.punctuation_rm(company_cnpj_cpf):
                        variables_error.append("CNPJ do prestador")
                    if razao_social_prestador_retorno != company_legal_name:
                        variables_error.append("Razão Social de prestador")

                    if variables_error:
                        mensagem = (
                            "Os seguintes campos não condizem com"
                            " o provedor NFS-e: \n"
                        )
                        mensagem += "\n".join(variables_error)
                    else:
                        mensagem = "NFS-e enviada e corresponde com o provedor"

            elif nao_encontrado:
                # NFS-e não foi enviada

                mensagem_erro = msg.get('Mensagem')
                correcao = msg.get('Correcao')
                codigo = msg.get('Codigo')
                mensagem = (
                    codigo + " - " + mensagem_erro + " - Correção: " + correcao + "\n"
                )

            else:
                mensagem = "Erro desconhecido."

        return mensagem

    def analisa_retorno_cancelamento(self, processo):
        pass


    def _post(self, body, servico):
        header_string = '1'

        body_string, body_etree = self._generateds_to_string_etree(body)

        if servico.operacao == "ConsultaNFeRecebidaNumero":
            self._url = "https://servicos.barueri.sp.gov.br"

        if header_string:
            with self._transmissao.cliente(
                    urljoin(self._url, servico.endpoint)
            ) as cliente:
                resposta = cliente.service[servico.operacao](
                    header_string,
                    body_string,
                )
        else:
            with self._transmissao.cliente(
                urljoin(self._url, servico.endpoint)
            ) as cliente:
                resposta = cliente.service[servico.operacao](
                    body_string,
                )

        return self.analisar_retorno(
            servico.operacao, body, body_string, resposta, servico.classe_retorno
        )

    def analisar_retorno(self, operacao, raiz, xml, retorno, classe):
        resposta = False
        if retorno:
            classe.Validate_simpletypes_ = False
            # resultado = etree.tostring(etree.fromstring(retorno.encode("utf-8")))
            # resposta = classe.parseString(resultado, silence=True)
            resposta = retorno
        return RetornoSoap(operacao, raiz, xml, retorno, resposta)
