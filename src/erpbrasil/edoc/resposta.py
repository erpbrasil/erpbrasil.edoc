# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY Luis Felipe Mileo - KMEE INFORMATICA LTDA
# License MIT

import re
from lxml import etree


class RetornoSoap(object):

    def __init__(self, webservice, raiz, xml, retorno, resposta):
        self.webservice = webservice
        self.envio_raiz = raiz
        self.envio_xml = xml
        self.resposta = resposta
        self.retorno = retorno


def analisar_retorno_raw(operacao, raiz, xml, retorno, classe):
    retorno.raise_for_status()
    match = re.search('<soap:Body>(.*?)</soap:Body>',
                      retorno.text.replace('\n', ''))
    if match:
        xml_resposta = match.group(1)
        resultado = etree.tostring(etree.fromstring(xml_resposta)[0])
        classe.Validate_simpletypes_ = False
        resposta = classe.parseString(resultado, silence=True)
        return RetornoSoap(operacao, raiz, xml, retorno, resposta)


def analisar_retorno(operacao, raiz, xml, retorno, classe):
    resposta = False
    if retorno:
        classe.Validate_simpletypes_ = False
        resultado = etree.tostring(
            etree.fromstring(retorno.encode('utf-8')))
        resposta = classe.parseString(resultado, silence=True)
    return RetornoSoap(operacao, raiz, xml, retorno, resposta)
