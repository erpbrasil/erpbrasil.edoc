# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import datetime
import time

from lxml import etree

from erpbrasil.edoc.edoc import DocumentoEletronico

try:

    from nfelib.bindings.nfe.v4_0.proc_nfe_v4_00 import NfeProc
    from nfelib.bindings.nfe.v4_0.inut_nfe_v4_00 import InutNfe
    from nfelib.bindings.nfe.v4_0.ret_inut_nfe_v4_00 import RetInutNfe
    from nfelib.bindings.nfe.v4_0.cons_stat_serv_v4_00 import ConsStatServ
    from nfelib.bindings.nfe.v4_0.ret_cons_stat_serv_v4_00 import RetConsStatServ
    from nfelib.bindings.nfe.v4_0.cons_sit_nfe_v4_00 import ConsSitNfe
    from nfelib.bindings.nfe.v4_0.ret_cons_sit_nfe_v4_00 import RetConsSitNfe
    from nfelib.bindings.nfe.v4_0.envi_nfe_v4_00 import EnviNfe
    from nfelib.bindings.nfe.v4_0.ret_envi_nfe_v4_00 import RetEnviNfe
    from nfelib.bindings.nfe.v4_0.cons_reci_nfe_v4_00 import ConsReciNfe
    from nfelib.bindings.nfe.v4_0.ret_cons_reci_nfe_v4_00 import RetConsReciNfe
    from nfelib.bindings.nfe_dist_dfe.v1_0 import DistDfeInt
    from nfelib.bindings.nfe_dist_dfe.v1_0 import RetDistDfeInt
    from nfelib.bindings.nfe_evento_generico.v1_0.env_evento_v1_00 import EnvEvento as EnvEventoGenerico
    from nfelib.bindings.nfe_evento_generico.v1_0.leiaute_evento_v1_00 import Tevento
    from nfelib.bindings.nfe_evento_cce.v1_0.leiaute_cce_v1_00 import Tevento as TeventoCCe
    from nfelib.bindings.nfe_evento_generico.v1_0.ret_env_evento_v1_00 import RetEnvEvento as RetEnvEventoGenerico
    from nfelib.bindings.nfe_evento_cancel.v1_0.evento_canc_nfe_v1_00 import Evento as EventoCancNfe
    from nfelib.bindings.nfe_evento_cce.v1_0.cce_v1_00 import Evento as EventoCCe
    from nfelib.bindings.nfe_evento_cce.v1_0.ret_env_cce_v1_00 import RetEnvEvento as RetEnvEventoCCe

    # xsd Consulta Cadastro
    # TODO PROCESSAR OS SCHEMAS NO XSDATA
    #from nfelib.bindings.nfe_cons.v2_0.cons_sit_nfe_v2_01 import ConsSitNfe
    #from nfelib.bindings.nfe_cons.v2_0.ret_cons_sit_nfe_v2_01 import RetConsSitNfe

except ImportError:
    pass


TEXTO_CARTA_CORRECAO = """A Carta de Correcao e disciplinada pelo paragrafo \
1o-A do art. 7o do Convenio S/N, de 15 de dezembro de 1970 e \
pode ser utilizada para regularizacao de erro ocorrido na \
emissao de documento fiscal, desde que o erro nao esteja \
relacionado com: I - as variaveis que determinam o valor do \
imposto tais como: base de calculo, aliquota, diferenca de \
preco, quantidade, valor da operacao ou da prestacao; II - \
a correcao de dados cadastrais que implique mudanca do \
remetente ou do destinatario; III - a data de emissao \
ou de saida."""

WS_DFE_DISTRIBUICAO = 'NFeDistribuicaoDFe'
WS_DOWNLOAD_NFE = 'nfeDistDfeInteresse'
WS_NFCE_CONSULTA_DESTINADAS = 'NfeConsultaDest'
WS_NFCE_QR_CODE = 'NfeQRCode'
WS_NFE_AUTORIZACAO = 'NfeAutorizacao'
WS_NFE_CADASTRO = 'NfeConsultaCadastro'

WS_NFE_CONSULTA = 'NfeConsultaProtocolo'
WS_NFE_INUTILIZACAO = 'NfeInutilizacao'
WS_NFE_RECEPCAO_EVENTO = 'RecepcaoEvento'
WS_NFE_RET_AUTORIZACAO = 'NfeRetAutorizacao'

WS_NFE_SITUACAO = 'NfeStatusServico'

AMBIENTE_PRODUCAO = 1
AMBIENTE_HOMOLOGACAO = 2

NFE_MODELO = '55'
NFCE_MODELO = '65'

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

SVRS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl',  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'nfe-homologacao.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl',  # noqa
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFCE_QR_CODE: 'http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'nfce-homologacao.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFCE_QR_CODE: 'http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?',
        }
    }
}

SVAN = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'www.sefazvirtual.fazenda.gov.br',
        WS_NFE_INUTILIZACAO: 'NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl',
        WS_NFE_CONSULTA: 'NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
        WS_NFE_SITUACAO: 'NFeStatusServico4/NFeStatusServico4.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
        WS_NFE_AUTORIZACAO: 'NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'hom.sefazvirtual.fazenda.gov.br',
        WS_NFE_INUTILIZACAO: 'NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl',
        WS_NFE_CONSULTA: 'NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
        WS_NFE_SITUACAO: 'NFeStatusServico4/NFeStatusServico4.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
        WS_NFE_AUTORIZACAO: 'NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
    }
}

SVC_AN = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'www.svc.fazenda.gov.br',
        WS_NFE_CONSULTA: 'NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
        WS_NFE_SITUACAO: 'NFeStatusServico4/NFeStatusServico4.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
        WS_NFE_AUTORIZACAO: 'NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'hom.svc.fazenda.gov.br',
        WS_NFE_CONSULTA: 'NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
        WS_NFE_SITUACAO: 'NFeStatusServico4/NFeStatusServico4.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
        WS_NFE_AUTORIZACAO: 'NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
    }
}

SVC_RS = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'nfe.svrs.rs.gov.br',
        WS_NFE_RECEPCAO_EVENTO: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
        WS_NFE_AUTORIZACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
        WS_NFE_CONSULTA: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_SITUACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'nfe-homologacao.svrs.rs.gov.br',
        WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
        WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
        WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
    }
}

AN = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'www1.nfe.fazenda.gov.br',
        WS_DFE_DISTRIBUICAO: 'NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl',
        WS_DOWNLOAD_NFE: 'NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'hom.nfe.fazenda.gov.br',
        WS_DFE_DISTRIBUICAO: 'NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl',
        WS_DOWNLOAD_NFE: 'NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?Wsdl',  # noqa
    },
}

UFAM = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefaz.am.gov.br',
            WS_NFE_INUTILIZACAO: 'services2/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'services2/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'services2/services/NfeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'services2/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'services2/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'services2/services/NfeRetAutorizacao4?wsdl',  # noqa
            WS_NFE_CADASTRO: 'services2/services/cadconsultacadastro2?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homnfe.sefaz.am.gov.br',
            WS_NFE_INUTILIZACAO: 'services2/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'services2/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'services2/services/NfeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'services2/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'services2/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'services2/services/NfeRetAutorizacao4?wsdl',  # noqa
            WS_NFE_CADASTRO: 'services2/services/cadconsultacadastro2?wsdl',
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.sefaz.am.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfce-services/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfce-services/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfce-services/services/NfeRetAutorizacao4?wsdl',
            WS_NFE_INUTILIZACAO: 'nfce-services/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfce-services/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'nfce-services/services/NfeStatusServico4?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homnfce.sefaz.am.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfce-services/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfce-services/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfce-services/services/NfeRetAutorizacao4?wsdl',
            WS_NFE_INUTILIZACAO: 'nfce-services/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfce-services/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'nfce-services/services/NfeStatusServico4?wsdl',
            WS_NFCE_QR_CODE: 'http://homnfce.sefaz.am.gov.br/nfceweb/consultarNFCe.jsp',
        }
    }
}

UFBA = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefaz.ba.gov.br',
            WS_NFE_INUTILIZACAO: 'webservices/NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
            WS_NFE_SITUACAO: 'webservices/NFeStatusServico4/NFeStatusServico4.asmx?wsdl',  # noqa
            WS_NFE_RECEPCAO_EVENTO: 'webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'webservices/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_RET_AUTORIZACAO: 'webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'webservices/CadConsultaCadastro4/CadConsultaCadastro4.asmx?wsdl',  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'hnfe.sefaz.ba.gov.br',
            WS_NFE_INUTILIZACAO: 'webservices/NFeInutilizacao4/NFeInutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'webservices/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',  # noqa
            WS_NFE_SITUACAO: 'webservices/NFeStatusServico4/NFeStatusServico4.asmx?wsdl',  # noqa
            WS_NFE_RECEPCAO_EVENTO: 'webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'webservices/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_RET_AUTORIZACAO: 'webservices/NFeRetAutorizacao4/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'webservices/CadConsultaCadastro4/CadConsultaCadastro4.asmx?wsdl',  # noqa
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFCE_QR_CODE: 'http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'nfce-homologacao.svrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFCE_QR_CODE: 'http://dec.fazenda.df.gov.br/ConsultarNFCe.aspx?',
        }
    }
}

UFCE = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'nfe.sefaz.ce.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe4/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe4/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe4/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe4/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe4/services/NFeAutorizacao4?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe4/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe4/services/CadConsultaCadastro4?wsdl',
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'nfeh.sefaz.ce.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe4/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe4/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe4/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe4/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe4/services/NFeAutorizacao4?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe4/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe4/services/CadConsultaCadastro4?wsdl',
    }
}

UFGO = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'nfe.sefaz.go.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe/services/NFeAutorizacao4?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe/services/CadConsultaCadastro4?wsdl',
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'homolog.sefaz.go.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe/services/NFeAutorizacao4?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe/services/CadConsultaCadastro4?wsdl',
    }
}

UFMT = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefaz.mt.gov.br',
            WS_NFE_INUTILIZACAO: 'nfews/v2/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfews/v2/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'nfews/v2/services/NfeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'nfews/v2/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfews/v2/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfews/v2/services/NfeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfews/v2/services/CadConsultaCadastro4?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.sefaz.mt.gov.br',
            WS_NFE_INUTILIZACAO: 'nfews/v2/services/NfeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfews/v2/services/NfeConsulta4?wsdl',
            WS_NFE_SITUACAO: 'nfews/v2/services/NfeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'nfews/v2/services/RecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfews/v2/services/NfeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfews/v2/services/NfeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfews/v2/services/CadConsultaCadastro4?wsdl',
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.sefaz.mt.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfcews/services/RecepcaoEvento4',
            WS_NFE_AUTORIZACAO: 'nfcews/services/NfeAutorizacao4',
            WS_NFE_RET_AUTORIZACAO: 'nfcews/services/NfeRetAutorizacao4',
            WS_NFE_INUTILIZACAO: 'nfcews/services/NfeInutilizacao4',
            WS_NFE_CONSULTA: 'nfcews/services/NfeConsulta4',
            WS_NFE_SITUACAO: 'nfcews/services/NfeStatusServico4',
            WS_NFCE_QR_CODE: 'http://www.sefaz.mt.gov.br/nfce/consultanfce',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.sefaz.mt.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfcews/services/RecepcaoEvento4',
            WS_NFE_AUTORIZACAO: 'nfcews/services/NfeAutorizacao4',
            WS_NFE_RET_AUTORIZACAO: 'nfcews/services/NfeRetAutorizacao4',
            WS_NFE_INUTILIZACAO: 'nfcews/services/NfeInutilizacao4',
            WS_NFE_CONSULTA: 'nfcews/services/NfeConsulta4',
            WS_NFE_SITUACAO: 'nfcews/services/NfeStatusServico4',
            WS_NFCE_QR_CODE: 'http://www.sefaz.mt.gov.br/nfce/consultanfce',
        }
    }
}

UFMS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefaz.ms.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'ws/CadConsultaCadastro4?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'hom.nfe.sefaz.ms.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'ws/CadConsultaCadastro4?wsdl',
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.sefaz.ms.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4',
            WS_NFE_CADASTRO: 'CadConsultaCadastro4',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4',
            WS_NFCE_QR_CODE: 'www.dfe.ms.gov.br/nfce/qrcode?',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'hom.nfce.sefaz.ms.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4',
            WS_NFE_CADASTRO: 'ws/CadConsultaCadastro4',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4',
            WS_NFCE_QR_CODE: 'www.dfe.ms.gov.br/nfce/qrcode?'
        }
    }
}

UFMG = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'nfe.fazenda.mg.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe2/services/NFeInutilizacao4',
        WS_NFE_CONSULTA: 'nfe2/services/NFeConsultaProtocolo4',
        WS_NFE_SITUACAO: 'nfe2/services/NFeStatusServico4',
        WS_NFE_RECEPCAO_EVENTO: 'nfe2/services/NFeRecepcaoEvento4',
        WS_NFE_AUTORIZACAO: 'nfe2/services/NFeAutorizacao4',
        WS_NFE_RET_AUTORIZACAO: 'nfe2/services/NFeRetAutorizacao4',
        WS_NFE_CADASTRO: 'nfe2/services/CadConsultaCadastro4',

    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'hnfe.fazenda.mg.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe2/services/NFeInutilizacao4',
        WS_NFE_CONSULTA: 'nfe2/services/NFeConsultaProtocolo4',
        WS_NFE_SITUACAO: 'nfe2/services/NFeStatusServico4',
        WS_NFE_RECEPCAO_EVENTO: 'nfe2/services/NFeRecepcaoEvento4',
        WS_NFE_AUTORIZACAO: 'nfe2/services/NFeAutorizacao4',
        WS_NFE_RET_AUTORIZACAO: 'nfe2/services/NFeRetAutorizacao4',
        WS_NFE_CADASTRO: 'nfe2/services/CadConsultaCadastro4',
    }
}

UFPR = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefa.pr.gov.br',
            WS_NFE_INUTILIZACAO: 'nfe/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfe/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'nfe/NFeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'nfe/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfe/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfe/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfe/CadConsultaCadastro4?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.nfe.sefa.pr.gov.br',
            WS_NFE_INUTILIZACAO: 'nfe/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfe/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'nfe/NFeStatusServico4?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'nfe/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfe/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfe/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfe/CadConsultaCadastro4?wsdl',
        },
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.sefa.pr.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfce/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfce/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfce/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfce/CadConsultaCadastro4?wsdl',
            WS_NFE_INUTILIZACAO: 'nfce/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfce/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'nfce/NFeStatusServico4?wsdl',
            WS_NFCE_QR_CODE: 'www.fazenda.pr.gov.br/nfce/qrcode?',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.nfce.sefa.pr.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'nfce/NFeRecepcaoEvento4?wsdl',
            WS_NFE_AUTORIZACAO: 'nfce/NFeAutorizacao4?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'nfce/NFeRetAutorizacao4?wsdl',
            WS_NFE_CADASTRO: 'nfce/CadConsultaCadastro4?wsdl',
            WS_NFE_INUTILIZACAO: 'nfce/NFeInutilizacao4?wsdl',
            WS_NFE_CONSULTA: 'nfce/NFeConsultaProtocolo4?wsdl',
            WS_NFE_SITUACAO: 'nfce/NFeStatusServico4?wsdl',
            WS_NFCE_QR_CODE: 'www.fazenda.pr.gov.br/nfce/qrcode?'
        }
    }
}

UFPE = {
    AMBIENTE_PRODUCAO: {
        'servidor': 'nfe.sefaz.pe.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe-service/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe-service/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe-service/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe-service/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe-service/services/NFeAutorizacao4?Wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe-service/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe-service/services/CadConsultaCadastro2?wsdl',
    },
    AMBIENTE_HOMOLOGACAO: {
        'servidor': 'nfehomolog.sefaz.pe.gov.br',
        WS_NFE_INUTILIZACAO: 'nfe-service/services/NFeInutilizacao4?wsdl',
        WS_NFE_CONSULTA: 'nfe-service/services/NFeConsultaProtocolo4?wsdl',
        WS_NFE_SITUACAO: 'nfe-service/services/NFeStatusServico4?wsdl',
        WS_NFE_RECEPCAO_EVENTO: 'nfe-service/services/NFeRecepcaoEvento4?wsdl',
        WS_NFE_AUTORIZACAO: 'nfe-service/services/NFeAutorizacao4?wsdl',
        WS_NFE_RET_AUTORIZACAO: 'nfe-service/services/NFeRetAutorizacao4?wsdl',
        WS_NFE_CADASTRO: 'nfe-service/services/CadConsultaCadastro2?wsdl',
    }
}

UFRS = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.sefazrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl',  # noqa
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'nfe-homologacao.sefazrs.rs.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao/nfeinutilizacao4.asmx?wsdl',  # noqa
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento4.asmx?wsdl',  # noqa
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao4.asmx?wsdl',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro4.asmx?wsdl',  # noqa
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.sefazrs.rs.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento.asmx',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao.asmx',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao.asmx',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro2.asmx',  # noqa
            WS_NFE_INUTILIZACAO: 'ws/NfeInutilizacao/NfeInutilizacao2.asmx',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta2.asmx',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico2.asmx',
            WS_NFCE_QR_CODE: 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'nfce-homologacao.sefazrs.rs.gov.br',
            WS_NFE_RECEPCAO_EVENTO: 'ws/recepcaoevento/recepcaoevento.asmx',
            WS_NFE_AUTORIZACAO: 'ws/NfeAutorizacao/NFeAutorizacao.asmx',
            WS_NFE_RET_AUTORIZACAO: 'ws/NfeRetAutorizacao/NFeRetAutorizacao.asmx',  # noqa
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro/cadconsultacadastro2.asmx',  # noqa
            WS_NFE_INUTILIZACAO: 'ws/NfeInutilizacao/NfeInutilizacao2.asmx',
            WS_NFE_CONSULTA: 'ws/NfeConsulta/NfeConsulta2.asmx',
            WS_NFE_SITUACAO: 'ws/NfeStatusServico/NfeStatusServico2.asmx',
            WS_NFCE_QR_CODE: 'https://www.sefaz.rs.gov.br/NFCE/NFCE-COM.aspx'
        }
    }
}

UFSP = {
    NFE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfe.fazenda.sp.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/nfeconsultaprotocolo4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/nfestatusservico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/nferecepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/nfeautorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/nferetautorizacao4.asmx?wsdl',
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro4.asmx?wsdl',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.nfe.fazenda.sp.gov.br',
            WS_NFE_INUTILIZACAO: 'ws/nfeinutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/nfeconsultaprotocolo4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/nfestatusservico4.asmx?wsdl',
            WS_NFE_RECEPCAO_EVENTO: 'ws/nferecepcaoevento4.asmx?wsdl',
            WS_NFE_AUTORIZACAO: 'ws/nfeautorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/nferetautorizacao4.asmx?wsdl',
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro4.asmx?wsdl',
        }
    },
    NFCE_MODELO: {
        AMBIENTE_PRODUCAO: {
            'servidor': 'nfce.fazenda.sp.gov.br',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4.asmx?wsdl',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4.asmx?wsdl',
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro2.asmx',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4.asmx?wsdl',
            WS_NFCE_QR_CODE: '',
        },
        AMBIENTE_HOMOLOGACAO: {
            'servidor': 'homologacao.nfce.fazenda.sp.gov.br',
            WS_NFE_AUTORIZACAO: 'ws/NFeAutorizacao4.asmx?wsdl',
            WS_NFE_RET_AUTORIZACAO: 'ws/NFeRetAutorizacao4.asmx?wsdl',
            WS_NFE_INUTILIZACAO: 'ws/NFeInutilizacao4.asmx?wsdl',
            WS_NFE_CONSULTA: 'ws/NFeConsultaProtocolo4.asmx?wsdl',
            WS_NFE_SITUACAO: 'ws/NFeStatusServico4.asmx?wsdl',
            WS_NFE_CADASTRO: 'ws/cadconsultacadastro2.asmx',
            WS_NFE_RECEPCAO_EVENTO: 'ws/NFeRecepcaoEvento4.asmx?wsdl',
            WS_NFCE_QR_CODE: 'https://homologacao.nfce.fazenda.sp.gov.br/NFCEConsultaPublica/Paginas/ConstultaQRCode.aspx',
        }
    }
}

ESTADO_WS = {
    'AC': SVRS,
    'AL': SVRS,
    'AM': UFAM,
    'AP': SVRS,
    'BA': UFBA,
    'CE': UFCE,
    'DF': SVRS,
    'ES': SVRS,
    'GO': UFGO,
    'MA': SVAN,
    'MG': UFMG,
    'MS': UFMS,
    'MT': UFMT,
    'PA': SVAN,
    'PB': SVRS,
    'PE': UFPE,
    'PI': SVAN,
    'PR': UFPR,
    'RJ': SVRS,
    'RN': SVRS,
    'RO': SVRS,
    'RR': SVRS,
    'RS': UFRS,
    'SC': SVRS,
    'SE': SVRS,
    'SP': UFSP,
    'TO': SVRS,
    'AN': AN,
}


def localizar_url(servico, estado, mod='55', ambiente=2):
    sigla = SIGLA_ESTADO[estado]
    ws = ESTADO_WS[sigla]

    if servico in (WS_DFE_DISTRIBUICAO, WS_DOWNLOAD_NFE):
        ws = AN

    if mod in ws:
        dominio = ws[mod][ambiente]['servidor']
        complemento = ws[mod][ambiente][servico]
    else:
        dominio = ws[ambiente]['servidor']
        complemento = ws[ambiente][servico]

    if sigla == 'RS' and servico == WS_NFE_CADASTRO:
        dominio = 'cad.sefazrs.rs.gov.br'
    if sigla in ('AC', 'RN', 'PB', 'SC', 'RJ') and servico == WS_NFE_CADASTRO:
        dominio = 'cad.svrs.rs.gov.br'
    if sigla == 'AN' and servico == WS_NFE_RECEPCAO_EVENTO:
        dominio = 'www.nfe.fazenda.gov.br'

    return f"https://{dominio}/{complemento}"


Metodo = collections.namedtuple('Metodo', ['webservice', 'metodo'])

METODO_WS = {
    WS_NFE_INUTILIZACAO: Metodo('NFeInutilizacao4', 'nfeInutilizacaoNF'),
    WS_NFE_CONSULTA: Metodo('NFeConsultaProtocolo4', 'nfeConsultaNF'),
    WS_NFE_SITUACAO: Metodo('NFeStatusServico4', 'nfeStatusServicoNF'),
    WS_NFE_CADASTRO: Metodo('CadConsultaCadastro4', 'consultaCadastro2'),
    WS_NFE_RECEPCAO_EVENTO: Metodo('NFeRecepcaoEvento4', 'nfeRecepcaoEvento'),
    WS_NFE_AUTORIZACAO: Metodo('NFeAutorizacao4', 'NfeAutorizacao'),
    WS_NFE_RET_AUTORIZACAO: Metodo('NFeRetAutorizacao4', 'NfeRetAutorizacao'),
    WS_DFE_DISTRIBUICAO: Metodo('NFeDistribuicaoDFe', 'nfeDistDfeInteresse')
}


class NFe(DocumentoEletronico):
    _namespace = 'http://www.portalfiscal.inf.br/nfe'
    _edoc_situacao_arquivo_recebido_com_sucesso = '103'
    _edoc_situacao_servico_em_operacao = '107'
    _consulta_servico_ao_enviar = True
    _consulta_documento_antes_de_enviar = True
    _maximo_tentativas_consulta_recibo = 5

    def __init__(self, transmissao, uf, versao='4.00', ambiente='2',
                 mod='55'):
        super(NFe, self).__init__(transmissao)
        self.versao = str(versao)
        self.ambiente = str(ambiente)
        self.uf = int(uf)
        self.mod = str(mod)

    def _edoc_situacao_ja_enviado(self, proc_consulta):
        if proc_consulta.resposta.c_stat in ('100', '110', '150', '301', '302'):
            return True
        return False

    def get_documento_id(self, edoc):
        return edoc.inf_nfe.id[:3], edoc.inf_nfe.id[3:]

    def status_servico(self):
        raiz = ConsStatServ(
            versao=self.versao,
            tp_amb=self.ambiente,
            c_uf=self.uf,
            x_serv='STATUS',
        )
        return self._post(
            raiz,
            localizar_url(WS_NFE_SITUACAO, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeStatusServicoNF',
            RetConsStatServ
        )

    def consulta_documento(self, chave):
        raiz = ConsSitNfe(
            versao=self.versao,
            tp_amb=self.ambiente,
            x_serv='CONSULTAR',
            ch_nfe=chave,
        )
        return self._post(
            raiz,
            # 'https://hom.sefazvirtual.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx?wsdl',
            localizar_url(WS_NFE_CONSULTA, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeConsultaNF',
            RetConsSitNfe
        )

    def envia_documento(self, edoc):
        """

        Exportar o documento
        Assinar o documento
        Adicionar o mesmo ao envio

        :param edoc:
        :return:
        """
        xml_assinado = self.assina_raiz(edoc, edoc.inf_nfe.id)

        raiz = EnviNfe(
            versao=self.versao,
            id_lote=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            ind_sinc='0'
        )
        xml_envio_string, xml_envio_etree = self.render_edoc(
            raiz
        )
        xml_envio_etree.append(etree.fromstring(xml_assinado))

        # teste_string, teste_etree = self.render_edoc(xml_envio_etree)

        return self._post(
            xml_envio_etree,
            # 'https://hom.sefazvirtual.fazenda.gov.br/NFeAutorizacao4/NFeAutorizacao4.asmx?wsdl',
            localizar_url(WS_NFE_AUTORIZACAO, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeAutorizacaoLote',
            RetEnviNfe
        )

    def envia_inutilizacao(self, evento):
        tinut = InutNfe(
            versao=self.versao,
            inf_inut=evento,
            signature=None)

        xml_assinado = self.assina_raiz(tinut, tinut.inf_inut.id)

        xml_envio_etree = etree.fromstring(xml_assinado)

        return self._post(
            xml_envio_etree,
            localizar_url(WS_NFE_INUTILIZACAO, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeInutilizacaoNF',
            RetInutNfe
        )

    def consulta_recibo(self, numero=False, proc_envio=False):
        if proc_envio:
            numero = proc_envio.resposta.inf_rec.n_rec

        if not numero:
            return

        raiz = ConsReciNfe(
            versao=self.versao,
            tp_amb=self.ambiente,
            n_rec=numero,
        )
        return self._post(
            raiz,
            localizar_url(WS_NFE_RET_AUTORIZACAO, str(self.uf), self.mod,
                          int(self.ambiente)),
            # 'ws/nferetautorizacao4.asmx'
            'nfeRetAutorizacaoLote',
            RetConsReciNfe,
        )

    def enviar_lote_evento(self, lista_eventos, numero_lote=False):
        if not numero_lote:
            numero_lote = self._gera_numero_lote()



        raiz = EnvEventoGenerico(versao="1.00", id_lote=numero_lote)
        xml_envio_string, xml_envio_etree = self.render_edoc(
            raiz
        )

        for inf_evento in lista_eventos:
            if isinstance(inf_evento, TeventoCCe.InfEvento):
                Evento = TeventoCCe
            if isinstance(inf_evento, EventoCancNfe.InfEvento):
                Evento = EventoCancNfe

            evento = Evento(
                versao="1.00", inf_evento=inf_evento,
            )
            xml_assinado = self.assina_raiz(evento, evento.inf_evento.id)
            xml_envio_etree.append(etree.fromstring(xml_assinado))

        return self._post(
            xml_envio_etree,
            localizar_url(WS_NFE_RECEPCAO_EVENTO, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeRecepcaoEvento',
            RetEnvEventoGenerico
        )

    def cancela_documento(self, chave, protocolo_autorizacao, justificativa,
                          data_hora_evento=False):
        tipo_evento = '110111'
        sequencia = '1'
        raiz = EventoCancNfe.InfEvento(
            id='ID' + tipo_evento + chave + sequencia.zfill(2),
            c_orgao=self.uf,
            tp_amb=self.ambiente,
            cnpj=chave[6:20],
            ch_nfe=chave,
            dh_evento=data_hora_evento or self._hora_agora(),
            tp_evento='110111',
            n_seq_evento='1',
            ver_evento='1.00',
            det_evento=EventoCancNfe.InfEvento.DetEvento(
                versao="1.00",
                desc_evento='Cancelamento',
                n_prot=protocolo_autorizacao,
                x_just=justificativa
            ),
        )
        return raiz

    def carta_correcao(self, chave, sequencia, justificativa,
                       data_hora_evento=False):
        tipo_evento = '110110'
        raiz = EventoCCe.InfEvento(
            id='ID' + tipo_evento + chave + sequencia.zfill(2),
            c_orgao=self.uf,
            tp_amb=self.ambiente,
            cnpj=chave[6:20],
            cpf=None,
            ch_nfe=chave,
            dh_evento=data_hora_evento or self._hora_agora(),
            tp_evento=tipo_evento,
            n_seq_evento=sequencia,
            ver_evento='1.00',
            det_evento=EventoCCe.InfEvento.DetEvento(
                versao="1.00",
                desc_evento='Carta de Correcao',
                x_correcao=justificativa,
                x_cond_uso=TEXTO_CARTA_CORRECAO,
            ),
        )
        return raiz

    def inutilizacao(self, cnpj, mod, serie, num_ini, num_fin,
                     justificativa):
        ano = str(datetime.date.today().year)[2:]
        uf = str(self.uf)
        raiz = InutNfe.InfInut(
            id='ID' + uf + ano + cnpj + mod + serie.zfill(3) +
               str(num_ini).zfill(9) + str(num_fin).zfill(9),
            tp_amb=self.ambiente,
            x_serv='INUTILIZAR',
            c_uf=self.uf,
            ano=ano,
            cnpj=cnpj,
            mod=mod,
            serie=serie,
            n_nfini=str(num_ini),
            n_nffin=str(num_fin),
            x_just=justificativa,
        )
        return raiz

    def _verifica_servico_em_operacao(self, proc_servico):
        if proc_servico.resposta.c_stat == self._edoc_situacao_servico_em_operacao:
            return True
        return False

    def _verifica_documento_ja_enviado(self, proc_consulta):
        if proc_consulta.resposta.c_stat in ('100', '110', '150', '301', '302'):
            return True
        return False

    def _verifica_resposta_envio_sucesso(self, proc_envio):
        if proc_envio.resposta.c_stat == \
                self._edoc_situacao_arquivo_recebido_com_sucesso:
            return True
        return False

    def _aguarda_tempo_medio(self, proc_envio):
        time.sleep(float(proc_envio.resposta.inf_rec.t_med) * 1.3)

    def _edoc_situacao_em_processamento(self, proc_recibo):
        if proc_recibo.resposta.c_stat == '105':
            return True
        return False

    def consultar_distribuicao(self, cnpj_cpf, ultimo_nsu=False,
                               nsu_especifico=False, chave=False):
        """

        :param cnpj_cpf: CPF ou CNPJ a ser consultado
        :param ultimo_nsu: Último NSU para pesquisa. Formato: '999999999999999'
        :param nsu_especifico: NSU Específico para pesquisa.
                                Formato: '999999999999999'
        :param chave: Chave de acesso do documento
        :return: Retorna uma estrutura contendo as estruturas de envio
        e retorno preenchidas
        """

        if not ultimo_nsu and not nsu_especifico and not chave:
            return

        dist_nsu = cons_nsu = cons_ch_nfe = None
        if ultimo_nsu:
            dist_nsu = DistDfeInt.DistNsu(
                ult_nsu=ultimo_nsu
            )
        if nsu_especifico:
            cons_nsu = DistDfeInt.ConsNsu(
                nsu=nsu_especifico
            )
        if chave:
            cons_ch_nfe = DistDfeInt.ConsChNfe(
                ch_nfe=chave
            )

        if dist_nsu and cons_nsu or dist_nsu and cons_ch_nfe or cons_nsu and cons_ch_nfe:
            # TODO: Raise?
            return

        raiz = DistDfeInt(
            versao=self.versao,
            tp_amb=self.ambiente,
            c_ufautor=self.uf,
            cnpj=cnpj_cpf if len(cnpj_cpf) > 11 else None,
            cpf=cnpj_cpf if len(cnpj_cpf) <= 11 else None,
            dist_nsu=dist_nsu,
            cons_nsu=cons_nsu,
            cons_ch_nfe=cons_ch_nfe,
        )

        return self._post(
            raiz,
            localizar_url(WS_DFE_DISTRIBUICAO, str(self.uf), self.mod,
                          int(self.ambiente)),
            'nfeDistDfeInteresse',
            RetDistDfeInt
        )

    def monta_processo(self, edoc, proc_envio, proc_recibo):
        nfe = proc_envio.envio_raiz.find('{' + self._namespace + '}NFe')
        protocolos = proc_recibo.resposta.prot_nfe
        if nfe and protocolos:
            if not isinstance(protocolos, list):
                protocolos = [protocolos]
            for protocolo in protocolos:
                nfe_proc = NfeProc(
                    versao=self.versao,
                    prot_nfe=protocolo,
                )
                xml_file, nfe_proc = self.render_edoc(nfe_proc)
                prot_nfe = nfe_proc.find('{' + self._namespace + '}protNFe')
                prot_nfe.addprevious(nfe)
                proc_recibo.processo = nfe_proc
                proc_recibo.processo_xml = \
                    self.render_edoc(nfe_proc)[0]
                proc_recibo.protocolo = protocolo
            return True

    # TODO falta por as classes no nfelib verao xsdata

    # def consultar_cadastro(self, uf, cnpj=None, cpf=None, ie=None):

    #     if not cnpj and not cpf and not ie:
    #         return

    #     infCons = ConsSitNfe(
    #         x_serv='CONS-CAD',
    #         uf=uf,
    #         ie=ie,
    #         cnpj=cnpj,
    #         cpf=cpf,
    #     )

    #     raiz = ConsSitNfe(
    #         versao='2.00',
    #         inf_cons=infCons,
    #     )

    #     return self._post(
    #         raiz,
    #         localizar_url(
    #             WS_NFE_CADASTRO, str(self.uf), self.mod, int(self.ambiente)),
    #         'consultaCadastro',
    #         RetConsSitNfe
    #     )
