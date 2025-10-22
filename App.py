import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import csv
import os
import nltk
import spacy
from pyresparser import ResumeParser
from datetime import datetime
from streamlit_tags import st_tags
from PIL import Image

# ===============================
# 🧩 NLTK Setup
# ===============================
nltk_data_dir = os.path.join(os.getcwd(), "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)
for pkg in ['stopwords', 'punkt', 'wordnet', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']:
    try:
        nltk.download(pkg, download_dir=nltk_data_dir, quiet=True)
    except:
        pass

# ===============================
# 🧠 spaCy Model Load
# ===============================
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None
    st.warning("⚠️ spaCy model 'en_core_web_sm' not found — please ensure it's in requirements.txt.")

# ===============================
# 💾 CSV Storage (No MySQL)
# ===============================
DB_FILE = "user_data.csv"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "Name", "Email_ID", "Resume_Score", "Timestamp",
            "Page_no", "Predicted_Field", "User_level",
            "Actual_skills", "Recommended_skills", "Recommended_courses"
        ])

def insert_data(name, email, res_score, timestamp, no_of_pages,
                reco_field, cand_level, skills, recommended_skills, courses):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.reader(f))
        next_id = len(rows)

    with open(DB_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            next_id, name, email, res_score, timestamp,
            no_of_pages, reco_field, cand_level,
            skills, recommended_skills, courses
        ])

# ===============================
# 📊 Streamlit App
# ===============================
st.set_page_config(page_title="Smart Resume Analyser", layout="wide")

st.title("📄 Smart Resume Analyser with Admin Dashboard")

menu = ["Normal User", "Admin"]
choice = st.sidebar.selectbox("Select User Type", menu)

# ===============================
# 👤 NORMAL USER
# ===============================
if choice == "Normal User":
    st.subheader("Upload Your Resume")

    uploaded_file = st.file_uploader("Choose a resume (PDF format)", type=["pdf"])
    if uploaded_file is not None:
        with open("Uploaded_Resume.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ Resume uploaded successfully!")

        # Parse Resume
        with st.spinner("Analyzing Resume..."):
            resume_data = ResumeParser("Uploaded_Resume.pdf").get_extracted_data()

        if resume_data:
            st.subheader("📋 Extracted Resume Details")
            st.write(resume_data)

            # Get recommendations
            skills = ", ".join(resume_data.get("skills", []))
            cand_level = "Intermediate"
            reco_field = "Data Science" if "python" in skills.lower() else "Other"
            recommended_skills = "Machine Learning, SQL, Statistics" if "python" in skills.lower() else "Communication"
            courses = "AI for Everyone, Python Basics" if "python" in skills.lower() else "Soft Skills Mastery"

            # Save data
            insert_data(
                resume_data.get("name", "Unknown"),
                resume_data.get("email", "NA"),
                85,  # example score
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                1,
                reco_field,
                cand_level,
                skills,
                recommended_skills,
                courses
            )

            st.success("✅ Analysis Complete & Saved!")
        else:
            st.error("❌ Could not extract information. Try another resume.")

# ===============================
# 🧑‍💼 ADMIN DASHBOARD
# ===============================
elif choice == "Admin":
    st.subheader("Admin Dashboard")

    password = st.text_input("Enter Admin Password", type="password")
    if password == "admin123":  # Change as needed
        st.success("Access Granted ✅")

        if os.path.exists(DB_FILE):
            df = pd.read_csv(DB_FILE)
            st.dataframe(df)

            # Summary Chart
            if not df.empty:
                st.subheader("📊 Field Distribution")
                field_counts = df["Predicted_Field"].value_counts()
                fig = go.Figure(data=[
                    go.Bar(x=field_counts.index, y=field_counts.values)
                ])
                fig.update_layout(title="Resumes by Predicted Field")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No records found yet.")
    elif password:
        st.error("Invalid password ❌")

# ===============================
# 🧾 Footer
# ===============================
st.markdown("---")
st.caption("Developed by Kushal © 2025 | Streamlit Cloud Compatible")
