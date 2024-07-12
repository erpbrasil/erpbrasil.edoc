# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import logging
import re

from lxml import etree


class RetornoSoap:
    def __init__(self, webservice, raiz, xml, retorno, resposta):
        self.webservice = webservice
        self.envio_raiz = raiz
        self.envio_xml = xml
        self.resposta = resposta
        self.retorno = retorno


def analisar_retorno_raw(operacao, raiz, xml, retorno, classe):
    retorno.raise_for_status()
    pattern = r"<[a-zA-Z0-9:]Body.?>(.*?)</[a-zA-Z0-9:]*Body>"
    match = re.search(pattern, retorno.text.replace("\n", ""))
    if match:
        xml_resposta = match.group(1)
        xml_etree = etree.fromstring(xml_resposta)
        resultado = xml_etree[0]

        nome_classe = classe.__name__.split(".")[-1]
        xml_classe_tags = list(
            filter(
                lambda children: nome_classe in children.tag, xml_etree.findall(".//")
            )
        )
        if xml_classe_tags:
            resultado = xml_classe_tags[0]

        resultado = etree.tostring(resultado)
        classe.Validate_simpletypes_ = False
        resposta = classe.parseString(resultado, silence=True)
        return RetornoSoap(operacao, raiz, xml, retorno, resposta)
    else:
        logging.warning("'match' em 'analisar_retorno_raw' é None")


def analisar_retorno(operacao, raiz, xml, retorno, classe):
    resposta = False
    if retorno:
        classe.Validate_simpletypes_ = False
        resultado = etree.tostring(etree.fromstring(retorno.encode("utf-8")))
        resposta = classe.parseString(resultado, silence=True)
    return RetornoSoap(operacao, raiz, xml, retorno, resposta)
