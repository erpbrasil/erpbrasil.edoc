import os
from unittest import TestCase

import vcr
from erpbrasil.assinatura.certificado import Certificado
from erpbrasil.base import misc
from erpbrasil.transmissao import TransmissaoSOAP
from requests import Session

try:
    from nfselib.ginfes.v3_01.servico_enviar_lote_rps_envio import (
        EnviarLoteRpsEnvio,
        ListaRpsType,
        tcCpfCnpj,
        tcDadosServico,
        tcDadosTomador,
        tcEndereco,
        tcIdentificacaoPrestador,
        tcIdentificacaoRps,
        tcIdentificacaoTomador,
        tcInfRps,
        tcLoteRps,
        tcRps,
        tcValores,
    )
except ImportError:
    pass

from erpbrasil.edoc.provedores.cidades import NFSeFactory


class Tests(TestCase):

    def setUp(self):
        certificado_nfe_caminho = os.environ.get(
            'certificado_nfe_caminho',
            'test/fixtures/dummy_cert.pfx'
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
            cidade_ibge=3132404,
            cnpj_prestador=misc.punctuation_rm('23.130.935/0001-98'),
            im_prestador=misc.punctuation_rm('35172'),
        )

    @vcr.use_cassette(
        'tests/fixtures/vcr_cassettes/test_envia_documento_ginfes.yaml')
    def test_envia_documento_ginfes(self):
        retorno = self.nfse.envia_documento(create_nfse_object())
        resultado = self.nfse.consulta_recibo(proc_envio=retorno)

        self.assertIn(resultado.resposta.Situacao, [2, 4])

    @vcr.use_cassette(
        'tests/fixtures/vcr_cassettes/test_cancelar_documento_ginfes.yaml')
    def test_cancelar_documento_ginfes(self):

        retorno = self.nfse.cancela_documento(115)
        resultado = self.nfse.analisa_retorno_cancelamento(retorno)

        self.assertTrue(resultado[0])

    @vcr.use_cassette(
        'tests/fixtures/vcr_cassettes/test_consulta_documento_ginfes.yaml')
    def test_consulta_documento_ginfes(self):

        retorno = self.nfse.consulta_nfse_rps(
            rps_number=304,
            rps_serie=111,
            rps_type=1
        )
        resultado = self.nfse.analisa_retorno_consulta(retorno, 304, '23130935000198', 'KMEE INFORMATICA LTDA')
        self.assertEqual(resultado, 'NFS-e cancelada em 11/20/2020')


def create_nfse_object():
    return EnviarLoteRpsEnvio(
        LoteRps=tcLoteRps(
            Cnpj=misc.punctuation_rm('23.130.935/0001-98'),
            InscricaoMunicipal=misc.punctuation_rm('35172'),
            QuantidadeRps=1,
            ListaRps=ListaRpsType(
                Rps=[
                    tcRps(
                        InfRps=tcInfRps(
                            Id='rps334',
                            IdentificacaoRps=tcIdentificacaoRps(
                                Numero=334,
                                Serie=111,
                                Tipo=1,
                            ),
                            DataEmissao='2020-11-20T12:00:21',
                            NaturezaOperacao=1,
                            RegimeEspecialTributacao=1,
                            OptanteSimplesNacional=1,
                            IncentivadorCultural=2,
                            Status=1,
                            RpsSubstituido=None,
                            Servico=tcDadosServico(
                                Valores=tcValores(
                                    ValorServicos=100.0,
                                    ValorDeducoes=0.0,
                                    ValorPis=0.0,
                                    ValorCofins=0.0,
                                    ValorInss=0.0,
                                    ValorIr=0.0,
                                    ValorCsll=0.0,
                                    IssRetido=2,
                                    ValorIss=2.0,
                                    ValorIssRetido=0.0,
                                    OutrasRetencoes=0.0,
                                    BaseCalculo=100.0,
                                    Aliquota=0.02,
                                    ValorLiquidoNfse=100.0,
                                ),
                                ItemListaServico='105',
                                CodigoCnae=1830003,
                                CodigoTributacaoMunicipio='6202300',
                                Discriminacao='[ODOO_DEV] Customized Odoo Development',
                                CodigoMunicipio=3132404,
                            ),
                            Prestador=tcIdentificacaoPrestador(
                                Cnpj='23130935000198',
                                InscricaoMunicipal='35172',
                            ),
                            Tomador=tcDadosTomador(
                                IdentificacaoTomador=tcIdentificacaoTomador(
                                    CpfCnpj=tcCpfCnpj(
                                        Cnpj='62228384000151',
                                        Cpf=None,
                                    ),
                                    InscricaoMunicipal=None,
                                ),
                                RazaoSocial='AMD South America Ltda',
                                Endereco=tcEndereco(
                                    Endereco='Rua Samuel Morse',
                                    Numero='134',
                                    Complemento=None,
                                    Bairro='Brooklin',
                                    CodigoMunicipio=3550308,
                                    Uf='SP',
                                    Cep=4576060,
                                ) or None,
                            ),
                            IntermediarioServico=None,
                            ConstrucaoCivil=None,
                        )
                    )
                ]
            )
        )
    )
