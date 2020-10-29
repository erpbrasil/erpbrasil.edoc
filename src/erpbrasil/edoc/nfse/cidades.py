# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - KMEE

from __future__ import division, print_function, unicode_literals

from erpbrasil.edoc.nfse.ginfes import Ginfes
from erpbrasil.edoc.nfse.dsf import Dsf
from erpbrasil.edoc.nfse.paulistana import Paulistana

cidades = {
    1501402: Dsf,  # Belem-PA
    2211001: Dsf,  # Teresina - PI
    3132404: Ginfes,  # ITAJUBA - MG
    3170206: Dsf,  # Uberlândia-MG
    3303500: Dsf,  # Nova Iguaçu - RJ
    3509502: Dsf,  # Campinas - SP
    5002704: Dsf,  # Campo Grande - MS
    3550308: Paulistana,  # São Paulo - SP
}


def NFSeFactory(
    transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador):
    """Factory"""
    return cidades[int(cidade_ibge)](
        transmissao, ambiente, cidade_ibge, cnpj_prestador, im_prestador)
