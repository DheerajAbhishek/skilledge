# AI Resume Analyzer - Project Reference

## Overview
A tool which parses information from a resume using natural language processing and finds the keywords, cluster them onto sectors based on their keywords. And lastly show recommendations, predictions, analytics to the applicant / recruiter based on keyword matching.

---

## Scope 😲

1. **Structured Data Export**: Get all resume data into a structured tabular format and CSV, enabling organizations to use data for analytics purposes

2. **Resume Improvement**: By providing recommendations, predictions and overall score, users can improve their resume and keep testing it on the tool

3. **User Engagement**: Increase traffic to the tool through user section features

4. **College Integration**: Can be used by colleges to get insights of students and their resumes before placements

5. **Role Analytics**: Get analytics for roles which users are mostly looking for

6. **Feedback Loop**: Improve the tool by gathering user feedback

---

## Tech Stack 🍻

### Frontend
- **Streamlit** - Python-based web framework for data applications

### Backend
- **Python 3.9.12**
- **Natural Language Processing (NLP)**
- **pyresparser** - Resume parsing library
- **spaCy** - NLP library

### Database
- **MySQL** - Relational database for storing user and resume data

### Key Modules
- `pymysql` - MySQL database connector
- `streamlit` - Web interface
- `spacy` - NLP processing
- `pyresparser` - Resume parsing
- `pandas` - Data manipulation
- `plotly` - Data visualization

---

## Features 🤦‍♂️

### Client Side Features

#### Data Extraction
- **Fetching Location and Miscellaneous Data**
- **Using Parsing Techniques to fetch:**
  - Basic Info
  - Skills
  - Keywords

#### Recommendations & Analytics
Using logical programs, the tool provides:
- Skills that can be added
- Predicted job role
- Course and certificates recommendations
- Resume tips and ideas
- Overall Score
- Interview & Resume tip videos

### Admin Side Features

#### Data Management
- Get all applicant's data into tabular format
- Download user's data into CSV file
- View all saved uploaded PDFs in Uploaded Resume folder
- Get user feedback and ratings

#### Analytics & Visualization
**Pie Charts for:**
- Ratings
- Predicted field/roles
- Experience level
- Resume score
- User count
- City
- State
- Country

#### Feedback System
- Form filling
- Rating from 1-5
- Show overall ratings pie chart
- Past user comments history

---

## Requirements 😅

Have these things installed to make your process smooth:

1. **Python (3.9.12)** - [Download](https://www.python.org/downloads/release/python-3912/)
2. **MySQL** - [Download](https://www.mysql.com/downloads/)
3. **Visual Studio Code** (Preferred Code Editor) - [Download](https://code.visualstudio.com/Download)
4. **Visual Studio Build Tools for C++** - [Download](https://aka.ms/vs/17/release/vs_BuildTools.exe)

---

## Setup & Installation 👀

### Step 1: Clone the Repository

```bash
git clone https://github.com/deepakpadhi986/AI-Resume-Analyzer.git
```

Or download the code file manually.

### Step 2: Create Virtual Environment

Open your command prompt and change your project directory to AI-Resume-Analyzer:

```bash
cd AI-Resume-Analyzer
python -m venv venvapp
cd venvapp/Scripts
activate
```

### Step 3: Install Dependencies

```bash
cd ../..
cd App
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 4: Database Setup

1. Create a MySQL database named `cv`
2. Update database credentials in `App.py`:

```python
# Location: AI-Resume-Analyzer/App/App.py (Line 95)
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root@MySQL4admin',  # Change this to your MySQL password
    db='cv'
)
```

### Step 5: Fix Resume Parser

Go to `venvapp\Lib\site-packages\pyresparser` folder and replace the `resume_parser.py` with the `resume_parser.py` provided in the pyresparser folder of the project.

### Step 6: Run the Application

Make sure your virtual environment is activated and working directory is inside App folder:

```bash
streamlit run App.py
```

**Congratulations! 🥳😱 Your setup and installation is finished 😵🤯**

---

## Known Issues 🤪

### GeocoderUnavailable Error
If you encounter `GeocoderUnavailable` error, check:
- Your internet connection
- Network speed

### Installation Issues 🤧
- Check out the installation video (if available)
- Feel free to send an email for support

---

## Usage

After the setup, the tool works automatically:
1. Upload a resume
2. See the magic happen!

**Try first with the resume uploaded in `Uploaded_Resumes` folder**

### Admin Access
- **Admin UserID**: `admin`
- **Admin Password**: `admin@resume-analyzer`

---

## Roadmap 🛵

- ✅ Predict user experience level
- ✅ Add resume scoring criteria for skills and projects
- ✅ Added fields and recommendations for web, android, iOS, data science
- ⬜ Add more fields for other roles and their recommendations
- ⬜ Fetch more details from user's resume
- ⬜ View individual user details

---

## Contributing 🤘

Pull requests are welcome!

For major changes, please open an issue first to discuss what you would like to change.

---

## Acknowledgement 🤗

- **Dr Bright** - The Full Stack Data Scientist BootCamp
- **Resume Parser with Natural Language Processing**
- **pyresparser** library

---

## Additional Resources

- **Synopsis**: Attached with the project
- **Full Report**: Email for FREE copy

---

## Project Structure

```
AI-Resume-Analyzer/
├── App/
│   ├── App.py                 # Main application file
│   ├── requirements.txt       # Python dependencies
│   └── ...
├── Uploaded_Resumes/         # Storage for uploaded resumes
├── pyresparser/              # Custom resume parser
│   └── resume_parser.py      # Modified parser file
└── venvapp/                  # Virtual environment (after setup)
```

---

## Key Features Summary

### For Job Seekers
- Resume analysis and scoring
- Skill recommendations
- Job role predictions
- Course suggestions
- Resume improvement tips
- Interview preparation videos

### For Recruiters
- Bulk resume analysis
- Data export to CSV
- Analytics dashboard
- Candidate insights
- Resume comparison

### For Colleges
- Student resume insights
- Placement readiness assessment
- Skill gap analysis
- Trend analytics

---

## Security Notes

⚠️ **Important**: Change default database credentials before deployment
⚠️ **Important**: Change admin password in production environment

---

## License

Please refer to the original repository for license information.

---

## Contact & Support

For issues, questions, or contributions, please refer to the GitHub repository:
https://github.com/deepakpadhi986/AI-Resume-Analyzer

---

*Last Updated: January 26, 2026*
