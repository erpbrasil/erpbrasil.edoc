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
    # Consulta Status
    from nfelib.mdfe.bindings.v3_0.cons_stat_serv_mdfe_v3_00 import ConsStatServMdfe
    from nfelib.mdfe.bindings.v3_0.ret_cons_stat_serv_mdfe_v3_00 import RetConsStatServMdfe

    # Consulta Documento
    from nfelib.mdfe.bindings.v3_0.cons_sit_mdfe_v3_00 import ConsSitMdfe
    from nfelib.mdfe.bindings.v3_0.ret_cons_sit_mdfe_v3_00 import RetConsSitMdfe

    # Consulta Não Encerrados
    from nfelib.mdfe.bindings.v3_0.cons_mdfe_nao_enc_v3_00 import ConsMdfeNaoEnc
    from nfelib.mdfe.bindings.v3_0.ret_cons_mdfe_nao_enc_v3_00 import RetConsMdfeNaoEnc

    # Envio
    from nfelib.mdfe.bindings.v3_0.envi_mdfe_v3_00 import EnviMdfe
    from nfelib.mdfe.bindings.v3_0.ret_envi_mdfe_v3_00 import RetEnviMdfe

    # Consulta Recibo
    from nfelib.mdfe.bindings.v3_0.cons_reci_mdfe_v3_00 import ConsReciMdfe
    from nfelib.mdfe.bindings.v3_0.ret_cons_reci_mdfe_v3_00 import RetConsReciMdfe

    # Processamento
    from nfelib.mdfe.bindings.v3_0.proc_mdfe_v3_00 import MdfeProc

    # Eventos
    from nfelib.mdfe.bindings.v3_0.evento_mdfe_v3_00 import EventoMdfe
    from nfelib.mdfe.bindings.v3_0.ret_evento_mdfe_v3_00 import RetEventoMdfe
    from nfelib.mdfe.bindings.v3_0.ev_canc_mdfe_v3_00 import EvCancMdfe
    from nfelib.mdfe.bindings.v3_0.ev_enc_mdfe_v3_00 import EvEncMdfe
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

    def _verifica_servico_em_operacao(self, proc_servico):
        return proc_servico.resposta.cStat == self._edoc_situacao_servico_em_operacao

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
        return self._post(
            ConsStatServMdfe(tpAmb=self.ambiente, versao=self.versao),
            localizar_url(WS_MDFE_SITUACAO, int(self.ambiente)),
            "mdfeStatusServicoMDF" ,
            RetConsStatServMdfe
        )

    def consulta_documento(self, chave):
        raiz = ConsSitMdfe(
            versao=self.versao,
            tpAmb=self.ambiente,
            chMDFe=chave,
        )
        return self._post(
            raiz,
            localizar_url(WS_MDFE_CONSULTA, int(self.ambiente)),
            "mdfeConsultaMDF",
            RetConsSitMdfe
        )

    def consulta_nao_encerrados(self, cnpj):
        raiz = ConsMdfeNaoEnc(
            versao=self.versao,
            tpAmb=self.ambiente,
            CNPJ=cnpj,
        )
        return self._post(
            raiz,
            localizar_url(WS_MDFE_CONSULTA_NAO_ENCERRADOS, int(self.ambiente)),
            "mdfeConsNaoEnc",
            RetConsMdfeNaoEnc,
        )

    def envia_documento(self, edoc):
        """

        Exportar o documento
        Assinar o documento
        Adicionar o mesmo ao envio

        :param edoc:
        :return:
        """
        raiz = EnviMdfe(
            versao=self.versao,
            idLote=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            MDFe=edoc
        )
        xml_assinado = self.assina_raiz(raiz, edoc.infMDFe.Id)
        return self._post(
            xml_assinado,
            localizar_url(WS_MDFE_RECEPCAO, int(self.ambiente)),
            "mdfeRecepcaoLote",
            RetEnviMdfe
        )

    def consulta_recibo(self, numero=False, proc_envio=False):
        if proc_envio:
            numero = proc_envio.resposta.infRec.nRec

        if not numero:
            return

        raiz = ConsReciMdfe(
            versao=self.versao,
            tpAmb=self.ambiente,
            nRec=numero,
        )
        return self._post(
            raiz,
            localizar_url(WS_MDFE_RET_RECEPCAO, int(self.ambiente)),
            "mdfeRetRecepcao",
            RetConsReciMdfe,
        )

    def monta_processo(self, edoc, proc_envio, proc_recibo):
        mdfe = proc_envio.envio_raiz.find('{' + self._namespace + '}MDFe')
        protocolos = proc_recibo.resposta.protMDFe
        if mdfe and protocolos:
            if type(protocolos) != list:
                protocolos = [protocolos]
            for protocolo in protocolos:
                mdfe_proc = MdfeProc(versao=self.versao, protMDFe=protocolo)
                proc_recibo.processo = mdfe_proc
                proc_recibo.processo_xml = mdfe_proc.to_xml()
                proc_recibo.protocolo = protocolo

    def envia_evento(self, evento, tipo, chave, sequencia="001", data_hora=False):
        inf_evento = EventoMdfe.InfEvento(
            Id="ID" + tipo + chave + sequencia.zfill(2),
            cOrgao=self.uf,
            tpAmb=self.ambiente,
            CNPJ=chave[6:20],
            chMDFe=chave,
            dhEvento=data_hora or self._hora_agora(),
            tpEvento=tipo,
            nSeqEvento=sequencia,
            detEvento=EventoMdfe.InfEvento.DetEvento(
                versaoEvento="3.00",
                any_element=evento
            ),
        )
        raiz = EventoMdfe(versao="3.00", infEvento=inf_evento)
        xml_assinado = etree.fromstring(self.assina_raiz(raiz, raiz.infEvento.Id))

        return self._post(
            xml_assinado,
            localizar_url(WS_MDFE_RECEPCAO_EVENTO, int(self.ambiente)),
            "mdfeRecepcaoEvento",
            RetEventoMdfe
        )

    def cancela_documento(self, chave, protocolo_autorizacao, justificativa,
                          data_hora_evento=False):
        evento_canc = EvCancMdfe(
            descEvento="Cancelamento",
            nProt=protocolo_autorizacao,
            xJust=justificativa
        )
        return self.envia_evento(
            evento=evento_canc,
            tipo="110111",
            chave=chave,
            data_hora=data_hora_evento
        )

    def encerra_documento(self, chave, protocolo_autorizacao, estado, municipio,
                          data_hora_evento=False):
        encerramento = EvEncMdfe(
            descEvento="Encerramento",
            dtEnc=self._data_hoje(),
            nProt=protocolo_autorizacao,
            cUF=estado,
            cMun=municipio
        )
        return self.envia_evento(
            evento=encerramento,
            tipo="110112",
            chave=chave,
            data_hora=data_hora_evento
        )
