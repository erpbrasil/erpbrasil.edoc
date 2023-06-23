# -*- encoding: utf-8 -*-
# See http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
# Trecho duplicado para permitir a importação do erpbrasil.edoc.pdf e o
# erpbrasil.edoc.gen
try:
    __import__("pkg_resources").declare_namespace(__name__)
except ImportError:
    from pkgutil import extend_path

    __path__ = extend_path(__path__, __name__)
__version__ = '2.4.0'

import abc

ABC = abc.ABCMeta('ABC', (object,), {})


def importar_documento(xml):
    pass
