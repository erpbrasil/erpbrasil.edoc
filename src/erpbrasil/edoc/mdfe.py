# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import time
import binascii
import base64

from erpbrasil.assinatura.assinatura import Assinatura
from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico

try:
    from mdfelib.v3_00 import retConsMDFeNaoEnc
    from mdfelib.v3_00 import retConsReciMDFe
    from mdfelib.v3_00 import retConsSitMDFe
    from mdfelib.v3_00 import retConsStatServMDFe
    from mdfelib.v3_00 import retEnviMDFe
    from mdfelib.v3_00 import procMDFe
    from mdfelib.v3_00 import retEventoMDFe
    from mdfelib.v3_00 import evCancMDFe
    from mdfelib.v3_00 import evEncMDFe
except ImportError:
    pass

WS_MDFE_CONSULTA = "MDFeConsulta"
WS_MDFE_SITUACAO = "MDFeStatusServico"
WS_MDFE_CONSULTA_NAO_ENCERRADOS = "MDFeConsNaoEnc"
WS_MDFE_DISTRIBUICAO = "MDFeDistribuicaoDFe"

WS_MDFE_RECEPCAO = "MDFeRecepcao"
WS_MDFE_RECEPCAO_SINC = "MDFeRecepcaoSinc"
WS_MDFE_RET_RECEPCAO = "MDFeRetRecepcao"
WS_MDFE_RECEPCAO_EVENTO = "MDFeRecepcaoEvento"

AMBIENTE_PRODUCAO = 1
AMBIENTE_HOMOLOGACAO = 2

MDFE_MODELO = "58"

SVC_RS = {
    AMBIENTE_PRODUCAO: {
        "servidor": "mdfe.svrs.rs.gov.br",
        WS_MDFE_RECEPCAO: "ws/MDFeRecepcao/MDFeRecepcao.asmx?wsdl",
        WS_MDFE_RET_RECEPCAO: "ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl",
        WS_MDFE_RECEPCAO_EVENTO: "ws/MDFeRecepcaoEvento/MDFeRecepcaoEvento.asmx?wsdl",
        WS_MDFE_CONSULTA: "ws/MDFeConsulta/MDFeConsulta.asmx?wsdl",
        WS_MDFE_SITUACAO: "ws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl",
        WS_MDFE_CONSULTA_NAO_ENCERRADOS: "ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl",
        WS_MDFE_DISTRIBUICAO: "ws/MDFeDistribuicaoDFe/MDFeDistribuicaoDFe.asmx?wsdl",
        WS_MDFE_RECEPCAO_SINC: "ws/MDFeRecepcaoSinc/MDFeRecepcaoSinc.asmx?wsdl",
    },
    AMBIENTE_HOMOLOGACAO: {
        "servidor": "mdfe-homologacao.svrs.rs.gov.br",
        WS_MDFE_RECEPCAO: "ws/MDFeRecepcao/MDFeRecepcao.asmx?wsdl",
        WS_MDFE_RET_RECEPCAO: "ws/MDFeRetRecepcao/MDFeRetRecepcao.asmx?wsdl",
        WS_MDFE_RECEPCAO_EVENTO: "ws/MDFeRecepcaoEvento/MDFeRecepcaoEvento.asmx?wsdl",
        WS_MDFE_CONSULTA: "ws/MDFeConsulta/MDFeConsulta.asmx?wsdl",
        WS_MDFE_SITUACAO: "ws/MDFeStatusServico/MDFeStatusServico.asmx?wsdl",
        WS_MDFE_CONSULTA_NAO_ENCERRADOS: "ws/MDFeConsNaoEnc/MDFeConsNaoEnc.asmx?wsdl",
        WS_MDFE_DISTRIBUICAO: "ws/MDFeDistribuicaoDFe/MDFeDistribuicaoDFe.asmx?wsdl",
        WS_MDFE_RECEPCAO_SINC: "ws/MDFeRecepcaoSinc/MDFeRecepcaoSinc.asmx?wsdl",
    }
}

QR_CODE_URL = "https://dfe-portal.svrs.rs.gov.br/mdfe/qrCode"

NAMESPACES = {
    "mdfe": "http://www.portalfiscal.inf.br/mdfe",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}

def localizar_url(servico, ambiente=2):
    dominio = SVC_RS[ambiente]["servidor"]
    complemento = SVC_RS[ambiente][servico]

    return "https://%s/%s" % (dominio, complemento)


class MDFe(DocumentoEletronico):
    _namespace = "http://www.portalfiscal.inf.br/mdfe"

    _edoc_situacao_arquivo_recebido_com_sucesso = "103"
    _edoc_situacao_servico_em_operacao = "107"
    _edoc_situacao_ja_enviado = ("100", "101", "132")

    _consulta_servico_ao_enviar = True
    _maximo_tentativas_consulta_recibo = 5

    def __init__(self, transmissao, uf, versao="3.00", ambiente="2",
                 mod="58"):
        super(MDFe, self).__init__(transmissao)
        self.versao = str(versao)
        self.ambiente = str(ambiente)
        self.uf = int(uf)
        self.mod = str(mod)

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        return proc_envio.resposta.cStat == \
            self._edoc_situacao_arquivo_recebido_com_sucesso

    def _aguarda_tempo_medio(self, proc_envio):
        time.sleep(float(proc_envio.resposta.infRec.tMed) * 1.3)

    def _edoc_situacao_em_processamento(self, proc_recibo):
        return proc_recibo.resposta.cStat == "105"

    def get_documento_id(self, edoc):
        return edoc.infMDFe.Id[:3], edoc.infMDFe.Id[3:]

    def monta_qrcode(self, chave):
        return f"{QR_CODE_URL}?chMDFe={chave}&tpAmb={self.ambiente}"

    def monta_qrcode_contingencia(self, edoc, xml_assinado):
        chave = edoc.infMDFe.Id.replace("MDFe", "")

        xml = ET.fromstring(xml_assinado)
        digest_value = xml.find('.//ds:DigestValue', namespaces=NAMESPACES).text
        digest_value_hex = binascii.hexlify(digest_value.encode()).decode()

        return f"{self.monta_qrcode(chave)}&sign={digest_value_hex}"

    def status_servico(self):
        raiz = retConsStatServMDFe.TConsStatServ(
            versao=self.versao,
            tpAmb=self.ambiente,
            cUF=self.uf,
            xServ="STATUS",
        )
        raiz.original_tagname_ = "consStatServMDFe"
        return self._post(
            raiz,
            localizar_url(WS_MDFE_SITUACAO, int(self.ambiente)),
            "mdfeStatusServicoMDF" ,
            retConsStatServMDFe
        )

    def consulta_documento(self, chave):
        raiz = retConsSitMDFe.TConsSitMDFe(
            versao=self.versao,
            tpAmb=self.ambiente,
            xServ="CONSULTAR",
            chMDFe=chave,
        )
        raiz.original_tagname_ = "consSitMDFe"
        return self._post(
            raiz,
            localizar_url(WS_MDFE_CONSULTA, int(self.ambiente)),
            "mdfeConsultaMDF",
            retConsSitMDFe
        )

    def consulta_nao_encerrados(self, cnpj):
        raiz = retConsMDFeNaoEnc.TConsMDFeNaoEnc(
            versao=self.versao,
            tpAmb=self.ambiente,
            xServ="CONSULTAR NÃO ENCERRADOS",
            CNPJ=cnpj,
        )
        raiz.original_tagname_ = "consMDFeNaoEnc"

        return self._post(
            raiz,
            localizar_url(WS_MDFE_CONSULTA_NAO_ENCERRADOS, int(self.ambiente)),
            "mdfeConsNaoEnc",
            retConsMDFeNaoEnc,
        )

    def envia_documento(self, edoc):
        """

        Exportar o documento
        Assinar o documento
        Adicionar o mesmo ao envio

        :param edoc:
        :return:
        """
        xml_assinado = self.assina_raiz(edoc, edoc.infMDFe.Id)

        raiz = retEnviMDFe.TEnviMDFe(
            versao=self.versao,
            idLote=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        )
        raiz.original_tagname_ = "enviMDFe"
        xml_envio_string, xml_envio_etree = self._generateds_to_string_etree(
            raiz
        )
        xml_envio_etree.append(etree.fromstring(xml_assinado))

        return self._post(
            xml_envio_etree,
            localizar_url(WS_MDFE_RECEPCAO, int(self.ambiente)),
            "mdfeRecepcaoLote",
            retEnviMDFe
        )

    def consulta_recibo(self, numero=False, proc_envio=False):
        if proc_envio:
            numero = proc_envio.resposta.infRec.nRec

        if not numero:
            return

        raiz = retConsReciMDFe.TConsReciMDFe(
            versao=self.versao,
            tpAmb=self.ambiente,
            nRec=numero,
        )
        raiz.original_tagname_ = "consReciMDFe"
        return self._post(
            raiz,
            localizar_url(WS_MDFE_RET_RECEPCAO, int(self.ambiente)),
            "mdfeRetRecepcao",
            retConsReciMDFe,
        )

    def monta_processo(self, edoc, proc_envio, proc_recibo):
        mdfe = proc_envio.envio_raiz.find('{' + self._namespace + '}MDFe')
        protocolos = proc_recibo.resposta.protMDFe
        if mdfe and protocolos:
            if type(protocolos) != list:
                protocolos = [protocolos]
            for protocolo in protocolos:
                mdfe_proc = procMDFe.mdfeProc(
                    versao=self.versao,
                    protMDFe=protocolo,
                )
                mdfe_proc.original_tagname_ = 'mdfeProc'
                xml_file, mdfe_proc = self._generateds_to_string_etree(mdfe_proc)
                proc_recibo.processo = mdfe_proc
                proc_recibo.processo_xml = \
                    self._generateds_to_string_etree(mdfe_proc)[0]
                proc_recibo.protocolo = protocolo

    def send_event(self, evento):
        raiz = retEventoMDFe.TEvento(versao="3.00", infEvento=evento)
        raiz.original_tagname_ = "eventoMDFe"
        xml_assinado = etree.fromstring(self.assina_raiz(raiz, raiz.infEvento.Id))

        return self._post(
            xml_assinado,
            localizar_url(WS_MDFE_RECEPCAO_EVENTO, int(self.ambiente)),
            "mdfeRecepcaoEvento",
            retEventoMDFe
        )

    def cancela_documento(self, chave, protocolo_autorizacao, justificativa,
                          data_hora_evento=False):
        tipo = "110111"
        sequencia = "1"
        data_hora_evento = data_hora_evento or self._hora_agora()

        cancelamento = evCancMDFe.evCancMDFe(
            descEvento="Cancelamento",
            nProt=protocolo_autorizacao,
            xJust=justificativa
        )
        cancelamento_string, _ = self._generateds_to_string_etree(cancelamento)

        raiz = evCancMDFe.infEventoType(
            Id="ID" + tipo + chave + sequencia.zfill(2),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chMDFe=chave,
            dhEvento=data_hora_evento,
            tpEvento=tipo,
            nSeqEvento=sequencia,
            detEvento=evCancMDFe.detEventoType(
                versaoEvento="3.00",
                anytypeobjs_=cancelamento_string
            ),
        )
        raiz.original_tagname_ = "infEvento"
        return self.send_event(raiz)

    def encerra_documento(self, chave, protocolo_autorizacao, estado, municipio,
                          data_hora_evento=False):
        tipo = "110112"
        sequencia = "1"
        data_hora_evento = data_hora_evento or self._hora_agora()

        encerramento = evEncMDFe.evEncMDFe(
            descEvento="Encerramento",
            dtEnc=self._data_hoje(),
            nProt=protocolo_autorizacao,
            cUF=estado,
            cMun=municipio
        )
        encerramento_string, _ = self._generateds_to_string_etree(encerramento)

        raiz = evEncMDFe.infEventoType(
            Id="ID" + tipo + chave + sequencia.zfill(2),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chMDFe=chave,
            dhEvento=data_hora_evento,
            tpEvento=tipo,
            nSeqEvento=sequencia,
            detEvento=evEncMDFe.detEventoType(
                versaoEvento="3.00",
                anytypeobjs_=encerramento_string
            ),
        )
        raiz.original_tagname_ = "infEvento"
        return self.send_event(raiz)
