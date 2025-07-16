import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

st.set_page_config(page_title="Campus Lead Gen - Doorlist Fit Finder")
st.title("🎓 Campus Event Intelligence Tracker")
st.markdown("""
This tool scrapes a student organization directory (works best with CampusLabs Engage)
and finds orgs likely to host ticketed or RSVP-based events — ideal for Doorlist outreach.
""")

# --- Config
DEFAULT_URL = "https://msu.campuslabs.com/engage/organizations"
KEYWORDS = ["ticket", "rsvp", "eventbrite", "sold out", "guest list", "linktree"]

# --- Functions
@st.cache_data(show_spinner=False)
def fetch_orgs(directory_url):
    try:
        root = directory_url.split('/')[2]  # Extract domain like engage.msu.edu
        api_url = f"https://{root}/api/discovery/search/organizations?take=1000"
        resp = requests.get(api_url)
        if resp.status_code != 200:
            st.error(f"Failed to fetch org data. Status code: {resp.status_code}")
            return []
        try:
            data = resp.json()
        except ValueError:
            st.error("Failed to decode JSON from response.")
            return []
        orgs = []
        for item in data.get("value", []):
            name = item.get("name", "").strip()
            category = item.get("categoryName", "N/A")
            link = f"https://{root}/organization/" + item.get("url", "")
            orgs.append({"Name": name, "Category": category, "Link": link})
        return orgs
    except Exception as e:
        st.error(f"Error fetching orgs: {e}")
        return []

def score_org_page(url):
    try:
        res = requests.get(url, timeout=10)
        text = res.text.lower()
        score = sum(kw in text for kw in KEYWORDS)
        return score
    except:
        return 0

# --- User Input
input_url = st.text_input("Enter CampusLabs org directory URL:", value=DEFAULT_URL)

if st.button("Find Leads"):
    with st.spinner("Scraping orgs and scoring..."):
        orgs = fetch_orgs(input_url)
        if not orgs:
            st.warning("No organizations found or failed to fetch data.")
        else:
            for org in orgs:
                org["Score"] = score_org_page(org["Link"])

            leads = [org for org in orgs if org.get("Score", 0) > 0]

            if not leads:
                st.warning("No high-scoring orgs found. Try a different directory URL or check keywords.")
            else:
                df = pd.DataFrame(leads)
                if "Score" not in df.columns:
                    st.error("Score column missing. Something went wrong during parsing.")
                else:
                    df = df.sort_values("Score", ascending=False)
                    st.success(f"Found {len(df)} high-potential orgs!")
                    st.dataframe(df)
                    st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="doorlist_leads.csv")
else:
    st.info("Paste the URL of a CampusLabs organization directory (e.g., https://msu.campuslabs.com/engage/organizations)")
