# Namespace compartilhado com erpbrasil.base, erpbrasil.assinatura e erpbrasil.transmissao.
# Mesmo conteudo do __init__ da erpbrasil.base; convive com os pacotes antigos
# (setuptools nspkg.pth) e com portions PEP 420.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)
