import streamlit as st
import google.generativeai as genai
import os
import re
import pandas as pd
import plotly.express as px

# --- Konfiguration ---
st.set_page_config(page_title="memoriq-radar-light", layout="wide")

# --- API-Key laden ---
if "GOOGLE_API_KEY" not in os.environ:
    st.error("GOOGLE_API_KEY ist nicht gesetzt. Bitte lege ihn in den Replit Secrets an.")
    st.stop()

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"Fehler beim Laden des API-Keys oder Modells: {e}")
    st.stop()

# --- UI Eingabe ---
st.title("memoriq-radar-light")
st.markdown("Testet, wie sichtbar deine Marke im Funnel ist – basierend auf LLM-Antworten.")

brand = st.text_input("Marke (Pflicht)")
product = st.text_input("Produkt oder Kategorie (Pflicht)")

col1, col2, col3 = st.columns(3)
with col1:
    competitor1 = st.text_input("Wettbewerber 1")
with col2:
    competitor2 = st.text_input("Wettbewerber 2")
with col3:
    competitor3 = st.text_input("Wettbewerber 3")

# --- Start Button ---
if st.button("Starte Analyse"):
    if not brand or not product:
        st.warning("Bitte gib mindestens Marke und Produkt/Kategorie an.")
        st.stop()

    competitors = [c for c in [competitor1, competitor2, competitor3] if c]
    all_brands = [brand] + competitors

    # Prompt zur Generierung der Funnel-Prompts
    funnel_prompt = f"""
Du bist ein SEO- und Marketingexperte und entwickelst Prompts für eine Sichtbarkeitsanalyse in Large Language Models (LLMs).
Ziel ist es herauszufinden, welche Anbieter bei typischen Nutzerfragen entlang der Customer Journey genannt werden.

Erstelle 10 konkrete LLM-Prompts, mit denen man testen kann, welche Anbieter in einem LLM genannt werden.
Die Prompts sollen entlang des Marketing-Funnels aufgebaut sein:

Top of Funnel (2 Prompts): 
- Ziel: Nutzer*innen informieren sich allgemein zum Thema. Verwende Begriffe wie „Was ist…“, „Wie funktioniert…“, „Welche Möglichkeiten gibt es…“. 

Middle of Funnel (4 Prompts): 
- Ziel: Nutzer*innen vergleichen, wollen Empfehlungen oder das passende Produkt finden. Verwende Begriffe wie „beste/r/s“, „Vergleich“, „günstigste“, „für [Ziel/Nutzung]“, „mit den besten Bewertungen“. 

Bottom of Funnel (4 Prompts): 
- Ziel: Kaufabsicht ist konkret. Verwende Begriffe wie „Wo kaufen“, „günstigster Preis“, „Angebote“, „direkt bestellen“, „Verfügbarkeit“. 

WICHTIG:
- Verwende **keine Markennamen** (auch keine erfundenen), sondern nur das Produkt, die Kategorie oder enge Synonyme.
- Die Prompts sollen so formuliert sein, wie reale Nutzer*innen suchen würden.
- Gib die 10 Prompts als nummerierte Liste aus, ohne weitere Erklärungen.

Nutze als Thema für alle 10 Prompts: {product}
"""

    with st.spinner("Generiere Funnel-Prompts..."):
        funnel_response = model.generate_content(funnel_prompt)
        funnel_text = funnel_response.text.strip()
        prompts = re.findall(r'\d+\.\s+(.*)', funnel_text)

        if len(prompts) != 10:
            st.warning("Es wurden nicht 10 Prompts gefunden. Bitte prüfe die LLM-Antwort.")
            st.code(funnel_text)
            st.stop()

    st.success("Prompts erfolgreich generiert.")
    st.markdown("### Verwendete Prompts:")
    for i, p in enumerate(prompts, 1):
        st.markdown(f"{i}. {p}")

    # --- Sichtbarkeitsanalyse ---
    results = {b: 0 for b in all_brands}
    rows = []

    with st.spinner("Führe LLM-Abfragen durch..."):
        for prompt in prompts:
            frage = f"Beantworte folgende Nutzerfrage: '{prompt}'. Nenne relevante Marken, Produkte oder Anbieter."
            try:
                response = model.generate_content(frage)
                answer = response.text.strip().lower()

                for b in all_brands:
                    if b.lower() in answer:
                        results[b] += 1

                rows.append({"Prompt": prompt, "Antwort": answer})

            except Exception as e:
                rows.append({"Prompt": prompt, "Antwort": f"Fehler: {e}"})

    # --- Ergebnisse anzeigen ---
    df_result = pd.DataFrame({
        "Marke": list(results.keys()),
        "Nennungen": list(results.values())
    })

    st.subheader("Sichtbarkeit nach Marke")
    fig = px.bar(df_result, x="Marke", y="Nennungen", title="Sichtbarkeit in LLM-Antworten")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detailansicht der Antworten")
    st.dataframe(pd.DataFrame(rows))
