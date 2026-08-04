from types import SimpleNamespace
from unittest import TestCase

from erpbrasil.base import misc
from erpbrasil.edoc.provedores.cidades import NFSeFactory
from erpbrasil.edoc.provedores.issnet import Issnet
from erpbrasil.transmissao import TransmissaoSOAP
from nfselib.issnet.v1_00.servico_enviar_lote_rps_envio import (
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
from requests import Session

from .test_certificate_mixin import TestCertificateMixin

NS_CONSULTA = (
    "http://www.issnetonline.com.br/webserviceabrasf/vsd/"
    "servico_consultar_nfse_rps_resposta.xsd"
)
NS_TC = "http://www.issnetonline.com.br/webserviceabrasf/vsd/tipos_complexos.xsd"


class AnalisaRetornoConsultaTests(TestCase):
    """`analisa_retorno_consulta` so depende do XML de retorno, sem rede."""

    def setUp(self):
        self.nfse = Issnet.__new__(Issnet)

    def _xml_enviada(self, numero="304", cnpj="23130935000198", razao_social="KMEE"):
        return f"""<root xmlns:consulta="{NS_CONSULTA}" xmlns:tc="{NS_TC}">
  <consulta:CompNfse>
    <tc:InfNfse>
      <tc:Numero>{numero}</tc:Numero>
      <tc:CodigoVerificacao>ABC123</tc:CodigoVerificacao>
      <tc:DataEmissao>2020-11-20T12:00:21</tc:DataEmissao>
    </tc:InfNfse>
    <tc:IdentificacaoPrestador>
      <tc:CpfCnpj>
        <tc:Cnpj>{cnpj}</tc:Cnpj>
      </tc:CpfCnpj>
    </tc:IdentificacaoPrestador>
    <tc:PrestadorServico>
      <tc:RazaoSocial>{razao_social}</tc:RazaoSocial>
    </tc:PrestadorServico>
  </consulta:CompNfse>
</root>"""

    def test_nfse_enviada_e_dados_conferem(self):
        processo = SimpleNamespace(
            retorno=self._xml_enviada(), webservice="ConsultarNFSePorRPS"
        )
        mensagem, res = self.nfse.analisa_retorno_consulta(
            processo, "304", "23130935000198", "KMEE"
        )
        self.assertEqual(mensagem, "NFS-e enviada e corresponde com o provedor")
        self.assertEqual(
            res,
            {
                "codigo_verificacao": "ABC123",
                "numero": "304",
                "data_emissao": "2020-11-20T12:00:21",
            },
        )

    def test_nfse_enviada_sem_number_informado(self):
        processo = SimpleNamespace(
            retorno=self._xml_enviada(), webservice="ConsultarNFSePorRPS"
        )
        mensagem, _res = self.nfse.analisa_retorno_consulta(
            processo, None, "23130935000198", "KMEE"
        )
        self.assertEqual(mensagem, "NFS-e enviada e corresponde com o provedor")

    def test_nfse_enviada_dados_nao_conferem(self):
        processo = SimpleNamespace(
            retorno=self._xml_enviada(
                numero="999", cnpj="00000000000000", razao_social="OUTRA EMPRESA"
            ),
            webservice="ConsultarNFSePorRPS",
        )
        mensagem, res = self.nfse.analisa_retorno_consulta(
            processo, "304", "23130935000198", "KMEE"
        )
        self.assertIn("Número", mensagem)
        self.assertIn("CNPJ do prestador", mensagem)
        self.assertIn("Razão Social de prestador", mensagem)
        self.assertEqual(res["numero"], "999")

    def test_nfse_cancelada(self):
        xml = f"""<root xmlns:consulta="{NS_CONSULTA}" xmlns:tc="{NS_TC}">
  <consulta:CompNfse>
    <consulta:NfseCancelamento>
      <consulta:DataHora>2020-11-20T12:00:21</consulta:DataHora>
    </consulta:NfseCancelamento>
  </consulta:CompNfse>
</root>"""
        processo = SimpleNamespace(retorno=xml, webservice="ConsultarNFSePorRPS")
        mensagem = self.nfse.analisa_retorno_consulta(processo, "304", "x", "y")
        self.assertEqual(mensagem, "NFS-e cancelada em 11/20/2020")

    def test_nfse_nao_encontrada(self):
        xml = f"""<root xmlns:consulta="{NS_CONSULTA}" xmlns:tc="{NS_TC}">
  <consulta:MensagemRetorno>
    <tc:Mensagem>NFS-e não encontrada</tc:Mensagem>
    <tc:Correcao>Verifique o número informado</tc:Correcao>
    <tc:Codigo>E001</tc:Codigo>
  </consulta:MensagemRetorno>
</root>"""
        processo = SimpleNamespace(retorno=xml, webservice="ConsultarNFSePorRPS")
        mensagem = self.nfse.analisa_retorno_consulta(processo, "304", "x", "y")
        self.assertEqual(
            mensagem,
            "E001 - NFS-e não encontrada - Correção: Verifique o número informado\n",
        )

    def test_erro_desconhecido(self):
        xml = f'<root xmlns:consulta="{NS_CONSULTA}" xmlns:tc="{NS_TC}"></root>'
        processo = SimpleNamespace(retorno=xml, webservice="ConsultarNFSePorRPS")
        mensagem = self.nfse.analisa_retorno_consulta(processo, "304", "x", "y")
        self.assertEqual(mensagem, "Erro desconhecido.")

    def test_webservice_diferente_retorna_mensagem_vazia(self):
        xml = f'<root xmlns:consulta="{NS_CONSULTA}" xmlns:tc="{NS_TC}"></root>'
        processo = SimpleNamespace(retorno=xml, webservice="OutroServico")
        mensagem = self.nfse.analisa_retorno_consulta(processo, "304", "x", "y")
        self.assertEqual(mensagem, "")


class AnalisaRetornoCancelamentoTests(TestCase):
    def setUp(self):
        self.nfse = Issnet.__new__(Issnet)

    def test_cancelamento_com_sucesso(self):
        xml = f'<root xmlns:tc="{NS_TC}"><tc:Sucesso>true</tc:Sucesso></root>'
        processo = SimpleNamespace(retorno=xml, webservice="CancelarNfse")
        situacao, mensagem = self.nfse.analisa_retorno_cancelamento(processo)
        self.assertTrue(situacao)
        self.assertEqual(mensagem, "")

    def test_cancelamento_com_erro_e_correcao(self):
        xml = (
            f'<root xmlns:tc="{NS_TC}">'
            "<tc:Mensagem>Erro ao cancelar</tc:Mensagem>"
            "<tc:Correcao>Verifique dados</tc:Correcao>"
            "<tc:Codigo>E002</tc:Codigo></root>"
        )
        processo = SimpleNamespace(retorno=xml, webservice="CancelarNfse")
        situacao, mensagem = self.nfse.analisa_retorno_cancelamento(processo)
        self.assertFalse(situacao)
        self.assertEqual(
            mensagem, "E002 - Erro ao cancelar - Correção: Verifique dados\n"
        )

    def test_cancelamento_com_erro_sem_correcao(self):
        xml = (
            f'<root xmlns:tc="{NS_TC}">'
            "<tc:Mensagem>Erro ao cancelar</tc:Mensagem>"
            "<tc:Correcao/>"
            "<tc:Codigo>E002</tc:Codigo></root>"
        )
        processo = SimpleNamespace(retorno=xml, webservice="CancelarNfse")
        situacao, mensagem = self.nfse.analisa_retorno_cancelamento(processo)
        self.assertFalse(situacao)
        self.assertEqual(mensagem, "E002 - Erro ao cancelar")

    def test_webservice_diferente_retorna_none(self):
        xml = f'<root xmlns:tc="{NS_TC}"><tc:Sucesso>true</tc:Sucesso></root>'
        processo = SimpleNamespace(retorno=xml, webservice="OutroServico")
        self.assertIsNone(self.nfse.analisa_retorno_cancelamento(processo))


class PreparaDocumentosTests(TestCertificateMixin, TestCase):
    """Testa a montagem/assinatura do XML sem realizar nenhuma chamada de rede."""

    def setUp(self):
        super().setUp()
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(self.certificate, session)
        self.nfse = NFSeFactory(
            transmissao=transmissao,
            ambiente="2",
            cidade_ibge=3543402,  # Ribeirao Preto - SP
            cnpj_prestador=misc.punctuation_rm("23.130.935/0001-98"),
            im_prestador=misc.punctuation_rm("35172"),
        )

    def test_get_documento_id(self):
        edoc = SimpleNamespace(
            LoteRps=SimpleNamespace(id="lote1", NumeroLote=1),
        )
        self.assertEqual(self.nfse.get_documento_id(edoc), ("lote1", 1))

    def test_prepara_envia_documento_assina_e_numera_o_lote(self):
        edoc = create_nfse_object()
        xml_assinado = self.nfse._prepara_envia_documento(edoc)

        self.assertTrue(edoc.LoteRps.id.startswith("lote"))
        self.assertIsInstance(edoc.LoteRps.NumeroLote, int)
        self.assertTrue(xml_assinado.startswith('<?xml version="1.0"?>'))
        self.assertIn("23130935000198", xml_assinado)

    def test_prepara_consulta_recibo(self):
        proc_envio = SimpleNamespace(resposta=SimpleNamespace(Protocolo="PROTO123"))
        xml = self.nfse._prepara_consulta_recibo(proc_envio)
        self.assertIn("PROTO123", xml)
        self.assertTrue(xml.startswith('<?xml version="1.0"?>'))

    def test_prepara_consultar_lote_rps(self):
        xml = self.nfse._prepara_consultar_lote_rps("PROTO123")
        self.assertIn("PROTO123", xml)

    def test_prepara_consultar_nfse_rps(self):
        xml = self.nfse._prepara_consultar_nfse_rps(
            rps_number=304, rps_serie=111, rps_type=1
        )
        self.assertIn("23130935000198", xml)

    def test_prepara_cancelar_nfse_envio_homologacao(self):
        xml = self.nfse._prepara_cancelar_nfse_envio(115)
        self.assertNotIn("tcPedidoCancelamento", xml)
        self.assertIn("<Pedido", xml)
        self.assertIn("999", xml)  # CodigoMunicipio em homologacao (ambiente != "1")

    def test_prepara_cancelar_nfse_envio_producao(self):
        session = Session()
        session.verify = False
        transmissao = TransmissaoSOAP(self.certificate, session)
        nfse_producao = NFSeFactory(
            transmissao=transmissao,
            ambiente="1",
            cidade_ibge=3543402,
            cnpj_prestador=misc.punctuation_rm("23.130.935/0001-98"),
            im_prestador=misc.punctuation_rm("35172"),
        )
        xml = nfse_producao._prepara_cancelar_nfse_envio(115)
        self.assertIn("3543402", xml)  # CodigoMunicipio = self.cidade em producao

    def test_verifica_resposta_envio_sucesso(self):
        self.assertTrue(
            self.nfse._verifica_resposta_envio_sucesso(
                SimpleNamespace(resposta=SimpleNamespace(Protocolo="X"))
            )
        )
        self.assertFalse(
            self.nfse._verifica_resposta_envio_sucesso(
                SimpleNamespace(resposta=SimpleNamespace(Protocolo=None))
            )
        )

    def test_edoc_situacao_em_processamento(self):
        self.assertTrue(
            self.nfse._edoc_situacao_em_processamento(
                SimpleNamespace(resposta=SimpleNamespace(Situacao=2))
            )
        )
        self.assertFalse(
            self.nfse._edoc_situacao_em_processamento(
                SimpleNamespace(resposta=SimpleNamespace(Situacao=4))
            )
        )


def create_nfse_object():
    return EnviarLoteRpsEnvio(
        LoteRps=tcLoteRps(
            Cnpj="23130935000198",
            InscricaoMunicipal="35172",
            QuantidadeRps=1,
            ListaRps=ListaRpsType(
                Rps=[
                    tcRps(
                        InfRps=tcInfRps(
                            id="rps334",
                            IdentificacaoRps=tcIdentificacaoRps(
                                Numero=334, Serie=111, Tipo=1
                            ),
                            DataEmissao="2020-11-20T12:00:21",
                            NaturezaOperacao=1,
                            RegimeEspecialTributacao=1,
                            OptanteSimplesNacional=1,
                            IncentivadorCultural=2,
                            Status=1,
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
                                ItemListaServico="105",
                                CodigoCnae=1830003,
                                CodigoTributacaoMunicipio="6202300",
                                Discriminacao="[ODOO_DEV] Customized Odoo Development",
                                MunicipioPrestacaoServico=3543402,
                            ),
                            Prestador=tcIdentificacaoPrestador(
                                CpfCnpj=tcCpfCnpj(Cnpj="23130935000198"),
                                InscricaoMunicipal="35172",
                            ),
                            Tomador=tcDadosTomador(
                                IdentificacaoTomador=tcIdentificacaoTomador(
                                    CpfCnpj=tcCpfCnpj(Cnpj="62228384000151"),
                                ),
                                RazaoSocial="AMD South America Ltda",
                                Endereco=tcEndereco(
                                    Endereco="Rua Samuel Morse",
                                    Numero="134",
                                    Bairro="Brooklin",
                                    Cidade=3550308,
                                    Estado="SP",
                                    Cep=4576060,
                                ),
                            ),
                        )
                    )
                ]
            ),
        )
    )
