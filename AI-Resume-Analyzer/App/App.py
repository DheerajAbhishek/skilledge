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
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image
# pre stored data for prediction purposes
from Courses import ds_course,web_course,android_course,ios_course,uiux_course,cybersecurity_course,cloud_course,data_analyst_course,ml_ai_course,devops_course,resume_videos,interview_videos
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
    st.markdown('''
    <div style="margin: 36px 0 20px 0;">
        <h4 style="font-size: 1.125rem; font-weight: 600; color: #FFFFFF;">Recommended Courses</h4>
        <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.9375rem;">Curated learning resources to boost your skills</p>
    </div>
    ''', unsafe_allow_html=True)
    
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider('Number of recommendations', 1, 10, 5)
    random.shuffle(course_list)
    
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"""
        <a href="{c_link}" target="_blank" style="text-decoration: none; display: block; margin-bottom: 12px;">
            <div style="background: #1C1C1E; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 16px 20px; display: flex; align-items: center; justify-content: space-between; transition: all 0.2s cubic-bezier(0.25, 0.1, 0.25, 1);" onmouseover="this.style.transform='translateX(4px)'; this.style.boxShadow='0 0 20px rgba(10, 132, 255, 0.15)';" onmouseout="this.style.transform='none'; this.style.boxShadow='none';">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <span style="background: rgba(10, 132, 255, 0.2); color: #0A84FF; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.875rem;">{c}</span>
                    <span style="color: #FFFFFF !important; font-weight: 500; font-size: 0.9375rem;">{c_name}</span>
                </div>
                <span style="color: rgba(235, 235, 245, 0.6); font-size: 1.125rem;">&#8594;</span>
            </div>
        </a>
        """, unsafe_allow_html=True)
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
        print(" Using MongoDB URI from Streamlit secrets")
    except Exception as secret_err:
        print(f" Streamlit secrets not found: {secret_err}")
        pass
    
    # If not in secrets, try environment variable
    if not mongodb_uri:
        mongodb_uri = os.environ.get('MONGODB_URI')
        if mongodb_uri:
            print(" Using MongoDB URI from environment variable")
    
    # If still not found, use local MongoDB
    if not mongodb_uri:
        mongodb_uri = 'mongodb://localhost:27017/'
        print(" Using local MongoDB (localhost:27017)")
    
    print(f"Attempting to connect to: {mongodb_uri[:20]}...")
    
    # For MongoDB Atlas, we need special SSL handling
    if 'mongodb+srv' in mongodb_uri or 'mongodb.net' in mongodb_uri:
        print("Connecting to MongoDB Atlas...")
        import ssl
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
            retryWrites=True,
            w='majority',
            tls=True,
            tlsAllowInvalidCertificates=True  # Allow for development/testing
        )
    else:
        print("Connecting to local MongoDB...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    
    # Test connection with timeout
    print("Testing connection with ping...")
    client.admin.command('ping')
    
    db = client['skilledge_db']
    user_collection = db['user_data']
    feedback_collection = db['user_feedback']
    DB_AVAILABLE = True
    print(" MongoDB connected successfully!")
    print(f" Database: skilledge_db")
except Exception as e:
    print(f" MongoDB connection failed: {str(e)}")
    print(f" Error type: {type(e).__name__}")
    import traceback
    print(traceback.format_exc())
    print(" Running in demo mode without database. Data will not be saved.")
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


# Apple VisionOS-Inspired Design System CSS
def load_css():
    st.markdown("""
    <style>
        /* ============================================
           APPLE PRO DARK MODE - macOS Sequoia / VisionOS
           High Contrast Dark Theme
           ============================================ */
        
        /* Import Inter as SF Pro alternative */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* ============================================
           DESIGN TOKENS - Apple Dark Mode Colors
           ============================================ */
        :root {
            /* Background Hierarchy (Depth Levels) */
            --bg-level-0: #000000;           /* Base - Main page background */
            --bg-level-1: #1C1C1E;           /* Cards, Bento boxes, modals */
            --bg-level-2: #2C2C2E;           /* Inlays, inputs, nested elements */
            --bg-level-3: #3A3A3C;           /* Elevated elements */
            
            /* Text Colors */
            --text-primary: #FFFFFF;          /* Headlines, primary text */
            --text-body: #F2F2F7;            /* Body text (slightly off-white to reduce eye strain) */
            --text-secondary: rgba(235, 235, 245, 0.6);  /* Muted text, captions */
            --text-tertiary: rgba(235, 235, 245, 0.3);   /* Placeholder, disabled */
            
            /* Dark Mode System Colors (Desaturated for dark backgrounds) */
            --system-blue: #0A84FF;
            --system-green: #30D158;
            --system-indigo: #5E5CE6;
            --system-orange: #FF9F0A;
            --system-pink: #FF375F;
            --system-purple: #BF5AF2;
            --system-red: #FF453A;
            --system-teal: #64D2FF;
            --system-yellow: #FFD60A;
            --system-mint: #66D4CF;
            --system-cyan: #5AC8FA;
            --system-graphite: #8E8E93;
            
            /* Glass Materials - Dark Translucent */
            --glass-dark: rgba(28, 28, 30, 0.7);
            --glass-medium: rgba(44, 44, 46, 0.8);
            --glass-light: rgba(58, 58, 60, 0.6);
            
            /* Borders & Separators */
            --separator: rgba(255, 255, 255, 0.1);
            --separator-strong: rgba(255, 255, 255, 0.15);
            --border-focused: rgba(10, 132, 255, 0.5);
            
            /* Fills */
            --fill-primary: rgba(120, 120, 128, 0.36);
            --fill-secondary: rgba(120, 120, 128, 0.32);
            --fill-tertiary: rgba(118, 118, 128, 0.24);
            --fill-quaternary: rgba(116, 116, 128, 0.18);
            
            /* Radii - Squircle-like Continuous Curves */
            --radius-xs: 8px;
            --radius-sm: 12px;
            --radius-md: 18px;
            --radius-lg: 22px;
            --radius-xl: 28px;
            --radius-pill: 980px;
            
            /* Shadows - Diffused Glow for Dark Mode */
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.4);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.5);
            --shadow-lg: 0 10px 30px rgba(0, 0, 0, 0.5);
            --shadow-xl: 0 20px 50px rgba(0, 0, 0, 0.6);
            --glow-blue: 0 0 20px rgba(10, 132, 255, 0.3), 0 0 40px rgba(10, 132, 255, 0.1);
            --glow-active: 0 0 30px rgba(10, 132, 255, 0.4), 0 10px 30px rgba(0, 0, 0, 0.5);
            
            /* Transitions - Spring-loaded Feel */
            --spring-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
            --spring-smooth: cubic-bezier(0.25, 0.1, 0.25, 1);
            --duration-fast: 0.15s;
            --duration-normal: 0.2s;
            --duration-slow: 0.35s;
        }
        
        /* ============================================
           GLOBAL RESET & BASE STYLES
           ============================================ */
        * {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        .stApp {
            background: var(--bg-level-0) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif !important;
            color: var(--text-primary) !important;
        }
        
        /* GLOBAL FIX: Hide material icon text fallbacks like "arrow_right", "arrow_down" */
        [data-testid="stIconMaterial"] {
            font-size: 0 !important;
            width: 24px !important;
            height: 24px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        [data-testid="stIconMaterial"]::before {
            font-size: 1.25rem !important;
        }
        
        /* Hide Streamlit Branding */
        [data-testid="stSidebar"] { display: none !important; }
        #MainMenu, footer, header { visibility: hidden !important; height: 0 !important; }
        .stDeployButton { display: none !important; }
        [data-testid="stToolbar"] { display: none !important; }
        
        /* Main Container - Centered Content */
        .main .block-container {
            max-width: 1280px !important;
            padding: 48px 32px !important;
            margin: 0 auto !important;
        }
        
        /* ============================================
           TYPOGRAPHY - SF Pro Dynamic Type Scale
           ============================================ */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.022em !important;
            line-height: 1.15 !important;
        }
        
        /* Large Title */
        h1 {
            font-size: 2.75rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.028em !important;
        }
        
        /* Title 1 */
        h2 {
            font-size: 1.75rem !important;
            font-weight: 600 !important;
        }
        
        /* Title 2 */
        h3 {
            font-size: 1.375rem !important;
            font-weight: 600 !important;
        }
        
        /* Title 3 / Headline */
        h4 {
            font-size: 1.125rem !important;
            font-weight: 600 !important;
        }
        
        /* Body Text - Using slightly off-white for reduced eye strain */
        p, span, div, label, li {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif !important;
            color: var(--text-body);
            font-size: 1rem;
            line-height: 1.5;
        }
        
        /* Secondary/Tertiary Labels */
        .text-secondary { color: var(--text-secondary) !important; }
        .text-tertiary { color: var(--text-tertiary) !important; }
        
        /* Ensure all Streamlit text is properly colored for dark mode */
        .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stText"],
        .element-container p,
        .element-container span,
        .stTextInput label,
        .stSelectbox label,
        .stTextArea label {
            color: var(--text-primary) !important;
        }
        
        /* Fix list items and general text */
        ul, ol, li {
            color: var(--text-primary) !important;
        }
        
        /* Ensure form labels are visible */
        label {
            color: var(--text-primary) !important;
        }
        
        /* Fix any inherit color issues */
        .stApp {
            color: var(--text-primary);
        }
        
        /* ============================================
           NAVIGATION BAR - Dark Glass Material
           ============================================ */
        .navbar {
            background: var(--glass-dark);
            backdrop-filter: saturate(180%) blur(30px);
            -webkit-backdrop-filter: saturate(180%) blur(30px);
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 0 0 32px 0;
            border-radius: var(--radius-lg);
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-md);
            position: relative;
            z-index: 100;
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--system-blue) 0%, var(--system-purple) 50%, var(--system-pink) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.03em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .navbar-brand::before {
            content: "";
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, var(--system-blue) 0%, var(--system-purple) 50%, var(--system-pink) 100%);
            border-radius: var(--radius-sm);
            display: inline-block;
        }
        
        .navbar-nav {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        
        .navbar-nav-btn {
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 0.875rem;
            font-weight: 500;
            padding: 8px 16px;
            border-radius: var(--radius-pill);
            cursor: pointer;
            transition: all var(--duration-fast) var(--spring-smooth);
            font-family: 'Inter', -apple-system, sans-serif;
        }
        
        .navbar-nav-btn:hover {
            background: var(--fill-tertiary);
        }
        
        .navbar-nav-btn.active {
            background: var(--system-blue);
            color: white;
        }
        
        .navbar-user {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            background: var(--bg-level-2);
            padding: 8px 16px;
            border-radius: var(--radius-pill);
            transition: all var(--duration-fast) var(--spring-smooth);
        }
        
        .navbar-user:hover {
            background: var(--bg-level-3);
        }
        
        /* ============================================
           BUTTONS - Prominent & Secondary Styles
           ============================================ */
        /* Prominent Button - Solid Blue with White Text */
        .stButton > button {
            background: var(--system-blue) !important;
            color: var(--text-primary) !important;
            border: none !important;
            border-radius: var(--radius-pill) !important;
            padding: 12px 24px !important;
            font-size: 0.9375rem !important;
            font-weight: 500 !important;
            font-family: 'Inter', -apple-system, sans-serif !important;
            letter-spacing: -0.01em !important;
            transition: all var(--duration-fast) var(--spring-bounce) !important;
            box-shadow: 0 4px 14px rgba(10, 132, 255, 0.4) !important;
            position: relative;
            overflow: hidden;
        }
        
        .stButton > button::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 50%;
            background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 100%);
            border-radius: var(--radius-pill) var(--radius-pill) 0 0;
            pointer-events: none;
        }
        
        .stButton > button:hover {
            transform: scale(1.04) translateY(-1px) !important;
            box-shadow: var(--glow-blue) !important;
        }
        
        .stButton > button:active {
            transform: scale(0.97) !important;
            box-shadow: 0 2px 8px rgba(10, 132, 255, 0.3) !important;
        }
        
        /* Secondary Buttons - White text on Dark Gray */
        .stButton > button[kind="secondary"],
        [data-testid="baseButton-secondary"] {
            background: var(--bg-level-2) !important;
            color: var(--text-primary) !important;
            box-shadow: none !important;
            border: 1px solid var(--separator) !important;
        }
        
        .stButton > button[kind="secondary"]:hover,
        [data-testid="baseButton-secondary"]:hover {
            background: var(--bg-level-3) !important;
            transform: scale(1.02) !important;
        }
        
        [data-testid="baseButton-secondary"] {
            background: var(--bg-level-2) !important;
            color: var(--system-blue) !important;
            border: 1px solid var(--separator) !important;
            box-shadow: none !important;
        }
        
        [data-testid="baseButton-secondary"]:hover {
            background: var(--bg-level-3) !important;
            box-shadow: none !important;
        }
        
        /* ============================================
           BENTO BOX CARDS - Pro Dark Card Style
           ============================================ */
        .dashboard-card {
            background: var(--bg-level-1);
            border-radius: var(--radius-lg);
            padding: 24px;
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-lg);
            margin-bottom: 20px;
            transition: all var(--duration-normal) var(--spring-smooth);
            position: relative;
            overflow: hidden;
        }
        
        .dashboard-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
            opacity: 0.8;
        }
        
        .dashboard-card:hover {
            transform: scale(1.02);
            background: var(--bg-level-2);
            box-shadow: var(--glow-active);
            border-color: var(--border-focused);
        }
        
        /* Card Text Colors - White for dark mode */
        .dashboard-card h2, .dashboard-card h3, .dashboard-card h4,
        .dashboard-card p, .dashboard-card span, .dashboard-card li {
            color: var(--text-primary) !important;
        }
        
        /* Glass Card Variant - Dark Translucent */
        .glass-card {
            background: var(--glass-dark);
            backdrop-filter: saturate(180%) blur(30px);
            -webkit-backdrop-filter: saturate(180%) blur(30px);
            border: 1px solid var(--separator);
            border-radius: var(--radius-lg);
            padding: 24px;
            box-shadow: var(--shadow-md);
        }
        
        /* ============================================
           SCORE CARDS - Uniform Dark Grey Style
           ============================================ */
        .score-card {
            border-radius: var(--radius-lg);
            padding: 28px 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
            margin-bottom: 16px;
            background: var(--bg-level-2);
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-md);
            transition: all var(--duration-normal) var(--spring-bounce);
        }
        
        .score-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .score-card:hover {
            transform: scale(1.02) translateY(-2px);
            box-shadow: var(--glow-blue);
            border-color: rgba(10, 132, 255, 0.3);
        }
        
        /* All card variants now use the same dark style */
        .score-card.blue, 
        .score-card.green, 
        .score-card.orange, 
        .score-card.purple,
        .score-card.teal,
        .score-card.pink,
        .score-card.indigo { 
            background: var(--bg-level-2);
        }
        
        .score-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: white;
            margin: 8px 0;
            letter-spacing: -0.03em;
            text-shadow: 0 2px 12px rgba(0,0,0,0.15);
        }
        
        .score-label {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.92);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        
        /* ============================================
           JOB CARDS - Dark Mode Style
           ============================================ */
        .job-card {
            background: var(--bg-level-1);
            border-radius: var(--radius-lg);
            padding: 24px 28px;
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-lg);
            margin-bottom: 16px;
            transition: all var(--duration-normal) var(--spring-smooth);
            position: relative;
            padding-left: 40px;
        }
        
        .job-card::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, var(--system-blue) 0%, var(--system-cyan) 100%);
            border-radius: var(--radius-lg) 0 0 var(--radius-lg);
        }
        
        .job-card:hover {
            transform: translateX(4px) translateY(-2px);
            background: var(--bg-level-2);
            box-shadow: var(--glow-active);
            border-color: var(--border-focused);
        }
        
        .job-card h3 {
            color: var(--text-primary) !important;
            font-size: 1.125rem !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }
        
        .job-card p, .job-card span {
            color: var(--text-body) !important;
        }
        
        .job-platform-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 10px 18px;
            border-radius: var(--radius-pill);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.8125rem;
            margin: 4px;
            transition: all var(--duration-fast) var(--spring-bounce);
            background: var(--text-primary);
            color: var(--bg-level-0);
        }
        
        .job-platform-btn:hover {
            transform: scale(1.06) translateY(-1px);
            box-shadow: 0 4px 16px rgba(255, 255, 255, 0.2);
        }
        
        /* ============================================
           FILE UPLOADER - Dark Drop Zone
           ============================================ */
        [data-testid="stFileUploader"] {
            padding: 56px 32px;
            border: 2px dashed var(--separator-strong) !important;
            border-radius: var(--radius-xl);
            background: var(--bg-level-1) !important;
            min-height: 220px;
            transition: all var(--duration-normal) var(--spring-smooth);
            box-shadow: var(--shadow-md);
            position: relative;
        }
        
        [data-testid="stFileUploader"]::before {
            content: "";
            position: absolute;
            inset: -2px;
            border-radius: var(--radius-xl);
            padding: 2px;
            background: linear-gradient(135deg, var(--system-blue), var(--system-purple), var(--system-pink));
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0;
            transition: opacity var(--duration-normal) var(--spring-smooth);
            pointer-events: none;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: transparent !important;
            box-shadow: var(--glow-blue);
            transform: translateY(-2px);
        }
        
        [data-testid="stFileUploader"]:hover::before {
            opacity: 1;
        }
        
        [data-testid="stFileUploader"] > div {
            min-height: 160px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        
        [data-testid="stFileUploader"] label {
            font-size: 1.0625rem !important;
            font-weight: 500 !important;
            color: var(--text-primary) !important;
        }
        
        /* ============================================
           INPUT FIELDS - Dark Mode Inlay Style
           ============================================ */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: var(--bg-level-2) !important;
            border: 1px solid var(--separator) !important;
            border-radius: var(--radius-sm) !important;
            padding: 14px 18px !important;
            font-size: 1rem !important;
            font-family: 'Inter', -apple-system, sans-serif !important;
            transition: all var(--duration-fast) var(--spring-smooth) !important;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3) !important;
            color: var(--text-primary) !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: var(--system-blue) !important;
            box-shadow: 0 0 0 4px rgba(10, 132, 255, 0.2), inset 0 1px 3px rgba(0, 0, 0, 0.3) !important;
            outline: none !important;
        }
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: var(--text-tertiary) !important;
            opacity: 1 !important;
        }
        
        /* Password & All Input Text */
        input, textarea, select {
            color: var(--text-primary) !important;
            background: var(--bg-level-2) !important;
        }
        
        /* Labels */
        .stSelectbox label, .stTextInput label, 
        .stTextArea label, .stSlider label,
        .stFileUploader label {
            color: var(--text-primary) !important;
            font-weight: 500 !important;
            font-size: 0.9375rem !important;
        }
        
        /* ============================================
           PROGRESS BAR - Rounded Apple Style
           ============================================ */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--system-blue) 0%, var(--system-cyan) 100%) !important;
            border-radius: var(--radius-pill) !important;
        }
        
        .stProgress > div > div {
            background: var(--bg-level-2) !important;
            border-radius: var(--radius-pill) !important;
            height: 8px !important;
        }
        
        /* ============================================
           EXPANDERS - Dark Accordion Style
           ============================================ */
        .streamlit-expanderHeader {
            background: var(--bg-level-1) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--separator) !important;
            font-weight: 500 !important;
            font-size: 0.9375rem !important;
            padding: 16px 20px !important;
            box-shadow: var(--shadow-sm) !important;
            color: var(--text-primary) !important;
            transition: all var(--duration-fast) var(--spring-smooth) !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: var(--bg-level-2) !important;
            border-color: var(--border-focused) !important;
        }
        
        .streamlit-expanderHeader p,
        .streamlit-expanderHeader span,
        .streamlit-expanderHeader div {
            color: var(--text-primary) !important;
        }
        
        /* Fix expander arrow icons - hide text fallbacks */
        [data-testid="stExpander"] details summary svg {
            stroke: var(--text-primary) !important;
            width: 20px !important;
            height: 20px !important;
        }
        
        [data-testid="stExpander"] summary span[data-testid="stMarkdownContainer"] {
            color: var(--text-primary) !important;
        }
        
        /* Hide arrow_right and arrow_down text fallbacks */
        [data-testid="stExpander"] summary [data-testid="stIconMaterial"],
        [data-testid="stExpander"] summary span:has(> [data-icon]) {
            font-size: 0 !important;
        }
        
        /* Hide the literal text "arrow_right" and "arrow_down" */
        [data-testid="stExpander"] details > summary > span:first-child {
            font-size: 0 !important;
            display: inline-flex !important;
            align-items: center !important;
        }
        
        /* Show proper arrow using ::before pseudo-element */
        [data-testid="stExpander"] details > summary > span:first-child::before {
            content: "\\25B6" !important;
            font-size: 0.75rem !important;
            color: var(--text-secondary) !important;
            margin-right: 8px !important;
            transition: transform 0.2s ease !important;
        }
        
        [data-testid="stExpander"] details[open] > summary > span:first-child::before {
            content: "\\25BC" !important;
        }
        
        /* Alternative: Hide any span containing arrow text */
        [data-testid="stExpander"] summary span[style*="material"] {
            visibility: hidden !important;
            width: 0 !important;
            overflow: hidden !important;
        }
        
        /* Hide text arrows and show proper icons */
        [data-testid="stExpander"] summary {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }
        
        [data-testid="stExpander"] summary::marker,
        [data-testid="stExpander"] summary::-webkit-details-marker {
            display: none !important;
        }
        
        .streamlit-expanderContent {
            background: var(--bg-level-1) !important;
            border: 1px solid var(--separator) !important;
            border-top: none !important;
            border-radius: 0 0 var(--radius-sm) var(--radius-sm) !important;
            padding: 20px !important;
        }
        
        .streamlit-expanderContent p,
        .streamlit-expanderContent span,
        .streamlit-expanderContent li {
            color: var(--text-body) !important;
        }
        
        /* ============================================
           METRICS - Large Display Numbers
           ============================================ */
        [data-testid="stMetricValue"] {
            font-size: 2.25rem !important;
            font-weight: 700 !important;
            color: var(--text-primary) !important;
            letter-spacing: -0.03em !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8125rem !important;
            color: var(--text-secondary) !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }
        
        /* ============================================
           SLIDER - Smooth Track Style
           ============================================ */
        .stSlider > div > div > div > div {
            background: var(--system-blue) !important;
        }
        
        .stSlider > div > div > div {
            background: var(--bg-level-2) !important;
        }
        
        /* ============================================
           ALERTS & NOTIFICATIONS - Dark Mode
           ============================================ */
        .stSuccess, .stInfo, .stWarning, .stError {
            border-radius: var(--radius-sm) !important;
            border: none !important;
            padding: 16px 20px !important;
            backdrop-filter: blur(8px) !important;
        }
        
        .stSuccess {
            background: rgba(48, 209, 88, 0.15) !important;
            border-left: 4px solid var(--system-green) !important;
        }
        
        .stSuccess p, .stSuccess span {
            color: var(--system-green) !important;
        }
        
        .stInfo {
            background: rgba(10, 132, 255, 0.15) !important;
            border-left: 4px solid var(--system-blue) !important;
        }
        
        .stInfo p, .stInfo span {
            color: var(--system-blue) !important;
        }
        
        .stWarning {
            background: rgba(255, 159, 10, 0.15) !important;
            border-left: 4px solid var(--system-orange) !important;
        }
        
        .stWarning p, .stWarning span {
            color: var(--system-orange) !important;
        }
        
        .stError {
            background: rgba(255, 69, 58, 0.15) !important;
            border-left: 4px solid var(--system-red) !important;
        }
        
        .stError p, .stError span {
            color: var(--system-red) !important;
        }
        
        /* ============================================
           SKILL TAGS - Vibrant Pills (Dark Mode)
           ============================================ */
        .skill-tag {
            display: inline-flex;
            align-items: center;
            background: rgba(10, 132, 255, 0.2);
            color: var(--system-blue);
            padding: 8px 16px;
            border-radius: var(--radius-pill);
            margin: 4px;
            font-size: 0.8125rem;
            font-weight: 500;
            transition: all var(--duration-fast) var(--spring-bounce);
        }
        
        .skill-tag:hover {
            background: rgba(10, 132, 255, 0.3);
            transform: scale(1.05);
        }
        
        .skill-tag-success {
            background: rgba(48, 209, 88, 0.2);
            color: var(--system-green);
        }
        
        .skill-tag-warning {
            background: rgba(255, 159, 10, 0.2);
            color: var(--system-orange);
        }
        
        .skill-tag-hot {
            background: rgba(255, 55, 95, 0.2);
            color: var(--system-pink);
        }
        
        /* ============================================
           HERO SECTION - Cinematic Welcome
           ============================================ */
        .hero-section {
            text-align: center;
            padding: 100px 24px 60px;
            max-width: 720px;
            margin: 0 auto;
        }
        
        .hero-title {
            font-size: 5rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.05em;
            line-height: 1.05;
            margin-bottom: 20px;
        }
        
        .hero-subtitle {
            font-size: 1.5rem;
            font-weight: 400;
            color: var(--text-secondary);
            margin-bottom: 48px;
            line-height: 1.5;
        }
        
        .hero-gradient {
            background: linear-gradient(135deg, var(--system-blue) 0%, var(--system-purple) 50%, var(--system-pink) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* ============================================
           LOGIN/SIGNUP CARDS - Dark Elevated Form
           ============================================ */
        .login-card {
            background: var(--bg-level-1);
            border-radius: var(--radius-xl);
            padding: 48px;
            box-shadow: var(--shadow-xl);
            max-width: 420px;
            margin: 0 auto;
            border: 1px solid var(--separator);
        }
        
        .login-card h2 {
            font-size: 1.625rem !important;
            text-align: center;
            margin-bottom: 8px !important;
            color: var(--text-primary) !important;
        }
        
        .login-subtitle {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9375rem;
            margin-bottom: 36px;
        }
        
        /* ============================================
           SECTION HEADERS - Apple Style
           ============================================ */
        .section-title {
            font-size: 1.875rem;
            font-weight: 600;
            color: var(--text-primary);
            letter-spacing: -0.025em;
            margin-bottom: 8px;
        }
        
        .section-subtitle {
            font-size: 1.0625rem;
            color: var(--text-secondary);
            font-weight: 400;
            margin-bottom: 32px;
        }
        
        /* ============================================
           BENTO GRID LAYOUT
           ============================================ */
        .bento-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .bento-item {
            background: var(--bg-level-1);
            border-radius: var(--radius-lg);
            padding: 24px;
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-md);
            transition: all var(--duration-normal) var(--spring-smooth);
        }
        
        .bento-item:hover {
            transform: translateY(-4px);
            box-shadow: var(--glow-active);
            background: var(--bg-level-2);
        }
        
        .bento-item.large {
            grid-column: span 2;
        }
        
        /* ============================================
           TRENDING BADGE - Animated
           ============================================ */
        .trending-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, var(--system-pink) 0%, #FF6B8A 100%);
            color: white;
            padding: 6px 14px;
            border-radius: var(--radius-pill);
            font-size: 0.6875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            animation: pulse-glow 2.5s ease-in-out infinite;
        }
        
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 0 0 rgba(255, 55, 95, 0.5); }
            50% { box-shadow: 0 0 0 10px rgba(255, 55, 95, 0); }
        }
        
        /* ============================================
           DATA TABLES - Dark Design
           ============================================ */
        .stDataFrame {
            border-radius: var(--radius-md) !important;
            overflow: hidden !important;
            box-shadow: var(--shadow-md) !important;
        }
        
        [data-testid="stDataFrame"] > div {
            background: var(--bg-level-1) !important;
        }
        
        /* ============================================
           CHARTS - Container Styling
           ============================================ */
        .chart-container {
            background: var(--bg-level-1);
            border-radius: var(--radius-lg);
            padding: 24px;
            border: 1px solid var(--separator);
            box-shadow: var(--shadow-md);
        }
        
        /* ============================================
           PDF VIEWER & MEDIA
           ============================================ */
        iframe {
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-xl) !important;
        }
        
        .stVideo > div {
            border-radius: var(--radius-lg) !important;
            overflow: hidden !important;
            box-shadow: var(--shadow-lg) !important;
        }
        
        /* ============================================
           RESPONSIVE BREAKPOINTS
           ============================================ */
        
        /* Extra Large Screens (1400px+) */
        @media (min-width: 1400px) {
            .main .block-container {
                max-width: 1400px !important;
                padding: 48px 60px !important;
            }
            .hero-title { font-size: 5.5rem; }
            .bento-grid { gap: 24px; }
        }
        
        /* Large Screens / Laptops (1200px - 1399px) */
        @media (max-width: 1399px) and (min-width: 1200px) {
            .main .block-container {
                padding: 40px 48px !important;
            }
            .hero-title { font-size: 4.5rem; }
            .hero-section { padding: 80px 24px 50px; }
        }
        
        /* Medium Screens / Tablets Landscape (992px - 1199px) */
        @media (max-width: 1199px) and (min-width: 992px) {
            .main .block-container {
                padding: 36px 32px !important;
            }
            .hero-title { font-size: 3.75rem; }
            .hero-subtitle { font-size: 1.375rem; }
            .hero-section { padding: 70px 20px 45px; }
            .login-card { padding: 40px 36px; }
            .dashboard-card { padding: 24px; }
            .bento-grid { 
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 18px;
            }
        }
        
        /* Tablets Portrait (768px - 991px) */
        @media (max-width: 991px) and (min-width: 768px) {
            :root {
                --radius-lg: 22px;
                --radius-xl: 26px;
            }
            
            .main .block-container {
                padding: 32px 24px !important;
            }
            .hero-title { font-size: 3rem; }
            .hero-subtitle { font-size: 1.25rem; }
            .hero-section { padding: 60px 16px 40px; max-width: 100%; }
            .navbar { padding: 14px 24px; }
            .login-card { padding: 36px 28px; max-width: 380px; }
            .dashboard-card { padding: 22px; }
            .score-card { padding: 28px 20px; }
            .score-value { font-size: 2.25rem; }
            .bento-grid { 
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 16px;
            }
            .section-title { font-size: 1.625rem; }
            .section-subtitle { font-size: 1rem; }
        }
        
        /* Mobile Landscape / Large Phones (576px - 767px) */
        @media (max-width: 767px) and (min-width: 576px) {
            :root {
                --radius-lg: 18px;
                --radius-xl: 22px;
            }
            
            .main .block-container {
                padding: 24px 20px !important;
            }
            .hero-title { font-size: 2.5rem; }
            .hero-subtitle { font-size: 1.125rem; }
            .hero-section { padding: 50px 16px 35px; max-width: 100%; }
            .navbar { padding: 12px 20px; }
            .navbar-brand { font-size: 1.25rem !important; }
            .login-card { padding: 32px 24px; max-width: 100%; margin: 0 16px; }
            .dashboard-card { padding: 20px; }
            .score-card { padding: 24px 16px; }
            .score-value { font-size: 2rem; }
            .bento-grid { 
                grid-template-columns: 1fr;
                gap: 14px;
            }
            .section-title { font-size: 1.5rem; }
            .section-subtitle { font-size: 0.9375rem; margin-bottom: 24px; }
            .skill-tag { padding: 6px 12px; font-size: 0.75rem; }
        }
        
        /* Mobile Portrait (up to 575px) */
        @media (max-width: 575px) {
            :root {
                --radius-lg: 16px;
                --radius-xl: 20px;
            }
            
            .main .block-container {
                padding: 16px 12px !important;
            }
            .hero-title { font-size: 2rem; letter-spacing: -0.03em; }
            .hero-subtitle { font-size: 1rem; margin-bottom: 32px; }
            .hero-section { padding: 40px 12px 30px; max-width: 100%; }
            .navbar { padding: 10px 16px; flex-wrap: wrap; gap: 8px; }
            .navbar-brand { font-size: 1.125rem !important; }
            .navbar-user { font-size: 0.875rem !important; }
            .login-card { 
                padding: 28px 20px; 
                max-width: 100%; 
                margin: 0 12px; 
                border-radius: var(--radius-lg);
            }
            .login-card h2 { font-size: 1.375rem !important; }
            .dashboard-card { padding: 16px; border-radius: var(--radius-lg); }
            .score-card { padding: 20px 14px; }
            .score-value { font-size: 1.75rem; }
            .bento-grid { 
                grid-template-columns: 1fr;
                gap: 12px;
            }
            .section-title { font-size: 1.375rem; }
            .section-subtitle { font-size: 0.875rem; margin-bottom: 20px; }
            .skill-tag { 
                padding: 5px 10px; 
                font-size: 0.6875rem; 
                margin: 2px;
            }
            
            /* Fix overlapping elements on small screens */
            [data-testid="column"] {
                min-width: 100% !important;
            }
            
            /* Stack elements vertically */
            .stHorizontalBlock {
                flex-direction: column !important;
            }
            
            /* Reduce button padding */
            .stButton > button {
                padding: 10px 20px !important;
                font-size: 0.875rem !important;
            }
            
            /* Smaller input fields */
            .stTextInput input, .stTextArea textarea {
                font-size: 0.9375rem !important;
                padding: 12px !important;
            }
        }
        
        /* Extra Small Screens (up to 400px) */
        @media (max-width: 400px) {
            .main .block-container {
                padding: 12px 8px !important;
            }
            .hero-title { font-size: 1.75rem; }
            .hero-subtitle { font-size: 0.9375rem; }
            .hero-section { padding: 32px 8px 24px; }
            .login-card { padding: 24px 16px; margin: 0 8px; }
            .score-value { font-size: 1.5rem; }
            .dashboard-card { padding: 14px; }
            .section-title { font-size: 1.25rem; }
            
            /* Prevent horizontal scroll */
            body, html {
                overflow-x: hidden !important;
            }
            
            .main {
                overflow-x: hidden !important;
            }
        }
        
        /* Fix for Streamlit columns on all mobile */
        @media (max-width: 768px) {
            /* Force single column layout */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            
            /* Fix dataframe/table overflow */
            [data-testid="stDataFrame"] {
                overflow-x: auto !important;
            }
            
            /* Fix expander width */
            .streamlit-expanderHeader {
                font-size: 0.9375rem !important;
            }
            
            /* Adjust chart containers */
            [data-testid="stPlotlyChart"],
            [data-testid="stVegaLiteChart"] {
                width: 100% !important;
                overflow-x: auto !important;
            }
        }
        
        /* Prevent content overflow globally */
        .element-container, .stMarkdown {
            max-width: 100% !important;
            overflow-wrap: break-word !important;
            word-wrap: break-word !important;
        }
        
        img, video, iframe {
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* ============================================
           SCROLLBAR - Dark Minimal Style
           ============================================ */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-level-0);
        }
        
        ::-webkit-scrollbar-thumb {
            background: var(--bg-level-3);
            border-radius: var(--radius-pill);
            border: 3px solid var(--bg-level-0);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: var(--system-graphite);
        }
        
        /* ============================================
           TAGS INPUT WIDGET
           ============================================ */
        [data-baseweb="tag"] {
            background: rgba(10, 132, 255, 0.2) !important;
            color: var(--system-blue) !important;
            border-radius: var(--radius-pill) !important;
            border: none !important;
        }
        
        [data-baseweb="tag"] span {
            color: var(--system-blue) !important;
        }
        
        /* ============================================
           FORM CONTAINER
           ============================================ */
        .stForm {
            background: var(--bg-level-1) !important;
            border: 1px solid var(--separator) !important;
            border-radius: var(--radius-lg) !important;
            padding: 28px !important;
            box-shadow: var(--shadow-md) !important;
        }
        
        /* ============================================
           SELECT BOX STYLING
           ============================================ */
        .stSelectbox > div > div {
            background: var(--bg-level-2) !important;
            border: 1px solid var(--separator) !important;
            border-radius: var(--radius-sm) !important;
            color: var(--text-primary) !important;
        }
        
        .stSelectbox > div > div > div {
            color: var(--text-primary) !important;
        }
        
        /* ============================================
           ADDITIONAL TEXT FIXES
           ============================================ */
        [data-testid="stNotification"] p,
        [data-testid="stNotification"] span {
            color: inherit !important;
        }
        
        .row-widget.stSelectbox label,
        .row-widget.stTextInput label,
        .row-widget.stTextArea label,
        .row-widget.stSlider label,
        .row-widget.stFileUploader label {
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }
        
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"],
        [data-testid="stMetricDelta"] {
            color: var(--text-primary) !important;
        }
        
        /* ============================================
           MAIN CONTENT PADDING FIX
           ============================================ */
        .st-emotion-cache-zy6yx3 {
            padding-left: 2rem;
            padding-right: 3rem;
            padding: 27px;
        }
        
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
    # Get current page for active state
    current_page = st.session_state.get('page', 'dashboard')
    
    # Create columns for navigation using Streamlit buttons inside navbar area
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5, nav_col6 = st.columns([1.5, 1, 1, 1, 1, 1.5])
    
    with nav_col1:
        st.markdown('<div class="navbar-brand">skilledge</div>', unsafe_allow_html=True)
    
    with nav_col2:
        if st.button("Dashboard", use_container_width=True, key="nav_dashboard", type="secondary" if current_page != 'dashboard' else "primary"):
            st.session_state.page = 'dashboard'
            st.rerun()
    
    with nav_col3:
        if st.button("About", use_container_width=True, key="nav_about", type="secondary" if current_page != 'about' else "primary"):
            st.session_state.page = 'about'
            st.rerun()
    
    with nav_col4:
        if st.button("Feedback", use_container_width=True, key="nav_feedback", type="secondary" if current_page != 'feedback' else "primary"):
            st.session_state.page = 'feedback'
            st.rerun()
    
    with nav_col5:
        if st.button("Sign Out", use_container_width=True, key="nav_logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = 'login'
            st.rerun()
    
    with nav_col6:
        st.markdown(f'<div class="navbar-user">{username}</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border: none; border-top: 1px solid var(--separator); margin: 16px 0 32px 0;'>", unsafe_allow_html=True)

###### AI-Powered Interview Questions Generator ######
def generate_interview_questions(field, level, skills):
    """Generate interview questions based on field and experience level"""
    
    questions_db = {
        'Data Science': [
            {'question': 'What is the difference between supervised and unsupervised learning?',
             'answer': 'Supervised learning uses labeled data to train models (e.g., classification, regression), while unsupervised learning finds patterns in unlabeled data (e.g., clustering, dimensionality reduction).',
             'tips': 'Give real-world examples like spam detection (supervised) vs customer segmentation (unsupervised).'},
            {'question': 'Explain the bias-variance tradeoff.',
             'answer': 'Bias is error from oversimplified models (underfitting). Variance is error from models too sensitive to training data (overfitting). The goal is to find the right balance for optimal generalization.',
             'tips': 'Mention techniques like cross-validation and regularization to manage this tradeoff.'},
            {'question': 'How do you handle missing data?',
             'answer': 'Options include: deletion (listwise/pairwise), imputation (mean/median/mode, KNN, regression), or using algorithms that handle missing values (XGBoost). Choice depends on data pattern and amount.',
             'tips': 'Discuss checking if data is MCAR, MAR, or MNAR before deciding approach.'},
            {'question': 'What is feature engineering and why is it important?',
             'answer': 'Feature engineering is creating new features from raw data to improve model performance. It includes normalization, encoding categoricals, creating interaction terms, and domain-specific transformations.',
             'tips': 'Share a specific example where feature engineering significantly improved your model.'},
            {'question': 'Explain cross-validation and its types.',
             'answer': 'Cross-validation assesses model generalization. K-Fold splits data into k parts, training on k-1 and testing on 1 iteratively. Other types: Stratified K-Fold, Leave-One-Out, Time Series Split.',
             'tips': 'Mention when to use which type based on dataset characteristics.'},
        ],
        'Web Development': [
            {'question': 'Explain the difference between REST and GraphQL.',
             'answer': 'REST uses multiple endpoints with fixed data structures. GraphQL uses a single endpoint where clients specify exact data needed, reducing over/under-fetching.',
             'tips': 'Discuss pros/cons: REST is simpler and cacheable; GraphQL is flexible but more complex.'},
            {'question': 'What is the Virtual DOM and how does it work?',
             'answer': 'Virtual DOM is an in-memory representation of the real DOM. When state changes, a new virtual DOM is created, diffed with the old one, and only necessary changes are applied to the real DOM.',
             'tips': 'Mention frameworks that use it (React) vs those that don\'t (Svelte compiles away).'},
            {'question': 'How do you optimize website performance?',
             'answer': 'Techniques include: minification, compression, lazy loading, CDN usage, caching, code splitting, image optimization, reducing HTTP requests, and using efficient algorithms.',
             'tips': 'Mention tools like Lighthouse, WebPageTest for measuring performance.'},
            {'question': 'Explain CORS and how to handle it.',
             'answer': 'CORS (Cross-Origin Resource Sharing) is a security feature blocking requests to different domains. Handle via server headers (Access-Control-Allow-Origin) or proxy in development.',
             'tips': 'Explain the preflight OPTIONS request for non-simple requests.'},
            {'question': 'What are Web Components?',
             'answer': 'Web Components are reusable custom elements using Custom Elements, Shadow DOM, and HTML Templates. They provide encapsulation and work across frameworks.',
             'tips': 'Compare with framework-specific components like React or Vue components.'},
        ],
        'Android Development': [
            {'question': 'Explain the Android Activity Lifecycle.',
             'answer': 'Activities go through: onCreate  onStart  onResume (running)  onPause  onStop  onDestroy. Understanding this helps manage resources and handle configuration changes.',
             'tips': 'Discuss saving state in onSaveInstanceState and restoring in onCreate.'},
            {'question': 'What is the difference between Service and IntentService?',
             'answer': 'Service runs on the main thread and handles multiple requests. IntentService runs on a worker thread, handles one request at a time, and stops itself when done.',
             'tips': 'Note that IntentService is deprecated; recommend WorkManager for background tasks.'},
            {'question': 'How does RecyclerView work?',
             'answer': 'RecyclerView efficiently displays large lists by recycling views. Key components: Adapter (binds data), ViewHolder (caches views), LayoutManager (positions items).',
             'tips': 'Discuss DiffUtil for efficient updates and view types for heterogeneous lists.'},
            {'question': 'Explain Kotlin Coroutines for Android.',
             'answer': 'Coroutines provide lightweight concurrency. Use viewModelScope/lifecycleScope for automatic cancellation. Dispatchers control threads: Main for UI, IO for network/disk.',
             'tips': 'Compare with RxJava and explain structured concurrency benefits.'},
            {'question': 'What is Jetpack Compose?',
             'answer': 'Compose is Android\'s modern declarative UI toolkit. Uses composable functions, state-driven rendering, and eliminates XML layouts for more maintainable code.',
             'tips': 'Discuss recomposition, remember, and state hoisting patterns.'},
        ],
        'IOS Development': [
            {'question': 'Explain the iOS App Lifecycle.',
             'answer': 'States: Not Running  Inactive  Active  Background  Suspended. AppDelegate/SceneDelegate methods handle transitions like applicationDidBecomeActive.',
             'tips': 'Discuss differences between AppDelegate and SceneDelegate (iOS 13+).'},
            {'question': 'What is ARC in Swift?',
             'answer': 'ARC (Automatic Reference Counting) manages memory by tracking strong references. Objects are deallocated when reference count reaches zero. Use weak/unowned to prevent retain cycles.',
             'tips': 'Give examples of retain cycles in closures and delegates.'},
            {'question': 'Explain the difference between struct and class in Swift.',
             'answer': 'Structs are value types (copied on assignment), classes are reference types (shared). Structs are preferred for immutable data; classes for shared mutable state or inheritance.',
             'tips': 'Discuss when Apple recommends each and performance implications.'},
            {'question': 'What is SwiftUI and how does it differ from UIKit?',
             'answer': 'SwiftUI is declarative (describe what you want), UIKit is imperative (describe how to build). SwiftUI uses state-driven updates and works across Apple platforms.',
             'tips': 'Discuss interoperability with UIViewRepresentable.'},
            {'question': 'How do you handle concurrency in Swift?',
             'answer': 'Options: GCD (DispatchQueue), OperationQueue, or async/await (Swift 5.5+). Async/await provides cleaner syntax with actors for thread-safe state.',
             'tips': 'Explain MainActor for UI updates and Sendable protocol.'},
        ],
        'UI-UX Development': [
            {'question': 'What is the difference between UX and UI design?',
             'answer': 'UX focuses on overall user experience (research, flows, usability). UI focuses on visual design (colors, typography, components). Both work together for great products.',
             'tips': 'Give examples: UX decides a checkout needs 3 steps; UI designs how each step looks.'},
            {'question': 'Explain your design process.',
             'answer': 'Typical process: Research  Define  Ideate  Prototype  Test  Iterate. Each phase has specific deliverables like personas, user flows, wireframes, and usability reports.',
             'tips': 'Share a specific project example walking through your process.'},
            {'question': 'How do you conduct user research?',
             'answer': 'Methods include: interviews, surveys, usability testing, A/B testing, analytics review, card sorting, and contextual inquiry. Choice depends on goals, timeline, and resources.',
             'tips': 'Discuss both qualitative and quantitative research importance.'},
            {'question': 'What are design systems and why are they important?',
             'answer': 'Design systems are collections of reusable components, guidelines, and principles. They ensure consistency, speed up development, and improve collaboration between design and dev teams.',
             'tips': 'Reference examples like Material Design, Apple HIG, or your own work.'},
            {'question': 'How do you handle accessibility in design?',
             'answer': 'Follow WCAG guidelines: sufficient color contrast, keyboard navigation, screen reader support, clear focus states, alt text, and testing with assistive technologies.',
             'tips': 'Mention specific tools like axe, Lighthouse, or VoiceOver for testing.'},
        ],
        'Cyber Security': [
            {'question': 'What is the CIA Triad in cybersecurity?',
             'answer': 'CIA stands for Confidentiality (protecting data from unauthorized access), Integrity (ensuring data is accurate and unaltered), and Availability (ensuring systems are accessible when needed). These are the core principles of information security.',
             'tips': 'Give real-world examples like encryption for confidentiality, checksums for integrity, and DDoS protection for availability.'},
            {'question': 'Explain the difference between symmetric and asymmetric encryption.',
             'answer': 'Symmetric encryption uses the same key for encryption and decryption (AES, DES). Asymmetric uses a public-private key pair (RSA, ECC). Symmetric is faster but has key distribution challenges; asymmetric solves this but is slower.',
             'tips': 'Mention how HTTPS uses both: asymmetric for key exchange, symmetric for data transfer.'},
            {'question': 'What is a penetration test and how does it differ from vulnerability assessment?',
             'answer': 'Vulnerability assessment identifies and lists security weaknesses. Penetration testing goes further by actively exploiting vulnerabilities to assess real-world impact. Pen tests simulate actual attacks to test defenses.',
             'tips': 'Discuss methodologies like OWASP, PTES, and the importance of scope definition.'},
            {'question': 'How would you respond to a security incident?',
             'answer': 'Follow incident response phases: 1) Preparation, 2) Identification, 3) Containment, 4) Eradication, 5) Recovery, 6) Lessons Learned. Document everything and communicate with stakeholders appropriately.',
             'tips': 'Mention specific tools like SIEM, EDR, and the importance of having an incident response plan.'},
            {'question': 'What is the OWASP Top 10 and why is it important?',
             'answer': 'OWASP Top 10 is a list of the most critical web application security risks including injection, broken authentication, XSS, insecure deserialization, etc. It helps developers and security professionals prioritize security efforts.',
             'tips': 'Be prepared to explain mitigation strategies for each vulnerability type.'},
        ],
        'Cloud Computing': [
            {'question': 'What are the different types of cloud service models?',
             'answer': 'IaaS (Infrastructure as a Service) provides virtualized computing resources. PaaS (Platform as a Service) provides platform for developing applications. SaaS (Software as a Service) delivers software over the internet. Examples: AWS EC2 (IaaS), Heroku (PaaS), Salesforce (SaaS).',
             'tips': 'Explain the shared responsibility model and when to use each service type.'},
            {'question': 'Explain the difference between horizontal and vertical scaling.',
             'answer': 'Vertical scaling (scale up) adds more power to existing machines (CPU, RAM). Horizontal scaling (scale out) adds more machines to distribute load. Horizontal is preferred for cloud as it offers better fault tolerance and no upper limits.',
             'tips': 'Discuss auto-scaling groups and load balancers for horizontal scaling.'},
            {'question': 'What is Infrastructure as Code (IaC) and why is it important?',
             'answer': 'IaC manages infrastructure through code/configuration files instead of manual processes. Tools like Terraform, CloudFormation, and Pulumi enable version control, reproducibility, and automation of infrastructure deployment.',
             'tips': 'Mention benefits like consistency, disaster recovery, and CI/CD integration.'},
            {'question': 'How do you ensure high availability in cloud architecture?',
             'answer': 'Use multiple availability zones, load balancers, auto-scaling, database replication, CDN, health checks, and failover mechanisms. Design for failure with redundancy at every layer.',
             'tips': 'Discuss specific AWS/Azure/GCP services for HA like Route 53, ALB, Multi-AZ RDS.'},
            {'question': 'What is containerization and how does Kubernetes help?',
             'answer': 'Containers package applications with dependencies for consistent deployment. Kubernetes orchestrates containers providing auto-scaling, self-healing, load balancing, and declarative configuration for managing containerized workloads.',
             'tips': 'Explain pods, services, deployments, and the difference between Docker and Kubernetes.'},
        ],
        'Data Analyst': [
            {'question': 'What is the difference between data analytics and data science?',
             'answer': 'Data analytics focuses on analyzing historical data to find insights and trends using statistical methods and visualization. Data science involves building predictive models, machine learning, and creating algorithms for future predictions.',
             'tips': 'Emphasize that analysts answer "what happened" while scientists predict "what will happen".'},
            {'question': 'How do you handle missing data in a dataset?',
             'answer': 'Options include: deletion (if minimal), imputation (mean/median/mode), forward/backward fill for time series, using algorithms that handle nulls, or flagging as a separate category. Choice depends on data type and business context.',
             'tips': 'Always investigate WHY data is missing before choosing a method.'},
            {'question': 'Explain the difference between INNER JOIN and LEFT JOIN.',
             'answer': 'INNER JOIN returns only matching rows from both tables. LEFT JOIN returns all rows from the left table and matching rows from the right (NULL for non-matches). Understanding joins is crucial for combining data from multiple sources.',
             'tips': 'Draw Venn diagrams to illustrate and mention performance implications.'},
            {'question': 'How would you present complex data findings to non-technical stakeholders?',
             'answer': 'Use clear visualizations, avoid jargon, focus on business impact, tell a story with the data, use analogies, provide actionable recommendations, and prepare for questions with supporting details.',
             'tips': 'Mention specific tools like Tableau, Power BI, and the importance of knowing your audience.'},
            {'question': 'What is A/B testing and how would you design one?',
             'answer': 'A/B testing compares two versions to determine which performs better. Design includes: defining hypothesis, selecting metrics, determining sample size, ensuring random assignment, running for sufficient duration, and analyzing statistical significance.',
             'tips': 'Discuss p-values, confidence intervals, and common pitfalls like peeking at results early.'},
        ],
        'Machine Learning': [
            {'question': 'Explain the difference between supervised, unsupervised, and reinforcement learning.',
             'answer': 'Supervised uses labeled data for prediction (classification/regression). Unsupervised finds patterns in unlabeled data (clustering/dimensionality reduction). Reinforcement learning learns through trial and error with rewards/penalties.',
             'tips': 'Give examples: spam detection (supervised), customer segmentation (unsupervised), game AI (reinforcement).'},
            {'question': 'What is overfitting and how do you prevent it?',
             'answer': 'Overfitting occurs when a model learns noise in training data, performing poorly on new data. Prevention: cross-validation, regularization (L1/L2), early stopping, dropout, data augmentation, simpler models, more training data.',
             'tips': 'Explain the bias-variance tradeoff and how to detect overfitting using validation curves.'},
            {'question': 'Explain how a Random Forest algorithm works.',
             'answer': 'Random Forest is an ensemble of decision trees. It uses bagging (bootstrap aggregating) and random feature selection to build multiple trees, then aggregates predictions through voting (classification) or averaging (regression).',
             'tips': 'Discuss advantages: handles non-linearity, feature importance, resistant to overfitting.'},
            {'question': 'What is the difference between precision and recall?',
             'answer': 'Precision = TP/(TP+FP) measures accuracy of positive predictions. Recall = TP/(TP+FN) measures how many actual positives were found. Trade-off depends on use case: medical diagnosis needs high recall, spam filter needs high precision.',
             'tips': 'Explain F1-score as harmonic mean and when to use each metric.'},
            {'question': 'How do you deploy a machine learning model to production?',
             'answer': 'Steps include: model serialization (pickle/ONNX), creating API endpoints (Flask/FastAPI), containerization (Docker), cloud deployment (AWS SageMaker/GCP AI Platform), monitoring, versioning, and setting up retraining pipelines.',
             'tips': 'Discuss MLOps practices, model monitoring, and handling data drift.'},
        ],
        'DevOps': [
            {'question': 'What is CI/CD and why is it important?',
             'answer': 'CI (Continuous Integration) automatically builds and tests code changes. CD (Continuous Delivery/Deployment) automates release process. Benefits: faster releases, early bug detection, consistent deployments, reduced manual errors.',
             'tips': 'Mention tools like Jenkins, GitLab CI, GitHub Actions, and discuss pipeline stages.'},
            {'question': 'Explain the difference between Docker and Kubernetes.',
             'answer': 'Docker is a containerization platform for packaging applications. Kubernetes is an orchestration platform for managing containers at scale. Docker creates containers; Kubernetes manages, scales, and networks multiple containers across clusters.',
             'tips': 'Discuss when you need Kubernetes vs just Docker Compose.'},
            {'question': 'What is Infrastructure as Code and which tools have you used?',
             'answer': 'IaC manages infrastructure through code files enabling version control, reproducibility, and automation. Tools: Terraform (multi-cloud), CloudFormation (AWS), Ansible (configuration), Pulumi (programming languages).',
             'tips': 'Discuss declarative vs imperative approaches and state management.'},
            {'question': 'How do you monitor applications in production?',
             'answer': 'Use metrics (Prometheus), logging (ELK Stack), tracing (Jaeger), and alerting (PagerDuty). Monitor: application performance, infrastructure health, business metrics. Implement dashboards (Grafana) and set up meaningful alerts.',
             'tips': 'Discuss the four golden signals: latency, traffic, errors, saturation.'},
            {'question': 'Explain blue-green and canary deployment strategies.',
             'answer': 'Blue-green maintains two identical environments, switching traffic between them for zero-downtime deployments. Canary gradually routes traffic to new version (1%, 10%, 50%, 100%), allowing early detection of issues.',
             'tips': 'Discuss rollback strategies and when to use each approach.'},
        ]
    }
    
    # Get questions for the field or return general questions
    field_questions = questions_db.get(field, [
        {'question': 'Tell me about yourself and your background.',
         'answer': 'Structure: Present (current role/skills)  Past (relevant experience)  Future (career goals aligned with position). Keep it 2-3 minutes.',
         'tips': 'Tailor to the job; focus on relevant achievements.'},
        {'question': 'What are your greatest strengths?',
         'answer': 'Choose 2-3 strengths relevant to the role. Provide specific examples demonstrating each strength with measurable results.',
         'tips': 'Use the STAR method (Situation, Task, Action, Result).'},
        {'question': 'Where do you see yourself in 5 years?',
         'answer': 'Show ambition aligned with the company\'s growth. Express desire to develop skills, take on responsibilities, and contribute to team success.',
         'tips': 'Research company\'s career paths before answering.'},
    ])
    
    return field_questions[:5]


###### Smart Experience Level Detection ######
def detect_experience_level(resume_text, no_of_pages=1):
    """
    Intelligently detect candidate experience level based on multiple factors:
    - Years of experience mentioned
    - Date ranges in work history
    - Graduation year
    - Number of job positions
    - Keywords and patterns
    """
    import re
    from datetime import datetime
    
    current_year = datetime.now().year
    resume_lower = resume_text.lower() if resume_text else ""
    resume_upper = resume_text.upper() if resume_text else ""
    
    experience_score = 0
    experience_details = {
        'years_mentioned': 0,
        'job_count': 0,
        'has_internship': False,
        'graduation_year': None,
        'date_ranges_found': [],
        'work_duration_years': 0
    }
    
    # 1. Look for explicit years of experience patterns
    years_patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',  # "3 years experience", "5+ yrs exp"
        r'(?:experience|exp)\s*(?:of\s*)?(\d+)\+?\s*(?:years?|yrs?)',  # "experience of 3 years"
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|of)\s*(?:industry|field|domain)',  # "5 years in industry"
    ]
    
    max_years = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, resume_lower)
        for match in matches:
            try:
                years = int(match)
                if 0 < years < 50:  # Sanity check
                    max_years = max(max_years, years)
            except:
                pass
    
    experience_details['years_mentioned'] = max_years
    
    # 2. Find date ranges (WORK history only, excluding education)
    # Pattern: "2020 - 2024", "Jan 2020 - Present", "2019-present"
    date_range_patterns = [
        r'(20\d{2})\s*[-to]+\s*(20\d{2}|present|current|ongoing|now)',
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*20\d{2})\s*[-to]+\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*20\d{2}|present|current|ongoing|now)',
    ]
    
    # Education keywords to exclude date ranges near these
    education_keywords = [
        'b\.?tech', 'b\.?e\.?', 'b\.?sc', 'b\.?com', 'b\.?a\.?', 'bca', 'bba',
        'm\.?tech', 'm\.?e\.?', 'm\.?sc', 'm\.?com', 'm\.?a\.?', 'mca', 'mba',
        'bachelor', 'master', 'degree', 'diploma', 'ph\.?d', 'doctorate',
        'school', 'college', 'university', 'institute', 'education',
        '10th', '12th', 'xii', 'x\s', 'ssc', 'hsc', 'cbse', 'icse',
        'secondary', 'higher\s*secondary', 'intermediate', 'matriculation',
        'class\s*10', 'class\s*12', 'board', 'jee', 'neet', 'gate',
        'cgpa', 'gpa', 'percentage', 'marks', 'grade', 'semester',
        'graduation', 'graduated', 'pursuing', 'enrolled'
    ]
    education_pattern = '|'.join(education_keywords)
    
    total_work_years = 0
    date_ranges = []
    
    for pattern in date_range_patterns:
        # Use finditer to get match positions
        for match in re.finditer(pattern, resume_lower):
            start_str, end_str = match.groups()
            match_start = match.start()
            match_end = match.end()
            
            # Check context around the date range (100 chars before and after)
            context_start = max(0, match_start - 100)
            context_end = min(len(resume_lower), match_end + 100)
            context = resume_lower[context_start:context_end]
            
            # Skip if education keywords found in context
            if re.search(education_pattern, context):
                continue  # This is likely an education date, skip it
            
            try:
                # Extract year from start
                start_year_match = re.search(r'20\d{2}', start_str)
                start_year = int(start_year_match.group()) if start_year_match else None
                
                # Extract year from end (or use current year for "present")
                if any(word in end_str.lower() for word in ['present', 'current', 'ongoing', 'now']):
                    end_year = current_year
                else:
                    end_year_match = re.search(r'20\d{2}', end_str)
                    end_year = int(end_year_match.group()) if end_year_match else None
                
                if start_year and end_year and start_year <= end_year:
                    duration = end_year - start_year
                    if duration <= 20:  # Sanity check
                        date_ranges.append((start_year, end_year, duration))
                        total_work_years += duration
            except:
                pass
    
    experience_details['date_ranges_found'] = date_ranges
    experience_details['work_duration_years'] = total_work_years
    
    # 3. Find graduation year
    grad_patterns = [
        r'(?:graduated?|graduation|batch\s*of|class\s*of|passed\s*out)\s*:?\s*(20\d{2})',
        r'(20\d{2})\s*[-]\s*(20\d{2})\s*(?:b\.?tech|b\.?e|b\.?sc|m\.?tech|m\.?sc|mba|bca|mca)',
        r'(?:b\.?tech|b\.?e|b\.?sc|bca)\s*[-(]?\s*(20\d{2})',
    ]
    
    for pattern in grad_patterns:
        match = re.search(pattern, resume_lower)
        if match:
            try:
                # Get the last year (graduation year)
                years_found = re.findall(r'20\d{2}', match.group())
                if years_found:
                    grad_year = int(max(years_found))
                    if 2000 <= grad_year <= current_year + 4:
                        experience_details['graduation_year'] = grad_year
                        break
            except:
                pass
    
    # 4. Count job positions/company mentions
    job_indicators = [
        r'\b(?:software\s*engineer|developer|analyst|manager|lead|intern|trainee|associate|executive|consultant)\b',
        r'\b(?:worked\s*at|employed\s*at|joined|position|role\s*:)\b',
        r'\b(?:pvt\.?\s*ltd|private\s*limited|inc\.|llc|corporation|corp\.|technologies|solutions|systems)\b',
    ]
    
    job_count = 0
    for pattern in job_indicators:
        matches = re.findall(pattern, resume_lower)
        job_count += len(matches)
    
    experience_details['job_count'] = min(job_count // 2, 10)  # Normalize (divide by 2 as patterns may overlap)
    
    # 5. Check for internship mentions
    internship_patterns = r'\b(?:internship|intern|trainee|summer\s*training|industrial\s*training)\b'
    experience_details['has_internship'] = bool(re.search(internship_patterns, resume_lower))
    
    # 6. Calculate experience score and determine level
    
    # Years mentioned score
    if max_years >= 5:
        experience_score += 40
    elif max_years >= 3:
        experience_score += 30
    elif max_years >= 1:
        experience_score += 15
    
    # Work duration from date ranges
    if total_work_years >= 5:
        experience_score += 35
    elif total_work_years >= 3:
        experience_score += 25
    elif total_work_years >= 1:
        experience_score += 10
    
    # Graduation year factor
    if experience_details['graduation_year']:
        years_since_grad = current_year - experience_details['graduation_year']
        if years_since_grad >= 5:
            experience_score += 20
        elif years_since_grad >= 2:
            experience_score += 10
        elif years_since_grad <= 1:
            experience_score -= 10  # Recent graduate, likely fresher
    
    # Internship bonus (but caps at intermediate)
    if experience_details['has_internship']:
        experience_score += 10
    
    # Job count factor
    if experience_details['job_count'] >= 3:
        experience_score += 15
    elif experience_details['job_count'] >= 1:
        experience_score += 5
    
    # Note: Page count is NOT used as it's unreliable
    # (freshers can have long resumes, experienced can have short ones)
    
    # Determine final level
    if experience_score >= 50:
        level = "Experienced"
        level_detail = f"5+ years (Score: {experience_score})"
    elif experience_score >= 25:
        level = "Intermediate"
        level_detail = f"1-4 years (Score: {experience_score})"
    else:
        level = "Fresher"
        level_detail = f"0-1 years (Score: {experience_score})"
    
    return {
        'level': level,
        'level_detail': level_detail,
        'score': experience_score,
        'details': experience_details
    }


###### Job Recommendations Generator ######
def generate_job_recommendations(field, level, skills):
    """Generate job recommendations based on field and experience level"""
    
    jobs_db = {
        'Data Science': [
            {'title': 'Data Scientist', 'level': 'Mid-Senior', 'salary': '12 - 25 LPA',
             'skills': ['Python', 'Machine Learning', 'SQL', 'Statistics', 'TensorFlow'],
             'description': 'Analyze complex data sets to drive business decisions and build predictive models.'},
            {'title': 'Machine Learning Engineer', 'level': 'Mid-Senior', 'salary': '15 - 30 LPA',
             'skills': ['Python', 'TensorFlow', 'PyTorch', 'MLOps', 'Cloud'],
             'description': 'Design and deploy ML models at scale in production environments.'},
            {'title': 'Data Analyst', 'level': 'Fresher-Entry', 'salary': '4 - 8 LPA',
             'skills': ['SQL', 'Excel', 'Tableau', 'Python', 'Statistics'],
             'description': 'Transform data into actionable insights through analysis and visualization.'},
            {'title': 'Junior Data Scientist', 'level': 'Fresher', 'salary': '5 - 12 LPA',
             'skills': ['Python', 'SQL', 'Statistics', 'Pandas', 'Machine Learning'],
             'description': 'Assist in building ML models and performing data analysis under senior guidance.'},
        ],
        'Web Development': [
            {'title': 'Frontend Developer', 'level': 'Fresher-Entry', 'salary': '3 - 8 LPA',
             'skills': ['React', 'JavaScript', 'HTML', 'CSS', 'TypeScript'],
             'description': 'Build responsive and interactive user interfaces for web applications.'},
            {'title': 'Full Stack Developer', 'level': 'Mid-Senior', 'salary': '8 - 20 LPA',
             'skills': ['React', 'Node.js', 'Python', 'SQL', 'AWS'],
             'description': 'Develop both frontend and backend components of web applications.'},
            {'title': 'Backend Developer', 'level': 'Entry-Mid', 'salary': '5 - 15 LPA',
             'skills': ['Node.js', 'Python', 'SQL', 'APIs', 'Docker'],
             'description': 'Design and implement server-side logic and database architecture.'},
            {'title': 'Junior Web Developer', 'level': 'Fresher', 'salary': '2.5 - 6 LPA',
             'skills': ['HTML', 'CSS', 'JavaScript', 'React', 'Git'],
             'description': 'Develop and maintain websites under guidance of senior developers.'},
        ],
        'Android Development': [
            {'title': 'Android Developer', 'level': 'Fresher-Entry', 'salary': '3 - 8 LPA',
             'skills': ['Kotlin', 'Android SDK', 'Jetpack', 'REST APIs', 'Git'],
             'description': 'Build native Android applications with modern architecture patterns.'},
            {'title': 'Mobile App Developer', 'level': 'Mid-Senior', 'salary': '8 - 18 LPA',
             'skills': ['Flutter', 'Kotlin', 'Swift', 'Firebase', 'REST APIs'],
             'description': 'Develop cross-platform mobile applications for Android and iOS.'},
            {'title': 'Junior Android Developer', 'level': 'Fresher', 'salary': '2.5 - 6 LPA',
             'skills': ['Java', 'Kotlin', 'Android SDK', 'XML', 'Git'],
             'description': 'Develop and maintain Android apps under senior developer guidance.'},
            {'title': 'Flutter Developer', 'level': 'Entry-Mid', 'salary': '4 - 12 LPA',
             'skills': ['Flutter', 'Dart', 'Firebase', 'REST APIs', 'Git'],
             'description': 'Build cross-platform mobile apps using Flutter framework.'},
        ],
        'IOS Development': [
            {'title': 'iOS Developer', 'level': 'Fresher-Entry', 'salary': '3.5 - 10 LPA',
             'skills': ['Swift', 'UIKit', 'SwiftUI', 'Core Data', 'REST APIs'],
             'description': 'Build native iOS applications for iPhone and iPad.'},
            {'title': 'Senior iOS Engineer', 'level': 'Senior', 'salary': '15 - 30 LPA',
             'skills': ['Swift', 'Architecture', 'Performance', 'Testing', 'Leadership'],
             'description': 'Lead iOS development and mentor junior developers.'},
            {'title': 'Junior iOS Developer', 'level': 'Fresher', 'salary': '3 - 7 LPA',
             'skills': ['Swift', 'UIKit', 'Xcode', 'Git', 'REST APIs'],
             'description': 'Develop iOS apps and learn best practices under senior guidance.'},
            {'title': 'React Native Developer', 'level': 'Entry-Mid', 'salary': '4 - 12 LPA',
             'skills': ['React Native', 'JavaScript', 'iOS', 'Android', 'Redux'],
             'description': 'Build cross-platform mobile apps using React Native.'},
        ],
        'UI-UX Development': [
            {'title': 'UI/UX Designer', 'level': 'Fresher-Entry', 'salary': '3 - 8 LPA',
             'skills': ['Figma', 'Adobe XD', 'Prototyping', 'User Research', 'Wireframing'],
             'description': 'Design intuitive and visually appealing user interfaces.'},
            {'title': 'Product Designer', 'level': 'Mid-Senior', 'salary': '10 - 22 LPA',
             'skills': ['Figma', 'User Research', 'Design Systems', 'Prototyping', 'Strategy'],
             'description': 'Lead end-to-end product design from research to implementation.'},
            {'title': 'Junior UI Designer', 'level': 'Fresher', 'salary': '2.5 - 6 LPA',
             'skills': ['Figma', 'Adobe XD', 'Photoshop', 'Wireframing', 'Visual Design'],
             'description': 'Create visual designs and UI components under senior guidance.'},
            {'title': 'UX Researcher', 'level': 'Entry-Mid', 'salary': '5 - 15 LPA',
             'skills': ['User Research', 'Usability Testing', 'Data Analysis', 'Interviewing', 'Surveys'],
             'description': 'Conduct user research to inform product decisions.'},
        ],
        'Cyber Security': [
            {'title': 'Security Analyst', 'level': 'Fresher-Entry', 'salary': '4 - 10 LPA',
             'skills': ['SIEM', 'Network Security', 'Incident Response', 'Vulnerability Assessment', 'Linux'],
             'description': 'Monitor and analyze security threats and incidents to protect organizational assets.'},
            {'title': 'Penetration Tester', 'level': 'Entry-Mid', 'salary': '6 - 15 LPA',
             'skills': ['Kali Linux', 'Metasploit', 'Burp Suite', 'Python', 'OWASP'],
             'description': 'Conduct authorized simulated attacks to identify security vulnerabilities.'},
            {'title': 'Security Engineer', 'level': 'Mid-Senior', 'salary': '12 - 25 LPA',
             'skills': ['Cloud Security', 'DevSecOps', 'Firewall', 'IAM', 'Encryption'],
             'description': 'Design and implement security solutions and infrastructure.'},
            {'title': 'SOC Analyst', 'level': 'Fresher', 'salary': '3.5 - 8 LPA',
             'skills': ['SIEM', 'Log Analysis', 'Threat Detection', 'Incident Response', 'Networking'],
             'description': 'Monitor security operations center and respond to security events.'},
            {'title': 'Cybersecurity Consultant', 'level': 'Senior', 'salary': '18 - 35 LPA',
             'skills': ['Risk Assessment', 'Compliance', 'Security Architecture', 'Leadership', 'Communication'],
             'description': 'Advise organizations on security strategy and best practices.'},
        ],
        'Cloud Computing': [
            {'title': 'Cloud Engineer', 'level': 'Fresher-Entry', 'salary': '5 - 12 LPA',
             'skills': ['AWS', 'Azure', 'Linux', 'Networking', 'Python'],
             'description': 'Deploy and manage cloud infrastructure and services.'},
            {'title': 'DevOps Engineer', 'level': 'Entry-Mid', 'salary': '8 - 18 LPA',
             'skills': ['CI/CD', 'Docker', 'Kubernetes', 'Terraform', 'Jenkins'],
             'description': 'Build and maintain CI/CD pipelines and automate infrastructure.'},
            {'title': 'Cloud Architect', 'level': 'Senior', 'salary': '20 - 40 LPA',
             'skills': ['Cloud Architecture', 'Multi-cloud', 'Security', 'Cost Optimization', 'Leadership'],
             'description': 'Design scalable, secure, and cost-effective cloud solutions.'},
            {'title': 'Site Reliability Engineer', 'level': 'Mid-Senior', 'salary': '15 - 30 LPA',
             'skills': ['Kubernetes', 'Monitoring', 'Automation', 'Incident Management', 'Python'],
             'description': 'Ensure reliability and performance of large-scale distributed systems.'},
            {'title': 'Cloud Administrator', 'level': 'Fresher', 'salary': '3.5 - 8 LPA',
             'skills': ['AWS', 'Azure', 'Linux', 'Networking', 'Monitoring'],
             'description': 'Manage and monitor cloud resources and services.'},
        ],
        'Data Analyst': [
            {'title': 'Data Analyst', 'level': 'Fresher-Entry', 'salary': '4 - 10 LPA',
             'skills': ['SQL', 'Excel', 'Python', 'Tableau', 'Statistics'],
             'description': 'Analyze data to provide actionable business insights.'},
            {'title': 'Business Intelligence Analyst', 'level': 'Entry-Mid', 'salary': '6 - 15 LPA',
             'skills': ['Power BI', 'SQL', 'Data Modeling', 'ETL', 'Reporting'],
             'description': 'Create dashboards and reports for business decision-making.'},
            {'title': 'Senior Data Analyst', 'level': 'Mid-Senior', 'salary': '12 - 22 LPA',
             'skills': ['Python', 'SQL', 'Statistical Analysis', 'Leadership', 'Stakeholder Management'],
             'description': 'Lead analytics projects and mentor junior analysts.'},
            {'title': 'Analytics Consultant', 'level': 'Senior', 'salary': '18 - 30 LPA',
             'skills': ['Analytics Strategy', 'Data Visualization', 'Communication', 'Domain Expertise'],
             'description': 'Advise organizations on data-driven decision making.'},
            {'title': 'Junior Data Analyst', 'level': 'Fresher', 'salary': '3 - 6 LPA',
             'skills': ['SQL', 'Excel', 'Basic Python', 'Data Cleaning', 'Reporting'],
             'description': 'Support data analysis tasks under senior guidance.'},
        ],
        'Machine Learning': [
            {'title': 'Machine Learning Engineer', 'level': 'Entry-Mid', 'salary': '8 - 20 LPA',
             'skills': ['Python', 'TensorFlow', 'PyTorch', 'MLOps', 'SQL'],
             'description': 'Build and deploy machine learning models at scale.'},
            {'title': 'AI Engineer', 'level': 'Mid-Senior', 'salary': '15 - 30 LPA',
             'skills': ['Deep Learning', 'NLP', 'Computer Vision', 'LLMs', 'Cloud'],
             'description': 'Develop AI-powered applications and solutions.'},
            {'title': 'ML Research Scientist', 'level': 'Senior', 'salary': '25 - 50 LPA',
             'skills': ['Research', 'Publications', 'Mathematics', 'Novel Algorithms', 'PhD'],
             'description': 'Conduct cutting-edge ML research and publish findings.'},
            {'title': 'Junior ML Engineer', 'level': 'Fresher', 'salary': '5 - 10 LPA',
             'skills': ['Python', 'Scikit-learn', 'Pandas', 'Mathematics', 'SQL'],
             'description': 'Assist in building ML pipelines and model development.'},
            {'title': 'MLOps Engineer', 'level': 'Mid-Senior', 'salary': '12 - 25 LPA',
             'skills': ['MLflow', 'Kubernetes', 'CI/CD', 'Model Monitoring', 'Cloud'],
             'description': 'Build infrastructure for ML model deployment and monitoring.'},
        ],
        'DevOps': [
            {'title': 'DevOps Engineer', 'level': 'Fresher-Entry', 'salary': '5 - 12 LPA',
             'skills': ['Linux', 'Docker', 'CI/CD', 'Git', 'Scripting'],
             'description': 'Automate development and deployment processes.'},
            {'title': 'Senior DevOps Engineer', 'level': 'Mid-Senior', 'salary': '15 - 28 LPA',
             'skills': ['Kubernetes', 'Terraform', 'AWS', 'Security', 'Architecture'],
             'description': 'Design and implement DevOps strategies and infrastructure.'},
            {'title': 'Platform Engineer', 'level': 'Mid-Senior', 'salary': '18 - 35 LPA',
             'skills': ['Kubernetes', 'Platform Design', 'Developer Experience', 'Automation'],
             'description': 'Build internal platforms to improve developer productivity.'},
            {'title': 'Release Engineer', 'level': 'Entry-Mid', 'salary': '6 - 14 LPA',
             'skills': ['CI/CD', 'Release Management', 'Automation', 'Git', 'Scripting'],
             'description': 'Manage software releases and deployment pipelines.'},
            {'title': 'Build Engineer', 'level': 'Fresher', 'salary': '4 - 8 LPA',
             'skills': ['CI/CD', 'Build Tools', 'Git', 'Linux', 'Scripting'],
             'description': 'Maintain build systems and automate build processes.'},
        ]
    }
    
    return jobs_db.get(field, [
        {'title': 'Software Developer', 'level': 'Fresher-Entry', 'salary': '3 - 8 LPA',
         'skills': ['Programming', 'Problem Solving', 'Git', 'Agile', 'Communication'],
         'description': 'Develop software solutions to meet business requirements.'},
        {'title': 'Junior Software Engineer', 'level': 'Fresher', 'salary': '2.5 - 6 LPA',
         'skills': ['Programming', 'Data Structures', 'Git', 'Problem Solving', 'Communication'],
         'description': 'Write and maintain code under guidance of senior engineers.'},
    ])


###### Trending Skills Generator ######
def get_trending_skills(field):
    """Get trending skills for 2026 based on field"""
    
    trending_db = {
        'Data Science': {
            'hot': ['Generative AI', 'LLMs', 'MLOps', 'LangChain', 'Vector Databases'],
            'growing': ['AutoML', 'Feature Stores', 'Model Monitoring', 'Data Mesh', 'dbt'],
            'essential': ['Python', 'SQL', 'TensorFlow', 'PyTorch', 'Pandas']
        },
        'Web Development': {
            'hot': ['Next.js 14', 'Astro', 'Bun', 'tRPC', 'Edge Computing'],
            'growing': ['Remix', 'SvelteKit', 'Turbopack', 'Server Components', 'WebAssembly'],
            'essential': ['React', 'TypeScript', 'Node.js', 'Tailwind CSS', 'Git']
        },
        'Android Development': {
            'hot': ['Jetpack Compose', 'Kotlin Multiplatform', 'Gemini AI', 'Compose Multiplatform'],
            'growing': ['KMM', 'Ktor', 'Room', 'WorkManager', 'App Bundles'],
            'essential': ['Kotlin', 'Android SDK', 'MVVM', 'Coroutines', 'Firebase']
        },
        'IOS Development': {
            'hot': ['SwiftUI', 'Swift Concurrency', 'VisionOS', 'SwiftData', 'App Intents'],
            'growing': ['Combine', 'TCA', 'SPM', 'WidgetKit', 'App Clips'],
            'essential': ['Swift', 'UIKit', 'Core Data', 'Xcode', 'TestFlight']
        },
        'UI-UX Development': {
            'hot': ['AI Design Tools', 'Figma Dev Mode', 'Design Systems', 'Motion Design', 'AR/VR UX'],
            'growing': ['Design Tokens', 'Variable Fonts', 'Micro-interactions', '3D Design', 'Voice UI'],
            'essential': ['Figma', 'User Research', 'Prototyping', 'Accessibility', 'Design Thinking']
        },
        'Cyber Security': {
            'hot': ['AI Security', 'Zero Trust Architecture', 'Cloud Security', 'XDR', 'Threat Intelligence'],
            'growing': ['DevSecOps', 'Container Security', 'API Security', 'SOAR', 'Identity Governance'],
            'essential': ['SIEM', 'Penetration Testing', 'Network Security', 'Incident Response', 'Compliance']
        },
        'Cloud Computing': {
            'hot': ['FinOps', 'Platform Engineering', 'GitOps', 'Serverless', 'AI/ML Cloud Services'],
            'growing': ['Multi-cloud', 'Cloud Native', 'Service Mesh', 'Observability', 'Edge Computing'],
            'essential': ['AWS', 'Azure', 'Kubernetes', 'Terraform', 'Docker']
        },
        'Data Analyst': {
            'hot': ['AI-Assisted Analytics', 'Real-time Analytics', 'Data Storytelling', 'Product Analytics'],
            'growing': ['dbt', 'Looker', 'DataOps', 'Reverse ETL', 'Metrics Layer'],
            'essential': ['SQL', 'Python', 'Tableau/Power BI', 'Excel', 'Statistics']
        },
        'Machine Learning': {
            'hot': ['LLMs', 'Generative AI', 'RAG', 'Fine-tuning', 'Prompt Engineering'],
            'growing': ['MLOps', 'AutoML', 'Edge ML', 'Federated Learning', 'Responsible AI'],
            'essential': ['Python', 'TensorFlow/PyTorch', 'Scikit-learn', 'SQL', 'Mathematics']
        },
        'DevOps': {
            'hot': ['Platform Engineering', 'GitOps', 'FinOps', 'AI for DevOps', 'Internal Developer Platforms'],
            'growing': ['eBPF', 'Service Mesh', 'Policy as Code', 'Backstage', 'Crossplane'],
            'essential': ['Kubernetes', 'Docker', 'Terraform', 'CI/CD', 'Linux']
        }
    }
    
    return trending_db.get(field, {
        'hot': ['AI/ML Integration', 'Cloud Computing', 'DevOps', 'Cybersecurity'],
        'growing': ['Microservices', 'Containers', 'API Design', 'CI/CD'],
        'essential': ['Git', 'Problem Solving', 'Communication', 'Agile']
    })


###### Job Search URLs Generator ######
def get_job_search_urls(job_title):
    """Generate job search URLs for different platforms"""
    import urllib.parse
    encoded_title = urllib.parse.quote(job_title)
    
    return {
        'naukri': f'https://www.naukri.com/{encoded_title.lower().replace("%20", "-")}-jobs',
        'linkedin': f'https://www.linkedin.com/jobs/search/?keywords={encoded_title}',
        'indeed': f'https://www.indeed.co.in/jobs?q={encoded_title}',
        'glassdoor': f'https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={encoded_title}',
        'internshala': f'https://internshala.com/jobs/{encoded_title.lower().replace("%20", "-")}-jobs'
    }


###### Resume-Based Interview Questions Generator ######
def generate_resume_based_questions(skills, field, projects_text=""):
    """Generate interview questions specifically based on resume skills"""
    
    skill_questions = {
        'Python': [
            {'q': 'Explain the difference between lists and tuples in Python.', 
             'a': 'Lists are mutable (can be changed) and use square brackets []. Tuples are immutable (cannot be changed) and use parentheses (). Tuples are faster and used when data shouldn\'t change.'},
            {'q': 'What are Python decorators and how do you use them?',
             'a': 'Decorators are functions that modify other functions. They use @decorator syntax. Common uses: logging, timing, authentication. Example: @login_required before a function.'}
        ],
        'JavaScript': [
            {'q': 'Explain the difference between let, const, and var.',
             'a': 'var is function-scoped and hoisted. let is block-scoped, can be reassigned. const is block-scoped and cannot be reassigned (but objects/arrays can be mutated).'},
            {'q': 'What is the event loop in JavaScript?',
             'a': 'The event loop handles async operations. It checks the call stack, executes sync code first, then processes callback queue (setTimeout) and microtask queue (Promises) in order.'}
        ],
        'React': [
            {'q': 'Explain the useState and useEffect hooks.',
             'a': 'useState manages component state - returns [state, setState]. useEffect handles side effects (API calls, subscriptions) - runs after render. Dependencies array controls when it runs.'},
            {'q': 'What is the Virtual DOM and how does React use it?',
             'a': 'Virtual DOM is an in-memory representation of real DOM. React compares new vs old virtual DOM (diffing), then updates only changed parts of real DOM (reconciliation) for better performance.'}
        ],
        'Node.js': [
            {'q': 'What is the difference between process.nextTick() and setImmediate()?',
             'a': 'process.nextTick() executes immediately after current operation, before I/O events. setImmediate() executes in next iteration of event loop, after I/O events.'},
            {'q': 'Explain middleware in Express.js.',
             'a': 'Middleware are functions with access to req, res, next. They execute in order, can modify request/response, end the cycle, or call next(). Used for auth, logging, error handling.'}
        ],
        'SQL': [
            {'q': 'Explain the difference between INNER JOIN, LEFT JOIN, and RIGHT JOIN.',
             'a': 'INNER JOIN returns matching rows from both tables. LEFT JOIN returns all from left table + matches from right. RIGHT JOIN returns all from right table + matches from left.'},
            {'q': 'What are indexes and when would you use them?',
             'a': 'Indexes speed up data retrieval by creating a data structure for quick lookups. Use on frequently queried columns, WHERE clauses, JOIN columns. Avoid on frequently updated columns.'}
        ],
        'Machine Learning': [
            {'q': 'Explain overfitting and how to prevent it.',
             'a': 'Overfitting is when model learns training data too well but fails on new data. Prevention: more data, regularization (L1/L2), dropout, cross-validation, early stopping, simpler model.'},
            {'q': 'What is the difference between precision and recall?',
             'a': 'Precision = TP/(TP+FP) - of predicted positives, how many are correct. Recall = TP/(TP+FN) - of actual positives, how many were found. Use F1-score for balance.'}
        ],
        'Git': [
            {'q': 'What is the difference between git merge and git rebase?',
             'a': 'Merge creates a new commit combining branches, preserving history. Rebase moves commits to new base, creating linear history. Rebase rewrites history - don\'t use on public branches.'},
            {'q': 'How do you resolve merge conflicts?',
             'a': 'Open conflicted files, look for <<<<<<< markers, manually choose/combine changes, remove markers, stage resolved files with git add, then commit.'}
        ],
        'AWS': [
            {'q': 'Explain the difference between EC2, Lambda, and ECS.',
             'a': 'EC2: Virtual servers you manage. Lambda: Serverless functions, pay per execution. ECS: Container orchestration service. Choose based on control vs convenience needs.'},
            {'q': 'What is the difference between S3 storage classes?',
             'a': 'Standard: frequent access. Intelligent-Tiering: auto-moves data. Standard-IA: infrequent access. Glacier: archival (minutes-hours retrieval). Glacier Deep: long-term archive (12+ hours).'}
        ],
        'Docker': [
            {'q': 'What is the difference between Docker image and container?',
             'a': 'Image is a read-only template with instructions. Container is a running instance of an image. One image can create many containers. Images are built from Dockerfiles.'},
            {'q': 'Explain Docker networking modes.',
             'a': 'Bridge: default, isolated network. Host: shares host network. None: no networking. Overlay: multi-host communication. Macvlan: assigns MAC address, appears as physical device.'}
        ]
    }
    
    questions = []
    for skill in skills:
        skill_key = skill if skill in skill_questions else None
        # Try to match partial skills
        if not skill_key:
            for key in skill_questions:
                if key.lower() in skill.lower() or skill.lower() in key.lower():
                    skill_key = key
                    break
        
        if skill_key and skill_key in skill_questions:
            for qa in skill_questions[skill_key]:
                questions.append({
                    'skill': skill,
                    'question': qa['q'],
                    'answer': qa['a']
                })
    
    return questions[:8]  # Return top 8 questions


###### Main function run() ######

def run():
    # Initialize session state first (before any checks)
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    load_css()
    
    # If database is not available, skip authentication
    if not DB_AVAILABLE:
        st.warning("Running in demo mode - Database unavailable. Authentication and data saving are disabled.")
        st.session_state.logged_in = True
        st.session_state.username = "Demo User"
        if st.session_state.page in ['login', 'signup']:
            st.session_state.page = 'dashboard'
    
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
    # Hero section with Apple-style branding
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">
            <span class="hero-gradient">skilledge</span>
        </div>
        <div class="hero-subtitle">AI-powered resume analysis.<br>Elevate your career.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Centered login card
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 36px;'>
            <h2 style='margin-bottom: 8px; font-size: 1.625rem; color: #FFFFFF;'>Welcome back</h2>
            <p style='color: rgba(235, 235, 245, 0.6); font-size: 1rem;'>Sign in to continue to your dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Sign In", use_container_width=True, key="login_button"):
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
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; color: rgba(235, 235, 245, 0.6); font-size: 0.9375rem;'>Don't have an account?
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Create Account", use_container_width=True, key="create_account_button", type="secondary"):
            st.session_state.page = 'signup'
            st.rerun()

def show_signup_page():
    # Hero section
    st.markdown("""
    <div class="hero-section" style="padding: 60px 24px 40px;">
        <div class="hero-title" style="font-size: 2.75rem;">Join <span class="hero-gradient">skilledge</span>
        </div>
        <div class="hero-subtitle" style="font-size: 1.25rem;">Create your account and start your journey
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Centered signup card
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 28px;'>
            <h3 style='margin-bottom: 8px; font-size: 1.375rem; color: #FFFFFF;'>Create your account</h3>
            <p style='color: rgba(235, 235, 245, 0.6); font-size: 0.9375rem;'>Fill in your details to get started</p>
        </div>
        """, unsafe_allow_html=True)
        
        username = st.text_input("Username", key="signup_username", placeholder="Choose a username")
        email = st.text_input("Email", key="signup_email", placeholder="your@email.com")
        password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password", placeholder="Confirm your password")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        if st.button("Create Account", use_container_width=True, key="signup_button"):
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
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='text-align: center; color: rgba(235, 235, 245, 0.6); font-size: 0.9375rem;'>Already have an account?
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Sign In Instead", use_container_width=True, key="back_to_login_button", type="secondary"):
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
        # Use environment variable or fallback for Docker/cloud environments
        try:
            dev_user = os.getlogin()
        except:
            dev_user = os.environ.get('USER', os.environ.get('USERNAME', 'webapp_user'))
        os_name_ver = platform.system() + " " + platform.release()
        
        # Geocoding - handle failures gracefully
        try:
            g = geocoder.ip('me')
            latlong = g.latlng if g.latlng else [0, 0]
            geolocator = Nominatim(user_agent="http")
            location = geolocator.reverse(latlong, language='en')
            address = location.raw['address']
            city = address.get('city', 'Unknown')
            state = address.get('state', 'Unknown')
            country = address.get('country', 'Unknown')
        except:
            latlong = [0, 0]
            city = 'Unknown'
            state = 'Unknown'
            country = 'Unknown'


        # Upload Resume - Apple Pro Dark Mode design
        st.markdown('''
        <div style="text-align: center; padding: 48px 0 32px 0;">
            <h1 style="font-size: 2.75rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em; margin-bottom: 16px;">Upload Your Resume
            </h1>
            <p style="font-size: 1.125rem; color: rgba(235, 235, 245, 0.6); font-weight: 400; max-width: 520px; margin: 0 auto; line-height: 1.5;">Get AI-powered insights, skill recommendations, and personalized career guidance
            </p>
        </div>
        ''',unsafe_allow_html=True)
        
        # Create centered columns for better layout
        col1, col2, col3 = st.columns([0.5, 3, 0.5])
        with col2:
            ## file upload in pdf format with larger area
            pdf_file = st.file_uploader("Drop your PDF here or click to browse", type=["pdf"], help="Upload your resume in PDF format", label_visibility="visible")
        if pdf_file is not None:
            with st.spinner(' Analyzing your resume...'):
                time.sleep(4)
        
            ### Create Uploaded_Resumes directory if it doesn't exist
            upload_dir = './Uploaded_Resumes'
            os.makedirs(upload_dir, exist_ok=True)
            
            ### saving the uploaded resume to folder
            save_image_path = os.path.join(upload_dir, pdf_file.name)
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

            ### parsing and extracting whole resume using enhanced text extraction
            resume_data = None
            try:
                resume_text = pdf_reader(save_image_path)
                
                # Enhanced extraction using regex and keyword matching
                import re
                
                # Try to extract email
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, resume_text)
                email = emails[0] if emails else None
                
                # Try to extract phone
                phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}'
                phones = re.findall(phone_pattern, resume_text)
                phone = phones[0] if phones else None
                
                # Extract name (first few lines, skip common headers)
                lines = [line.strip() for line in resume_text.split('\n') if line.strip()]
                name = None
                for line in lines[:5]:  # Check first 5 lines
                    if line and len(line) < 50 and not any(word in line.lower() for word in ['resume', 'cv', 'curriculum']):
                        name = line
                        break
                
                # Extract skills using regex with variations for better matching
                # Each tuple: (display_name, [regex_patterns])
                skills_patterns = {
                    # Programming Languages
                    'Python': [r'\bpython\b'],
                    'Java': [r'\bjava\b(?!script)'],
                    'JavaScript': [r'\bjavascript\b', r'\bjs\b', r'\bnode\.?js\b', r'\breact\.?js\b', r'\bvue\.?js\b', r'\bnext\.?js\b', r'\bnuxt\.?js\b', r'\bangular\.?js\b'],
                    'C++': [r'\bc\+\+\b', r'\bcpp\b'],
                    'C#': [r'\bc#\b', r'\bcsharp\b', r'\bc sharp\b'],
                    'PHP': [r'\bphp\b'],
                    'Ruby': [r'\bruby\b'],
                    'Go': [r'\bgolang\b', r'\bgo\s+lang\b'],
                    'Rust': [r'\brust\b'],
                    'Swift': [r'\bswift\b'],
                    'Kotlin': [r'\bkotlin\b'],
                    'TypeScript': [r'\btypescript\b', r'\bts\b'],
                    'Scala': [r'\bscala\b'],
                    'R': [r'\br\s+programming\b', r'\br\s+language\b'],
                    'MATLAB': [r'\bmatlab\b'],
                    # Web Technologies
                    'HTML': [r'\bhtml\b', r'\bhtml5\b'],
                    'CSS': [r'\bcss\b', r'\bcss3\b', r'\bsass\b', r'\bscss\b', r'\bless\b'],
                    'React': [r'\breact\b', r'\breact\.?js\b', r'\breactjs\b'],
                    'Angular': [r'\bangular\b', r'\bangular\.?js\b', r'\bangularjs\b'],
                    'Vue': [r'\bvue\b', r'\bvue\.?js\b', r'\bvuejs\b'],
                    'Node.js': [r'\bnode\b', r'\bnode\.?js\b', r'\bnodejs\b'],
                    'Django': [r'\bdjango\b'],
                    'Flask': [r'\bflask\b'],
                    'Spring': [r'\bspring\b', r'\bspring\s*boot\b'],
                    'Express': [r'\bexpress\b', r'\bexpress\.?js\b'],
                    'jQuery': [r'\bjquery\b'],
                    'Bootstrap': [r'\bbootstrap\b'],
                    'Tailwind': [r'\btailwind\b', r'\btailwindcss\b'],
                    'Next.js': [r'\bnext\b', r'\bnext\.?js\b', r'\bnextjs\b'],
                    'Webpack': [r'\bwebpack\b'],
                    # Mobile
                    'Android': [r'\bandroid\b'],
                    'iOS': [r'\bios\b', r'\biphone\b', r'\bipad\b'],
                    'Flutter': [r'\bflutter\b'],
                    'React Native': [r'\breact\s*native\b'],
                    'Xamarin': [r'\bxamarin\b'],
                    # Databases
                    'SQL': [r'\bsql\b', r'\bplsql\b', r'\bpl/sql\b'],
                    'MySQL': [r'\bmysql\b'],
                    'PostgreSQL': [r'\bpostgres\b', r'\bpostgresql\b', r'\bpsql\b'],
                    'MongoDB': [r'\bmongo\b', r'\bmongodb\b'],
                    'Redis': [r'\bredis\b'],
                    'Oracle': [r'\boracle\b'],
                    'SQLite': [r'\bsqlite\b'],
                    'Firebase': [r'\bfirebase\b'],
                    'Elasticsearch': [r'\belastic\b', r'\belasticsearch\b'],
                    # Cloud & DevOps
                    'AWS': [r'\baws\b', r'\bamazon\s*web\s*services\b', r'\bec2\b', r'\bs3\b', r'\blambda\b'],
                    'Azure': [r'\bazure\b', r'\bmicrosoft\s*azure\b'],
                    'GCP': [r'\bgcp\b', r'\bgoogle\s*cloud\b'],
                    'Docker': [r'\bdocker\b'],
                    'Kubernetes': [r'\bkubernetes\b', r'\bk8s\b'],
                    'Jenkins': [r'\bjenkins\b'],
                    'Git': [r'\bgit\b', r'\bgithub\b', r'\bgitlab\b'],
                    'CI/CD': [r'\bci/cd\b', r'\bcicd\b', r'\bcontinuous\s*integration\b'],
                    'Terraform': [r'\bterraform\b'],
                    'Linux': [r'\blinux\b', r'\bubuntu\b', r'\bcentos\b', r'\bdebian\b'],
                    # Data Science & ML
                    'Machine Learning': [r'\bmachine\s*learning\b', r'\bml\b'],
                    'Deep Learning': [r'\bdeep\s*learning\b', r'\bdl\b', r'\bneural\s*network\b'],
                    'TensorFlow': [r'\btensorflow\b', r'\btf\b'],
                    'PyTorch': [r'\bpytorch\b', r'\btorch\b'],
                    'Keras': [r'\bkeras\b'],
                    'Scikit-learn': [r'\bscikit\b', r'\bsklearn\b', r'\bscikit-learn\b'],
                    'Pandas': [r'\bpandas\b'],
                    'NumPy': [r'\bnumpy\b'],
                    'Matplotlib': [r'\bmatplotlib\b'],
                    'Data Analysis': [r'\bdata\s*analysis\b', r'\bdata\s*analyst\b'],
                    'Data Visualization': [r'\bdata\s*visualization\b', r'\bdata\s*viz\b'],
                    'Tableau': [r'\btableau\b'],
                    'Power BI': [r'\bpower\s*bi\b', r'\bpowerbi\b'],
                    'Excel': [r'\bexcel\b', r'\bms\s*excel\b'],
                    'NLP': [r'\bnlp\b', r'\bnatural\s*language\b'],
                    'Computer Vision': [r'\bcomputer\s*vision\b', r'\bcv\b', r'\bopencv\b'],
                    # Other
                    'Agile': [r'\bagile\b'],
                    'Scrum': [r'\bscrum\b'],
                    'REST API': [r'\brest\b', r'\brest\s*api\b', r'\brestful\b'],
                    'GraphQL': [r'\bgraphql\b'],
                    'Microservices': [r'\bmicroservice\b', r'\bmicroservices\b'],
                    'Selenium': [r'\bselenium\b'],
                    'Figma': [r'\bfigma\b'],
                    'Adobe XD': [r'\badobe\s*xd\b', r'\bxd\b'],
                    'Photoshop': [r'\bphotoshop\b'],
                    'Illustrator': [r'\billustrator\b'],
                }
                
                detected_skills = []
                resume_lower = resume_text.lower()
                for skill_name, patterns in skills_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, resume_lower, re.IGNORECASE):
                            detected_skills.append(skill_name)
                            break  # Found this skill, move to next
                
                # Remove duplicates and sort
                detected_skills = sorted(list(set(detected_skills)))
                
                # Extract degree information
                degree_keywords = {
                    'bachelor': 'Bachelor',
                    'master': 'Master',
                    'phd': 'PhD',
                    'doctorate': 'PhD',
                    'b.tech': 'B.Tech',
                    'b.e': 'B.E',
                    'm.tech': 'M.Tech',
                    'mba': 'MBA',
                    'bca': 'BCA',
                    'mca': 'MCA',
                    'bsc': 'B.Sc',
                    'msc': 'M.Sc',
                    'ba': 'B.A',
                    'ma': 'M.A'
                }
                
                degree = None
                for key, value in degree_keywords.items():
                    if key in resume_lower:
                        degree = value
                        break
                
                # Count pages
                with open(save_image_path, 'rb') as f:
                    from pdfminer3.pdfpage import PDFPage
                    pages = list(PDFPage.get_pages(f))
                    no_of_pages = len(pages)
                
                # Create resume_data structure
                resume_data = {
                    'name': name,
                    'email': email,
                    'mobile_number': phone,
                    'skills': detected_skills,
                    'no_of_pages': no_of_pages,
                    'degree': degree
                }
                
                st.success("Resume parsed successfully")
                print("DEBUG - Extracted resume data:", resume_data)
                
            except Exception as parse_error:
                st.error("Unable to parse the resume. Please ensure it's a valid PDF with text (not scanned image).")
                print(f"Resume parsing failed: {str(parse_error)}")
                import traceback
                print("ERROR:", traceback.format_exc())
                return
                
            if resume_data:
                
                ## Get the whole resume data into resume_text (if not already loaded)
                if 'resume_text' not in locals():
                    resume_text = pdf_reader(save_image_path)
                print("DEBUG - Resume text length:", len(resume_text) if resume_text else 0)

                ## Showing Analyzed data from (resume_data)
                st.markdown('''
                <div style="margin: 48px 0 28px 0;">
                    <h2 style="font-size: 1.875rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Resume Analysis
                    </h2>
                </div>
                ''', unsafe_allow_html=True)
                
                # Get name with fallback
                candidate_name = resume_data.get('name') or 'Candidate'
                st.markdown(f'''
                <div style="background: linear-gradient(145deg, #5E5CE6 0%, #BF5AF2 50%, #FF375F 100%); border-radius: 20px; padding: 28px; margin-bottom: 28px; position: relative; overflow: hidden; box-shadow: 0 0 30px rgba(94, 92, 230, 0.3);">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 50%; background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 100%); pointer-events: none;"></div>
                    <h3 style="color: white; font-weight: 600; margin: 0; font-size: 1.25rem;">Hello, {candidate_name}</h3>
                    <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0 0; font-size: 0.9375rem;">Here is what we found in your resume</p>
                </div>
                ''', unsafe_allow_html=True)
                
                st.markdown('''
                <div style="margin: 28px 0 16px 0;">
                    <h4 style="font-size: 1.125rem; font-weight: 600; color: #FFFFFF;">Basic Information</h4>
                </div>
                ''', unsafe_allow_html=True)
                
                # Check if any data was extracted
                has_data = any([
                    resume_data.get('name'),
                    resume_data.get('email'),
                    resume_data.get('mobile_number'),
                    resume_data.get('skills'),
                    resume_data.get('no_of_pages')
                ])
                
                if not has_data:
                    st.warning("Unable to extract information from your resume. This could be because:")
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
                
                ## Predicting Candidate Experience Level using Smart Detection
                no_of_pages = resume_data.get('no_of_pages') or 0
                resume_text = resume_text or ""  # Ensure resume_text is not None
                
                # Use the smart experience detection function
                exp_result = detect_experience_level(resume_text, no_of_pages)
                cand_level = exp_result['level']
                
                # Display experience level with Apple-style card
                st.markdown('''
                <div style="margin: 36px 0 16px 0;">
                    <h4 style="font-size: 1.125rem; font-weight: 600; color: #FFFFFF;">Experience Level</h4>
                </div>
                ''', unsafe_allow_html=True)
                
                if cand_level == "Experienced":
                    level_color = "#FF9F0A"
                    level_bg = "linear-gradient(145deg, #FF9F0A 0%, #FFCC00 50%, #FFD60A 100%)"
                    level_icon = ""
                elif cand_level == "Intermediate":
                    level_color = "#30D158"
                    level_bg = "linear-gradient(145deg, #30D158 0%, #32D74B 50%, #34C759 100%)"
                    level_icon = ""
                else:
                    level_color = "#0A84FF"
                    level_bg = "linear-gradient(145deg, #0A84FF 0%, #32ADE6 50%, #64D2FF 100%)"
                    level_icon = ""
                
                st.markdown(f'''
                <div style="background: {level_bg}; border-radius: 20px; padding: 28px; text-align: center; margin-bottom: 20px; position: relative; overflow: hidden; box-shadow: 0 0 30px rgba(10, 132, 255, 0.2);">
                    <div style="position: absolute; top: 0; left: 0; right: 0; height: 50%; background: linear-gradient(180deg, rgba(255,255,255,0.2) 0%, transparent 100%); pointer-events: none;"></div>
                    <h3 style="color: white; font-weight: 700; margin: 0 0 4px 0; font-size: 1.625rem;">{cand_level}</h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.875rem; font-weight: 500;">Detected experience level</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Show experience breakdown
                with st.expander("View Experience Analysis Details"):
                    details = exp_result['details']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Work History Analysis:**")
                        if details['years_mentioned'] > 0:
                            st.success(f"Years mentioned: {details['years_mentioned']} years")
                        else:
                            st.info("No explicit years of experience found")
                        
                        if details['work_duration_years'] > 0:
                            st.success(f"Work duration from dates: ~{details['work_duration_years']} years")
                        
                        if details['date_ranges_found']:
                            st.write("**Date ranges detected:**")
                            for start, end, duration in details['date_ranges_found'][:3]:
                                st.write(f"  - {start} - {end} ({duration} yr{'s' if duration > 1 else ''})")
                    
                    with col2:
                        st.markdown("**Education and Background:**")
                        if details['graduation_year']:
                            years_since = 2026 - details['graduation_year']
                            st.info(f"Graduation year: {details['graduation_year']} ({years_since} years ago)")
                        else:
                            st.info("Graduation year not detected")
                        
                        if details['has_internship']:
                            st.success("Internship experience detected")
                        else:
                            st.warning("No internship mentions found")
                        
                        st.write(f"**Job indicators found:** {details['job_count']}")
                    
                    st.markdown("---")
                    st.markdown(f"**Experience Score:** `{exp_result['score']}/100`")
                    st.caption("Score breakdown: Years mentioned (40pts) + Work duration (35pts) + Graduation factor (20pts) + Job count (15pts) + Internship (10pts)")


                ## Skills Analyzing and Recommendation
                st.markdown('''
                <div style="margin: 48px 0 20px 0;">
                    <h4 style="font-size: 1.125rem; font-weight: 600; color: #FFFFFF;">Skills Analysis and Recommendations</h4>
                </div>
                ''', unsafe_allow_html=True)
                
                ### Current Analyzed Skills
                current_skills = resume_data.get('skills') or []
                keywords = st_tags(label='### Your Current Skills',
                text='Skills detected from your resume',value=current_skills,key = '1  ')

                ### Keywords for Recommendations
                ds_keyword = ['tensorflow','keras','pytorch','machine learning','deep Learning','flask','streamlit']
                web_keyword = ['react', 'django', 'node jS', 'react js', 'php', 'laravel', 'magento', 'wordpress','javascript', 'angular js', 'C#', 'Asp.net', 'flask']
                android_keyword = ['android','android development','flutter','kotlin','xml','kivy']
                ios_keyword = ['ios','ios development','swift','cocoa','cocoa touch','xcode']
                uiux_keyword = ['ux','adobe xd','figma','zeplin','balsamiq','ui','prototyping','wireframes','storyframes','adobe photoshop','photoshop','editing','adobe illustrator','illustrator','adobe after effects','after effects','adobe premier pro','premier pro','adobe indesign','indesign','wireframe','solid','grasp','user research','user experience']
                cybersecurity_keyword = ['cybersecurity','cyber security','information security','network security','penetration testing','ethical hacking','siem','soc','security analyst','vulnerability assessment','malware analysis','incident response','firewall','ids','ips','cryptography','nist','iso 27001','ceh','cissp','oscp','kali linux','metasploit','burp suite','wireshark','nmap','owasp','threat intelligence','security operations','infosec']
                cloud_keyword = ['aws','amazon web services','azure','microsoft azure','gcp','google cloud','cloud computing','cloud engineer','cloudformation','lambda','ec2','s3','vpc','iam','cloud architect','sre','site reliability','openshift','helm','prometheus','grafana','cloud native','serverless','iaas','paas','saas']
                data_analyst_keyword = ['data analyst','data analysis','business analyst','business intelligence','bi analyst','tableau','power bi','powerbi','looker','metabase','data studio','sql','excel analytics','reporting','dashboards','etl','data warehouse','snowflake','redshift','bigquery','google analytics','mixpanel','amplitude','ab testing','a/b testing','statistical analysis','data mining']
                ml_ai_keyword = ['machine learning engineer','ml engineer','ai engineer','artificial intelligence','deep learning','neural network','nlp','natural language processing','computer vision','opencv','llm','large language model','gpt','bert','transformer','huggingface','langchain','rag','reinforcement learning','recommendation system','mlops','model deployment','feature engineering','scikit-learn','sklearn','xgboost','lightgbm','catboost']
                devops_keyword = ['devops','devops engineer','site reliability','sre','ci/cd','continuous integration','continuous deployment','jenkins','gitlab ci','github actions','circleci','docker','kubernetes','k8s','terraform','ansible','puppet','chef','infrastructure as code','iac','monitoring','logging','elk stack','grafana','prometheus','nagios','datadog','new relic','argocd','gitops']
                n_any = ['english','communication','writing', 'microsoft office', 'leadership','customer management', 'social media']
                ### Skill Recommendations Starts                
                recommended_skills = []
                reco_field = ''
                rec_course = ''

                ### condition starts to check skills from keywords and predict field
                for i in current_skills:
                
                    # Helper function to normalize skill names for comparison
                    def normalize_skill(skill):
                        """Normalize skill name for comparison"""
                        s = skill.lower().strip()
                        # Remove common suffixes/variations
                        s = s.replace('.js', '').replace('js', '').replace('.', '').strip()
                        # Common mappings
                        mappings = {
                            'react': ['react', 'reactjs', 'react js'],
                            'node': ['node', 'nodejs', 'node js'],
                            'angular': ['angular', 'angularjs', 'angular js'],
                            'vue': ['vue', 'vuejs', 'vue js'],
                            'javascript': ['javascript', 'js'],
                            'typescript': ['typescript', 'ts'],
                            'c#': ['c#', 'csharp', 'c sharp'],
                        }
                        for key, variants in mappings.items():
                            if s in variants or any(v in s for v in variants):
                                return key
                        return s
                    
                    def skills_match(user_skills, recommended):
                        """Check if user has the recommended skill (with normalization)"""
                        user_normalized = [normalize_skill(s) for s in user_skills]
                        # Handle both single skill string and list of skills
                        if isinstance(recommended, list):
                            recommended = recommended[0] if recommended else ''
                        rec_normalized = normalize_skill(recommended)
                        return rec_normalized in user_normalized or any(rec_normalized in u for u in user_normalized)
                    
                    #### Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        reco_field = 'Data Science'
                        st.success("** Our analysis says you are looking for Data Science Jobs.**")
                        recommended_skills = ['Data Visualization','Predictive Analysis','Statistical Modeling','Data Mining','Clustering & Classification','Data Analytics','Quantitative Analysis','Web Scraping','ML Algorithms','Keras','PyTorch','Probability','Scikit-learn','TensorFlow','Flask','Streamlit']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '2')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(ds_course)
                        break

                    #### Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        reco_field = 'Web Development'
                        st.success("** Our analysis says you are looking for Web Development Jobs **")
                        recommended_skills = ['React','Django','Node.js','PHP','Laravel','Magento','WordPress','JavaScript','Angular','Vue','C#','Flask','Express']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '3')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(web_course)
                        break

                    #### Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        reco_field = 'Android Development'
                        st.success("** Our analysis says you are looking for Android App Development Jobs **")
                        recommended_skills = ['Android','Flutter','Kotlin','XML','Java','Kivy','Git','SDK','SQLite','Firebase']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '4')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(android_course)
                        break

                    #### IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        reco_field = 'IOS Development'
                        st.success("** Our analysis says you are looking for IOS App Development Jobs **")
                        recommended_skills = ['iOS','Swift','Cocoa','Cocoa Touch','Xcode','Objective-C','SQLite','SwiftUI','UIKit','Core Data']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '5')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(ios_course)
                        break

                    #### Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        reco_field = 'UI-UX Development'
                        st.success("** Our analysis says you are looking for UI-UX Development Jobs **")
                        recommended_skills = ['UI Design','User Experience','Adobe XD','Figma','Sketch','Prototyping','Wireframes','Adobe Photoshop','Illustrator','After Effects','InDesign','User Research','Usability Testing']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '6')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(uiux_course)
                        break

                    #### Cyber Security Recommendation
                    elif i.lower() in cybersecurity_keyword:
                        print(i.lower())
                        reco_field = 'Cyber Security'
                        st.success("** Our analysis says you are looking for Cyber Security Jobs **")
                        recommended_skills = ['Network Security','Penetration Testing','SIEM','Incident Response','Vulnerability Assessment','Ethical Hacking','Firewall Management','Cryptography','Malware Analysis','Cloud Security','Python','Linux','OWASP','Threat Intelligence','Compliance (ISO 27001, NIST)']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '7')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(cybersecurity_course)
                        break

                    #### Cloud Computing Recommendation
                    elif i.lower() in cloud_keyword:
                        print(i.lower())
                        reco_field = 'Cloud Computing'
                        st.success("** Our analysis says you are looking for Cloud Computing Jobs **")
                        recommended_skills = ['AWS','Azure','GCP','Docker','Kubernetes','Terraform','Linux','CI/CD','Jenkins','Python','Networking','IAM','CloudFormation','Serverless','Microservices','Monitoring','Ansible','Git']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '8')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(cloud_course)
                        break

                    #### Data Analyst Recommendation
                    elif i.lower() in data_analyst_keyword:
                        print(i.lower())
                        reco_field = 'Data Analyst'
                        st.success("** Our analysis says you are looking for Data Analyst Jobs **")
                        recommended_skills = ['SQL','Python','Excel','Tableau','Power BI','Statistics','Data Visualization','ETL','Data Cleaning','Pandas','Google Analytics','A/B Testing','Storytelling','Business Intelligence','Data Warehousing']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '9')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(data_analyst_course)
                        break

                    #### Machine Learning / AI Recommendation
                    elif i.lower() in ml_ai_keyword:
                        print(i.lower())
                        reco_field = 'Machine Learning'
                        st.success("** Our analysis says you are looking for Machine Learning / AI Jobs **")
                        recommended_skills = ['Python','TensorFlow','PyTorch','Scikit-learn','Deep Learning','NLP','Computer Vision','MLOps','SQL','Statistics','Mathematics','Feature Engineering','Model Deployment','Docker','AWS/GCP ML Services','LLMs','Pandas','NumPy']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '10')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(ml_ai_course)
                        break

                    #### DevOps Recommendation
                    elif i.lower() in devops_keyword:
                        print(i.lower())
                        reco_field = 'DevOps'
                        st.success("** Our analysis says you are looking for DevOps Jobs **")
                        recommended_skills = ['Linux','Docker','Kubernetes','CI/CD','Jenkins','Terraform','AWS','Azure','Git','Python/Bash','Ansible','Monitoring','Prometheus','Grafana','GitOps','Infrastructure as Code','Networking','Security']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Recommended skills generated from System',value=recommended_skills,key = '11')
                        st.markdown('''<h5 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job</h5>''',unsafe_allow_html=True)
                        
                        #Skill Gap Analysis
                        st.markdown("---")
                        st.subheader("Skill Gap Analysis")
                        missing_skills = [skill for skill in recommended_skills if not skills_match(current_skills, skill)]
                        matching_skills = [skill for skill in recommended_skills if skills_match(current_skills, skill)]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Skills You Have", len(matching_skills))
                            if matching_skills:
                                with st.expander("View Matching Skills"):
                                    for skill in matching_skills:
                                        st.markdown(f"- {skill}")
                        
                        with col2:
                            st.metric("Skills to Learn", len(missing_skills))
                            if missing_skills:
                                with st.expander("View Missing Skills"):
                                    for skill in missing_skills:
                                        st.markdown(f"- {skill}")
                        
                        # Calculate skill match percentage
                        if recommended_skills:
                            skill_match_percentage = (len(matching_skills) / len(recommended_skills)) * 100
                            st.progress(skill_match_percentage / 100)
                            st.info(f"You match {skill_match_percentage:.1f}% of recommended skills for {reco_field}")
                        
                        # course recommendation
                        rec_course = course_recommender(devops_course)
                        break

                    #### For Not Any Recommendations
                    elif i.lower() in n_any:
                        print(i.lower())
                        reco_field = 'NA'
                        st.warning("** Currently our tool predicts and recommends for Data Science, Data Analyst, Machine Learning/AI, Web, Android, IOS, UI/UX, Cyber Security, Cloud Computing and DevOps**")
                        recommended_skills = ['No Recommendations']
                        recommended_keywords = st_tags(label='### Recommended skills for you.',
                        text='Currently No Recommendations',value=recommended_skills,key = '12')
                        st.markdown('''<h5 style='text-align: left; color: #092851;'>Maybe Available in Future Updates</h5>''',unsafe_allow_html=True)
                        # course recommendation
                        rec_course = "Sorry! Not Available for this Field"
                        break


                ##Resume Scorer &Resume Writing Tips
                st.markdown('''
                <div style="margin: 48px 0 20px 0;">
                    <h4 style="font-size: 1.125rem; font-weight: 600; color: #FFFFFF;">Resume Tips and Insights</h4>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.9375rem;">Suggestions to improve your resume quality</p>
                </div>
                ''', unsafe_allow_html=True)
                
                resume_score = 0
                resume_lower = resume_text.lower()  # Convert to lowercase for case-insensitive matching
                
                ### Predicting Whether these key points are added to the resume
                # Collect positives and negatives separately
                positives = []
                negatives = []
                
                if re.search(r'\b(objective|summary|profile|about\s*me)\b', resume_lower):
                    resume_score = resume_score + 6
                    positives.append("Objective/Summary")
                else:
                    negatives.append(("Career Objective", "It will give your career intention to the Recruiters"))

                if re.search(r'\b(education|school|college|university|degree|bachelor|master|b\.?tech|m\.?tech)\b', resume_lower):
                    resume_score = resume_score + 12
                    positives.append("Education Details")
                else:
                    negatives.append(("Education", "It will give your qualification level to the recruiter"))

                if re.search(r'\b(experience|work\s*experience|employment|work\s*history)\b', resume_lower):
                    resume_score = resume_score + 16
                    positives.append("Experience")
                else:
                    negatives.append(("Experience", "It will help you stand out from the crowd"))

                if re.search(r'\b(internship|internships|intern)\b', resume_lower):
                    resume_score = resume_score + 6
                    positives.append("Internships")
                else:
                    negatives.append(("Internships", "It will help you stand out from the crowd"))

                if re.search(r'\b(skills|skill|technical\s*skills|core\s*competencies)\b', resume_lower):
                    resume_score = resume_score + 7
                    positives.append("Skills")
                else:
                    negatives.append(("Skills", "It will help you a lot"))

                if re.search(r'\b(hobbies|hobby)\b', resume_lower):
                    resume_score = resume_score + 4
                    positives.append("Hobbies")
                else:
                    negatives.append(("Hobbies", "It shows your personality to the Recruiters"))

                if re.search(r'\b(interests|interest)\b', resume_lower):
                    resume_score = resume_score + 5
                    positives.append("Interests")
                else:
                    negatives.append(("Interests", "It shows your interest beyond the job"))

                if re.search(r'\b(achievements|achievement|accomplishments|awards)\b', resume_lower):
                    resume_score = resume_score + 13
                    positives.append("Achievements")
                else:
                    negatives.append(("Achievements", "It shows you are capable for the position"))

                if re.search(r'\b(certifications|certification|certified|certificate)\b', resume_lower):
                    resume_score = resume_score + 12
                    positives.append("Certifications")
                else:
                    negatives.append(("Certifications", "It shows your specialization for the position"))

                if re.search(r'\b(projects|project|portfolio)\b', resume_lower):
                    resume_score = resume_score + 19
                    positives.append("Projects")
                else:
                    negatives.append(("Projects", "It shows work related to the required position"))

                # Display in two columns - Positives on Left, Negatives on Right
                tips_col1, tips_col2 = st.columns(2)
                
                with tips_col1:
                    st.markdown('''
                    <div style="background: rgba(48, 209, 88, 0.1); border: 1px solid rgba(48, 209, 88, 0.3); border-radius: 16px; padding: 20px; height: 100%;">
                        <h5 style="color: #30D158; margin-bottom: 16px; font-size: 1rem; font-weight: 600;">What You Have</h5>
                    </div>
                    ''', unsafe_allow_html=True)
                    for item in positives:
                        st.markdown(f'''<p style="color: #30D158; margin: 8px 0; font-size: 0.9rem;">[+] {item}</p>''', unsafe_allow_html=True)
                
                with tips_col2:
                    st.markdown('''
                    <div style="background: rgba(255, 69, 58, 0.1); border: 1px solid rgba(255, 69, 58, 0.3); border-radius: 16px; padding: 20px; height: 100%;">
                        <h5 style="color: #FF453A; margin-bottom: 16px; font-size: 1rem; font-weight: 600;">What to Add</h5>
                    </div>
                    ''', unsafe_allow_html=True)
                    for item, reason in negatives:
                        st.markdown(f'''<p style="color: #FF453A; margin: 8px 0; font-size: 0.9rem;">[-] {item}</p>''', unsafe_allow_html=True)

                ## EnhancedResume Score Section with detailed breakdown
                st.markdown('''
                <div style="margin: 40px 0 16px 0;">
                    <h4 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF;">Resume Score</h4>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem;">Overall quality assessment based on content completeness</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Max possible score from sections: 6+12+16+6+7+4+5+13+12+19 = 100
                # Cap resume_score at 100
                resume_score = min(resume_score, 100)
                
                # Calculate overall score percentage
                max_score = 100
                score_percentage = (resume_score / max_score) * 100
                
                # Display score with gauge-like visualization
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(
                        """
                        <style>
                            .stProgress > div > div > div > div {
                                background-color: #30D158;
                            }
                        </style>""",
                        unsafe_allow_html=True,
                    )
                    
                    ### Score Bar
                    my_bar = st.progress(0)
                    score = 0
                    for percent_complete in range(int(score_percentage)):
                        score +=1
                        time.sleep(0.01)
                        my_bar.progress(percent_complete + 1)
                    
                    # Display score with color coding
                    if score_percentage >= 80:
                        score_color = "#30D158"
                        score_label = "Excellent"
                    elif score_percentage >= 60:
                        score_color = "#FF9F0A"
                        score_label = "Good"
                    elif score_percentage >= 40:
                        score_color = "#FFD60A"
                        score_label = "Average"
                    else:
                        score_color = "#d73b5c"
                        score_label = "Needs Improvement"
                    
                    st.markdown(f'''<h1 style='text-align: center; color: {score_color};'>{int(score_percentage)}%</h1>''', unsafe_allow_html=True)
                    st.markdown(f'''<h3 style='text-align: center; color: {score_color};'>{score_label}</h3>''', unsafe_allow_html=True)
                
                # Detailed score breakdown
                with st.expander("View Detailed Score Breakdown"):
                    breakdown_data = {
                        'Section': ['Objective/Summary', 'Education', 'Experience', 'Internships', 'Skills Section', 
                                   'Hobbies', 'Interests', 'Achievements', 'Certifications', 'Projects'],
                        'Points Earned': [
                            6 if re.search(r'\b(objective|summary|profile|about\s*me)\b', resume_lower) else 0,
                            12 if re.search(r'\b(education|school|college|university|degree|bachelor|master|b\.?tech|m\.?tech)\b', resume_lower) else 0,
                            16 if re.search(r'\b(experience|work\s*experience|employment|work\s*history)\b', resume_lower) else 0,
                            6 if re.search(r'\b(internship|internships|intern)\b', resume_lower) else 0,
                            7 if re.search(r'\b(skills|skill|technical\s*skills|core\s*competencies)\b', resume_lower) else 0,
                            4 if re.search(r'\b(hobbies|hobby)\b', resume_lower) else 0,
                            5 if re.search(r'\b(interests|interest)\b', resume_lower) else 0,
                            13 if re.search(r'\b(achievements|achievement|accomplishments|awards)\b', resume_lower) else 0,
                            12 if re.search(r'\b(certifications|certification|certified|certificate)\b', resume_lower) else 0,
                            19 if re.search(r'\b(projects|project|portfolio)\b', resume_lower) else 0,
                        ],
                        'Max Points': [6, 12, 16, 6, 7, 4, 5, 13, 12, 19]
                    }
                    breakdown_df = pd.DataFrame(breakdown_data)
                    breakdown_df['Status'] = breakdown_df.apply(lambda x: 'Yes' if x['Points Earned'] > 0 else 'No', axis=1)
                    st.dataframe(breakdown_df, use_container_width=True)
                    st.info(f"**Total Score: {int(resume_score)}/100** ({int(score_percentage)}%)")
                
                st.warning("** Note: This score is calculated based on the content and completeness of your Resume. **")

                # print(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data['name'], resume_data['email'], str(resume_score), timestamp, str(resume_data['no_of_pages']), reco_field, cand_level, str(resume_data['skills']), str(recommended_skills), str(rec_course), pdf_name)

                ## ============ DASHBOARD OVERVIEW ============
                st.markdown('''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Analysis Dashboard
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">A comprehensive view of your resume analysis results</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Dashboard metrics row
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.markdown(f"""
                    <div class='score-card blue'>
                        <div class='score-label'>Resume Score</div>
                        <div class='score-value'>{int(score_percentage)}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col2:
                    st.markdown(f"""
                    <div class='score-card purple'>
                        <div class='score-label'>Skills Found</div>
                        <div class='score-value'>{len(current_skills)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col3:
                    matched_count = len([s for s in recommended_skills if skills_match(current_skills, s)])
                    st.markdown(f"""
                    <div class='score-card green'>
                        <div class='score-label'>Skills Match</div>
                        <div class='score-value'>{matched_count}/{len(recommended_skills)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metric_col4:
                    st.markdown(f"""
                    <div class='score-card orange'>
                        <div class='score-label'>Level</div>
                        <div class='score-value' style='font-size: 1.5rem;'>{cand_level}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Visual Analysis Charts
                st.markdown('''
                <div style="margin: 32px 0 16px 0;">
                    <h4 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF;">Visual Analytics</h4>
                </div>
                ''', unsafe_allow_html=True)
                
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Skills Match Pie Chart
                    skills_matched = len([s for s in recommended_skills if skills_match(current_skills, s)])
                    skills_missing = len(recommended_skills) - skills_matched
                    
                    fig_skills = px.pie(
                        values=[skills_matched, skills_missing],
                        names=['Matched', 'To Learn'],
                        title='Skills Gap Analysis',
                        color_discrete_sequence=['#30D158', '#FF453A'],
                        hole=0.6
                    )
                    fig_skills.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter, -apple-system, sans-serif', color='#FFFFFF'),
                        showlegend=True,
                        legend=dict(orientation='h', yanchor='bottom', y=-0.2),
                        margin=dict(t=40, b=40, l=20, r=20)
                    )
                    st.plotly_chart(fig_skills, use_container_width=True)
                
                with chart_col2:
                    # Score Breakdown Bar Chart
                    score_sections = {
                        'Objective': 6 if re.search(r'\b(objective|summary|profile)\b', resume_lower) else 0,
                        'Education': 12 if re.search(r'\b(education|school|college|university)\b', resume_lower) else 0,
                        'Experience': 16 if re.search(r'\b(experience|work\s*experience)\b', resume_lower) else 0,
                        'Skills': 7 if re.search(r'\b(skills|skill)\b', resume_lower) else 0,
                        'Projects': 19 if re.search(r'\b(projects|project)\b', resume_lower) else 0,
                        'Certs': 12 if re.search(r'\b(certifications|certified)\b', resume_lower) else 0,
                    }
                    
                    fig_bar = px.bar(
                        x=list(score_sections.keys()),
                        y=list(score_sections.values()),
                        title='Section Scores',
                        labels={'x': '', 'y': 'Points'},
                        color_discrete_sequence=['#0A84FF']
                    )
                    fig_bar.update_traces(marker_color='#0A84FF')
                    fig_bar.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(family='Inter, -apple-system, sans-serif', color='#FFFFFF'),
                        showlegend=False,
                        margin=dict(t=40, b=40, l=20, r=20),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                #Quick Summary Cards
                st.markdown('''
                <div style="margin: 32px 0 16px 0;">
                    <h4 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF;">Quick Summary</h4>
                </div>
                ''', unsafe_allow_html=True)
                
                summary_col1, summary_col2 = st.columns(2)
                
                with summary_col1:
                    st.markdown(f"""
                    <div class='dashboard-card'>
                        <h4 style='color: #FFFFFF;'>Profile Summary</h4>
                        <ul style='color: #F2F2F7; list-style: none; padding: 0;'>
                            <li><strong>Name:</strong> {resume_data.get('name') or 'Not Found'}</li>
                            <li><strong>Email:</strong> {resume_data.get('email') or 'Not Found'}</li>
                            <li><strong>Pages:</strong> {resume_data.get('no_of_pages') or 'N/A'}</li>
                            <li><strong>Predicted Field:</strong> {reco_field}</li>
                            <li><strong>Experience Level:</strong> {cand_level}</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                with summary_col2:
                    skills_list = ', '.join(current_skills[:8]) + ('...' if len(current_skills) > 8 else '')
                    st.markdown(f"""
                    <div class='dashboard-card'>
                        <h4 style='color: #FFFFFF;'>Skills Overview</h4>
                        <ul style='color: #F2F2F7; list-style: none; padding: 0;'>
                            <li><strong>Detected Skills:</strong> {len(current_skills)}</li>
                            <li><strong>Recommended:</strong> {len(recommended_skills)}</li>
                            <li><strong>Matching:</strong> {matched_count} skills</li>
                            <li><strong>Gap:</strong> {len(recommended_skills) - matched_count} skills to learn</li>
                            <li><strong>Top Skills:</strong> {skills_list}</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                ## ============ END DASHBOARD ============

                ### Getting Current Date and Time
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date+'_'+cur_time)


                ## Calling insert_data to add all the data into user_data                
                insert_data(str(sec_token), str(ip_add), (host_name), (dev_user), (os_name_ver), (latlong), (city), (state), (country), (act_name), (act_mail), (act_mob), resume_data.get('name') or 'Unknown', resume_data.get('email') or 'Unknown', str(resume_score), timestamp, str(resume_data.get('no_of_pages') or 0), reco_field, cand_level, str(current_skills), str(recommended_skills), str(rec_course), pdf_name)

                ## AI-Powered Interview Questions
                st.markdown(f'''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Interview Preparation
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">AI-generated questions tailored for {reco_field} roles</p>
                </div>
                ''', unsafe_allow_html=True)
                
                # Generate interview questions based on field and experience level
                interview_questions = generate_interview_questions(reco_field, cand_level, current_skills)
                
                if interview_questions:
                    for idx, qa in enumerate(interview_questions, 1):
                        with st.expander(f"Question {idx}: {qa['question']}"):
                            st.markdown("**Suggested Answer:**")
                            st.write(qa['answer'])
                            if 'tips' in qa:
                                st.markdown("**Tips:**")
                                st.info(qa['tips'])
                
                ## Skill-Based Interview Questions (Based on Resume Skills)
                st.markdown('''
                <div style="margin: 32px 0 16px 0;">
                    <h4 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF;">Skill-Specific Questions</h4>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem;">Based on the skills detected in your resume</p>
                </div>
                ''', unsafe_allow_html=True)
                
                skill_based_questions = generate_resume_based_questions(current_skills, reco_field)
                
                if skill_based_questions:
                    for idx, sq in enumerate(skill_based_questions, 1):
                        with st.expander(f"{sq['skill']} - {sq['question'][:60]}..."):
                            st.markdown(f"**Skill:** `{sq['skill']}`")
                            st.markdown(f"**Question:** {sq['question']}")
                            st.markdown("**Answer:**")
                            st.info(sq['answer'])
                else:
                    st.info("Add more technical skills to your resume to get skill-specific interview questions!")
                
                ## Trending Skills Section
                st.markdown('''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Trending Skills 2026
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">Skills in high demand for your field</p>
                </div>
                ''', unsafe_allow_html=True)
                
                trending_skills = get_trending_skills(reco_field)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("""
                    <div class='dashboard-card' style='border-top: 4px solid #ff3b30;'>
                        <h4 style='color: #ff3b30; font-weight: 600; margin-bottom: 4px;'>Hot Skills</h4>
                        <p style='color: rgba(235, 235, 245, 0.6); font-size: 0.8rem; margin-bottom: 16px;'>High demand right now</p>
                    </div>
                    """, unsafe_allow_html=True)
                    for skill in trending_skills['hot']:
                        if skills_match(current_skills, skill):
                            st.success(f"{skill}")
                        else:
                            st.warning(f"{skill}")
                
                with col2:
                    st.markdown("""
                    <div class='dashboard-card' style='border-top: 4px solid #0071e3;'>
                        <h4 style='color: #0071e3; font-weight: 600; margin-bottom: 4px;'>Growing Skills</h4>
                        <p style='color: rgba(235, 235, 245, 0.6); font-size: 0.8rem; margin-bottom: 16px;'>Rising in demand</p>
                    </div>
                    """, unsafe_allow_html=True)
                    for skill in trending_skills['growing']:
                        if skills_match(current_skills, skill):
                            st.success(f"{skill}")
                        else:
                            st.info(f"{skill}")
                
                with col3:
                    st.markdown("""
                    <div class='dashboard-card' style='border-top: 4px solid #34c759;'>
                        <h4 style='color: #34c759; font-weight: 600; margin-bottom: 4px;'>Essential Skills</h4>
                        <p style='color: rgba(235, 235, 245, 0.6); font-size: 0.8rem; margin-bottom: 16px;'>Must-have foundations</p>
                    </div>
                    """, unsafe_allow_html=True)
                    for skill in trending_skills['essential']:
                        if skills_match(current_skills, skill):
                            st.success(f"{skill}")
                        else:
                            st.error(f"{skill}")
                
                ## Job Recommendations
                st.markdown('''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Job Opportunities
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">Roles that match your skills and experience level</p>
                </div>
                ''', unsafe_allow_html=True)
                
                job_recommendations = generate_job_recommendations(reco_field, cand_level, current_skills)
                
                if job_recommendations:
                    cols = st.columns(2)
                    for idx, job in enumerate(job_recommendations):
                        job_urls = get_job_search_urls(job['title'])
                        with cols[idx % 2]:
                            st.markdown(f"""
                            <div class='job-card'>
                                <h3 style='color: #FFFFFF; margin-bottom: 16px; font-size: 1.25rem; font-weight: 600;'>{job['title']}</h3>
                                <div style='display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap;'>
                                    <span style='background: rgba(0, 113, 227, 0.1); color: #0071e3; padding: 6px 14px; border-radius: 980px; font-size: 0.8rem; font-weight: 500;'>{job['level']}</span>
                                    <span style='background: rgba(52, 199, 89, 0.1); color: #34c759; padding: 6px 14px; border-radius: 980px; font-size: 0.8rem; font-weight: 500;'>{job['salary']}</span>
                                </div>
                                <p style='color: rgba(235, 235, 245, 0.6); margin: 0 0 12px 0; font-size: 0.9rem; line-height: 1.5;'>{job['description']}</p>
                                <p style='color: #FFFFFF; font-size: 0.85rem; margin-bottom: 16px;'><strong>Skills:</strong> {', '.join(job['skills'][:5])}</p>
                                <div style='display: flex; flex-wrap: wrap; gap: 8px; padding-top: 16px; border-top: 1px solid rgba(0,0,0,0.06);'>
                                    <a href='{job_urls['naukri']}' target='_blank' class='job-platform-btn'>Naukri</a>
                                    <a href='{job_urls['linkedin']}' target='_blank' class='job-platform-btn'>LinkedIn</a>
                                    <a href='{job_urls['indeed']}' target='_blank' class='job-platform-btn'>Indeed</a>
                                    <a href='{job_urls['glassdoor']}' target='_blank' class='job-platform-btn'>Glassdoor</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                ## Recommending Resume Writing Video
                st.markdown('''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Resume Writing Tips
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">Expert advice to perfect your resume</p>
                </div>
                ''', unsafe_allow_html=True)
                resume_vid = random.choice(resume_videos)
                st.video(resume_vid)

                ## RecommendingInterview Preparation Video
                st.markdown('''
                <div style="margin: 48px 0 24px 0;">
                    <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; letter-spacing: -0.02em;">Interview Mastery
                    </h2>
                    <p style="color: rgba(235, 235, 245, 0.6); font-size: 1rem;">Tips to ace your interviews</p>
                </div>
                ''', unsafe_allow_html=True)
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
    st.markdown('''
    <div style="text-align: center; padding: 40px 0 32px 0;">
        <h1 style="font-size: 2.5rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em; margin-bottom: 12px;">Share Your Feedback
        </h1>
        <p style="font-size: 1.15rem; color: rgba(235, 235, 245, 0.6); font-weight: 400; max-width: 500px; margin: 0 auto;">Help us improve by sharing your experience
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # timestamp 
    ts = time.time()
    cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    timestamp = str(cur_date+'_'+cur_time)

    # Centered feedback form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("my_form"):
            feed_name = st.text_input('Your Name', placeholder="Enter your name")
            feed_email = st.text_input('Email Address', placeholder="your@email.com")
            feed_score = st.slider('Rate Your Experience', 1, 5, 4)
            comments = st.text_area('Your Feedback', placeholder="Share your thoughts with us...")
            Timestamp = timestamp        
            submitted = st.form_submit_button(" Submit Feedback")
            if submitted:
                if feed_name and feed_email:
                    insertf_data(feed_name, feed_email, feed_score, comments, Timestamp)    
                    st.success(" Thank you! Your feedback has been recorded.") 
                else:
                    st.warning("Please fill in all required fields")

    # Display feedback statistics
    if DB_AVAILABLE:
        st.markdown('''
        <div style="margin: 48px 0 24px 0;">
            <h3 style="font-size: 1.5rem; font-weight: 600; color: #FFFFFF;">Community Ratings</h3>
        </div>
        ''', unsafe_allow_html=True)
        
        feedback_data = list(feedback_collection.find({}))
        if feedback_data:
            feedback_df = pd.DataFrame(feedback_data)
            if 'feed_score' in feedback_df.columns:
                labels = feedback_df.feed_score.unique()
                values = feedback_df.feed_score.value_counts()
                fig = px.pie(
                    values=values, 
                    names=labels, 
                    title="User Ratings Distribution", 
                    color_discrete_sequence=['#0071e3', '#34c759', '#ff9500', '#af52de', '#ff3b30'],
                    hole=0.5
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Inter, -apple-system, sans-serif', color='#FFFFFF'),
                    margin=dict(t=40, b=40, l=20, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('''
            <div style="margin: 32px 0 16px 0;">
                <h4 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF;">Recent Comments</h4>
            </div>
            ''', unsafe_allow_html=True)
            
            if 'feed_name' in feedback_df.columns and 'comments' in feedback_df.columns:
                comment_df = feedback_df[['feed_name', 'comments']].copy()
                comment_df.columns = ['User', 'Comment']
                st.dataframe(comment_df, use_container_width=True)
        else:
            st.info("No feedback available yet. Be the first to share!")
    else:
        st.warning("Database not available")

def show_about():
    st.markdown('''
    <div style="text-align: center; padding: 60px 0 40px 0;">
        <h1 style="font-size: 3rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.03em; margin-bottom: 16px;">About <span style="background: linear-gradient(90deg, #0071e3, #af52de, #ff9500); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">skilledge</span>
        </h1>
        <p style="font-size: 1.25rem; color: rgba(235, 235, 245, 0.6); font-weight: 400; max-width: 600px; margin: 0 auto;">AI-powered resume analysis that helps you stand out in your job search
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # Features Grid
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Smart Resume Parsing
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Advanced NLP algorithms extract and analyze key information from your resume, identifying skills, experience, and qualifications with precision.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Comprehensive Analysis
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Get detailed insights into your resume's strengths and areas for improvement with our intelligent scoring system.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Skill Gap Analysis
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Discover which skills you need to learn based on your target career path and current market demands.
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Job Matching
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Receive personalized job recommendations across multiple platforms based on your skills and experience level.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">AI Interview Prep
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Practice with AI-generated interview questions tailored to your specific skills and target job roles.
            </p>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('''
        <div class="dashboard-card">
            <h3 style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Course Recommendations
            </h3>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; line-height: 1.6;">Get curated course suggestions from top platforms to upskill and stay competitive in your field.
            </p>
        </div>
        ''', unsafe_allow_html=True)
    
    # How it works section
    st.markdown('''
    <div style="margin: 48px 0 24px 0;">
        <h2 style="font-size: 2rem; font-weight: 600; color: #FFFFFF; text-align: center; margin-bottom: 32px;">How It Works
        </h2>
    </div>
    ''', unsafe_allow_html=True)
    
    step_col1, step_col2, step_col3, step_col4 = st.columns(4)
    
    with step_col1:
        st.markdown('''
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;"></div>
            <h4 style="color: #FFFFFF; font-weight: 600; margin-bottom: 8px;">Upload</h4>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.85rem;">Upload your resume in PDF format</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with step_col2:
        st.markdown('''
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;"></div>
            <h4 style="color: #FFFFFF; font-weight: 600; margin-bottom: 8px;">Analyze</h4>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.85rem;">AI analyzes your resume</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with step_col3:
        st.markdown('''
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;"></div>
            <h4 style="color: #FFFFFF; font-weight: 600; margin-bottom: 8px;">Insights</h4>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.85rem;">Get personalized insights</p>
        </div>
        ''', unsafe_allow_html=True)
    
    with step_col4:
        st.markdown('''
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 2.5rem; margin-bottom: 12px;"></div>
            <h4 style="color: #FFFFFF; font-weight: 600; margin-bottom: 8px;">Improve</h4>
            <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.85rem;">Apply recommendations</p>
        </div>
        ''', unsafe_allow_html=True)
    
    # Technology stack
    st.markdown('''
    <div style="margin: 48px 0 24px 0; text-align: center;">
        <h3 style="font-size: 1.5rem; font-weight: 600; color: #FFFFFF; margin-bottom: 16px;">Built With Modern Technology
        </h3>
        <p style="color: rgba(235, 235, 245, 0.6); font-size: 0.95rem; max-width: 500px; margin: 0 auto;">Powered by Python, Streamlit, spaCy NLP, MongoDB, and advanced machine learning algorithms
        </p>
    </div>
    ''', unsafe_allow_html=True)

# Calling the main (run()) function to make the whole process run
if __name__ == "__main__":
    run()




