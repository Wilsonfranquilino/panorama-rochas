# 💎 Panorama das Rochas Naturais — Brasil (POC)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge.svg)](https://panorama-rochas-jsou7qwx2pzpcu2otxsn4w.streamlit.app/)

Esta Prova de Conceito (POC) implementa uma infraestrutura de dados moderna utilizando a **Arquitetura Medallion** para consolidar a inteligência estratégica do setor de rochas ornamentais no Brasil. O objetivo é transformar dados públicos e setoriais em indicadores de decisão para entidades e órgãos governamentais.

## 🚀 Acesso Rápido
O dashboard está em produção e pode ser acessado diretamente pelo link abaixo:
👉 **[Acesse o Panorama de Rochas no Streamlit Cloud](https://panorama-rochas-jsou7qwx2pzpcu2otxsn4w.streamlit.app/)**

---

## 🏗️ Arquitetura e Engenharia de Dados
O pipeline foi desenhado para garantir integridade, auditabilidade e escalabilidade do dado:

* **Camada Bronze (Ingestão)**: Captura de dados brutos das fontes oficiais, armazenados em formato **Parquet** (Append-only).
* **Camada Silver (Refino)**: Normalização técnica, filtragem por NCMs específicas do setor de rochas (Granitos, Mármores, Quartzitos) e tratamento cambial.
* **Camada Gold (Inteligência)**: Modelagem de KPIs e métricas estratégicas prontas para consumo, processadas via **DuckDB**.

**Stack Tecnológica:** Python (Pandas/Requests), DuckDB (Engine de Processamento), Streamlit (Interface) e Docker para orquestração de ambiente.

## 📊 Fontes de Dados Integradas
O ecossistema consome dados diretamente de:
1.  **COMEX Stat (MDIC)**: Fluxos de exportação por NCM e valor FOB.
2.  **IBGE SIDRA**: Indicadores de produção industrial mineral.
3.  **BCB (SGS)**: Séries históricas de câmbio USD/BRL e índices inflacionários.
4.  **ANM**: Dados de produção mineral e arrecadação de royalties.
5.  **Centrorochas / ABIROCHAS**: Boletins técnicos e inteligência setorial.

## 📦 Como Executar Localmente
Para rodar o ambiente completo via **Docker**, garantindo que o ambiente de execução seja isolado:

```bash
# 1. Clone o repositório
git clone [https://github.com/seu-usuario/panorama-rochas.git](https://github.com/seu-usuario/panorama-rochas.git)
cd panorama-rochas

# 2. Build e execução via Docker Compose
docker-compose up --build