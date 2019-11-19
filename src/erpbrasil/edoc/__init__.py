__version__ = '0.0.0'

import abc

ABC = abc.ABCMeta('ABC', (object,), {})

from erpbrasil.edoc.nfe import NFe
from erpbrasil.edoc.nfse import NFSe

def importar_documento(xml):
    pass
