# skilledge - Made with Streamlit


###### Packages Used ######
import streamlit as st # core package used in this project
import pandas as pd
import base64, random
import time,datetime
from pymongo import MongoClient
import os
import socket
import platform
import geocoder
import secrets
import io,random
import plotly.express as px # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,resume_videos,interview_videos
import nltk
nltk.download('stopwords')


###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format 
def get_csv_download_link(df,filename,text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()      
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    try:
        with open(file, 'rb') as fh:
            for page in PDFPage.get_pages(fh,
                                          caching=True,
                                          check_extractable=True):
                page_interpreter.process_page(page)
                print(page)
            text = fake_file_handle.getvalue()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        text = ""
    finally:
        ## close open handles
        converter.close()
        fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations ‍**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


# MongoDB connector
try:
    # Try to get MongoDB URI from Streamlit secrets (cloud) or environment variable
    mongodb_uri = None
    
    # First, try Streamlit secrets (for Streamlit Cloud)
    try:
        mongodb_uri = st.secrets["MONGODB_URI"]
    except:
        pass
    
    # If not in secrets, try environment variable
    if not mongodb_uri:
        mongodb_uri = os.environ.get('MONGODB_URI')
    
    # If still not found, use local MongoDB
    if not mongodb_uri:
        mongodb_uri = 'mongodb://localhost:27017/'
    
    client = MongoClient(mongodb_uri)
    db = client['skilledge_db']
    user_collection = db['user_data']
    feedback_collection = db['user_feedback']
    DB_AVAILABLE = True
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"Warning: Database connection failed: {e}")
    print("Running in demo mode without database. Data will not be saved.")
    client = None
    db = None
    user_collection = None
    feedback_collection = None
    DB_AVAILABLE = False


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data collection
def insert_data(sec_token,ip_add,host_name,dev_user,os_name_ver,latlong,city,state,country,act_name,act_mail,act_mob,name,email,res_score,timestamp,no_of_pages,reco_field,cand_level,skills,recommended_skills,courses,pdf_name):
    if not DB_AVAILABLE:
        return
    document = {
        'sec_token': str(sec_token),
        'ip_add': str(ip_add),
        'host_name': host_name,
        'dev_user': dev_user,
        'os_name_ver': os_name_ver,
        'latlong': str(latlong),
        'city': city,
        'state': state,
        'country': country,
        'act_name': act_name,
        'act_mail': act_mail,
        'act_mob': act_mob,
        'Name': name,
        'Email_ID': email,
        'resume_score': str(res_score),
        'Timestamp': timestamp,
        'Page_no': str(no_of_pages),
        'Predicted_Field': reco_field,
        'User_level': cand_level,
        'Actual_skills': skills,
        'Recommended_skills': recommended_skills,
        'Recommended_courses': courses,
        'pdf_name': pdf_name
    }
    user_collection.insert_one(document)


# inserting feedback data into user_feedback collection
def insertf_data(feed_name,feed_email,feed_score,comments,Timestamp):
    if not DB_AVAILABLE:
        return
    document = {
        'feed_name': feed_name,
        'feed_email': feed_email,
        'feed_score': feed_score,
        'comments': comments,
        'Timestamp': Timestamp
    }
    feedback_collection.insert_one(document)


###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
   page_title="skilledge",
   page_icon='./Logo/recommend.png',
   layout="wide"
)

# Initialize session state for authentication
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# User database collection for authentication
if DB_AVAILABLE:
    auth_collection = db['users']


# Custom CSS for horizontal navbar
def load_css():
    st.markdown("""
    <style>
        /* Hide default sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Horizontal Navigation Bar */
        .navbar {
            background-color: #1e3a8a;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            border-radius: 8px;
        }
        
        .navbar-brand {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
        }
        
        .navbar-menu {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            transition: background-color 0.3s;
        }
        
        .nav-link:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        
        /* Make file uploader bigger */
        [data-testid="stFileUploader"] {
            padding: 3rem;
            border: 3px dashed #1e3a8a;
            border-radius: 12px;
            background-color: #f8fafc;
            min-height: 250px;
        }
        
        [data-testid="stFileUploader"] > div {
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        [data-testid="stFileUploader"] label {
            font-size: 1.2rem !important;
            font-weight: 500 !important;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Authentication functions
def signup_user(username, email, password):
    if not DB_AVAILABLE:
        return False, "Database not available"
    
    # Check if user already exists
    if auth_collection.find_one({'username': username}):
        return False, "Username already exists"
    
    if auth_collection.find_one({'email': email}):
        return False, "Email already registered"
    
    # Insert new user
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    auth_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password
    })
    return True, "Account created successfully"

def login_user(username, password):
    if not DB_AVAILABLE:
        return False, "Database not available"
    
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    user = auth_collection.find_one({'username': username, 'password': hashed_password})
    
    if user:
        return True, "Login successful"
    return False, "Invalid credentials"

def render_navbar(username):
    st.markdown(f"""
    <div class="navbar">
        <div class="navbar-brand">skilledge</div>
        <div class="navbar-menu">
            <span style="color: white;">Welcome, {username}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = 'dashboard'
            st.rerun()
    with col2:
        if st.button("About", use_container_width=True):
            st.session_state.page = 'about'
            st.rerun()
    with col3:
        if st.button("Feedback", use_container_width=True):
            st.session_state.page = 'feedback'
            st.rerun()
    with col4:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = 'login'
            st.rerun()

###### Main function run() ######

def run():
    load_css()
    
    # Check if user is logged in
    if not st.session_state.logged_in:
        # Show login/signup page
        if st.session_state.page == 'login':
            show_login_page()
        elif st.session_state.page == 'signup':
            show_signup_page()
    else:
        # Show main application with navbar
        render_navbar(st.session_state.username)
        
        if st.session_state.page == 'dashboard':
            show_dashboard()
        elif st.session_state.page == 'about':
            show_about()
        elif st.session_state.page == 'feedback':
            show_feedback()

def show_login_page():
    st.markdown("<h1 style='text-align: center;'>skilledge</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Login to Your Account</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login", use_container_width=True):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.page = 'dashboard'
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please fill in all fields")
        
        with col_b:
            if st.button("Create Account", use_container_width=True):
                st.session_state.page = 'signup'
                st.rerun()

def show_signup_page():
    st.markdown("<h1 style='text-align: center;'>skilledge</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create New Account</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Sign Up", use_container_width=True):
                if username and email and password and confirm_password:
                    if password == confirm_password:
                        success, message = signup_user(username, email, password)
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.session_state.page = 'login'
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.warning("Please fill in all fields")
        
        with col_b:
            if st.button("Back to Login", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()

def show_dashboard():
        
        # Collecting Miscellaneous Information (automatically)
        # Removed manual input fields - using system info only
        act_name = st.session_state.username  # Use logged in username
        act_mail = 'user@example.com'  # Placeholder
        act_mob  = 'N/A'  # Placeholder
        sec_token = secrets.token_urlsafe(12)
        host_name = socket.gethostname()
        ip_add = socket.gethostbyname(host_name)
        dev_user = os.getlogin()
        os_name_ver = platform.system() + " " + platform.release()
        g = geocoder.ip('me')
        latlong = g.latlng
        geolocator = Nominatim(user_agent="http")
        location = geolocator.reverse(latlong, language='en')
        address = location.raw['address']
        cityy = address.get('city', '')
        statee = address.get('state', '')
        countryy = address.get('country', '')  
        city = cityy
        state = statee
        country = countryy


        # Upload Resume - Larger upload area
        st.markdown('''<h2 style='text-align: center; color: #021659; margin-bottom: 30px;'>Upload Your Resume</h2>''',unsafe_allow_html=True)
        st.markdown('''<h4 style='text-align: center; color: #555;'>Get Smart Recommendations and Insights</h4>''',unsafe_allow_html=True)
        
        # Create centered columns for better layout
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            ## file upload in pdf format with larger area
            pdf_file = st.file_uploader("", type=["pdf"], help="Upload your resume in PDF format", label_visibility="collapsed")
        if pdf_file is not None:
            with st.spinner('Hang On While We Cook Magic For You...'):
                time.sleep(4)
        
            ### saving the uploaded resume to folder
            save_image_path = './Uploaded_Resumes/'+pdf_file.name
            pdf_name = pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
                f.flush()  # Ensure file is written to disk
                os.fsync(f.fileno())  # Force write to disk
            
            # Verify file was saved correctly
            if not os.path.exists(save_image_path):
                st.error("Error: Failed to save the uploaded file.")
                return
            
            show_pdf(save_image_path)

            ### parsing and extracting whole resume 
            try:
                resume_data = ResumeParser(save_image_path).get_extracted_data()
                # Debug: Print extracted data
                print("DEBUG - Extracted resume data:", resume_data)
            except Exception as e:
                st.error(f"Error parsing resume: {str(e)}")
                st.warning("Please make sure you uploaded a valid PDF file.")
                import traceback
                print("ERROR:", traceback.format_exc())
                return
                
            if resume_data:
                
                ## Get the whole resume data into resume_text
                resume_text = pdf_reader(save_image_path)
                print("DEBUG - Resume text length:", len(resume_text) if resume_text else 0)

                ## Showing Analyzed data from (resume_data)
                st.header("**Resume Analysis **")
                
                # Get name with fallback
                candidate_name = resume_data.get('name') or 'Candidate'
                st.success("Hello "+ candidate_name)
                
                st.subheader("**Your Basic info **")
                
                # Check if any data was extracted
                has_data = any([
                    resume_data.get('name'),
                    resume_data.get('email'),
                    resume_data.get('mobile_number'),
                    resume_data.get('skills'),
                    resume_data.get('no_of_pages')
                ])
                
                if not has_data:
                    st.warning("⚠️ Unable to extract information from your resume. This could be because:")
                    st.markdown("""
                    - The PDF is scanned/image-based (not text-based)
                    - The PDF has unusual formatting
                    - The text is in a non-standard encoding
                    
                    **Suggestion:** Try converting your resume to a text-based PDF or use a different PDF version.
                    """)
                
                try:
                    st.text('Name: '+ (resume_data.get('name') or 'Not found'))
                    st.text('Email: ' + (resume_data.get('email') or 'Not found'))
                    st.text('Contact: ' + (resume_data.get('mobile_number') or 'Not found'))
                    st.text('Degree: '+ (str(resume_data.get('degree')) if resume_data.get('degree') else 'Not found'))                    
                    st.text('Resume pages: '+str(resume_data.get('no_of_pages') or 0))

                except:
                    pass
                ## Predicting Candidate Experience Level 

                ### Trying with different possibilities
                cand_level = ''
                no_of_pages = resume_data.get('no_of_pages') or 0
                resume_text = resume_text or ""  # Ensure resume_text is not None
                if no_of_pages < 1:                
                    cand_level = "NA"
                    st.markdown( '''<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>''',unsafe_allow_html=True)
                
                #### if internship then intermediate level
                elif 'INTERNSHIP' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIPS' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internship' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                elif 'Internships' in resume_text:
                    cand_level = "Intermediate"
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>''',unsafe_allow_html=True)
                
                #### if Work Experience/Experience then Experience level
                elif 'EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'WORK EXPERIENCE' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                elif 'Work Experience' in resume_text:
                    cand_level = "Experienced"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at experience level!''',unsafe_allow_html=True)
                else:
                    cand_level = "Fresher"
                    st.markdown('''<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!''',unsafe_allow_html=True)


                ## Skills Analyzing and Recommendation
                st.subheader("**Skills Recommendation **")
                
                ### Current Analyzed Skills
                current_skills = resume_data.get('skills') or []
                keywords = st_tags(label='### Your Current Skills',
                text='See our skills recommendation below',value=current_skills,key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in current_skills:
                
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','Pytorch','Probability','Scikit-learn','Tensorflow',"Flask",'Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node JS','React JS','php','laravel','Magento','wordpress','Javascript','Angular JS','c#','Flask','SDK']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Android development','Flutter','Kotlin','XML','Java','Kivy','GIT','SDK','SQLite']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['IOS','IOS Development','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','Plist','StoreKit',"UI-Kit",'AV Foundation','Auto-Layout']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI','User Experience','Adobe XD','Figma','Zeplin','Balsamiq','Prototyping','Wireframes','Storyframes','Adobe Photoshop','Editing','Illustrator','After Effects','Premier Pro','Indesign','Wireframe','Solid','Grasp','User Research']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool only predicts and recommends for Data Science, Web, Android, IOS and UI/UX Development**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break


                ## Resume Scorer & Resume Writing Tips
                st.subheader("**Resume Tips & Ideas **")
                resume_score = 0
                
                ### Predicting Whether these key points are added to the resume
                if 'Objective' or 'Summary' in resume_text:
                    resume_score = resume_score+6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>''',unsafe_allow_html=True)                
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)

                if 'Education' or 'School' or 'College'  in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>''',unsafe_allow_html=True)

                if 'EXPERIENCE' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                elif 'Experience' in resume_text:
                    resume_score = resume_score + 16
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'INTERNSHIPS'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'INTERNSHIP'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internships'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                elif 'Internship'  in resume_text:
                    resume_score = resume_score + 6
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>''',unsafe_allow_html=True)

                if 'SKILLS'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'SKILL'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skills'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                elif 'Skill'  in resume_text:
                    resume_score = resume_score + 7
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Skills. It will help you a lot</h4>''',unsafe_allow_html=True)

                if 'HOBBIES' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                elif 'Hobbies' in resume_text:
                    resume_score = resume_score + 4
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)

                if 'INTERESTS'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                elif 'Interests'in resume_text:
                    resume_score = resume_score + 5
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Interest. It will show your interest other that job.</h4>''',unsafe_allow_html=True)

                if 'ACHIEVEMENTS' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                elif 'Achievements' in resume_text:
                    resume_score = resume_score + 13
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)

                if 'CERTIFICATIONS' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certifications' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                elif 'Certification' in resume_text:
                    resume_score = resume_score + 12
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>''',unsafe_allow_html=True)

                if 'PROJECTS' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'PROJECT' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Projects' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                elif 'Project' in resume_text:
                    resume_score = resume_score + 19
                    st.markdown('''<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h5 style='text-align: left; color: #ff0000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)

                st.subheader("**Resume Score **")
                
                st.markdown(
                    """
                    <style>
                        .stProgress > div > div > div > div {
                            background-color: #d73b5c;
                        }
                    </style>""",
                    unsafe_allow_html=True,
                )

                ### Score Bar
                my_bar = st.progress(0)
                score = 0
                for percent_complete in range(resume_score):
                    score +=1
                    time.sleep(0.1)
                    my_bar.progress(percent_complete + 1)

                ### Score
                st.success('** Your Resume Writing Score: ' + str(score)+'**')
                st.warning("** Note: This score is calculated based on the content that you have in your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)


                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data.get('name') or 'Unknown', resume_data.get('email') or 'Unknown', str(resume_score), timestamp, str(resume_data.get('no_of_pages') or 0), reco_field, cand_level, str(current_skills), str(recommended_skills), str(rec_course), pdf_name)

                ## Recommending Resume Writing Video
                st.header("**Bonus Video for Resume Writing Tips**")
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## Recommending Interview Preparation Video
                st.header("**Bonus Video for Interview Tips**")
                interview_vid = random.choice(interview_videos)
                st.video(interview_vid)

                ## On Successful Result 
                st.balloons()

            else:
                st.error('Something went wrong..')

def show_feedback():   
        
        # timestamp 
        ts = time.time()
        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
        timestamp = str(cur_date+'_'+cur_time)

        # Feedback Form
        with st.form("my_form"):
            st.write("Feedback form")            
            feed_name = st.text_input('Name')
            feed_email = st.text_input('Email')
            feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
            comments = st.text_input('Comments')
            Timestamp = timestamp        
            submitted = st.form_submit_button("Submit")
            if submitted:
                ## Calling insertf_data to add dat into user feedback
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                ## Success Message 
                st.success("Thanks! Your Feedback was recorded.") 
                ## On Successful Submit
                st.balloons()    

        # Fetch feedback data from MongoDB
        if DB_AVAILABLE:
            # fetching feed_score and getting the unique values and total value count 
            feedback_data = list(feedback_collection.find({}))
            if feedback_data:
                plotfeed_data = pd.DataFrame(feedback_data)
                
                if 'feed_score' in plotfeed_data.columns:
                    labels = plotfeed_data.feed_score.unique()
                    values = plotfeed_data.feed_score.value_counts()

                    # plotting pie chart for user ratings
                    st.subheader("**Past User Rating's**")
                    fig = px.pie(values=values, names=labels, title="Chart of User Rating Score From 1 - 5", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                    st.plotly_chart(fig)
            else:
                st.info("No feedback data yet.")
        else:
            st.warning("Database not available.")


        #  Fetching Comment History
        if DB_AVAILABLE:
            plfeed_cmt_data = list(feedback_collection.find({}, {'feed_name': 1, 'comments': 1, '_id': 0}))
            st.subheader("**User Comment's**")
            if plfeed_cmt_data:
                dff = pd.DataFrame(plfeed_cmt_data, columns=['feed_name', 'comments'])
                dff.columns = ['User', 'Comment']
                st.dataframe(dff, width=1000)
            else:
                st.info("No feedback comments yet.")
        else:
            st.warning("Database not available. Cannot fetch comments.")

def show_feedback():
    st.header("**Feedback**")
    
    # timestamp 
    ts = time.time()
    cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    timestamp = str(cur_date+'_'+cur_time)

    # Feedback Form
    with st.form("my_form"):
        st.write("We value your feedback")            
        feed_name = st.text_input('Name')
        feed_email = st.text_input('Email')
        feed_score = st.slider('Rate Us From 1 - 5', 1, 5)
        comments = st.text_area('Comments')
        Timestamp = timestamp        
        submitted = st.form_submit_button("Submit")
        if submitted:
            if feed_name and feed_email:
                insertf_data(feed_name,feed_email,feed_score,comments,Timestamp)    
                st.success("Thanks! Your Feedback was recorded.") 
            else:
                st.warning("Please fill in all required fields")

    # Display feedback statistics
    if DB_AVAILABLE:
        st.subheader("**User Ratings**")
        feedback_data = list(feedback_collection.find({}))
        if feedback_data:
            feedback_df = pd.DataFrame(feedback_data)
            if 'feed_score' in feedback_df.columns:
                labels = feedback_df.feed_score.unique()
                values = feedback_df.feed_score.value_counts()
                fig = px.pie(values=values, names=labels, title="User Rating Distribution", color_discrete_sequence=px.colors.sequential.Aggrnyl)
                st.plotly_chart(fig)
            
            st.subheader("**User Comments**")
            if 'feed_name' in feedback_df.columns and 'comments' in feedback_df.columns:
                comment_df = feedback_df[['feed_name', 'comments']].copy()
                comment_df.columns = ['User', 'Comment']
                st.dataframe(comment_df, use_container_width=True)
        else:
            st.info("No feedback available yet.")
    else:
        st.warning("Database not available")

def show_about():
    st.header("**About skilledge**")
    
    st.markdown('''
    ### Overview
    
    skilledge is an intelligent tool that uses natural language processing to parse and analyze resumes. 
    The system identifies keywords, clusters them by sectors, and provides personalized recommendations to help 
    improve your resume and career prospects.
    
    ### Key Features
    
    - **Resume Parsing**: Automatically extracts information from PDF resumes
    - **Skill Analysis**: Identifies and categorizes your skills
    - **Career Recommendations**: Suggests relevant skills, courses, and career paths
    - **Resume Scoring**: Provides an objective score based on content quality
    - **Analytics Dashboard**: Comprehensive insights into your resume
    
    ### How to Use
    
    1. **Login/Signup**: Create an account or login to access the platform
    2. **Upload Resume**: Upload your resume in PDF format on the dashboard
    3. **Get Analysis**: Receive instant analysis with personalized recommendations
    4. **Improve**: Apply the suggestions to enhance your resume
    5. **Feedback**: Share your experience to help us improve
    
    ### Technology Stack
    
    - Natural Language Processing with spaCy
    - Machine Learning for skill categorization
    - MongoDB for data storage
    - Streamlit for the web interface
    
    ''', unsafe_allow_html=True)

# Calling the main (run()) function to make the whole process run
run()
