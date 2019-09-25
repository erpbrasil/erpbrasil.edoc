__version__ = '0.0.0'

import abc

ABC = abc.ABCMeta('ABC', (object,), {})

from erpbrasil.edoc.nfe import NFe


def importar_documento(xml):
    pass
