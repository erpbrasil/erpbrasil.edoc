# Copyright (C) 2026  KMEE
"""NFS-e pelo webservice do GissOnline (Eicon), versão 2.

O GissOnline V2 recebe RPS no leiaute ABRASF 2.04 ampliado com os grupos da
reforma tributária (tributos federais, comércio exterior, IBS/CBS, NBS), em
namespaces próprios (``http://www.giss.com.br/<mensagem>-v2_04.xsd``):

- SOAP 1.1 Document/Literal Wrapped, namespace ``http://nfse.abrasf.org.br``,
  com ``nfseCabecMsg`` + ``nfseDadosMsg`` (XML como texto) e retorno em
  ``outputXML``;
- o WSDL só abre com TLS mútuo (certificado ICP-Brasil), por isso o envelope
  é montado aqui e não pelo zeep;
- só o lote assíncrono é confiável: ``RecepcionarLoteRps`` devolve um
  protocolo e a nota sai em ``ConsultarLoteRps``;
- cada RPS é assinado (``InfDeclaracaoPrestacaoServico``) e depois o lote
  (``LoteRps``), nessa ordem, em RSA-SHA1: só o lote devolve E174.

Este provedor não gera o RPS: recebe o XML do ``EnviarLoteRpsEnvio`` pronto
(ex.: serializado com os bindings ``nfselib.giss``) e cuida de assinar,
empacotar, transmitir e interpretar a resposta.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List
from xml.sax.saxutils import escape

import requests
from lxml import etree

from erpbrasil.assinatura.assinatura import Assinatura
from erpbrasil.assinatura.certificado import ArquivoCertificado

_logger = logging.getLogger(__name__)

NS_SERVICO = "http://nfse.abrasf.org.br"
NS_GISS = "http://www.giss.com.br/{}-v2_04.xsd"
NS_TIPOS = NS_GISS.format("tipos")
NS_CABECALHO = NS_GISS.format("cabecalho")
NS_DS = "http://www.w3.org/2000/09/xmldsig#"
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"

VERSAO = "2.04"
URL_PRODUCAO = "https://ws-{}.giss.com.br/service-ws/nf/nfse-ws"
# a homologação é um ambiente único, compartilhado por todos os municípios,
# com regras e serviços que não são os do município em produção; é o host do
# Manual Técnico Serviços Prestados V1.8 (seção 4). O ws-homologacao-rtc
# recusa o tpRetPisCofins 0 que o XSD aceita (E160).
URL_HOMOLOGACAO = "https://v2-ws-homologacao.giss.com.br/service-ws/nf/nfse-ws"

# código IBGE -> prefixo do host de produção (nem sempre é o nome do município)
MUNICIPIOS = {
    2704302: "maceio",  # Maceió - AL
    3301009: "goytacazes",  # Campos dos Goytacazes - RJ
    3518800: "guarulhos",  # Guarulhos - SP
    3525904: "jundiai",  # Jundiaí - SP
    3547809: "santoandre",  # Santo André - SP
    3548500: "santos",  # Santos - SP
    3549805: "sjrp",  # São José do Rio Preto - SP
}

AMBIENTE_PRODUCAO = "1"
AMBIENTE_HOMOLOGACAO = "2"

# situação do lote em ConsultarLoteRps
LOTE_NAO_RECEBIDO = "1"
LOTE_NAO_PROCESSADO = "2"
LOTE_COM_ERRO = "3"
LOTE_PROCESSADO = "4"

# os códigos 3 e 5 são de uso exclusivo da prefeitura (E213)
CANCELAMENTO_ERRO_EMISSAO = "1"
CANCELAMENTO_SERVICO_NAO_PRESTADO = "2"
CANCELAMENTO_DUPLICIDADE = "4"
CODIGOS_CANCELAMENTO = (
    CANCELAMENTO_ERRO_EMISSAO,
    CANCELAMENTO_SERVICO_NAO_PRESTADO,
    CANCELAMENTO_DUPLICIDADE,
)


@dataclass
class MensagemRetorno:
    codigo: str
    mensagem: str
    correcao: str = ""
    identificacao_rps: str = ""

    def __str__(self):
        texto = f"{self.codigo} - {self.mensagem}"
        if self.correcao:
            texto += f" ({self.correcao})"
        if self.identificacao_rps:
            texto = f"[RPS {self.identificacao_rps}] {texto}"
        return texto


@dataclass
class NfseRetorno:
    """Uma NFS-e devolvida (``CompNfse``)."""

    xml: str
    numero: str = ""
    codigo_verificacao: str = ""
    data_emissao: str = ""
    numero_rps: str = ""
    serie_rps: str = ""
    chave_nacional: str = ""
    cancelada: bool = False


@dataclass
class RetornoGiss:
    operacao: str
    http_status: int
    xml_enviado: str
    xml_resposta: str
    protocolo: str = ""
    numero_lote: str = ""
    situacao: str = ""
    nfses: List[NfseRetorno] = field(default_factory=list)
    mensagens: List[MensagemRetorno] = field(default_factory=list)
    alertas: List[MensagemRetorno] = field(default_factory=list)
    data_cancelamento: str = ""

    @property
    def sucesso(self):
        return not self.mensagens and self.situacao != LOTE_COM_ERRO

    @property
    def em_processamento(self):
        return self.situacao in (LOTE_NAO_RECEBIDO, LOTE_NAO_PROCESSADO)

    @property
    def mensagem(self):
        return "\n".join(str(m) for m in self.mensagens)


def _local(el):
    return etree.QName(el).localname if isinstance(el.tag, str) else ""


def _filho(el, *nomes):
    """Desce por nomes locais: as respostas usam um namespace por mensagem."""
    for nome in nomes:
        if el is None:
            return None
        el = next((c for c in el if _local(c) == nome), None)
    return el


def _texto(el, *nomes):
    alvo = _filho(el, *nomes)
    return (alvo.text or "").strip() if alvo is not None else ""


def _todos(el, nome):
    return [d for d in el.iter() if _local(d) == nome]


def _sem_declaracao(xml):
    if isinstance(xml, bytes):
        xml = xml.decode("utf-8")
    xml = xml.strip()
    if xml.startswith("<?xml"):
        xml = xml[xml.index("?>") + 2 :].strip()
    return xml


def _namespaces_na_raiz(raiz):
    """Copia o documento com cada namespace declarado uma vez, na raiz.

    O ``XmlSerializer`` do xsdata declara o namespace dos tipos de novo em
    cada filho do ``LoteRps`` (``xmlns:ns1``), e o GissOnline recusa as
    assinaturas desse XML (E172). Na raiz vão o namespace da mensagem, como
    padrão, e o dos tipos, com o prefixo ``tipos``.
    """
    nsmap = {None: etree.QName(raiz).namespace}
    if nsmap[None] != NS_TIPOS:
        nsmap["tipos"] = NS_TIPOS
    nova = etree.Element(raiz.tag, attrib=raiz.attrib, nsmap=nsmap)
    pilha = [(raiz, nova)]
    while pilha:
        origem, destino = pilha.pop()
        destino.text = origem.text
        for filho in origem.iterchildren(tag=etree.Element):
            copia = etree.SubElement(destino, filho.tag, attrib=filho.attrib)
            copia.tail = filho.tail
            pilha.append((filho, copia))
    return nova


class Giss:
    """Cliente do webservice de NFS-e do GissOnline V2.

    :param transmissao: ``erpbrasil.transmissao.TransmissaoSOAP`` (só o
        certificado é usado: assina as mensagens e identifica o TLS mútuo)
    :param ambiente: "1" produção, "2" homologação
    :param cidade_ibge: código IBGE do município do prestador
    :param host: prefixo do host de produção de um município fora de
        ``MUNICIPIOS`` (``ws-<host>.giss.com.br``)
    :param session: ``requests.Session`` alternativa (testes)
    :param versao_cabecalho: ``versao`` e ``versaoDados`` do ``nfseCabecMsg``
    """

    def __init__(
        self,
        transmissao,
        ambiente,
        cidade_ibge,
        cnpj_prestador,
        im_prestador,
        host=None,
        session=None,
        timeout=60,
        verify=True,
        versao_cabecalho=VERSAO,
    ):
        self._transmissao = transmissao
        self.ambiente = str(ambiente)
        self.cidade = int(cidade_ibge)
        self.cnpj_prestador = "".join(c for c in cnpj_prestador or "" if c.isdigit())
        self.im_prestador = (im_prestador or "").strip()
        self.host = host
        self._session = session
        self.timeout = timeout
        self.verify = verify
        self.versao_cabecalho = versao_cabecalho

    # ------------------------------------------------------------------ url

    @property
    def url(self):
        if self.ambiente == AMBIENTE_HOMOLOGACAO:
            return URL_HOMOLOGACAO
        host = self.host or MUNICIPIOS.get(self.cidade)
        if not host:
            raise ValueError(f"Município {self.cidade} não configurado para o GissOnline")
        return URL_PRODUCAO.format(host)

    # ----------------------------------------------------------- assinatura

    def _assinar(self, element, reference):
        # RSA-SHA1 e o padrao do assina_xml2, e e o que o GissOnline exige
        return Assinatura(self._transmissao.certificado).assina_xml2(element, reference)

    def assinar_lote(self, lote_xml):
        """Assina cada RPS e depois o lote.

        A assinatura de cada RPS referencia o ``Id`` da
        ``InfDeclaracaoPrestacaoServico`` e fica irmã dela; a do lote
        referencia o ``Id`` do ``LoteRps``, nunca ``URI=""``, que invalidaria
        as dos RPS. O lote é assinado por último.
        """
        root = etree.fromstring(_sem_declaracao(lote_xml).encode("utf-8"))
        for assinatura in _todos(root, "Signature"):
            assinatura.getparent().remove(assinatura)
        root = _namespaces_na_raiz(root)
        lote = _filho(root, "LoteRps")
        if lote is None or not lote.get("Id"):
            raise ValueError("EnviarLoteRpsEnvio sem LoteRps com Id")
        ids = [inf.get("Id") for inf in _todos(root, "InfDeclaracaoPrestacaoServico")]
        if not ids or not all(ids):
            raise ValueError("RPS sem Id na InfDeclaracaoPrestacaoServico")
        xml = etree.tostring(root, encoding=str)
        for referencia in [*ids, lote.get("Id")]:
            xml = self._assinar(etree.fromstring(xml.encode("utf-8")), referencia)
            xml = self._recolocar_assinaturas(xml)
        return xml

    @staticmethod
    def _recolocar_assinaturas(xml):
        """Deixa cada assinatura logo depois do elemento que ela referencia.

        Com mais de uma assinatura no documento, versões do
        ``erpbrasil.assinatura`` movem a assinatura errada. A posição é
        refeita aqui a cada passo: a assinatura de um RPS fica dentro do
        ``LoteRps`` e entra no resumo do lote, então precisa estar no lugar
        antes de o lote ser assinado.
        """
        root = etree.fromstring(xml.encode("utf-8"))
        por_id = {el.get("Id"): el for el in root.iter() if el.get("Id")}
        for assinatura in _todos(root, "Signature"):
            referencia = _filho(assinatura, "SignedInfo", "Reference")
            alvo = por_id.get((referencia.get("URI") or "").lstrip("#"))
            if alvo is None or alvo.getnext() is assinatura:
                continue
            assinatura.tail = None
            alvo.addnext(assinatura)
        return etree.tostring(root, encoding=str)

    def _assinar_raiz(self, xml):
        """Consultas levam uma assinatura na raiz, sobre o documento todo."""
        return self._assinar(etree.fromstring(xml.encode("utf-8")), None)

    # ------------------------------------------------------------ transporte

    def envelope(self, operacao, dados_xml):
        versao = self.versao_cabecalho
        cabecalho = (
            f'<cabecalho versao="{versao}" xmlns="{NS_CABECALHO}"><versaoDados>{versao}</versaoDados></cabecalho>'
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<soapenv:Envelope xmlns:soapenv="{NS_SOAP}" xmlns:nfse="{NS_SERVICO}">'
            "<soapenv:Header/><soapenv:Body>"
            f"<nfse:{operacao}Request>"
            f"<nfseCabecMsg>{escape(cabecalho)}</nfseCabecMsg>"
            f"<nfseDadosMsg>{escape(_sem_declaracao(dados_xml))}</nfseDadosMsg>"
            f"</nfse:{operacao}Request>"
            "</soapenv:Body></soapenv:Envelope>"
        )

    def _http_post(self, operacao, envelope):
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f"{NS_SERVICO}/{operacao}",
        }
        dados = envelope.encode("utf-8")
        if self._session is not None:
            return self._session.post(self.url, data=dados, headers=headers, timeout=self.timeout)
        with ArquivoCertificado(self._transmissao.certificado, "w") as (key, cert):
            session = requests.Session()
            session.cert = (key, cert)
            session.verify = self.verify
            try:
                return session.post(self.url, data=dados, headers=headers, timeout=self.timeout)
            finally:
                session.close()

    def _post(self, operacao, dados_xml):
        resposta = self._http_post(operacao, self.envelope(operacao, dados_xml))
        corpo = resposta.content.decode("utf-8", errors="replace")
        _logger.debug("GissOnline %s HTTP %s", operacao, resposta.status_code)
        return self.analisar_resposta(operacao, corpo, http_status=resposta.status_code, xml_enviado=dados_xml)

    # ------------------------------------------------------------- mensagens

    def _prestador(self, pai, ns_pai, tag="Prestador"):
        prestador = etree.SubElement(pai, f"{{{ns_pai}}}{tag}")
        cpf_cnpj = etree.SubElement(prestador, f"{{{NS_TIPOS}}}CpfCnpj")
        tag_doc = "Cnpj" if len(self.cnpj_prestador) == 14 else "Cpf"
        etree.SubElement(cpf_cnpj, f"{{{NS_TIPOS}}}{tag_doc}").text = self.cnpj_prestador
        if self.im_prestador:
            etree.SubElement(prestador, f"{{{NS_TIPOS}}}InscricaoMunicipal").text = self.im_prestador
        return prestador

    @staticmethod
    def _raiz(mensagem, tag):
        ns = NS_GISS.format(mensagem)
        return etree.Element(f"{{{ns}}}{tag}", nsmap={None: ns, "tipos": NS_TIPOS}), ns

    def montar_consultar_lote_rps(self, protocolo):
        raiz, ns = self._raiz("consultar-lote-rps-envio", "ConsultarLoteRpsEnvio")
        self._prestador(raiz, ns)
        etree.SubElement(raiz, f"{{{ns}}}Protocolo").text = str(protocolo)
        return etree.tostring(raiz, encoding=str)

    def montar_consultar_nfse_rps(self, numero, serie, tipo="1"):
        raiz, ns = self._raiz("consultar-nfse-rps-envio", "ConsultarNfseRpsEnvio")
        rps = etree.SubElement(raiz, f"{{{ns}}}IdentificacaoRps")
        etree.SubElement(rps, f"{{{NS_TIPOS}}}Numero").text = str(int(numero))
        etree.SubElement(rps, f"{{{NS_TIPOS}}}Serie").text = str(serie)
        etree.SubElement(rps, f"{{{NS_TIPOS}}}Tipo").text = str(tipo)
        self._prestador(raiz, ns)
        return etree.tostring(raiz, encoding=str)

    def montar_cancelar_nfse(self, numero_nfse, codigo_cancelamento):
        if str(codigo_cancelamento) not in CODIGOS_CANCELAMENTO:
            raise ValueError(
                f"Código de cancelamento {codigo_cancelamento} inválido: o "
                f"contribuinte só pode usar {', '.join(CODIGOS_CANCELAMENTO)}"
            )
        raiz, ns = self._raiz("cancelar-nfse-envio", "CancelarNfseEnvio")
        pedido = etree.SubElement(raiz, f"{{{ns}}}Pedido")
        inf = etree.SubElement(
            pedido,
            f"{{{NS_TIPOS}}}InfPedidoCancelamento",
            Id=f"cancelamento{int(numero_nfse)}",
        )
        nfse = etree.SubElement(inf, f"{{{NS_TIPOS}}}IdentificacaoNfse")
        etree.SubElement(nfse, f"{{{NS_TIPOS}}}Numero").text = str(int(numero_nfse))
        cpf_cnpj = etree.SubElement(nfse, f"{{{NS_TIPOS}}}CpfCnpj")
        tag_doc = "Cnpj" if len(self.cnpj_prestador) == 14 else "Cpf"
        etree.SubElement(cpf_cnpj, f"{{{NS_TIPOS}}}{tag_doc}").text = self.cnpj_prestador
        if self.im_prestador:
            etree.SubElement(nfse, f"{{{NS_TIPOS}}}InscricaoMunicipal").text = self.im_prestador
        etree.SubElement(nfse, f"{{{NS_TIPOS}}}CodigoMunicipio").text = str(self.cidade)
        etree.SubElement(inf, f"{{{NS_TIPOS}}}CodigoCancelamento").text = str(codigo_cancelamento)
        return etree.tostring(raiz, encoding=str)

    # ------------------------------------------------------------- servicos

    def recepcionar_lote_rps(self, lote_xml):
        """Assina e transmite o lote; a resposta traz o protocolo."""
        return self._post("RecepcionarLoteRps", self.assinar_lote(lote_xml))

    def consultar_lote_rps(self, protocolo):
        dados = self._assinar_raiz(self.montar_consultar_lote_rps(protocolo))
        return self._post("ConsultarLoteRps", dados)

    def aguardar_lote(self, protocolo, tentativas=6, espera=3.0):
        """Consulta o lote até ele sair de "não processado".

        O manual de retorno recomenda esperar de 3 a 5 segundos e repetir com
        recuo. Devolve a última resposta, que ainda pode estar em
        processamento: quem chama decide se consulta de novo mais tarde.
        """
        retorno = None
        for tentativa in range(tentativas):
            if tentativa:
                time.sleep(espera * tentativa)
            retorno = self.consultar_lote_rps(protocolo)
            if not retorno.em_processamento:
                break
        return retorno

    def consultar_nfse_rps(self, numero, serie, tipo="1"):
        """Consulta a NFS-e de um RPS.

        É a chave de idempotência: depois de uma queda de conexão, consultar
        pelo RPS antes de reenviar o lote (E10, E71 e E233 são lote ou RPS já
        enviado).
        """
        dados = self._assinar_raiz(self.montar_consultar_nfse_rps(numero, serie, tipo))
        return self._post("ConsultarNfsePorRps", dados)

    def cancelar_nfse(self, numero_nfse, codigo_cancelamento=CANCELAMENTO_ERRO_EMISSAO):
        pedido = self.montar_cancelar_nfse(numero_nfse, codigo_cancelamento)
        referencia = f"cancelamento{int(numero_nfse)}"
        dados = self._assinar(etree.fromstring(pedido.encode("utf-8")), referencia)
        return self._post("CancelarNfse", self._recolocar_assinaturas(dados))

    # -------------------------------------------------------------- resposta

    @staticmethod
    def _mensagens(corpo, lista):
        mensagens = []
        for bloco in _todos(corpo, lista):
            for m in bloco:
                if _local(m) != "MensagemRetorno":
                    continue
                codigo, texto = _texto(m, "Codigo"), _texto(m, "Mensagem")
                if not codigo and not texto:
                    continue
                rps = _filho(m, "IdentificacaoRps")
                ident = ""
                if rps is not None:
                    ident = f"{_texto(rps, 'Serie')}/{_texto(rps, 'Numero')}"
                mensagens.append(
                    MensagemRetorno(
                        codigo=codigo,
                        mensagem=texto,
                        correcao=_texto(m, "Correcao"),
                        identificacao_rps=ident,
                    )
                )
        return mensagens

    @staticmethod
    def _nfse(comp):
        inf = _filho(comp, "Nfse", "InfNfse")
        rps = _filho(
            inf,
            "DeclaracaoPrestacaoServico",
            "InfDeclaracaoPrestacaoServico",
            "Rps",
            "IdentificacaoRps",
        )
        return NfseRetorno(
            xml=etree.tostring(comp, encoding=str),
            numero=_texto(inf, "Numero"),
            codigo_verificacao=_texto(inf, "CodigoVerificacao"),
            data_emissao=_texto(inf, "DataEmissao"),
            numero_rps=_texto(rps, "Numero"),
            serie_rps=_texto(rps, "Serie"),
            chave_nacional=_texto(comp, "ChaveNotaNacional"),
            cancelada=_filho(comp, "NfseCancelamento") is not None,
        )

    @classmethod
    def analisar_resposta(cls, operacao, xml_resposta, http_status=200, xml_enviado=""):
        retorno = RetornoGiss(
            operacao=operacao,
            http_status=http_status,
            xml_enviado=xml_enviado,
            xml_resposta=xml_resposta,
        )
        try:
            doc = etree.fromstring(_sem_declaracao(xml_resposta).encode("utf-8"))
        except (etree.XMLSyntaxError, ValueError):
            retorno.mensagens.append(MensagemRetorno("HTTP", f"Resposta inválida (HTTP {http_status})"))
            return retorno

        fault = next(iter(_todos(doc, "Fault")), None)
        if fault is not None:
            retorno.mensagens.append(
                MensagemRetorno(
                    _texto(fault, "faultcode") or "SOAP",
                    _texto(fault, "faultstring"),
                )
            )
            return retorno

        # a resposta vem como texto em outputXML, dentro do Body
        corpo = doc
        saida = next(iter(_todos(doc, "outputXML")), None)
        if saida is not None:
            if len(saida):
                corpo = saida[0]
            elif (saida.text or "").strip().startswith("<"):
                try:
                    corpo = etree.fromstring(_sem_declaracao(saida.text).encode("utf-8"))
                except etree.XMLSyntaxError:
                    retorno.mensagens.append(MensagemRetorno("XML", "outputXML não é um XML válido"))
                    return retorno

        retorno.protocolo = _texto(corpo, "Protocolo")
        retorno.numero_lote = _texto(corpo, "NumeroLote")
        retorno.situacao = _texto(corpo, "Situacao")
        retorno.mensagens = cls._mensagens(corpo, "ListaMensagemRetorno")
        retorno.mensagens += cls._mensagens(corpo, "ListaMensagemRetornoLote")
        retorno.alertas = cls._mensagens(corpo, "ListaMensagemAlertaRetorno")
        retorno.nfses = [cls._nfse(comp) for comp in _todos(corpo, "CompNfse")]
        cancelamento = _filho(corpo, "RetCancelamento", "NfseCancelamento")
        retorno.data_cancelamento = _texto(cancelamento, "Confirmacao", "DataHora")
        if http_status >= 400 and not retorno.mensagens:
            retorno.mensagens.append(MensagemRetorno("HTTP", f"Erro de transporte (HTTP {http_status})"))
        return retorno
