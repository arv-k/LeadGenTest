import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

st.set_page_config(page_title="Campus Lead Gen - Doorlist Fit Finder")
st.title("🎓 Campus Event Intelligence Tracker")
st.markdown("""
This tool scrapes a student organization directory (starting with USC EngageSC)
and finds orgs likely to host ticketed or RSVP-based events — ideal for Doorlist outreach.
""")

# --- Config
DEFAULT_URL = "https://engage.usc.edu/home/groups/"
KEYWORDS = ["ticket", "rsvp", "eventbrite", "sold out", "guest list", "linktree"]

# --- Functions
@st.cache_data(show_spinner=False)
def fetch_orgs(url):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    entries = soup.find_all("div", class_="group-info")
    orgs = []
    for entry in entries:
        name_tag = entry.find("a", class_="group-name")
        cat_tag = entry.find("div", class_="group-category")
        if name_tag:
            name = name_tag.text.strip()
            link = "https://engage.usc.edu" + name_tag.get("href")
            category = cat_tag.text.strip() if cat_tag else "N/A"
            orgs.append({"Name": name, "Category": category, "Link": link})
    return orgs

def score_org_page(url):
    try:
        res = requests.get(url, timeout=10)
        text = res.text.lower()
        score = sum(kw in text for kw in KEYWORDS)
        return score
    except:
        return 0

# --- User Input
input_url = st.text_input("Enter student org directory URL:", value=DEFAULT_URL)

if st.button("Find Leads"):
    with st.spinner("Scraping orgs and scoring..."):
        orgs = fetch_orgs(input_url)
        for org in orgs:
            org["Score"] = score_org_page(org["Link"])
        leads = [org for org in orgs if org["Score"] > 0]
        df = pd.DataFrame(leads).sort_values("Score", ascending=False)
        st.success(f"Found {len(df)} high-potential orgs!")
        st.dataframe(df)
        st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="doorlist_leads.csv")
else:
    st.info("Paste the URL of a student organization directory (e.g., EngageSC at USC)")
