# Panorama Rochas Naturais — POC

POC de arquitetura Medallion para inteligência estratégica do setor de rochas naturais do Brasil.

## Stack
- **Ingestor**: Python + requests + pdfplumber
- **Transformer**: Python + DuckDB + pandas
- **App**: Streamlit + Claude API
- **Infra**: Docker + docker-compose

## Arquitetura Medallion
- **Bronze**: dados brutos das APIs (Parquet, append-only)
- **Silver**: dados limpos, filtrados por NCM de rochas, com câmbio
- **Gold**: KPIs agregados, métricas estratégicas (DuckDB)

## Fontes de dados
1. COMEX Stat (MDIC) — exportações por NCM
2. IBGE SIDRA — produção industrial mineral
3. BCB SGS — câmbio USD/BRL histórico
4. ANM — produção mineral em toneladas
5. Centrorochas / ABIROCHAS — boletins PDF

## Como rodar
```bash
cp .env.example .env
# Adicione sua ANTHROPIC_API_KEY no .env
docker-compose up --build
# Acesse: http://localhost:8501
```

## O que o produto entrega
1. **IVM** — Índice de Vulnerabilidade de Mercado (HHI por destino + produto)
2. **Radar de Oportunidades** — mercados subexplorados com score de potencial
3. **Monitor de Valorização** — preço médio por m² ao longo do tempo
4. **Chat IA** — analista do setor respondendo em linguagem natural
