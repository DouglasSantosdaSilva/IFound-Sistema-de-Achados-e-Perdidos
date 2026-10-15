from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone


PRAZO_RETIRADA_DIAS = 15
DIAS_PROXIMO_VENCIMENTO = 3


@dataclass(frozen=True)
class PrazoRetirada:
    data_limite: date | None
    classificacao: str
    dias_restantes: int | None


def calcular_prazo_retirada(item, hoje=None):
    """Return the pickup deadline and its status, based only on the found date."""
    if item.status != 'achei':
        return PrazoRetirada(None, 'nao_aplicavel', None)

    if not item.data_encontrado:
        return PrazoRetirada(None, 'data_nao_informada', None)

    data_atual = hoje if hoje is not None else timezone.localdate()
    data_limite = item.data_encontrado + timedelta(days=PRAZO_RETIRADA_DIAS)
    dias_restantes = (data_limite - data_atual).days

    if dias_restantes < 0:
        classificacao = 'vencido'
    elif dias_restantes <= DIAS_PROXIMO_VENCIMENTO:
        classificacao = 'proximo_vencimento'
    else:
        classificacao = 'aguardando_retirada'

    return PrazoRetirada(data_limite, classificacao, dias_restantes)
