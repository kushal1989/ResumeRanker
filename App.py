import streamlit as st
import nltk
import spacy
import pandas as pd
import base64
import time, datetime
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
from PIL import Image
import pymysql
from Courses import ds_course, web_course, android_course, ios_course, uiux_course, artificial_course
import plotly.express as px
nltk.download('stopwords')
spacy.load('en_core_web_sm')


def fetch_yt_video(link):
    return link


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/csv;base64,{b64}">Download Report</a>'
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,
                                      caching=True,
                                      check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text


def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def course_recommender(course_list):
    st.subheader("Courses & Certificates Recommendations")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


connection = pymysql.connect(host='localhost', user='root', password='')
cursor = connection.cursor()


def insert_data(name, email, res_score, timestamp, no_of_pages, reco_field, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()


st.set_page_config(
    page_title="SMART RESUME ANALYZER",
    page_icon='./Logo/SRA_Logo.ico',
)


def run():
    st.title("Smart Resume Analyser")

    st.sidebar.markdown("# Choose User")
    activities = ["Normal User", "Admin"]
    choice = st.sidebar.selectbox("Choose the user type:", activities)
    img = Image.open('./Logo/SRA_Logo.png')
    img = img.resize((250, 250))
    st.image(img)


    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """
                    (ID INT NOT NULL AUTO_INCREMENT,
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
                     PRIMARY KEY (ID));
                    """
    cursor.execute(table_sql)
    if choice == 'Normal User':
        #             unsafe_allow_html=True)
        pdf_file = st.file_uploader("Upload your Resume", type=["pdf"])
        if pdf_file is not None:
            st.write("")
            with st.spinner('Uploading your Resume....'):
                 time.sleep(4)
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            st.write("")

            with st.spinner('Please Wait Analysing your Resume....'):
                 time.sleep(4)

            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("Resume Analysis")
                st.success("Hello " + resume_data['name'])
                st.subheader("Your Basic info")
                try:
                    st.text('Name: ' + resume_data['name'])
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                except:
                    pass
                cand_level = ''
                if resume_data['no_of_pages'] == 1:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level.</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] == 2:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at Intermediate level!</h4>''',
                                unsafe_allow_html=True)
                elif resume_data['no_of_pages'] >= 3:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Experience level!''',
                                unsafe_allow_html=True)

                st.subheader("Skills Recommendation")
                ## Skill shows
                keywords = st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='1')

                ##  recommendation
                ds_keyword = ['tensorflow', 'keras', 'pytorch', 'machine learning', 'deep Learning', 'flask',
                              'streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress',
                               'javascript', 'angular js', 'c#', 'flask']
                android_keyword = ['android', 'android development', 'flutter', 'kotlin', 'xml', 'kivy']
                ios_keyword = ['ios', 'ios development', 'swift', 'cocoa', 'cocoa touch', 'xcode']
                uiux_keyword = ['ux', 'adobe xd', 'figma', 'zeppelin', 'balsamic', 'ui', 'prototyping', 'wireframes',
                                'story frames', 'adobe photoshop', 'photoshop', 'editing', 'adobe illustrator',
                                'illustrator', 'adobe after effects', 'after effects', 'adobe premier pro',
                                'premier pro', 'adobe indesign', 'indesign', 'wireframe', 'solid', 'grasp',
                                'user research', 'user experience']
                artificial_keyword = ['Machine Learning', 'Deep Learning', 'Neural Networks', 'Natural Language Processing (NLP)',
                                      'Computer Vision', 'Robotics', 'Expert Systems', 'Reinforcement Learning', 'Speech Recognition',
                                      'AI Ethics', 'Knowledge Representation', 'Cognitive Computing', 'Pattern Recognition', 'Decision Trees',
                                      'Genetic Algorithms']

                recommended_skills = []
                reco_field = ''
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success(" Our analysis says your resume suits for Data Science Jobs.")
                        recommended_skills = ['Data Visualization', 'Predictive Analysis', 'Statistical Modeling',
                                              'Data Mining', 'Clustering & Classification', 'Data Analytics',
                                              'Quantitative Analysis', 'Web Scraping', 'ML Algorithms', 'Keras',
                                              'Pytorch', 'Probability', 'Scikit-learn', 'Tensorflow', "Flask",
                                              'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='2')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success(" Our analysis says your resume suits for Web Development Jobs ")
                        recommended_skills = ['React', 'Django', 'Node JS', 'React JS', 'php', 'laravel', 'Magento',
                                              'wordpress', 'Javascript', 'Angular JS', 'c#', 'Flask', 'SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='3')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success(" Our analysis says your resume suits for Android App Development Jobs ")
                        recommended_skills = ['Android', 'Android development', 'Flutter', 'Kotlin', 'XML', 'Java',
                                              'Kivy', 'GIT', 'SDK', 'SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='4')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success(" Our analysis says your resume suits for IOS App Development Jobs ")
                        recommended_skills = ['IOS', 'IOS Development', 'Swift', 'Cocoa', 'Cocoa Touch', 'Xcode',
                                              'Objective-C', 'SQLite', 'Plist', 'StoreKit', "UI-Kit", 'AV Foundation',
                                              'Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='5')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success(" Our analysis says your resume suits for UI-UX Development Jobs ")
                        recommended_skills = ['UI', 'User Experience', 'Adobe XD', 'Figma', 'Zeppelin', 'Balsamic',
                                              'Prototyping', 'Wireframes', 'Story frames', 'Adobe Photoshop', 'Editing',
                                              'Illustrator', 'After Effects', 'Premier Pro', 'Indesign', 'Wireframe',
                                              'Solid', 'Grasp', 'User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                            '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                        ## AI Recommendation
                    elif i.lower() in artificial_keyword:
                        print(i.lower())
                        reco_field = 'Artificial intelligence'
                        st.success(" Our analysis says your resume suits for Artificial Intelligence Jobs ")
                        recommended_skills =  ['Machine Learning', 'Deep Learning', 'Neural Networks', 'Natural Language Processing (NLP)',
                                               'Computer Vision', 'Robotics', 'Expert Systems', 'Reinforcement Learning', 'Speech Recognition',
                                               'AI Ethics', 'Knowledge Representation', 'Cognitive Computing', 'Pattern Recognition', 'Decision Trees',
                                               'Genetic Algorithms']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                                                       text='Recommended skills generated from System',
                                                       value=recommended_skills, key='6')
                        st.markdown(
                                 '''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to resume will boost the chances of getting a Job</h4>''',
                                 unsafe_allow_html=True)
                        rec_course = course_recommender(artificial_course)
                        break

                #
                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("Resume Tips & Ideas")
                resume_score = 0
                if 'Objective' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #FF0000;'>[-] According to our recommendation please add your career objective, it will give your career intention to the Recruiters.</h4>''',
                        unsafe_allow_html=True)

                if 'Declaration' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Declaration✍/h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #FF0000;'>[-] According to our recommendation please add Declaration✍. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',
                        unsafe_allow_html=True)

                if 'Hobbies' or 'Interests' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies⚽</h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #FF0000;'>[-] According to our recommendation please add Hobbies⚽. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',
                        unsafe_allow_html=True)

                if 'Achievements' or 'Certificates' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements🏅 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #FF0000;'>[-] According to our recommendation please add Achievements🏅. It will show that you are capable for the required position.</h4>''',
                        unsafe_allow_html=True)

                if 'Projects' or 'Personal Projects' in resume_text:
                    resume_score = resume_score + 20
                    st.markdown(
                        '''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects👨‍💻 </h4>''',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '''<h4 style='text-align: left; color: #FF0000;'>[-] According to our recommendation please add Projects👨‍💻. It will show that you have done work related the required position or not.</h4>''',
                        unsafe_allow_html=True)

                st.subheader("Resume Score")
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score += 1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)
                st.success(' Your Resume Writing Score: ' + str(score) + '')
                st.warning(
                    " Note: This score is calculated based on the content that you have added in your Resume. ")
                st.balloons()

                insert_data(resume_data['name'], resume_data['email'], str(resume_score), timestamp,
                            str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']),
                            str(recommended_skills), str(rec_course))

                st.header("Recommended Video for Resume Writing")
                resume_video_links = ['https://youtu.be/y8YH0Qbu5h4','https://youtu.be/J-4Fv8nq1iA',
                 'https://youtu.be/yp693O87GmM','https://youtu.be/UeMmCex9uTU',
                 'https://youtu.be/dQ7Q8ZdnuN0','https://youtu.be/HQqqQx5BCFY',
                 'https://youtu.be/CLUsplI4xMU','https://youtu.be/pbczsLkv7Cc']

                for video_link in resume_video_links:
                    video_title = fetch_yt_video(video_link)
                    st.subheader(f"✅ [**{video_title}**]({video_link})")

                st.header("Recommended Video for Interview")
                interview_video_links = ['https://youtu.be/Ji46s5BHdr0', 'https://youtu.be/seVxXHi2YMs',
                                    'https://youtu.be/9FgfsLa_SmY', 'https://youtu.be/2HQmjLu-6RQ',
                                    'https://youtu.be/DQd_AlIvHUw', 'https://youtu.be/oVVdezJ0e7w',
                                    'https://youtu.be/JZK1MZwUyUU', 'https://youtu.be/CyXLhHQS3KY']

                for video_link in interview_video_links:
                    video_title = fetch_yt_video(video_link)
                    st.subheader(f"✅ [**{video_title}**]({video_link})")
                connection.commit()
            else:
                st.error('Something went wrong..')
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        st.sidebar.subheader('ID & Password Required!')

        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'admin' and ad_password == 'admin123' or ad_user == 'kushal' and ad_password == '1234':
                if ad_user == 'admin':
                 st.success("Welcome ADMIN")
                elif ad_user == 'kushal':
                 st.success("Welcome kushal")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("User's Data")
                df = pd.DataFrame(data, columns=['ID', 'Name', 'Email', 'Resume Score', 'Timestamp', 'Total Page',
                                                 'Predicted Field', 'User Level', 'Actual Skills', 'Recommended Skills',
                                                 'Recommended Course'])
                st.dataframe(df)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                ## Admin Side Data
                query = 'select * from user_data;'
                plot_data = pd.read_sql(query, connection)

                ## Pie chart for predicted field recommendations
                labels = plot_data.Predicted_Field.unique()
                print(labels)
                values = plot_data.Predicted_Field.value_counts()
                print(values)
                st.subheader(" Pie-Chart for Predicted Field Recommendations")
                fig = px.pie(df, values=values, names=labels, title='Predicted Field according to the Skills')
                st.plotly_chart(fig)

                ### Pie chart for User's Experienced Level
                labels = plot_data.User_level.unique()
                values = plot_data.User_level.value_counts()
                st.subheader(" Pie-Chart for User's Experienced Level")
                fig = px.pie(df, values=values, names=labels, title="Predicted Experienced Level")
                st.plotly_chart(fig)

                # Display the best resumes from each category
                st.header("Best Resumes from Each Category")

                # Try to convert 'Resume Score' to numeric (ignore errors)
                df['Resume Score'] = pd.to_numeric(df['Resume Score'], errors='coerce')

                # Initialize variables to store the best scores and corresponding rows
                best_basic_resume = None
                best_intermediate_resume = None
                best_experienced_resume = None

                # Loop through each row and update the best scores and corresponding rows
                for level in ['Fresher', 'Intermediate', 'Experienced']:
                    filtered_df = df[df['User Level'] == level]
                    if not filtered_df.empty:
                        max_row = filtered_df.nlargest(1, 'Resume Score', 'all')
                        if level == 'Fresher':
                            best_basic_resume = max_row
                        elif level == 'Intermediate':
                            best_intermediate_resume = max_row
                        elif level == 'Experienced':
                            best_experienced_resume = max_row

                # Display the best resumes
                st.subheader("Best Basic Level Resume")
                st.dataframe(best_basic_resume)

                st.subheader("Best Intermediate Level Resume")
                st.dataframe(best_intermediate_resume)

                st.subheader("Best Experienced Level Resume")
                st.dataframe(best_experienced_resume)

                # ... (your existing code)

            else:
                st.error("Wrong ID or Password Provided")


run()
