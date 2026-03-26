"""Página Chat — analista IA do setor."""
import streamlit as st
from utils.ai import chat

def render():
    st.title("Analista IA — Panorama Rochas")
    st.markdown("""
    Pergunte sobre os dados do setor em linguagem natural.
    O analista tem acesso aos dados reais do COMEX Stat, ANM, IBGE e Centrorochas.
    """)

    sugestoes = [
        "Qual mercado tem maior potencial para quartzito em 2026?",
        "Por que o IVM está alto e o que o setor pode fazer?",
        "Quais produtos estão perdendo valor e quais estão ganhando?",
        "Como o Brasil se compara com Itália e China em diversificação?",
        "Quais estados exportadores cresceram mais nos últimos 3 anos?",
    ]

    st.caption("Sugestões de perguntas:")
    cols = st.columns(len(sugestoes))
    for i, sug in enumerate(sugestoes):
        if cols[i].button(sug[:35] + "…", key=f"sug_{i}"):
            st.session_state.pergunta_rapida = sug

    if "historico" not in st.session_state:
        st.session_state.historico = []

    for msg in st.session_state.historico:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    pergunta = st.chat_input("Faça uma pergunta sobre o setor de rochas naturais...")

    if hasattr(st.session_state, "pergunta_rapida") and st.session_state.pergunta_rapida:
        pergunta = st.session_state.pergunta_rapida
        st.session_state.pergunta_rapida = None

    if pergunta:
        with st.chat_message("user"):
            st.write(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Analisando dados..."):
                resposta = chat(pergunta, st.session_state.historico)
            st.write(resposta)

        st.session_state.historico += [
            {"role": "user",      "content": pergunta},
            {"role": "assistant", "content": resposta},
        ]
