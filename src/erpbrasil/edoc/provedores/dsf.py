# Copyright (C) 2019  Luis Felipe Mileo - KMEE


from erpbrasil.edoc.chave import ChaveNFSeDSF
from erpbrasil.edoc.nfse import NFSe, ServicoNFSe

try:
    from nfselib.dsf import (
        RetornoConsultaLote,
        RetornoConsultaNFSeRPS,
        RetornoEnvioLoteRPS,
    )

    dsf = True
except ImportError:
    dsf = False

endpoint = "WsNFe2/LoteRps.jws"

if dsf:
    servicos_base = {
        "consulta_recibo": ServicoNFSe(
            "consultarLote", endpoint, RetornoConsultaLote, True
        ),
        "consultar_lote_rps": ServicoNFSe(
            "ConsultarNota", endpoint, RetornoConsultaNFSeRPS, True
        ),
    }

    servicos_hml = {
        "envia_documento": ServicoNFSe(
            "testeEnviar", endpoint, RetornoEnvioLoteRPS, True
        ),
    }
    servicos_hml.update(servicos_base.copy())

    servicos_prod = {
        "envia_documento": ServicoNFSe("enviar", endpoint, RetornoEnvioLoteRPS, True),
    }
    servicos_prod.update(servicos_base.copy())

    url = {
        3509502: "http://issdigital.campinas.sp.gov.br",  # Campinas
        3170206: "http://udigital.uberlandia.mg.gov.br",  # Uberlândia-MG
        1501402: "http://www.issdigitalbel.com.br",  # Belem-PA
        5002704: "http://issdigital.pmcg.ms.gov.br",  # Campo Grande - MS
        3303500: "http://www.issmaisfacil.com.br",  # Nova Iguaçu - RJ
        2211001: "http://www.issdigitalthe.com.br",  # Teresina - PI
        # 2111300 : 'http://www.issdigitalslz.com.br',  # São Luiz - MA
    }


class Dsf(NFSe):
    def __init__(
        self, transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador
    ):
        # DSS só tem uma URL
        self._url = url[int(cidade_ibge)]

        # Não tem URL de homologação mas tem métodos para testes
        # no mesmo webservice

        if ambiente == "2":
            self._servicos = servicos_hml
        else:
            self._servicos = servicos_hml

        super().__init__(
            transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador
        )

    def envia_documento(self, edoc):
        for rps in edoc.Lote.RPS:
            chave = ChaveNFSeDSF(rps=rps)
            rps.Assinatura = chave.hash

        return super().envia_documento(edoc)
