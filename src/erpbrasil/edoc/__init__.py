__version__ = '0.0.0'

import abc

ABC = abc.ABCMeta('ABC', (object,), {})

from erpbrasil.edoc.nfe import NFe
from erpbrasil.edoc.nfse import nfse
from erpbrasil.edoc.nfse.cidades import NFSeFactory

def importar_documento(xml):
    pass
