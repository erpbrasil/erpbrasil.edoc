# coding=utf-8
# Copyright (C) 2023 Ygor de Carvalho - KMEE

from erpbrasil.edoc.nfe import NFe, SIGLA_ESTADO
import hashlib

try:
    from nfelib.v4_00.retEnviNFe import infNFeSuplType
except ImportError:
    pass

NFCE_AMBIENTE_PRODUCAO = "1"
NFCE_AMBIENTE_HOMOLOGACAO = "2"

ESTADO_QRCODE = {
    'AC': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaznet.ac.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.hml.sefaznet.ac.gov.br/nfce/qrcode?p=',
    },
    'AL': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.sefaz.al.gov.br/QRCode/consultarNFCe.jsp?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://nfce.sefaz.al.gov.br/QRCode/consultarNFCe.jsp?p=',
    },
    'AM': {
        NFCE_AMBIENTE_PRODUCAO: 'http://sistemas.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homnfce.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp?p=',
    },
    'AP': {
        NFCE_AMBIENTE_PRODUCAO: 'https://www.sefaz.ap.gov.br/nfce/nfcep.php?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://www.sefaz.ap.gov.br/nfcehml/nfce.php?p=',
    },
    'BA': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfe.sefaz.ba.gov.br/servicos/nfce/qrcode.aspx?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://hnfe.sefaz.ba.gov.br/servicos/nfce/qrcode.aspx?p=',
    },
    'CE': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.sefaz.ce.gov.br/pages/ShowNFCe.html?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://nfceh.sefaz.ce.gov.br/pages/ShowNFCe.html?p=',
    },
    'DF': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.fazenda.df.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.fazenda.df.gov.br/nfce/qrcode?p=',
    },
    'ES': {
        NFCE_AMBIENTE_PRODUCAO: 'http://app.sefaz.es.gov.br/ConsultaNFCe?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.es.gov.br/ConsultaNFCe?p=',
    },
    'GO': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfe.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homolog.sefaz.go.gov.br/nfeweb/sites/nfce/danfeNFCe?p=',
    },
    'MA': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.sefaz.ma.gov.br/portal/consultarNFCe.jsp?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.ma.gov.br/portal/consultarNFCe.jsp?p=',
    },
    'MG': {
        NFCE_AMBIENTE_PRODUCAO: 'https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/qrcode.xhtml?p=',
    },
    'MS': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.dfe.ms.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.dfe.ms.gov.br/nfce/qrcode?p=',
    },
    'MT': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaz.mt.gov.br/nfce/consultanfce?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.mt.gov.br/nfce/consultanfce?p=',
    },
    'PA': {
        NFCE_AMBIENTE_PRODUCAO: 'https://appnfc.sefa.pa.gov.br/portal/view/consultas/nfce/nfceForm.seam?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://appnfc.sefa.pa.gov.br/portal-homologacao/view/consultas/nfce/nfceForm.seam?p=',
    },
    'PB': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaz.pb.gov.br/nfce?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.sefaz.pb.gov.br/nfcehom?p=',
    },
    'PE': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.sefaz.pe.gov.br/nfce/consulta?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://nfcehomolog.sefaz.pe.gov.br/nfce/consulta?p=',
    },
    'PI': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaz.pi.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.sefaz.pi.gov.br/nfce/qrcode?p=',
    },
    'PR': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.fazenda.pr.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.fazenda.pr.gov.br/nfce/qrcode?p=',
    },
    'RJ': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www4.fazenda.rj.gov.br/consultaNFCe/QRCode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www4.fazenda.rj.gov.br/consultaNFCe/QRCode?p=',
    },
    'RN': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.set.rn.gov.br/consultarNFCe.aspx?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://hom.nfce.set.rn.gov.br/consultarNFCe.aspx?p=',
    },
    'RO': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.nfce.sefin.ro.gov.br/consultanfce/consulta.jsp?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.nfce.sefin.ro.gov.br/consultanfce/consulta.jsp?p=',
    },
    'RR': {
        NFCE_AMBIENTE_PRODUCAO: 'https://www.sefaz.rr.gov.br/nfce/servlet/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://200.174.88.103:8080/nfce/servlet/qrcode?p=',
    },
    'RS': {
        NFCE_AMBIENTE_PRODUCAO: 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx?p=',
    },
    'SC': {
        NFCE_AMBIENTE_PRODUCAO: 'https://sat.sef.sc.gov.br/nfce/consulta?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://hom.sat.sef.sc.gov.br/nfce/consulta?p=',
    },
    'SE': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.nfce.se.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.hom.nfe.se.gov.br/nfce/qrcode?p=',
    },
    'SP': {
        NFCE_AMBIENTE_PRODUCAO: 'https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://www.homologacao.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=',
    },
    'TO': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaz.to.gov.br/nfce/qrcode?p=',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.to.gov.br/nfce/qrcode?p=',
    },
}

ESTADO_CONSULTA_NFCE = {
    'AC': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaznet.ac.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaznet.ac.gov.br/nfce/consulta',
    },
    'AL': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.al.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.al.gov.br/nfce/consulta',
    },
    'AM': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.am.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.am.gov.br/nfce/consulta',
    },
    'AP': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.ap.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.ap.gov.br/nfce/consulta',
    },
    'BA': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.ba.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://hinternet.sefaz.ba.gov.br/nfce/consulta',
    },
    'CE': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.ce.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.ce.gov.br/nfce/consulta',
    },
    'DF': {
        NFCE_AMBIENTE_PRODUCAO: 'www.fazenda.df.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.fazenda.df.gov.br/nfce/consulta',
    },
    'ES': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.es.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.es.gov.br/nfce/consulta',
    },
    'GO': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.go.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.go.gov.br/nfce/consulta',
    },
    'MA': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.ma.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.ma.gov.br/nfce/consulta',
    },
    'MG': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.fazenda.mg.gov.br/portalnfce',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://hnfce.fazenda.mg.gov.br/portalnfce/',
    },
    'MS': {
        NFCE_AMBIENTE_PRODUCAO: 'www.dfe.ms.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.dfe.ms.gov.br/nfce/consulta',
    },
    'MT': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.sefaz.mt.gov.br/nfce/consultanfce',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.mt.gov.br/nfce/consultanfce',
    },
    'PA': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefa.pa.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefa.pa.gov.br/nfce/consulta',
    },
    'PB': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.pb.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.pb.gov.br/nfcehom',
    },
    'PE': {
        NFCE_AMBIENTE_PRODUCAO: 'http://nfce.sefaz.pe.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://nfce.sefaz.pe.gov.br/nfce/consulta',
    },
    'PI': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.pi.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.pi.gov.br/nfce/consulta',
    },
    'PR': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.fazenda.pr.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.fazenda.pr.gov.br/nfce/consulta',
    },
    'RJ': {
        NFCE_AMBIENTE_PRODUCAO: 'www.fazenda.rj.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.fazenda.rj.gov.br/nfce/consulta',
    },
    'RN': {
        NFCE_AMBIENTE_PRODUCAO: 'www.set.rn.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.set.rn.gov.br/nfce/consulta',
    },
    'RO': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefin.ro.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefin.ro.gov.br/nfce/consulta',
    },
    'RR': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.rr.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.rr.gov.br/nfce/consulta',
    },
    'RS': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.rs.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'www.sefaz.rs.gov.br/nfce/consulta',
    },
    'SC': {
        NFCE_AMBIENTE_PRODUCAO: 'https://sat.sef.sc.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://hom.sat.sef.sc.gov.br/nfce/consulta',
    },
    'SE': {
        NFCE_AMBIENTE_PRODUCAO: 'http://www.nfce.se.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://www.hom.nfe.se.gov.br/nfce/consulta',
    },
    'SP': {
        NFCE_AMBIENTE_PRODUCAO: 'https://www.nfce.fazenda.sp.gov.br/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'https://www.homologacao.nfce.fazenda.sp.gov.br/consulta',
    },
    'TO': {
        NFCE_AMBIENTE_PRODUCAO: 'www.sefaz.to.gov.br/nfce/consulta',
        NFCE_AMBIENTE_HOMOLOGACAO: 'http://homologacao.sefaz.to.gov.br/nfce/consulta.jsf',
    },
}


class NFCe(NFe):
    def __init__(self, transmissao, uf, versao="4.00", ambiente="2", mod="65",
                 qrcode_versao="2", csc_token=None, csc_code=None):
        super(NFCe, self).__init__(transmissao, uf, versao, ambiente)
        self.mod = str(mod)
        self.qrcode_versao = str(qrcode_versao)
        self.csc_token = str(csc_token)
        self.csc_code = str(csc_code)

    def monta_qrcode(self, edoc):
        nfce_chave = edoc.infNFe.Id.replace("NFe", "")
        pre_qrcode = f"{nfce_chave}|{self.qrcode_versao}|{self.ambiente}|{self.csc_token}"
        pre_qrcode_with_csc = pre_qrcode + f"{self.csc_code}"
        hash_object = hashlib.sha1(bytes(pre_qrcode_with_csc, "utf-8"))
        qr_hash = hash_object.hexdigest().upper()
        qrcode = f"{ESTADO_QRCODE[SIGLA_ESTADO[str(self.uf)]][self.ambiente]}" + pre_qrcode + f"|{qr_hash}"
        edoc.infNFeSupl = infNFeSuplType(qrCode=qrcode, urlChave=self.consulta_qrcode_url)

    @property
    def consulta_qrcode_url(self):
        return ESTADO_CONSULTA_NFCE[SIGLA_ESTADO[str(self.uf)]][self.ambiente]
