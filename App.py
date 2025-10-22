import streamlit as st
import nltk
import os

# ============================================
# 🧠 FIX 1: Ensure all NLTK data BEFORE pyresparser import
# ============================================
nltk_data_dir = os.path.join(os.getcwd(), 'nltk_data')
if not os.path.exists(nltk_data_dir):
    os.mkdir(nltk_data_dir)
nltk.data.path.append(nltk_data_dir)

nltk_packages = [
    'stopwords', 'punkt', 'wordnet',
    'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words'
]
for pkg in nltk_packages:
    try:
        nltk.data.find(f'corpora/{pkg}')
    except LookupError:
        nltk.download(pkg, download_dir=nltk_data_dir)

# ✅ Import pyresparser *after* NLTK data is ready
from pyresparser import ResumeParser

# ============================================
# 🧠 FIX 2: Use preinstalled spaCy model (avoid runtime install)
# ============================================
import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    st.warning("⚠️ spaCy model 'en_core_web_sm' not found. Please ensure it’s installed via requirements.txt.")
    nlp = None

# ============================================
# 📚 Other imports
# ============================================
import pandas as pd
import base64
import time, datetime
import io, random
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, artificial_course
import plotly.express as px

# ============================================
# 📘 Helper Functions
# ============================================
def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()

    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("🎯 Course & Certificate Recommendations")
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for i, (c_name, c_link) in enumerate(course_list[:no_of_reco], 1):
        st.markdown(f"({i}) [{c_name}]({c_link})")
        rec_course.append(c_name)
    return rec_course


# ============================================
# 💾 Database Setup
# ============================================
connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    DB_table_name = 'user_data'
    insert_sql = "INSERT INTO " + DB_table_name + """
    VALUES (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level,
                  skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# ============================================
# 🚀 Streamlit App Configuration
# ============================================
st.set_page_config(
    page_title="SMART RESUME ANALYZER",
    page_icon='./Logo/SRA_Logo.ico',
)

def run():
    st.title("🤖 Smart Resume Analyzer")
    st.sidebar.markdown("## Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose the user type:", activities)

    img = Image.open('./Logo/SRA_Logo.png')
    img = img.resize((250, 250))
    st.image(img)

    # Create DB & Table
    cursor.execute("CREATE DATABASE IF NOT EXISTS SRA;")
    connection.select_db("SRA")

    DB_table_name = 'user_data'
    table_sql = """CREATE TABLE IF NOT EXISTS """ + DB_table_name + """(
                     ID INT NOT NULL AUTO_INCREMENT,
                     Name varchar(100) NOT NULL,
                     Email_ID VARCHAR(50) NOT NULL,
                     resume_score VARCHAR(8) NOT NULL,
                     Timestamp VARCHAR(50) NOT NULL,
                     Page_no VARCHAR(5) NOT NULL,
                     Predicted_Field VARCHAR(25) NOT NULL,
                     User_level VARCHAR(30) NOT NULL,
                     Actual_skills VARCHAR(300) NOT NULL,
                     Recommended_skills VARCHAR(300) NOT NULL,
                     Recommended_courses VARCHAR(600) NOT NULL,
                     PRIMARY KEY (ID));"""
    cursor.execute(table_sql)

    # ============================================
    # 👤 NORMAL USER SECTION
    # ============================================
    if choice == 'Normal User':
        pdf_file = st.file_uploader("Upload your Resume", type=["pdf"])
        if pdf_file is not None:
            with st.spinner('📄 Uploading your Resume...'):
                time.sleep(2)
                save_image_path = './Uploaded_Resumes/' + pdf_file.name
                os.makedirs('./Uploaded_Resumes', exist_ok=True)
                with open(save_image_path, "wb") as f:
                    f.write(pdf_file.getbuffer())

            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            time.sleep(2)

            if resume_data:
                resume_text = pdf_reader(save_image_path)
                st.header("📋 Resume Analysis")
                st.success("Hello " + resume_data.get('name', 'User'))

                try:
                    st.text('📧 Email: ' + str(resume_data.get('email', '')))
                    st.text('📞 Contact: ' + str(resume_data.get('mobile_number', '')))
                    st.text('📄 Resume pages: ' + str(resume_data.get('no_of_pages', '')))
                except:
                    pass

                # Candidate level
                cand_level = ''
                pages = resume_data.get('no_of_pages', 1)
                if pages == 1:
                    cand_level = "Fresher"
                    st.markdown("<h4 style='color:#d73b5c;'>You are a Fresher!</h4>", unsafe_allow_html=True)
                elif pages == 2:
                    cand_level = "Intermediate"
                    st.markdown("<h4 style='color:#1ed760;'>You are at Intermediate level!</h4>", unsafe_allow_html=True)
                else:
                    cand_level = "Experienced"
                    st.markdown("<h4 style='color:#fba171;'>You are Experienced!</h4>", unsafe_allow_html=True)

                # Skills Recommendation
                st.subheader("🧩 Skills Recommendation")
                keywords = st_tags(label='### Skills Detected from Resume',
                                   text='See our skill recommendations',
                                   value=resume_data.get('skills', []),
                                   key='1')

                # Keyword lists
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit']
                web_keyword = ['react', 'django', 'node js', 'php', 'laravel', 'wordpress', 'javascript', 'angular']
                android_keyword = ['android', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'swift', 'xcode', 'cocoa']
                uiux_keyword = ['figma', 'adobe xd', 'ux', 'ui', 'wireframe']
                artificial_keyword = ['ai', 'artificial intelligence', 'neural networks', 'deep learning']

                recommended_skills, reco_field, rec_course = [], '', ''

                for i in resume_data.get('skills', []):
                    skill = i.lower()
                    if skill in ds_keyword:
                        reco_field = 'Data Science'
                        st.success("🎯 Suitable Field: Data Science")
                        recommended_skills = ['TensorFlow', 'Keras', 'Pytorch']
                        rec_course = course_recommender(ds_course)
                        break
                    elif skill in web_keyword:
                        reco_field = 'Web Development'
                        st.success("🎯 Suitable Field: Web Development")
                        recommended_skills = ['Django', 'Flask', 'React']
                        rec_course = course_recommender(web_course)
                        break
                    elif skill in android_keyword:
                        reco_field = 'Android Development'
                        st.success("🎯 Suitable Field: Android Development")
                        recommended_skills = ['Kotlin', 'Flutter']
                        rec_course = course_recommender(android_course)
                        break
                    elif skill in ios_keyword:
                        reco_field = 'iOS Development'
                        st.success("🎯 Suitable Field: iOS Development")
                        recommended_skills = ['Swift', 'Xcode']
                        rec_course = course_recommender(ios_course)
                        break
                    elif skill in uiux_keyword:
                        reco_field = 'UI/UX Design'
                        st.success("🎯 Suitable Field: UI/UX Design")
                        recommended_skills = ['Figma', 'Adobe XD']
                        rec_course = course_recommender(uiux_course)
                        break
                    elif skill in artificial_keyword:
                        reco_field = 'Artificial Intelligence'
                        st.success("🎯 Suitable Field: Artificial Intelligence")
                        recommended_skills = ['Deep Learning', 'NLP']
                        rec_course = course_recommender(artificial_course)
                        break

                # Save data
                ts = time.time()
                timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H:%M:%S')

                insert_data(resume_data.get('name', 'User'), resume_data.get('email', ''),
                            '80', timestamp, str(pages), reco_field, cand_level,
                            str(resume_data.get('skills', [])), str(recommended_skills), str(rec_course))

                st.balloons()

    # ============================================
    # 🔐 ADMIN SECTION
    # ============================================
    else:
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if (ad_user == 'admin' and ad_password == 'admin123') or (ad_user == 'kushal' and ad_password == '1234'):
                st.success(f"Welcome {ad_user.capitalize()}")
                cursor.execute("SELECT * FROM user_data")
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=[
                    'ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                    'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills', 'Recommended Course'
                ])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', '📥 Download Report'), unsafe_allow_html=True)

                plot_data = pd.read_sql('SELECT * FROM user_data;', connection)
                st.subheader("📊 Predicted Field Distribution")
                st.plotly_chart(px.pie(plot_data, names='Predicted_Field', title='Predicted Field by Skillset'))

                st.subheader("📊 User Experience Level Distribution")
                st.plotly_chart(px.pie(plot_data, names='User_level', title="User Experience Level"))
            else:
                st.error("Invalid Admin Credentials!")


# ============================================
# 🏁 Run the app
# ============================================
if __name__ == "__main__":
    run()
