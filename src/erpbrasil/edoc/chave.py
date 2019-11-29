# coding=utf-8
# Copyright (C) 2019  Luis Felipe Mileo - mileo at kmee com br

import hashlib
import datetime


class ChaveNFSeDSF(object):
    """Representa a **chave de acesso** da NFS-e-DSF conforme descrito na
    Especificação da Assinatura, pagina 9. Os campos são definidos assim:
    .. sourcecode:: text                     39
        0         11    16         28      36 40              55             70        80            94
        |         |     |                   | ||              |              |         |             |
        00000317330NF   00000003866320090905T NN000000000001686000000000000000082997990008764130000102 --> campos
        |         |     |           |       | |               |              |         |             |
        |         |     |           |       | |               |              |         |             CPF / CNPJ
        |         |     |           |       | |               |              |         Valor da dedução
        |         |     |           |       | |               |              Valor do serviço
        |         |     |           |       | |               Tipo de recolhimento
        |         |     |           |       | Situação da RPS ( N - Normal ou C- Canceldada)
        |         |     |           |       Tributação
        |         |     |           Data emissão
        |         |     Número RPS
        |         Serie RPS
        Inscrição Municipal
    """

    IM = slice(0, 11)

    SERIE = slice(11, 16)

    NUMERO = slice(16, 28)

    DATA = slice(28, 36)

    TRIBUTACAO = slice(36, 37)

    SITUACAO = slice(38, 39)

    TIPO_RECOLHIMENTO = slice(39, 40)

    VALOR_SERVICO = slice(40, 55)

    VALOR_DEDUCAO = slice(55, 70)

    CODIGO_ATIVIDADE = slice(70, 80)

    CPF_CNPJ = slice(80, 94)

    def __init__(self, chave=False, rps=False):
        if not (chave or rps):
            raise Exception
        elif rps:
            self.rps(rps)
        elif chave:
            self.chave = chave

    def __repr__(self):
        return '{:s}({!r})'.format(self.__class__.__name__, str(self))

    def __unicode__(self):
        return self._campos

    def __str__(self):
        return unicode(self).encode('utf-8')

    @property
    def inscricao_municipal(self):
        return self._inscricao_municipal

    @inscricao_municipal.setter
    def inscricao_municipal(self, value):
        self._inscricao_municipal = str(value).zfill(11)

    @property
    def serie(self):
        return self._serie

    @serie.setter
    def serie(self, value):
        self._serie = str(value).ljust(5)

    @property
    def numero(self):
        return self._numero

    @numero.setter
    def numero(self, value):
        self._numero = str(value).zfill(12)

    @property
    def data(self):
        return self._data.strftime('%Y%m%d')

    @data.setter
    def data(self, value):
        if isinstance(value, str) or isinstance(value, unicode):
            self._data = datetime.datetime.strptime(value, '%Y%m%d')
        elif isinstance(value, datetime.datetime):
            self._data = value

    @property
    def tributacao(self):
        return self._tributacao

    @tributacao.setter
    def tributacao(self, value):
        self._tributacao = str(value).ljust(2)

    @property
    def situacao(self):
        return self._situacao

    @situacao.setter
    def situacao(self, value):
        self._situacao = str(value)

    @property
    def tipo_recolhimento(self):
        return self._tipo_recolhimento

    @tipo_recolhimento.setter
    def tipo_recolhimento(self, value):
        self._tipo_recolhimento = str(value)

    @property
    def valor_servico(self):
        return self._valor_servico

    @property
    def valor_deducao(self):
        return self._valor_deducao

    @valor_servico.setter
    def valor_servico(self, value):
        if isinstance(value, str) or isinstance(value, unicode):
            self._valor_servico = value
        elif isinstance(value, float):
            self._valor_servico = str(value).replace('.', '')

    @valor_deducao.setter
    def valor_deducao(self, value):
        if isinstance(value, str) or isinstance(value, unicode):
            self._valor_deducao = value
        elif isinstance(value, float) or isinstance(value, int):
            self._valor_deducao = str(value).replace('.', '')

    @property
    def codigo_atividade(self):
        return self._codigo_atividade

    @codigo_atividade.setter
    def codigo_atividade(self, value):
        self._codigo_atividade = str(value).zfill(10)

    @property
    def cpf_cnpj(self):
        return self._cpf_cnpj

    @cpf_cnpj.setter
    def cpf_cnpj(self, value):
        self._cpf_cnpj = str(value).zfill(14)

    @property
    def chave(self):
        chave = (
            self.inscricao_municipal +
            self.serie +
            self.numero +
            self.data +
            self.tributacao +
            self.situacao +
            self.tipo_recolhimento +
            self.valor_servico +
            self.valor_deducao +
            self.codigo_atividade +
            self.cpf_cnpj
        )
        return chave

    @chave.setter
    def chave(self, value):
        self.inscricao_municipal = value[ChaveNFSeDSF.IM]
        self.serie = value[ChaveNFSeDSF.SERIE]
        self.numero = value[ChaveNFSeDSF.NUMERO]
        self.data = value[ChaveNFSeDSF.DATA]
        self.tributacao = value[ChaveNFSeDSF.TRIBUTACAO]
        self.situacao = value[ChaveNFSeDSF.SITUACAO]
        self.tipo_recolhimento = value[ChaveNFSeDSF.TIPO_RECOLHIMENTO]
        self.valor_servico = value[ChaveNFSeDSF.VALOR_SERVICO]
        self.valor_deducao = value[ChaveNFSeDSF.VALOR_DEDUCAO]
        self.codigo_atividade = value[ChaveNFSeDSF.CODIGO_ATIVIDADE]
        self.cpf_cnpj = value[ChaveNFSeDSF.CPF_CNPJ]

    def rps(self, rps):
        self.inscricao_municipal = rps.InscricaoMunicipalPrestador
        self.serie = rps.SerieRPS
        self.numero = rps.NumeroRPS
        self.data = rps.DataEmissaoRPS
        self.tributacao = rps.TipoRPS
        self.situacao = rps.SituacaoRPS
        self.tipo_recolhimento = rps.TipoRecolhimento

        valor_total = sum(float(item.ValorTotal) for item in rps.Itens)
        valor_deducoes = sum(float(item.ValorDeduzir) for item in rps.Deducoes)

        self.valor_servico = valor_total - valor_deducoes
        self.valor_deducao = valor_deducoes
        self.codigo_atividade = rps.CodigoAtividade
        self.cpf_cnpj = rps.CPFCNPJTomador

    @property
    def hash(self):
        hash_object = hashlib.sha1(self.chave.encode())
        return hash_object.hexdigest()
