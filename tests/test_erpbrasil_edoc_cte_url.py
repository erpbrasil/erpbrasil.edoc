import pytest

from erpbrasil.edoc import cte

UFS = [uf for uf in cte.SIGLA_ESTADO if uf != "AN"]
PROPRIOS = {
    "PR": ("cte.fazenda.pr.gov.br", "homologacao.cte.fazenda.pr.gov.br"),
    "MT": ("cte.sefaz.mt.gov.br", "homologacao.sefaz.mt.gov.br"),
    "MS": ("producao.cte.ms.gov.br", "homologacao.cte.ms.gov.br"),
    "MG": ("cte.fazenda.mg.gov.br", "hcte.fazenda.mg.gov.br"),
}


def _servidor_esperado(uf, ambiente):
    producao = ambiente == 1
    if uf in PROPRIOS:
        return PROPRIOS[uf][0 if producao else 1]
    if uf in ("AP", "PE", "RR", "SP"):
        return "nfe.fazenda.sp.gov.br" if producao else "homologacao.nfe.fazenda.sp.gov.br"
    return "cte.svrs.rs.gov.br" if producao else "cte-homologacao.svrs.rs.gov.br"


@pytest.mark.parametrize("ambiente", [1, 2])
@pytest.mark.parametrize("uf", UFS)
def test_url_autorizacao_todas_as_ufs(uf, ambiente):
    url = cte.get_service_url(uf, cte.WS_CTE_RECEPCAO_SINC, ambiente)
    assert url.startswith(f"https://{_servidor_esperado(uf, ambiente)}/")
    assert "CTeRecepcaoSincV4" in url


@pytest.mark.parametrize("uf", sorted(PROPRIOS))
def test_ufs_com_autorizadora_propria_resolvem_todos_os_servicos(uf):
    servicos = [
        cte.WS_CTE_CONSULTA,
        cte.WS_CTE_RECEPCAO_EVENTO,
        cte.WS_CTE_RECEPCAO_GT,
        cte.WS_CTE_RECEPCAO_OS,
        cte.WS_CTE_RECEPCAO_SINC,
        cte.WS_CTE_STATUS_SERVICO,
        cte.QR_CODE_URL,
    ]
    for ambiente in (1, 2):
        for servico in servicos:
            assert cte.get_service_url(uf, servico, ambiente)


def test_uf_desconhecida_levanta_value_error():
    with pytest.raises(ValueError):
        cte.get_service_url("XX", cte.WS_CTE_RECEPCAO_SINC, 1)
