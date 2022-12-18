# coding=utf-8
# Copyright (C) 2020 - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from erpbrasil.transmissao import TransmissaoSOAP
from lxml import etree

from erpbrasil.edoc.nfe import NFe
from erpbrasil.edoc.nfe import localizar_url
from erpbrasil.edoc.resposta import RetornoSoap

try:
    from nfelib.v4_00 import retEnvConfRecebto
    from nfelib.v4_00.retEnvConfRecebto import TEnvEvento as TEnvEventoManifestacao  # noga
    from nfelib.v4_00.retEnvConfRecebto import TEvento as TEventoManifestacao  # noga
    from nfelib.v4_00.retEnvConfRecebto import descEventoType as descEventoManifestacao  # noga
    from nfelib.v4_00.retEnvConfRecebto import detEventoType as detEventoManifestacao  # noga
    from nfelib.v4_00.retEnvConfRecebto import infEventoType as infEventoManifestacao  # noga
    from nfelib.v4_00.retEnvConfRecebto import tpEventoType as eventoManifestacao  # noga
except ImportError:
    pass

WS_NFE_RECEPCAO_EVENTO = 'RecepcaoEvento'

SIGLA_ESTADO = {
    '12': 'AC',
    '27': 'AL',
    '13': 'AM',
    '16': 'AP',
    '29': 'BA',
    '23': 'CE',
    '53': 'DF',
    '32': 'ES',
    '52': 'GO',
    '21': 'MA',
    '31': 'MG',
    '50': 'MS',
    '51': 'MT',
    '15': 'PA',
    '25': 'PB',
    '26': 'PE',
    '22': 'PI',
    '41': 'PR',
    '33': 'RJ',
    '24': 'RN',
    '11': 'RO',
    '14': 'RR',
    '43': 'RS',
    '42': 'SC',
    '28': 'SE',
    '35': 'SP',
    '17': 'TO',
    '91': 'AN'
}


class MDe(NFe):

    # ----------------------------- MANIFESTAÇÃO DO DESTINATÁRIO -----------------

    def nfe_recepcao_envia_lote_evento(self, lista_eventos, numero_lote=False):
        """
        Envia lote de eventos confRecebto.TEvento
        :param lista_eventos: Lista com os eventos (infEvento)
        :param numero_lote: Número do lote. Gerado caso None
        :return: retorna a resposta do _post() de envio do lote
        """

        if not numero_lote:
            numero_lote = self._gera_numero_lote()

        eventos = []
        raiz = TEnvEventoManifestacao(
            versao="1.00",
            idLote=numero_lote,
            evento=eventos
        )
        raiz.original_tagname_ = 'envEvento'
        xml_envio_string, xml_envio_etree = self.render_edoc(raiz)

        for raiz_evento in lista_eventos:
            evento = TEventoManifestacao(
                versao="1.00", infEvento=raiz_evento,
            )
            evento.original_tagname_ = 'evento'

            # Recupera o evento do XML assinado
            xml_assinado = self.assina_raiz(evento, evento.infEvento.Id
                                            ).replace('\n', '').encode()

            xml_envio_etree.append(etree.fromstring(xml_assinado))

            # FIXME: Essa forma de geração foi removida no ultimo refactor

            # Converte o xml_assinado para um objeto pelo
            # parser do esquema leiauteConfRecebto

            # xml_object = retEnvConfRecebto.parseString(xml_assinado)

            # Adiciona o xml_object na lista de eventos. Desse modo a lista
            # de eventos terá um evento assinado corretamente
            # eventos.append(xml_object)

        return self._post(
            xml_envio_etree,
            localizar_url(WS_NFE_RECEPCAO_EVENTO, str(91), self.mod,
                          int(self.ambiente)),
            'nfeRecepcaoEventoNF',
            retEnvConfRecebto
        )

    def nfe_recepcao_monta_evento(self, chave, cnpj_cpf, tpEvento, descEvento,
                                  dhEvento=None, xJust=None):
        """
        Método para montar o evento(infEvento) da manifestação
        :param chave: chave do documento
        :param cnpj_cpf: CPF ou CNPJ
        :param tpEvento:   Código do Evento
                                210200 – Confirmação da Operação
                                210210 – Ciência da Operação
                                210220 – Desconhecimento da Operação
                                210240 – Operação não Realizada
        :param descEvento: Informar a descrição do evento:
                                Confirmacao da Operacao
                                Ciencia da Operacao
                                Desconhecimento da Operacao
                                Operacao nao Realizada
        :param dhEvento:   Data/Hora no formato AAAA-MM-DDThh:mm:ssTZD
        :param xJust:      Este campo deve ser informado somente no
                                evento de Operação não realizada
        :return: Um objeto da classe confRecebto.infEventoType preenchido
        """

        nSeqEvento = '1'
        raiz = infEventoManifestacao(
            Id='ID{}{}{}'.format(tpEvento, chave, nSeqEvento.zfill(2)),
            cOrgao=91,
            tpAmb=self.ambiente,
            CNPJ=cnpj_cpf if len(cnpj_cpf) > 11 else None,
            CPF=cnpj_cpf if len(cnpj_cpf) <= 11 else None,
            chNFe=chave,
            dhEvento=dhEvento or self._hora_agora(),
            tpEvento=tpEvento,
            nSeqEvento=nSeqEvento,
            verEvento='1.00',
            detEvento=detEventoManifestacao(
                versao='1.00',
                descEvento=descEvento,
                xJust=xJust
            )
        )

        raiz.original_tagname_ = 'infEvento'

        return raiz

    def nfe_recepcao_evento(self, chave, cnpj_cpf, tpEvento, descEvento, xJust=None):
        """
        Envia a manifestação do destinatário para o WS
        :param cnpj_cpf:   CPF ou CNPJ
        :param tpEvento:   Código do Evento
                             210200 – Confirmação da Operação
                             210210 – Ciência da Operação
                             210220 – Desconhecimento da Operação
                             210240 – Operação não Realizada
        :param descEvento: Informar a descrição do evento:
                             Confirmacao da Operacao
                             Ciencia da Operacao
                             Desconhecimento da Operacao
                             Operacao nao Realizada
        :param xJust:      Este campo deve ser informado somente no
                             evento de Operação não realizada
        :return:
        """

        evento = self.nfe_recepcao_monta_evento(
            chave, cnpj_cpf, tpEvento, descEvento, xJust=xJust)

        # TODO: Verificar possibilidade de adaptar e utilizar código existente
        #  em self.enviar_lote_evento(lista_eventos=[evento]).
        #  A única diferença é a classe utilizada pelo evento

        return self.nfe_recepcao_envia_lote_evento(
            lista_eventos=[evento], numero_lote='1'
        )

    def confirmacao_da_operacao(self, chave, cnpj_cpf):
        return self.nfe_recepcao_evento(
            chave,
            cnpj_cpf,
            eventoManifestacao._2_10200,
            descEventoManifestacao.CONFIRMACAODA_OPERACAO,
        )

    def ciencia_da_operacao(self, chave, cnpj_cpf):
        return self.nfe_recepcao_evento(
            chave,
            cnpj_cpf,
            eventoManifestacao._2_10210,
            descEventoManifestacao.CIENCIADA_OPERACAO,
        )

    def desconhecimento_da_operacao(self, chave, cnpj_cpf):
        return self.nfe_recepcao_evento(
            chave,
            cnpj_cpf,
            eventoManifestacao._2_10220,
            descEventoManifestacao.DESCONHECIMENTODA_OPERACAO,
        )

    def operacao_nao_realizada(self, chave, cnpj_cpf):
        return self.nfe_recepcao_evento(
            chave,
            cnpj_cpf,
            eventoManifestacao._2_10240,
            descEventoManifestacao.OPERACAONAO_REALIZADA,
            xJust=''.zfill(15)
        )

    def analisar_retorno_raw(self, operacao, raiz, xml, retorno, classe):
        """
        Semelhante ao metodo generico, mas usando o primeiro filho
        do XML da resposta.
        """
        retorno.raise_for_status()
        match = re.search('<soap:Body>(.*?)</soap:Body>',
                          retorno.text.replace('\n', ''))
        if match:
            xml_resposta = match.group(1)
            xml = etree.fromstring(xml_resposta)[0]
            if "nfeDistDFeInteresseResult" in xml.tag:
                xml = xml[0]  # unwrapp retDistDFeInt
            resultado = etree.tostring(xml)
            classe.Validate_simpletypes_ = False
            resposta = classe.parseString(resultado, silence=True)
            return RetornoSoap(operacao, raiz, xml, retorno, resposta)

    def _post(self, raiz, url, operacao, classe):
        from .nfe import SIGLA_ESTADO

        xml_string, xml_etree = self.render_edoc(raiz)
        with self._transmissao.cliente(url):
            # Recupera a sigla do estado
            uf_list = [uf for nUF, uf in SIGLA_ESTADO.items() if
                       nUF == str(getattr(raiz, 'cUFAutor', ''))]
            if uf_list:
                kwargs = dict(uf=uf_list and uf_list[0])
            else:
                kwargs = {}
            retorno = self._transmissao.enviar(
                operacao, xml_etree, **kwargs
            )
            return self.analisar_retorno_raw(
                operacao, raiz, xml_string, retorno, classe
            )


class TransmissaoMDE(TransmissaoSOAP):
    def interpretar_mensagem(self, mensagem, **kwargs):
        # TODO: Finalizar refatoração
        if type(mensagem) == str:
            return etree.fromstring(mensagem, parser=etree.XMLParser(
                remove_blank_text=True
            ))

        operacao = kwargs.get('operacao', '')
        uf = kwargs.get('uf', '')

        if operacao and uf:
            _soapheaders = []
            xmlns = 'http://www.portalfiscal.inf.br/nfe/wsdl/'

            if 'distDFeInt' in mensagem.tag:
                mensagem = dict(nfeDadosMsg=mensagem)
            elif 'TEnvEvento' in mensagem.tag:
                xmlns += 'NFeRecepcaoEvento4'
                mensagem = dict(nfeCabecMsg=mensagem)
            elif operacao == 'nfeRecepcaoEvento' and 'consStatServ' in mensagem.tag:
                xmlns += 'RecepcaoEvento'
                mensagem = dict(mensagem=mensagem)

            if isinstance(mensagem, dict):
                header_str = \
                    '<nfeCabecMsg xmlns="{}">' \
                    '<cUF>{}</cUF>' \
                    '<versaoDados>{}</versaoDados>' \
                    '</nfeCabecMsg>'.format(
                        xmlns, uf, mensagem.get('versao', '1.00'))

                _soapheaders.append(etree.fromstring(header_str))
                mensagem['_soapheaders'] = _soapheaders

        return mensagem

    def enviar(self, operacao, mensagem, **kwargs):

        kwargs['operacao'] = operacao
        mensagem = self.interpretar_mensagem(mensagem, **kwargs)
        with self._cliente.settings(raw_response=self.raw_response):
            if isinstance(mensagem, dict):
                # TODO: Remover necessidade desse IF
                if operacao == 'nfeRecepcaoEvento' and 'consStatServ' in mensagem.tag:
                    return self._cliente.service[operacao](
                        mensagem,
                        _soapheaders=mensagem.get('_soapheaders')
                    )

                # TODO: Juntar dois retornos em um
                return self._cliente.service[operacao](
                    **mensagem
                )
            return self._cliente.service[operacao](
                mensagem
            )
