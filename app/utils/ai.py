"""Utilitário de chat com Claude API com contexto dos dados Gold."""
import os
from utils.db import query

SYSTEM_PROMPT = """Você é um analista especialista no setor de rochas naturais do Brasil.
Você tem acesso a dados reais de exportação do COMEX Stat, produção da ANM, câmbio do BCB e boletins da Centrorochas.

Responda sempre em português, de forma clara e estratégica.
Quando relevante, cite números concretos dos dados.
Foque em insights acionáveis para exportadores e formuladores de política setorial.

Contexto atual dos dados:
{contexto}
"""

def obter_contexto() -> str:
    try:
        ivm = query("SELECT ano, ivm, nivel_risco FROM metric_ivm ORDER BY ano DESC LIMIT 1")
        tot = query("SELECT ano, total_fob_usd, num_paises FROM gold_totais_anuais ORDER BY ano DESC LIMIT 1")
        top3 = query("""
            SELECT pais_nome, ROUND(pct_total,1) as pct
            FROM gold_ranking_destinos
            WHERE ano = (SELECT MAX(ano) FROM gold_ranking_destinos)
            AND rank <= 3
        """)
        ctx = f"""
- Último ano: {tot['ano'].iloc[0]}
- Exportações: US$ {tot['total_fob_usd'].iloc[0]/1e9:.2f} bilhões
- Países destino: {tot['num_paises'].iloc[0]}
- IVM: {ivm['ivm'].iloc[0]} (risco {ivm['nivel_risco'].iloc[0]})
- Top 3: {', '.join([f"{r['pais_nome']} ({r['pct']}%)" for _, r in top3.iterrows()])}
"""
        return ctx
    except Exception:
        return "Dados em processamento."

def chat(mensagem: str, historico: list) -> str:
    """Envia mensagem para Claude — inicializa cliente aqui, não no módulo."""
    import anthropic

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "Configure a variável ANTHROPIC_API_KEY no arquivo .env para usar o chat com IA."

    try:
        client = anthropic.Anthropic(api_key=api_key)
        contexto = obter_contexto()
        system = SYSTEM_PROMPT.format(contexto=contexto)
        messages = historico + [{"role": "user", "content": mensagem}]

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Erro ao conectar com a IA: {e}"
