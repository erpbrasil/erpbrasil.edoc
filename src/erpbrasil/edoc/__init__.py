# erpbrasil.edoc tambem e namespace: erpbrasil.edoc.pdf e erpbrasil.edoc.gen sao
# pacotes proprios que moram dentro dele (setuptools nspkg.pth, sem __init__).
# O extend_path mantem essa convivencia. Se um pacote legado do namespace estiver
# instalado (ex.: erpbrasil.edoc.pdf 1.2.1, com nspkg.pth), este arquivo nao e
# executado e `__version__` nao existe: usar importlib.metadata.version.
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

__version__ = "3.3.0"
