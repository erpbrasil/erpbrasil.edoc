# Copyright (C) 2026  KMEE
"""NFS-e padrão nacional (DPS) pelo webservice municipal NotaControl/ISSNet.

Municípios como Goiânia adotaram o leiaute nacional (DPS 1.01), mas recebem a
DPS pelo webservice próprio da NotaControl, e não pelo Ambiente de Dados
Nacional (ADN). O payload é o mesmo; o transporte muda:

- SOAP 1.1 Document/Literal, namespace ``http://www.sped.fazenda.gov.br/nfse``,
  com ``nfseCabecMsg`` + ``nfseDadosMsg`` (XML aninhado, sem gzip/base64);
- a DPS vai dentro de um ``LoteDps`` (``RecepcionarLoteDpsSincrono``), e o
  lote também é assinado: são duas assinaturas, a da ``infDPS`` e a do lote;
- o WSDL só abre com TLS mútuo, por isso o envelope é montado aqui e não pelo
  zeep.

Este provedor não gera a DPS: recebe o XML dela pronto (ex.: serializado pelo
``nfelib``) e cuida de assinar, empacotar, transmitir e interpretar a resposta.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from lxml import etree

from erpbrasil.assinatura.assinatura import Assinatura
from erpbrasil.assinatura.certificado import ArquivoCertificado

_logger = logging.getLogger(__name__)

NS = "http://www.sped.fazenda.gov.br/nfse"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"
NSMAP = {"n": NS}

VERSAO = "1.01"
URL_BASE = "https://nfse.issnetonline.com.br/wsnfsenacional/{}/nfse.asmx"
# producao usa o caminho do municipio; homologacao e um ambiente unico
MUNICIPIOS = {
    5208707: "goiania",
}

AMBIENTE_PRODUCAO = "1"
AMBIENTE_HOMOLOGACAO = "2"

ALGORITMOS = {
    # o modelo oficial de lote da NotaControl (v1.01) usa RSA-SHA1
    "sha1": {"signature_algorithm": "rsa-sha1", "digest_algorithm": "sha1"},
    "sha256": {"signature_algorithm": "rsa-sha256", "digest_algorithm": "sha256"},
}


@dataclass
class MensagemRetorno:
    codigo: str
    mensagem: str
    correcao: str = ""
    identificacao_dps: str = ""

    def __str__(self):
        texto = f"{self.codigo} - {self.mensagem}"
        if self.correcao:
            texto += f" ({self.correcao})"
        if self.identificacao_dps:
            texto = f"[DPS {self.identificacao_dps}] {texto}"
        return texto


@dataclass
class RetornoNotaControl:
    operacao: str
    http_status: int
    xml_enviado: str
    xml_resposta: str
    sucesso: bool = False
    protocolo: str = ""
    numero_lote: str = ""
    nfse_xml: List[str] = field(default_factory=list)
    chaves_acesso: List[str] = field(default_factory=list)
    numeros_nfse: List[str] = field(default_factory=list)
    mensagens: List[MensagemRetorno] = field(default_factory=list)
    alertas: List[MensagemRetorno] = field(default_factory=list)
    urls: List[dict] = field(default_factory=list)

    @property
    def mensagem(self):
        return "\n".join(str(m) for m in self.mensagens)


def _texto(el, caminho):
    valor = el.findtext(caminho, namespaces=NSMAP)
    return (valor or "").strip()


def _sem_declaracao(xml):
    if isinstance(xml, bytes):
        xml = xml.decode("utf-8")
    xml = xml.strip()
    if xml.startswith("<?xml"):
        xml = xml[xml.index("?>") + 2 :].strip()
    return xml


class NotaControl:
    """Cliente do webservice NFS-e nacional da NotaControl.

    :param transmissao: ``erpbrasil.transmissao.TransmissaoSOAP`` (só o
        certificado é usado: assina as mensagens e identifica o TLS mútuo)
    :param ambiente: "1" produção, "2" homologação
    :param cidade_ibge: código IBGE do município (ex.: 5208707 Goiânia)
    :param algoritmo: "sha1" (padrão, conforme o modelo oficial) ou "sha256"
    :param session: ``requests.Session`` alternativa (testes)
    """

    def __init__(
        self,
        transmissao,
        ambiente,
        cidade_ibge,
        cnpj_prestador,
        im_prestador,
        algoritmo="sha1",
        session=None,
        timeout=60,
        verify=True,
    ):
        self._transmissao = transmissao
        self.ambiente = str(ambiente)
        self.cidade = int(cidade_ibge)
        self.cnpj_prestador = "".join(c for c in cnpj_prestador or "" if c.isdigit())
        self.im_prestador = (im_prestador or "").strip()
        if algoritmo not in ALGORITMOS:
            raise ValueError(f"Algoritmo de assinatura inválido: {algoritmo}")
        self.algoritmo = algoritmo
        self._session = session
        self.timeout = timeout
        self.verify = verify

    # ------------------------------------------------------------------ url

    @property
    def url(self):
        if self.ambiente == AMBIENTE_HOMOLOGACAO:
            return URL_BASE.format("homologacao")
        try:
            return URL_BASE.format(MUNICIPIOS[self.cidade])
        except KeyError:
            raise ValueError(
                f"Município {self.cidade} não configurado para a NotaControl"
            ) from None

    # ----------------------------------------------------------- assinatura

    def _assinador(self):
        return Assinatura(self._transmissao.certificado)

    def _assinar(self, element, reference):
        return self._assinador().assina_xml2(
            element, reference, **ALGORITMOS[self.algoritmo]
        )

    def assinar_dps(self, dps_xml):
        """Assina a ``infDPS`` de uma DPS (a Signature fica irmã da infDPS)."""
        root = etree.fromstring(_sem_declaracao(dps_xml).encode("utf-8"))
        inf = root.find("n:infDPS", NSMAP)
        if inf is None:
            raise ValueError("DPS sem infDPS")
        # uma DPS ja assinada (ex.: pelo nfelib com outro algoritmo) e
        # reassinada com o algoritmo deste webservice
        for sig in root.findall(f"{{{NS_DS}}}Signature"):
            root.remove(sig)
        return self._assinar(root, inf.get("Id"))

    def montar_lote(self, dps_assinadas, numero_lote):
        """Monta o ``EnviarLoteDpsSincronoEnvio`` com as DPS já assinadas.

        As DPS entram como elementos (não como texto) para que o lote seja
        um XML único; a assinatura de cada DPS continua válida porque a
        canonicalização é feita sobre a ``infDPS``.
        """
        envio = etree.Element(f"{{{NS}}}EnviarLoteDpsSincronoEnvio", nsmap={None: NS})
        lote = etree.SubElement(
            envio, f"{{{NS}}}LoteDps", Id=f"Lote{numero_lote}", versao=VERSAO
        )
        etree.SubElement(lote, f"{{{NS}}}NumeroLote").text = str(numero_lote)
        prestador = etree.SubElement(lote, f"{{{NS}}}Prestador")
        tag_doc = "CNPJ" if len(self.cnpj_prestador) == 14 else "CPF"
        etree.SubElement(prestador, f"{{{NS}}}{tag_doc}").text = self.cnpj_prestador
        etree.SubElement(prestador, f"{{{NS}}}IM").text = self.im_prestador
        etree.SubElement(lote, f"{{{NS}}}QuantidadeDps").text = str(len(dps_assinadas))
        lista = etree.SubElement(lote, f"{{{NS}}}ListaDps")
        for dps in dps_assinadas:
            lista.append(etree.fromstring(_sem_declaracao(dps).encode("utf-8")))
        return etree.tostring(envio, encoding=str)

    def assinar_lote(self, lote_xml, numero_lote):
        root = etree.fromstring(_sem_declaracao(lote_xml).encode("utf-8"))
        return self._assinar(root, f"Lote{numero_lote}")

    # ------------------------------------------------------------ transporte

    @staticmethod
    def envelope(operacao, dados_xml):
        cabecalho = (
            f'<cabecalho versao="{VERSAO}" xmlns="{NS}">'
            f"<versaoDados>{VERSAO}</versaoDados></cabecalho>"
        )
        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
            f' xmlns:nfse="{NS}">'
            "<soapenv:Header/><soapenv:Body>"
            f"<nfse:{operacao}>"
            f"<nfse:nfseCabecMsg>{cabecalho}</nfse:nfseCabecMsg>"
            f"<nfse:nfseDadosMsg>{_sem_declaracao(dados_xml)}</nfse:nfseDadosMsg>"
            f"</nfse:{operacao}>"
            "</soapenv:Body></soapenv:Envelope>"
        )

    def _http_post(self, operacao, envelope):
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f"{NS}/{operacao}",
        }
        if self._session is not None:
            return self._session.post(
                self.url,
                data=envelope.encode("utf-8"),
                headers=headers,
                timeout=self.timeout,
            )
        with ArquivoCertificado(self._transmissao.certificado, "w") as (key, cert):
            session = requests.Session()
            session.cert = (key, cert)
            session.verify = self.verify
            try:
                return session.post(
                    self.url,
                    data=envelope.encode("utf-8"),
                    headers=headers,
                    timeout=self.timeout,
                )
            finally:
                session.close()

    def _post(self, operacao, dados_xml):
        envelope = self.envelope(operacao, dados_xml)
        resposta = self._http_post(operacao, envelope)
        corpo = resposta.content.decode("utf-8", errors="replace")
        _logger.debug("NotaControl %s HTTP %s", operacao, resposta.status_code)
        return self.analisar_resposta(
            operacao, corpo, http_status=resposta.status_code, xml_enviado=dados_xml
        )

    # ------------------------------------------------------------- servicos

    def recepcionar_lote_dps_sincrono(self, dps_xml_list, numero_lote):
        """Assina as DPS, monta e assina o lote e transmite (síncrono)."""
        assinadas = [self.assinar_dps(dps) for dps in dps_xml_list]
        lote = self.assinar_lote(self.montar_lote(assinadas, numero_lote), numero_lote)
        return self._post("RecepcionarLoteDpsSincrono", lote)

    def _prestador_xml(self):
        tag_doc = "CNPJ" if len(self.cnpj_prestador) == 14 else "CPF"
        return (
            f"<Prestador><{tag_doc}>{self.cnpj_prestador}</{tag_doc}>"
            f"<IM>{self.im_prestador}</IM></Prestador>"
        )

    def consultar_nfse_dps(self, numero_dps, serie_dps):
        dados = (
            f'<ConsultarNfseDpsEnvio xmlns="{NS}">'
            f"<IdentificacaoDps><NumDPS>{int(numero_dps)}</NumDPS>"
            f"<SerieDPS>{serie_dps}</SerieDPS></IdentificacaoDps>"
            f"{self._prestador_xml()}</ConsultarNfseDpsEnvio>"
        )
        return self._post("ConsultarNfseDps", dados)

    def consultar_url_nfse(self, numero_dps, serie_dps):
        dados = (
            f'<ConsultarUrlNfseEnvio xmlns="{NS}">{self._prestador_xml()}'
            f"<IdentificacaoDps><NumDPS>{int(numero_dps)}</NumDPS>"
            f"<SerieDPS>{serie_dps}</SerieDPS></IdentificacaoDps>"
            f"<Pagina>1</Pagina></ConsultarUrlNfseEnvio>"
        )
        return self._post("ConsultarUrlNfse", dados)

    def consultar_dps_disponivel(self):
        """Próximo número de DPS disponível para o prestador (só NotaControl)."""
        dados = (
            f'<ConsultarDpsDisponivelEnvio xmlns="{NS}">{self._prestador_xml()}'
            f"</ConsultarDpsDisponivelEnvio>"
        )
        return self._post("ConsultarDpsDisponivel", dados)

    def cancelar_nfse(self, ped_reg_evento_xml):
        """Transmite o pedido de registro de evento (``pedRegEvento``).

        O pedido é assinado aqui, na ``infPedReg``. A NotaControl aceita
        apenas códigos de motivo específicos no cancelamento; a mensagem de
        erro de motivo inválido é genérica, então vale conferir o cMotivo.
        """
        ped = etree.fromstring(_sem_declaracao(ped_reg_evento_xml).encode("utf-8"))
        inf = ped.find("n:infPedReg", NSMAP)
        assinado = self._assinar(ped, inf.get("Id"))
        dados = (
            f'<CancelarNfseEnvio xmlns="{NS}">'
            f"{_sem_declaracao(assinado)}</CancelarNfseEnvio>"
        )
        return self._post("CancelarNfse", dados)

    # -------------------------------------------------------------- resposta

    @staticmethod
    def _mensagens(el, caminho):
        mensagens = []
        for m in el.iterfind(caminho, namespaces=NSMAP):
            ident = ""
            num = _texto(m, "n:IdentificacaoDps/n:NumDPS")
            if num:
                ident = f"{_texto(m, 'n:IdentificacaoDps/n:SerieDPS')}/{num}"
            codigo = _texto(m, "n:Codigo")
            if not codigo and not _texto(m, "n:Mensagem"):
                continue
            mensagens.append(
                MensagemRetorno(
                    codigo=codigo,
                    mensagem=_texto(m, "n:Mensagem"),
                    correcao=_texto(m, "n:Correcao"),
                    identificacao_dps=ident,
                )
            )
        return mensagens

    @classmethod
    def analisar_resposta(cls, operacao, xml_resposta, http_status=200, xml_enviado=""):
        retorno = RetornoNotaControl(
            operacao=operacao,
            http_status=http_status,
            xml_enviado=xml_enviado,
            xml_resposta=xml_resposta,
        )
        try:
            doc = etree.fromstring(_sem_declaracao(xml_resposta).encode("utf-8"))
        except etree.XMLSyntaxError:
            retorno.mensagens.append(
                MensagemRetorno("HTTP", f"Resposta inválida (HTTP {http_status})")
            )
            return retorno

        fault = doc.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
        if fault is not None:
            retorno.mensagens.append(
                MensagemRetorno(
                    fault.findtext("faultcode") or "SOAP",
                    (fault.findtext("faultstring") or "").strip(),
                )
            )
            return retorno

        # a resposta vem dentro do Body, as vezes como texto escapado
        corpo = doc
        body = doc.find("{http://schemas.xmlsoap.org/soap/envelope/}Body")
        if body is not None:
            corpo = next(iter(body), body)
            result = next(iter(corpo), None)
            if result is not None and result.tag.endswith("Result"):
                if len(result):
                    corpo = result[0]
                elif (result.text or "").strip().startswith("<"):
                    corpo = etree.fromstring(result.text.strip().encode("utf-8"))

        # respostas sem namespace (ex.: ConsultarUrlNfseResposta) sao normalizadas
        if not corpo.tag.startswith("{"):
            corpo = etree.fromstring(
                etree.tostring(corpo, encoding=str)
                .replace(f"<{corpo.tag}", f'<{corpo.tag} xmlns="{NS}"', 1)
                .encode("utf-8")
            )

        retorno.protocolo = _texto(corpo, "n:Protocolo")
        retorno.numero_lote = _texto(corpo, "n:NumeroLote")
        retorno.mensagens = cls._mensagens(
            corpo, "n:ListaMensagemRetorno/n:MensagemRetorno"
        ) + cls._mensagens(corpo, "n:ListaMensagemRetornoLote/n:MensagemRetorno")
        retorno.alertas = cls._mensagens(
            corpo, ".//n:ListaMensagemAlertaRetorno/n:MensagemRetorno"
        )
        for nfse in corpo.iterfind(".//n:CompNfse/n:Nfse", NSMAP):
            inf = nfse.find("n:infNFSe", NSMAP)
            retorno.nfse_xml.append(etree.tostring(nfse, encoding=str))
            if inf is not None:
                retorno.chaves_acesso.append((inf.get("Id") or "")[3:])
                retorno.numeros_nfse.append(_texto(inf, "n:nNFSe"))
        for link in corpo.iterfind(".//n:ListaLinks/n:Links", NSMAP):
            retorno.urls.append(
                {
                    "numero_nfse": _texto(link, "n:IdentificacaoNfse/n:nDFSe"),
                    "visualizacao": _texto(link, "n:UrlVisualizacaoNfse"),
                    "autenticidade": _texto(link, "n:UrlVerificaAutenticidade"),
                    "visualizacao_nacional": _texto(
                        link, "n:UrlVisualizacaoNfseNacional"
                    ),
                }
            )
        if operacao == "RecepcionarLoteDpsSincrono":
            # lote sincrono: autorizado e so quando a NFS-e volta na resposta
            retorno.sucesso = bool(retorno.nfse_xml)
        else:
            retorno.sucesso = http_status == 200 and not retorno.mensagens
        return retorno


def dps_numero_serie(dps_xml) -> Optional[tuple]:
    """(nDPS, serie) de uma DPS, para as consultas por identificação."""
    root = etree.fromstring(_sem_declaracao(dps_xml).encode("utf-8"))
    inf = root.find("n:infDPS", NSMAP)
    if inf is None:
        return None
    return _texto(inf, "n:nDPS"), _texto(inf, "n:serie")
