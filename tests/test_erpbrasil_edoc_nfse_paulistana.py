import os
import vcr
from requests import Session
from unittest import TestCase

from erpbrasil.base import misc
from erpbrasil.transmissao import TransmissaoSOAP
from erpbrasil.assinatura.certificado import Certificado

try:
    from nfselib.paulistana.v02.PedidoEnvioLoteRPS import (
        CabecalhoType,
        PedidoEnvioLoteRPS,
        tpEndereco,
        tpCPFCNPJ,
        tpRPS,
        tpChaveRPS,
    )
except ImportError:
    pass

from erpbrasil.edoc.provedores.cidades import NFSeFactory


class Tests(TestCase):

    def setUp(self):
        certificado_nfe_caminho = os.environ.get(
            'certificado_nfe_caminho',
            'fixtures/dummy_cert.pfx'
        )
        certificado_nfe_senha = os.environ.get(
            'certificado_nfe_senha', 'dummy_password'
        )
        self.certificado = Certificado(
            certificado_nfe_caminho,
            certificado_nfe_senha
        )
        session = Session()
        session.verify = False

        transmissao = TransmissaoSOAP(self.certificado, session)

        self.nfse = NFSeFactory(
            transmissao=transmissao,
            ambiente='2',
            cidade_ibge=3550308,
            cnpj_prestador=misc.punctuation_rm('07.865.699/0001-00'),
            im_prestador=misc.punctuation_rm('3.570.741-0'),
        )

    @vcr.use_cassette('fixtures/vcr_cassettes/test_envia_documento.yaml')
    def test_envia_documento(self):
        retorno = self.nfse.envia_documento(create_nfse_object())
        resultado = self.nfse.consulta_recibo(proc_envio=retorno)

        self.assertFalse(resultado.resposta.Cabecalho.Sucesso)

    @vcr.use_cassette('fixtures/vcr_cassettes/test_cancelar_documento.yaml')
    def test_cancelar_documento(self):
        doc_numero = {
            'numero_nfse': '001',
            'codigo_verificacao': '0000',
        }

        retorno = self.nfse.cancela_documento(doc_numero)
        resultado = self.nfse.analisa_retorno_cancelamento_paulistana(retorno)

        self.assertFalse(resultado[0])
        self.assertEqual('1306 - A NFS-e que se deseja cancelar não foi gerada'
                         ' via Web Service.\n', resultado[1])

    @vcr.use_cassette('fixtures/vcr_cassettes/test_consulta_documento.yaml')
    def test_consulta_documento(self):
        serie_rps = 1
        number_rps = 1
        im_prestador = misc.punctuation_rm('3.570.741-0')
        cnpj_prestador = misc.punctuation_rm('07.865.699/0001-00')

        retorno = self.nfse.consulta_nfse_rps(
            numero_rps=number_rps,
            serie_rps=serie_rps,
            insc_prest=im_prestador,
            cnpj_prest=cnpj_prestador,
        )
        resultado = self.nfse.analisa_retorno_consulta(retorno)
        self.assertEqual('1106 - NFS-e não encontrada.', resultado)


def create_nfse_object():
    return PedidoEnvioLoteRPS(
        Cabecalho=CabecalhoType(
            Versao=1,
            CPFCNPJRemetente=tpCPFCNPJ(
                CNPJ='07865699000100',
            ),
            transacao=False,
            dtInicio='2020-10-29',
            dtFim='2020-10-29',
            QtdRPS=1,
            ValorTotalServicos=100.0,
            ValorTotalDeducoes=0.0,
        ),
        RPS=[
            tpRPS(
                Assinatura=b'35707410111  00000000029420201029TNN000000000' +
                           b'01000000000000000000002692262228384000151',
                ChaveRPS=tpChaveRPS(
                    InscricaoPrestador=35707410,
                    SerieRPS='111',
                    NumeroRPS=294,
                ),
                TipoRPS='RPS',
                DataEmissao='2020-10-29',
                StatusRPS='N',
                TributacaoRPS='T',
                ValorServicos=100.0,
                ValorDeducoes=0.0,
                ValorPIS=0.0,
                ValorCOFINS=0.0,
                ValorINSS=0.0,
                ValorIR=0.0,
                ValorCSLL=0.0,
                CodigoServico=2692,
                AliquotaServicos=0.0,
                ISSRetido=False,
                CPFCNPJTomador=tpCPFCNPJ(
                    CNPJ='62228384000151'
                ),
                InscricaoMunicipalTomador=None,
                InscricaoEstadualTomador=621240850633,
                RazaoSocialTomador='AMD South America Ltda',
                EnderecoTomador=tpEndereco(
                    Logradouro='Rua Samuel Morse',
                    NumeroEndereco='134',
                    ComplementoEndereco=None,
                    Bairro='Brooklin',
                    Cidade=3550308,
                    UF='SP',
                    CEP=4576060,
                ),
                EmailTomador='teste@teste.com.br',
                Discriminacao='[ODOO_DEV] Customized Odoo Development',
                ValorCargaTributaria=0.0,
                FonteCargaTributaria='100.0',
                MunicipioPrestacao=None,
            )
        ],
    )
