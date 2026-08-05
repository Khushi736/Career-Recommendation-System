import os
import secrets
import smtplib
import sqlite3
import PyPDF2
import datetime
from email.message import EmailMessage
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for, g
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from model import Course
from extensions import db
from model import User, Profile  # Assuming your class is named 'User' and not 'Users'


from flask import render_template, request, flash, current_app # Added current_app


# Load environment variables from .env file
load_dotenv()

# Ensure these are defined in your model.py
try:
    from model import predict_career, ats_score
except ImportError:
    # Fallback for testing if model.py isn't present
    def predict_career(s): return "Software Engineer"
    def ats_score(f, r): return {"score": 85}

# ==============================================================
# 1. CREATE THE APP (This MUST happen before any app.config)
# ==============================================================
app = Flask(__name__)

# ==============================================================
# 2. CONFIGURE THE APP
# ==============================================================
app.secret_key = os.environ.get("SECRET_KEY", "your_super_secret_key")

# Get the exact path to the folder where app.py lives
basedir = os.path.abspath(os.path.dirname(__file__))

# Force SQLAlchemy to look in this exact folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==============================================================
# 3. INITIALIZE THE DATABASE
# ==============================================================
db.init_app(app)

# ==============================================================
# 4. OTHER CONFIGURATION
# ==============================================================
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Debug print for environment check
print(f"DEBUG - EMAIL_USER is: {os.environ.get('EMAIL_USER')}")
# import datetime
# import os
# import secrets
# import smtplib
# import sqlite3
# from email.message import EmailMessage
# from dotenv import load_dotenv
# import datetime
# import PyPDF2
# from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import login_required, current_user # Assuming you are using flask_login

# from model import Category, Course
# from extensions import db

# # ... other imports like os, secrets, etc.

# # Load environment variables from .env file
# load_dotenv()

# from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for, g
# from werkzeug.utils import secure_filename
# from werkzeug.security import generate_password_hash, check_password_hash

# import os

# # Get the exact path to the folder where app.py lives
# basedir = os.path.abspath(os.path.dirname(__file__))

# # Force SQLAlchemy to look in this exact folder, NOT the instance folder
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

# # Ensure these are defined in your model.py
# try:
#     from model import predict_career, ats_score
# except ImportError:
#     # Fallback for testing if model.py isn't present
#     def predict_career(s): return "Software Engineer"
#     def ats_score(f, r): return {"score": 85}

# app = Flask(__name__)
# app.secret_key = os.environ.get("SECRET_KEY", "career_ai_secret_fallback")

# app.secret_key = 'your_super_secret_key' # Needed for flash messages
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db' # Point to your SQLite file
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db.init_app(app)

# # Configuration
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# # Debug print for environment check
# print(f"DEBUG - EMAIL_USER is: {os.environ.get('EMAIL_USER')}")

# ==========================================
# DATABASE CONNECTION MANAGEMENT
# ==========================================
def get_db():
    """Opens a new database connection for the current request context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect("database.db")
        db.row_factory = sqlite3.Row  # Allows accessing columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ==========================================
# PUBLIC ROUTES
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")

# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         name = request.form.get("name", "").strip()
#         email = request.form.get("email", "").strip()
#         password = request.form.get("password", "")

#         if not name or not email or not password:
#             return "Missing required fields!", 400

#         db = get_db()
#         existing = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
#         if existing:
#             return "User already exists! Please login."

#         hashed_pw = generate_password_hash(password)
        
#         # Added 'active' as default status
#         db.execute(
#             "INSERT INTO users(name, email, password, status) VALUES (?, ?, ?, ?)",
#             (name, email, hashed_pw, 'active')
#         )
#         db.commit()
#         return redirect(url_for("login"))

#     return render_template("register.html")





# --- Setup for File Uploads ---
# Define where you want to save the uploaded resumes
# UPLOAD_FOLDER = 'static/uploads/resumes'
# # Create the folder if it doesn't exist yet
# os.makedirs(UPLOAD_FOLDER, exist_ok=True) 
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Your Updated Route ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 1. Get all text inputs from the form
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        mobile = request.form.get("mobile", "").strip()
        
        # 2. Get the uploaded file
        resume_file = request.files.get("resume")

        # 3. Basic Validation
        if not name or not email or not password or not mobile:
            flash("Missing required fields!", "error")
            return render_template("register.html")
            
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return render_template("register.html")

        # 4. Check if user already exists (Triggers SweetAlert Popup)
        db = get_db()
        existing = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            # Flash the error and reload the page to trigger the popup
            flash("User already exists! Please login.", "error")
            return render_template("register.html")

        # 5. Handle the Resume Upload
        resume_filename = None
        if resume_file and resume_file.filename != '':
            if allowed_file(resume_file.filename):
                # secure_filename removes spaces and dangerous characters from the file name
                filename = secure_filename(resume_file.filename)
                resume_path = os.path.join(UPLOAD_FOLDER, filename)
                resume_file.save(resume_path) # Save file to your server
                resume_filename = filename    # We will store this filename in the database
            else:
                flash("Invalid file format. Please upload a PDF, DOC, or DOCX.", "error")
                return render_template("register.html")
        else:
            flash("Please upload your resume.", "error")
            return render_template("register.html")

        # 6. Hash password and Save to Database
        hashed_pw = generate_password_hash(password)
        
        # Note: Ensure your database table 'users' has 'mobile' and 'resume' columns!
        db.execute(
            "INSERT INTO users(name, email, password, mobile, resume, status) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, hashed_pw, mobile, resume_filename, 'active')
        )
        db.commit()
        
        # 7. Success flash and redirect
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session["user"] = user['name']
            session["user_id"] = user['id']
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials!"

    return render_template("login.html")



# Make sure 'session' is imported at the top of your file


@app.route('/logout')
def logout():
    # This removes all user data from the current browser session
    session.clear() 
    
    # Send a success message to the login page (using your SweetAlert setup)
    flash("You have been successfully logged out.", "success")
    
    # Redirect the user back to the login page
    return redirect(url_for('login'))


# Helper function to extract text from the PDF CV
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        text += content
    except Exception as e:
        print(f"Error reading CV: {e}")
    return text.lower()





import os
import sqlite3
from flask import session, redirect, url_for, render_template


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    

    current_user_id = session["user_id"]
    username = session.get("user", "User")
    # username = session["user"]
    # Use a dictionary to track unique roles and keep the best match
    unique_recommendations = {}
    user_data = {"name": username, "profile_pic": None}

    try:
        conn_user = sqlite3.connect('database.db')
        conn_user.row_factory = sqlite3.Row
        cursor_user = conn_user.cursor()

        cursor_user.execute("SELECT resume, profile_pic FROM users WHERE id = ?", (current_user_id,))
        user_row = cursor_user.fetchone()
        
        if user_row:
            user_data["profile_pic"] = user_row['profile_pic']
            resume_filename = user_row['resume']
            
            if resume_filename:
                cv_full_path = resume_filename if resume_filename.startswith('uploads/') else os.path.join('uploads', resume_filename)

                if os.path.exists(cv_full_path):
                    cv_text = extract_text_from_pdf(cv_full_path)
                    
                    conn_career = sqlite3.connect('career_database.db')
                    conn_career.row_factory = sqlite3.Row
                    cursor_career = conn_career.cursor()

                    # Fetching from career_skills (role, skills)
                    cursor_career.execute("SELECT role, skills FROM career_skills")
                    trained_roles = cursor_career.fetchall()

                    for role in trained_roles:
                        role_title = role['role']
                        skills_list = [s.strip().lower() for s in role['skills'].split(',')]
                        match_count = sum(1 for skill in skills_list if skill in cv_text)
                        
                        if match_count > 0:
                            percentage = int((match_count / len(skills_list)) * 100)
                            
                            # Standard Roadmap fallback
                            # roadmap_data = ["Complete projects", "Get Certified"]
                            
                            # DUPLICATE FIX: 
                            # If role isn't in dict, OR this version has a better match % than the stored one
                            if role_title not in unique_recommendations or percentage > unique_recommendations[role_title]['match_percentage']:
                                unique_recommendations[role_title] = {
                                    "title": role_title,
                                    "match_percentage": percentage,
                                    # "roadmap": roadmap_data
                                }
                    
                    conn_career.close()

        conn_user.close()

    except sqlite3.OperationalError as e:
        return f"Database Error: {e}"

    # Convert dictionary back to a sorted list (Top 3)
    recommendations = sorted(unique_recommendations.values(), key=lambda x: x['match_percentage'], reverse=True)[:3]

    return render_template("dashboard.html", 
                           current_user=user_data, 
                           recommended_careers=recommendations)


import os
import json
import PyPDF2
import requests
from dotenv import load_dotenv
from flask import request, jsonify, session, render_template, redirect, url_for, flash, current_app
from model import db, User, Profile
from werkzeug.utils import secure_filename
import time

# Load environment variables
load_dotenv()

# Define UPLOAD_FOLDER globally
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Get API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    print(f"✅ API Key loaded: {GEMINI_API_KEY[:15]}...")
else:
    print("❌ GEMINI_API_KEY not found in environment variables")

def extract_cv_with_gemini(filepath, retry_count=0):
    """Extract CV data using Gemini REST API with proper retry logic"""
    try:
        # Extract text from PDF
        extracted_text = ""
        print(f"📄 Reading PDF from: {filepath}")
        
        with open(filepath, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            print(f"📄 Number of pages: {len(reader.pages)}")
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text
                    print(f"✅ Page {page_num + 1}: {len(page_text)} characters")
                else:
                    print(f"⚠️ Page {page_num + 1}: No text extracted")
        
        if not extracted_text:
            print("❌ No text extracted from PDF")
            return None
        
        print(f"📝 Total extracted text length: {len(extracted_text)}")
        
        # AI Prompt
        prompt = f"""
        Parse this resume and return ONLY valid JSON. No markdown, no extra text, no explanation.
        
        Required JSON format:
        {{  
            "about": "A professional summary or bio about the person (2-3 sentences)",
            "skills": ["skill1", "skill2", "skill3"],
            "interests": ["interest1", "interest2"],
            "languages":["language1", "language2"],
            
            "work_experience": [
                {{
                    "company": "Company Name",
                    "role": "Job Title/Role",
                    "duration": "Start - End Date",
                    "description": "Brief description of responsibilities and achievements"
                }}
            ],

            "education": [
                "Degree Name from Institution Name, Year",
                "Another Degree from Institution Name, Year"
            ],
            
            "certifications": [
                "Certification 1 Name - Issuing Authority (Year)",
                "Certification 2 Name - Issuing Authority (Year)"
            ],
           
            "projects": [
                {{
                    "title": "Project Title",
                    "technologies": "Comma separated technologies used",
                    "description": "Brief description of the project",
                    "link": "Project URL if available, otherwise empty string"
                }}
            ],
            "achievements": ["Achievement 1", "Achievement 2"],
            "linkedin_url": "linkedin profile url if found in resume, otherwise empty string",
            "github_url": "github or portfolio url if found, otherwise empty string"
        }}
        
        Resume Text:
        {extracted_text[:8000]}
        """
        
        # Use the working model
        API_KEY = os.getenv('GEMINI_API_KEY')
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        print("🤖 Calling Gemini API...")
        response = requests.post(url, json=payload, timeout=60)
        
        # Handle rate limiting with retry
        if response.status_code == 429:
            error_data = response.json()
            retry_delay = 43  # Default fallback
            
            # Try to get the retry delay from response
            if 'error' in error_data and 'details' in error_data['error']:
                for detail in error_data['error']['details']:
                    if 'retryDelay' in detail:
                        # Parse retry delay (format: "43s")
                        delay_str = detail['retryDelay']
                        retry_delay = int(delay_str.replace('s', ''))
                        break
            
            if retry_count < 2:  # Retry up to 2 times
                print(f"⚠️ Rate limited. Waiting {retry_delay} seconds before retry...")
                print(f"⏳ Retry attempt {retry_count + 1}/2")
                time.sleep(retry_delay)
                return extract_cv_with_gemini(filepath, retry_count + 1)
            else:
                print(f"❌ Max retries reached. Using fallback data.")
                return get_fallback_cv_data(extracted_text)
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            if retry_count < 1:
                print("⚠️ Retrying once more...")
                time.sleep(5)
                return extract_cv_with_gemini(filepath, retry_count + 1)
            return None
        
        result = response.json()
        
        # Extract text from response
        if 'candidates' in result and len(result['candidates']) > 0:
            response_text = result['candidates'][0]['content']['parts'][0]['text']
            print(f"🤖 Response received (length: {len(response_text)})")
        else:
            print("❌ No response from API")
            return None
        
        # Clean response - remove markdown code blocks
        clean_response = response_text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()
        
        # Parse JSON
        parsed_data = json.loads(clean_response)
        print(f"✅ Successfully parsed CV data")
        print(f"📊 Extracted: {list(parsed_data.keys())}")

        # Ensure 'about' field exists
        if 'about' not in parsed_data or not parsed_data['about']:
            # Create a fallback about section
            name = parsed_data.get('name', 'The candidate')
            skills = ', '.join(parsed_data.get('skills', [])[:3])
            parsed_data['about'] = f"{name} is a professional with skills in {skills}. Seeking new opportunities in their field."
            print("⚠️ Created fallback about section")
        
        print(f"✅ About extracted: {parsed_data['about'][:100]}...")
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
        return get_fallback_cv_data(extracted_text if 'extracted_text' in locals() else "")
    except Exception as e:
        print(f"❌ CV extraction error: {e}")
        import traceback
        traceback.print_exc()
        return get_fallback_cv_data(extracted_text if 'extracted_text' in locals() else "")

def get_fallback_cv_data(extracted_text=""):
    """Provide fallback data when API fails"""
    print("🔄 Using fallback CV data")
    
    # Try to extract name from first line of resume
    lines = extracted_text.split('\n') if extracted_text else []
    name = "Professional"
    for line in lines[:5]:
        if line.strip() and len(line.strip()) < 50:
            name = line.strip()
            break
    
    return {
        "about": f"{name} is a dedicated professional with strong skills in business operations and management. Experienced in coordinating between departments and handling operational tasks efficiently.",
        "skills": ["Communication", "Teamwork", "Time Management", "Critical Thinking", "MS Excel", "MS PowerPoint", "Problem Solving"],
        "interests": ["Business Strategy", "Operations Management", "Leadership Development", "Data Analysis"],
        "languages": ["English", "Hindi"],
        "work_experience": [
            {
                "company": "Business Organization",
                "role": "Operations Intern",
                "duration": "Recent",
                "description": "Coordinated between departments, prepared reports, and supported operational activities."
            }
        ],
        "education": [
            "Bachelor's Degree in Business Administration",
            "Higher Secondary Education"
        ],
        "certifications": [
            "Business Management Certification",
            "Professional Development Certificate"
        ],
        "projects": [
            {
                "title": "Business Operations Project",
                "technologies": "MS Office, Data Analysis",
                "description": "Analyzed business processes and suggested improvements.",
                "link": ""
            }
        ],
        "achievements": [
            "Recognized for outstanding performance in team projects",
            "Successfully completed management training program"
        ],
        "linkedin_url": "",
        "github_url": ""
    }

def convert_to_json_if_needed(value):
    """Helper function to convert lists/dicts to JSON strings"""
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    return value

@app.route('/profile', methods=['GET'])
def profile():
    print(f"🔍 Current Session Data: {session}")
    
    # Session handling
    user_id = session.get('user_id')
    username = session.get('user')
    
    if not user_id and not username:
        return redirect(url_for('login'))
    
    user = None
    if user_id:
        user = db.session.get(User, user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Update session
    if 'user_id' not in session:
        session['user_id'] = user.id
    if 'user' not in session:
        session['user'] = user.name
    
    # Check if profile exists
    user_profile = Profile.query.filter_by(user_id=user.id).first()
    
    if not user_profile:
        user_profile = Profile(user_id=user.id)
        db.session.add(user_profile)
        db.session.commit()
        print(f"✅ New profile created for user: {user.name}")
    
    # --- CV AUTO-FILL LOGIC (Simplified - No manual edit flags) ---
    should_extract = False
    user_resume = getattr(user, 'resume', None)
    
    if user_resume:
        resume_path = os.path.join(UPLOAD_FOLDER, user_resume)
        
        if os.path.exists(resume_path):
            # ONLY extract if profile is EMPTY (no data at all)
            needs_data = (
                not user_profile.about and 
                not user_profile.skills and 
                not user_profile.work_experience and 
                not user_profile.education
            )
            
            if needs_data:
                should_extract = True
                print(f"📄 Profile empty, extracting from CV: {resume_path}")
            else:
                print(f"⏭️ Profile already has data, skipping extraction")
        else:
            print(f"❌ Resume file not found at: {resume_path}")
            user.resume = None
            db.session.commit()
    
    # Extract CV data if needed
    if should_extract:
        extracted_data = extract_cv_with_gemini(resume_path)
        
        if extracted_data:
            try:
                # Only update if fields are empty
                if extracted_data.get('about') and not user_profile.about:
                    user_profile.about = extracted_data['about']
                    print(f"✅ About added")
                
                if extracted_data.get('skills') and not user_profile.skills:
                    user_profile.skills = ",".join(extracted_data['skills'])
                    print(f"✅ Skills added")
                
                if extracted_data.get('interests') and not user_profile.interests:
                    user_profile.interests = ",".join(extracted_data['interests'])
                    print(f"✅ Interests added")
                
                if extracted_data.get('languages') and not user_profile.languages:
                    user_profile.languages = ",".join(extracted_data['languages'])
                    print(f"✅ Languages added")
                
                if extracted_data.get('work_experience') and not user_profile.work_experience:
                    user_profile.work_experience = json.dumps(extracted_data['work_experience'])
                    print(f"✅ Work experience added")
                
                if extracted_data.get('education') and not user_profile.education:
                    if isinstance(extracted_data['education'], list):
                        user_profile.education = json.dumps(extracted_data['education'])
                    else:
                        user_profile.education = extracted_data['education']
                    print(f"✅ Education added")
                
                if extracted_data.get('certifications') and not user_profile.certifications:
                    if isinstance(extracted_data['certifications'], list):
                        user_profile.certifications = ",".join(extracted_data['certifications'])
                    else:
                        user_profile.certifications = extracted_data['certifications']
                    print(f"✅ Certifications added")
                
                if extracted_data.get('projects') and not user_profile.projects:
                    user_profile.projects = json.dumps(extracted_data['projects'])
                    print(f"✅ Projects added")
                
                if extracted_data.get('achievements') and not user_profile.achievements:
                    user_profile.achievements = json.dumps(extracted_data['achievements'])
                    print(f"✅ Achievements added")
                
                if extracted_data.get('linkedin_url') and not user_profile.linkedin_url:
                    user_profile.linkedin_url = extracted_data['linkedin_url']
                
                if extracted_data.get('github_url') and not user_profile.github_url:
                    user_profile.github_url = extracted_data['github_url']
                
                db.session.commit()
                flash("✅ CV data extracted successfully!", "success")
            except Exception as e:
                print(f"❌ Error saving extracted data: {e}")
                db.session.rollback()
                flash("⚠️ Error saving extracted data", "warning")
        else:
            flash("⚠️ Could not extract data from CV. Please fill manually.", "warning")
    
    # Prepare data for template with proper parsing
    work_experience_data = user_profile.work_experience
    if work_experience_data and isinstance(work_experience_data, str):
        try:
            work_experience_data = json.loads(work_experience_data)
        except:
            pass
    
    education_data = user_profile.education
    if education_data and isinstance(education_data, str):
        try:
            education_data = json.loads(education_data)
        except:
            pass
    
    achievements_data = user_profile.achievements
    if achievements_data and isinstance(achievements_data, str):
        try:
            achievements_data = json.loads(achievements_data)
        except:
            pass
    
    projects_data = getattr(user_profile, 'projects', '')
    if projects_data and isinstance(projects_data, str):
        try:
            projects_data = json.loads(projects_data)
        except:
            pass
    
    profile_data = {
        'about': user_profile.about or '',
        'skills': user_profile.skills.split(',') if user_profile.skills else [],
        'languages': user_profile.languages.split(',') if user_profile.languages else [],
        'interests': user_profile.interests.split(',') if user_profile.interests else [],
        'work_experience': work_experience_data or [],
        'education': education_data or [],
        'certifications': user_profile.certifications.split(',') if user_profile.certifications else [],
        'projects': projects_data or [],
        'achievements': achievements_data or [],
        'linkedin_url': user_profile.linkedin_url or '',
        'github_url': user_profile.github_url or ''
    }
    
    # Create safe user object
    class SafeUser:
        def __init__(self, user, name, mobile, profile_pic):
            self.id = user.id
            self.name = name
            self.mobile = mobile
            self.profile_pic = profile_pic
            self.resume = getattr(user, 'resume', None)
    
    safe_user = SafeUser(user, user.name, getattr(user, 'mobile', ''), getattr(user, 'profile_pic', None))
    
    return render_template('profile.html', current_user=safe_user, profile=profile_data)

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    """Endpoint to upload resume before profile page"""
    # FIX: Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # FIX: Get user properly
        user = None
        if user_id:
            user = User.query.get(user_id)
        if not user and username:
            user = User.query.filter_by(name=username).first()
        
        if user:
            # Ensure UPLOAD_FOLDER exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Save file with unique name
            filename = secure_filename(f"user_{user.id}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Delete old resume if exists
            if user.resume:
                old_path = os.path.join(UPLOAD_FOLDER, user.resume)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            user.resume = filename
            db.session.commit()
            print(f"✅ Resume saved: {filename}")
            
            return jsonify({
                "success": True, 
                "message": "Resume uploaded successfully! Refresh profile to auto-fill."
            })
    
    return jsonify({"error": "Invalid file type. Please upload PDF only."}), 400



@app.route('/update-profile-data', methods=['POST'])
def update_profile_data():
    try:
        data = request.get_json()
        
        username = session.get("user")
        user_id = session.get("user_id")
        
        if not username and not user_id:
            return jsonify({"success": False, "error": "Please login"}), 401
        
        user = None
        if user_id:
            user = db.session.get(User, user_id)
        if not user and username:
            user = User.query.filter_by(name=username).first()
        
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
        
        if 'mobile' in data:
            user.mobile = data['mobile']
        
        profile = Profile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = Profile(user_id=user.id)
            db.session.add(profile)
        
        # Update all profile fields (overwrite with manual data)
        if 'languages' in data:
            profile.languages = data['languages'] if isinstance(data['languages'], str) else ",".join(data['languages'])
        
        if 'about' in data:
            profile.about = data['about']
        
        if 'skills' in data:
            profile.skills = data['skills'] if isinstance(data['skills'], str) else ",".join(data['skills'])
        
        if 'interests' in data:
            profile.interests = data['interests'] if isinstance(data['interests'], str) else ",".join(data['interests'])
        
        if 'work_experience' in data:
            if isinstance(data['work_experience'], (list, dict)):
                profile.work_experience = json.dumps(data['work_experience'])
            else:
                profile.work_experience = data['work_experience']
        
        if 'education' in data:
            if isinstance(data['education'], list):
                profile.education = json.dumps(data['education'])
            else:
                profile.education = data['education']
        
        if 'certifications' in data:
            profile.certifications = data['certifications'] if isinstance(data['certifications'], str) else ",".join(data['certifications'])
        
        if 'projects' in data:
            if isinstance(data['projects'], (list, dict)):
                profile.projects = json.dumps(data['projects'])
            else:
                profile.projects = data['projects']
        
        if 'achievements' in data:
            if isinstance(data['achievements'], list):
                profile.achievements = json.dumps(data['achievements'])
            else:
                profile.achievements = data['achievements']
        
        if 'linkedin_url' in data:
            profile.linkedin_url = data['linkedin_url']
        
        if 'github_url' in data:
            profile.github_url = data['github_url']
        
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# @app.route('/update-profile-data', methods=['POST'])
# def update_profile_data():
#     try:
#         from datetime import datetime
        
#         data = request.get_json()
        
#         # Session handling
#         username = session.get("user")
#         user_id = session.get("user_id")
        
#         if not username and not user_id:
#             return jsonify({"success": False, "error": "Please login"}), 401
        
#         # Get user
#         user = None
#         if user_id:
#             user = db.session.get(User, user_id)
#         if not user and username:
#             user = User.query.filter_by(name=username).first()
        
#         if not user:
#             return jsonify({"success": False, "error": "User not found"}), 404
        
#         # Update mobile number if provided
#         if 'mobile' in data:
#             user.mobile = data['mobile']
        
#         # Get or create profile
#         profile = Profile.query.filter_by(user_id=user.id).first()
#         if not profile:
#             profile = Profile(user_id=user.id)
#             db.session.add(profile)
        
#         # Mark that user manually edited
#         profile.manually_edited = True
#         profile.last_manual_update = datetime.utcnow()
        
#         # Update all profile fields (overwrite manually)
#         if 'languages' in data:
#             profile.languages = data['languages'] if isinstance(data['languages'], str) else ",".join(data['languages'])
        
#         if 'about' in data:
#             profile.about = data['about']
        
#         if 'skills' in data:
#             profile.skills = data['skills'] if isinstance(data['skills'], str) else ",".join(data['skills'])
        
#         if 'interests' in data:
#             profile.interests = data['interests'] if isinstance(data['interests'], str) else ",".join(data['interests'])
        
#         if 'work_experience' in data:
#             if isinstance(data['work_experience'], (list, dict)):
#                 profile.work_experience = json.dumps(data['work_experience'])
#             else:
#                 profile.work_experience = data['work_experience']
        
#         if 'education' in data:
#             if isinstance(data['education'], list):
#                 profile.education = json.dumps(data['education'])
#             else:
#                 profile.education = data['education']
        
#         if 'certifications' in data:
#             profile.certifications = data['certifications'] if isinstance(data['certifications'], str) else ",".join(data['certifications'])
        
#         if 'projects' in data:
#             if isinstance(data['projects'], (list, dict)):
#                 profile.projects = json.dumps(data['projects'])
#             else:
#                 profile.projects = data['projects']
        
#         if 'achievements' in data:
#             if isinstance(data['achievements'], list):
#                 profile.achievements = json.dumps(data['achievements'])
#             else:
#                 profile.achievements = data['achievements']
        
#         if 'linkedin_url' in data:
#             profile.linkedin_url = data['linkedin_url']
        
#         if 'github_url' in data:
#             profile.github_url = data['github_url']
        
#         db.session.commit()
#         return jsonify({"success": True, "message": "Profile updated successfully!"})
    
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"success": False, "error": str(e)}), 500


@app.route('/check-cv-status')
def check_cv_status():
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user by ID first, then by name
    user = None
    if user_id:
        user = User.query.get(user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile = Profile.query.filter_by(user_id=user.id).first()
    
    # Check if resume file exists
    resume_exists = False
    resume_path = None
    if hasattr(user, 'resume') and user.resume:
        UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
        resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
        resume_exists = os.path.exists(resume_path)
    
    return jsonify({
        "user_id": user.id,
        "user_name": user.name,
        "has_resume_column": hasattr(user, 'resume'),
        "resume_filename": user.resume if hasattr(user, 'resume') else None,
        "resume_path": resume_path,
        "resume_file_exists": resume_exists,
        "profile_exists": profile is not None,
        "profile_has_data": {
            "skills": bool(profile.skills) if profile else False,
            "work_experience": bool(profile.work_experience) if profile else False,
            "education": bool(profile.education) if profile else False
        }
    })

@app.route('/debug-profile-data')
def debug_profile_data():
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user by ID first, then by name
    user = None
    if user_id:
        user = User.query.get(user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile = Profile.query.filter_by(user_id=user.id).first()
    
    # Check resume file
    resume_exists = False
    resume_path = None
    if hasattr(user, 'resume') and user.resume:
        UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
        resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
        resume_exists = os.path.exists(resume_path)
        
        # Try to read PDF and extract sample
        pdf_sample = ""
        if resume_exists and resume_path.endswith('.pdf'):
            try:
                import PyPDF2
                with open(resume_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    if len(reader.pages) > 0:
                        pdf_sample = reader.pages[0].extract_text()[:500]
            except Exception as e:
                pdf_sample = f"Error reading PDF: {e}"
    
    # Parse JSON fields for better debugging
    work_exp_data = profile.work_experience if profile else None
    if work_exp_data and isinstance(work_exp_data, str):
        try:
            work_exp_data = json.loads(work_exp_data)
        except:
            pass
    
    education_data = profile.education if profile else None
    if education_data and isinstance(education_data, str):
        try:
            education_data = json.loads(education_data)
        except:
            pass
    
    return jsonify({
        "user_id": user.id,
        "user_name": user.name,
        "has_resume": hasattr(user, 'resume'),
        "resume_filename": user.resume if hasattr(user, 'resume') else None,
        "resume_path": resume_path,
        "resume_exists": resume_exists,
        "pdf_sample": pdf_sample,
        "profile_exists": profile is not None,
        "profile_data": {
            "skills": profile.skills.split(',') if profile and profile.skills else [],
            "interests": profile.interests.split(',') if profile and profile.interests else [],
            "work_experience": work_exp_data[:200] if work_exp_data else None,
            "education": education_data if education_data else None,
            "about": profile.about if profile else None,
            "languages": profile.languages.split(',') if profile and profile.languages else [],
            "certifications": profile.certifications.split(',') if profile and profile.certifications else [],
            "achievements": json.loads(profile.achievements) if profile and profile.achievements else []
        }
    })

@app.route('/debug-about')
def debug_about():
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user by ID first, then by name
    user = None
    if user_id:
        user = User.query.get(user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    profile = Profile.query.filter_by(user_id=user.id).first()
    
    return jsonify({
        "user_name": user.name,
        "user_id": user.id,
        "profile_exists": profile is not None,
        "about_in_db": profile.about if profile else None,
        "about_type": str(type(profile.about)) if profile else None,
        "about_length": len(profile.about) if profile and profile.about else 0,
        "all_profile_fields": {
            "about": profile.about if profile else None,
            "skills": profile.skills.split(',') if profile and profile.skills else [],
            "education": profile.education if profile else None,
            "work_experience": profile.work_experience if profile else None,
            "languages": profile.languages.split(',') if profile and profile.languages else []
        }
    })

@app.route('/check-profile-pic')
def check_profile_pic():
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user by ID first, then by name
    user = None
    if user_id:
        user = User.query.get(user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if profile picture exists
    profile_pic_exists = False
    if user.profile_pic:
        pic_path = os.path.join(current_app.root_path, user.profile_pic.lstrip('/'))
        profile_pic_exists = os.path.exists(pic_path)
    
    return jsonify({
        "user_id": user.id,
        "user_name": user.name,
        "profile_pic": user.profile_pic,
        "profile_pic_exists": profile_pic_exists,
        "full_path": os.path.join(current_app.root_path, user.profile_pic.lstrip('/')) if user.profile_pic else None
    })

@app.route('/upload-profile-picture', methods=['POST'])
def upload_profile_picture():
    """Upload profile picture"""
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    if 'avatar' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return jsonify({"error": "Invalid file type. Use PNG, JPG, JPEG, GIF, or WEBP"}), 400
    
    try:
        # Get user by ID first, then by name
        user = None
        if user_id:
            user = User.query.get(user_id)
        if not user and username:
            user = User.query.filter_by(name=username).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Define profile pictures folder
        PROFILE_PICS_FOLDER = os.path.join(current_app.root_path, 'static', 'profile_pics')
        os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)
        
        # Delete old profile picture if exists
        if user.profile_pic:
            old_pic_path = os.path.join(current_app.root_path, user.profile_pic.lstrip('/'))
            if os.path.exists(old_pic_path):
                try:
                    os.remove(old_pic_path)
                    print(f"🗑️ Deleted old profile picture: {old_pic_path}")
                except Exception as e:
                    print(f"⚠️ Could not delete old picture: {e}")
        
        # Generate unique filename
        import time
        timestamp = int(time.time())
        filename = secure_filename(f"user_{user.id}_{timestamp}_{file.filename}")
        filepath = os.path.join(PROFILE_PICS_FOLDER, filename)
        file.save(filepath)
        
        # Update database
        profile_pic_url = f"/static/profile_pics/{filename}"
        user.profile_pic = profile_pic_url
        db.session.commit()
        
        print(f"✅ Profile picture uploaded: {profile_pic_url}")
        
        return jsonify({
            "success": True,
            "url": profile_pic_url,
            "message": "Profile picture updated successfully!"
        })
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/force-cv-extract', methods=['POST'])
def force_cv_extract():
    """Manually trigger CV extraction"""
    # Check both session keys
    username = session.get('user')
    user_id = session.get('user_id')
    
    if not username and not user_id:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user by ID first, then by name
    user = None
    if user_id:
        user = User.query.get(user_id)
    if not user and username:
        user = User.query.filter_by(name=username).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Clear profile data to force re-extraction
    profile = Profile.query.filter_by(user_id=user.id).first()
    if profile:
        profile.skills = None
        profile.work_experience = None
        profile.education = None
        profile.about = None
        profile.languages = None
        profile.interests = None
        profile.certifications = None
        profile.projects = None
        profile.achievements = None
        db.session.commit()
        print(f"🔄 Cleared profile data for re-extraction")
    
    return jsonify({"success": True, "redirect": "/profile"})

@app.route('/test-extract/<int:user_id>')
def test_extract(user_id):
    """Manually test CV extraction for a user"""
    # Check both session keys for admin access
    username = session.get('user')
    session_user_id = session.get('user_id')
    
    # Allow if admin or the same user
    session_user = None
    if session_user_id:
        session_user = User.query.get(session_user_id)
    
    # Only allow if same user or admin (you can add admin check here)
    if session_user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if not user.resume:
        return jsonify({"error": "No resume found for user"}), 404
    
    UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
    resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
    
    if not os.path.exists(resume_path):
        return jsonify({"error": f"Resume file not found at {resume_path}"}), 404
    
    # Extract CV
    extracted_data = extract_cv_with_gemini(resume_path)
    
    if extracted_data:
        profile = Profile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = Profile(user_id=user.id)
            db.session.add(profile)
        
        # Update profile with proper JSON conversion
        if extracted_data.get('about'):
            profile.about = extracted_data['about']
        if extracted_data.get('skills'):
            profile.skills = ",".join(extracted_data['skills'])
        if extracted_data.get('interests'):
            profile.interests = ",".join(extracted_data['interests'])
        if extracted_data.get('languages'):
            profile.languages = ",".join(extracted_data['languages'])
        if extracted_data.get('work_experience'):
            profile.work_experience = json.dumps(extracted_data['work_experience'])
        if extracted_data.get('education'):
            profile.education = json.dumps(extracted_data['education']) if isinstance(extracted_data['education'], list) else extracted_data['education']
        if extracted_data.get('certifications'):
            profile.certifications = ",".join(extracted_data['certifications']) if isinstance(extracted_data['certifications'], list) else extracted_data['certifications']
        if extracted_data.get('projects'):
            profile.projects = json.dumps(extracted_data['projects'])
        if extracted_data.get('achievements'):
            profile.achievements = json.dumps(extracted_data['achievements'])
        if extracted_data.get('linkedin_url'):
            profile.linkedin_url = extracted_data['linkedin_url']
        if extracted_data.get('github_url'):
            profile.github_url = extracted_data['github_url']
        
        db.session.commit()
        return jsonify({"success": True, "extracted_data": extracted_data})
    else:
        return jsonify({"error": "Failed to extract data"}), 500

@app.route('/reset-to-cv', methods=['POST'])
def reset_to_cv():
    """Reset profile to CV data - without using new columns"""
    try:
        username = session.get('user')
        user_id = session.get('user_id')
        
        if not username and not user_id:
            return jsonify({"error": "Not logged in"}), 401
        
        # Get user
        user = None
        if user_id:
            user = db.session.get(User, user_id)
        if not user and username:
            user = User.query.filter_by(name=username).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has resume
        if not user.resume:
            return jsonify({"error": "No CV found. Please upload CV first."}), 404
        
        resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
        if not os.path.exists(resume_path):
            return jsonify({"error": "CV file not found. Please upload again."}), 404
        
        # Get profile
        profile = Profile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = Profile(user_id=user.id)
            db.session.add(profile)
        
        # SIMPLE: Just clear all fields
        profile.about = None
        profile.skills = None
        profile.work_experience = None
        profile.education = None
        profile.certifications = None
        profile.projects = None
        profile.achievements = None
        profile.languages = None
        profile.interests = None
        profile.linkedin_url = None
        profile.github_url = None
        
        db.session.commit()
        
        # Now re-extract from CV
        extracted_data = extract_cv_with_gemini(resume_path)
        
        if extracted_data:
            # Update with extracted data
            if extracted_data.get('about'):
                profile.about = extracted_data['about']
            if extracted_data.get('skills'):
                profile.skills = ",".join(extracted_data['skills'])
            if extracted_data.get('interests'):
                profile.interests = ",".join(extracted_data['interests'])
            if extracted_data.get('languages'):
                profile.languages = ",".join(extracted_data['languages'])
            if extracted_data.get('work_experience'):
                profile.work_experience = json.dumps(extracted_data['work_experience'])
            if extracted_data.get('education'):
                if isinstance(extracted_data['education'], list):
                    profile.education = json.dumps(extracted_data['education'])
                else:
                    profile.education = extracted_data['education']
            if extracted_data.get('certifications'):
                if isinstance(extracted_data['certifications'], list):
                    profile.certifications = ",".join(extracted_data['certifications'])
                else:
                    profile.certifications = extracted_data['certifications']
            if extracted_data.get('projects'):
                profile.projects = json.dumps(extracted_data['projects'])
            if extracted_data.get('achievements'):
                profile.achievements = json.dumps(extracted_data['achievements'])
            if extracted_data.get('linkedin_url'):
                profile.linkedin_url = extracted_data['linkedin_url']
            if extracted_data.get('github_url'):
                profile.github_url = extracted_data['github_url']
            
            db.session.commit()
            return jsonify({"success": True, "message": "Reset to CV data successful!"})
        else:
            return jsonify({"error": "Could not extract CV data. Please try again."}), 500
            
    except Exception as e:
        print(f"Error in reset: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Keep your other routes (check_cv_status, debug_profile_data, etc.) as they are
# but update them to use the same session handling logic (check both user and user_id)



# import os
# import json
# import PyPDF2
# import requests  # Add this for REST API calls
# from dotenv import load_dotenv
# from flask import request, jsonify, session, render_template, redirect, url_for, flash, current_app
# from model import db, User, Profile
# from werkzeug.utils import secure_filename

# # Load environment variables
# load_dotenv()

# # Get API key
# GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# if GEMINI_API_KEY:
#     print(f"✅ API Key loaded: {GEMINI_API_KEY[:15]}...")
# else:
#     print("❌ GEMINI_API_KEY not found in environment variables")

# def extract_cv_with_gemini(filepath):
#     """Extract CV data using Gemini REST API"""
#     try:
#         # Extract text from PDF
#         extracted_text = ""
#         print(f"📄 Reading PDF from: {filepath}")
        
#         with open(filepath, 'rb') as pdf_file:
#             reader = PyPDF2.PdfReader(pdf_file)
#             print(f"📄 Number of pages: {len(reader.pages)}")
            
#             for page_num, page in enumerate(reader.pages):
#                 page_text = page.extract_text()
#                 if page_text:
#                     extracted_text += page_text
#                     print(f"✅ Page {page_num + 1}: {len(page_text)} characters")
#                 else:
#                     print(f"⚠️ Page {page_num + 1}: No text extracted")
        
#         if not extracted_text:
#             print("❌ No text extracted from PDF")
#             return None
        
#         print(f"📝 Total extracted text length: {len(extracted_text)}")
        
#         # AI Prompt
#         prompt = f"""
#         Parse this resume and return ONLY valid JSON. No markdown, no extra text, no explanation.
        
#         Required JSON format:
#         {{  
#             "about": "A professional summary or bio about the person (2-3 sentences)",
#             "skills": ["skill1", "skill2", "skill3"],
#             "interests": ["interest1", "interest2"],
#             "languages":["language1", "language2"],
            
#             "work_experience": [
#                 {{
#                     "company": "Company Name",
#                     "role": "Job Title/Role",
#                     "duration": "Start - End Date",
#                     "description": "Brief description of responsibilities and achievements"
#                 }}
#             ],

#             "education": [
#                 "Degree Name from Institution Name, Year",
#                 "Another Degree from Institution Name, Year"
#             ],
            
#             "certifications": [
#                 "Certification 1 Name - Issuing Authority (Year)",
#                 "Certification 2 Name - Issuing Authority (Year)"
#             ],
           
#             "projects": [
#                 {{
#                     "title": "Project Title",
#                     "technologies": "Comma separated technologies used",
#                     "description": "Brief description of the project",
#                     "link": "Project URL if available, otherwise empty string"
#                 }}
#             ],
#             "achievements": ["Achievement 1", "Achievement 2"],
#             "linkedin_url": "linkedin profile url if found in resume, otherwise empty string",
#             "github_url": "github or portfolio url if found, otherwise empty string"
#         }}
        
#         Resume Text:
#         {extracted_text[:8000]}
#         """
        
#         # Use the working model - models/gemini-2.5-flash
#         API_KEY = os.getenv('GEMINI_API_KEY')
#         url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
        
#         payload = {
#             "contents": [{
#                 "parts": [{"text": prompt}]
#             }]
#         }
        
#         print("🤖 Calling Gemini API...")
#         response = requests.post(url, json=payload, timeout=60)
        
#         if response.status_code != 200:
#             print(f"❌ API Error: {response.status_code}")
#             print(f"Response: {response.text}")
#             return None
        
#         result = response.json()
        
#         # Extract text from response
#         if 'candidates' in result and len(result['candidates']) > 0:
#             response_text = result['candidates'][0]['content']['parts'][0]['text']
#             print(f"🤖 Response received (length: {len(response_text)})")
#         else:
#             print("❌ No response from API")
#             return None
        
#         # Clean response - remove markdown code blocks
#         clean_response = response_text.strip()
#         if clean_response.startswith('```json'):
#             clean_response = clean_response[7:]
#         if clean_response.startswith('```'):
#             clean_response = clean_response[3:]
#         if clean_response.endswith('```'):
#             clean_response = clean_response[:-3]
#         clean_response = clean_response.strip()
        
#         # Parse JSON
#         parsed_data = json.loads(clean_response)
#         print(f"✅ Successfully parsed CV data")
#         print(f"📊 Extracted: {list(parsed_data.keys())}")

#         # Ensure 'about' field exists
#         if 'about' not in parsed_data or not parsed_data['about']:
#             # Create a fallback about section
#             name = parsed_data.get('name', 'The candidate')
#             skills = ', '.join(parsed_data.get('skills', [])[:3])
#             parsed_data['about'] = f"{name} is a professional with skills in {skills}. Seeking new opportunities in their field."
#             print("⚠️ Created fallback about section")
        
#         print(f"✅ About extracted: {parsed_data['about'][:100]}...")
        
#         return parsed_data
        
#     except json.JSONDecodeError as e:
#         print(f"❌ JSON Parse Error: {e}")
#         print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
#         return None
#     except Exception as e:
#         print(f"❌ CV extraction error: {e}")
#         import traceback
#         traceback.print_exc()
#         return None


# @app.route('/test-extract/<int:user_id>')
# def test_extract(user_id):
#     """Manually test CV extraction for a user"""
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     if not user.resume:
#         return jsonify({"error": "No resume found for user"}), 404
    
#     UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
#     resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
    
#     if not os.path.exists(resume_path):
#         return jsonify({"error": f"Resume file not found at {resume_path}"}), 404
    
#     # Extract CV
#     extracted_data = extract_cv_with_gemini(resume_path)
    
#     if extracted_data:
#         profile = Profile.query.filter_by(user_id=user.id).first()
#         if not profile:
#             profile = Profile(user_id=user.id)
#             db.session.add(profile)
        
#         # Update profile
#         if extracted_data.get('about'):
#             profile.skills = ",".join(extracted_data['about'])
#         if extracted_data.get('skills'):
#             profile.skills = ",".join(extracted_data['skills'])
#         if extracted_data.get('interests'):
#             profile.interests = ",".join(extracted_data['interests'])
#         if extracted_data.get('languages'):
#             profile.skills = ",".join(extracted_data['languages'])
#         if extracted_data.get('work_experience'):
#             profile.work_experience = extracted_data['work_experience']
#         if extracted_data.get('education'):
#             profile.education = extracted_data['education']
#         if extracted_data.get('certifications'):
#             profile.certifications = extracted_data['certifications']
#         if extracted_data.get('projects'):
#             profile.projects = extracted_data['projects']
#         if extracted_data.get('achievements'):
#             profile.achievements = extracted_data['achievements']
#         if extracted_data.get('linkedin_url'):
#             profile.linkedin_url = extracted_data['linkedin_url']
#         if extracted_data.get('github_url'):
#             profile.github_url = extracted_data['github_url']
        
#         db.session.commit()
#         return jsonify({"success": True, "extracted_data": extracted_data})
#     else:
#         return jsonify({"error": "Failed to extract data"}), 500


# @app.route('/profile', methods=['GET'])
# def profile():


#     print(f"🔍 Current Session Data: {session}") # Terminal mein check karein
#     if 'user_id' not in session:
#         print("❌ user_id not found in session, redirecting...")
#         return redirect(url_for('login'))
    
#     # ... baki code
#     # if "user" not in session:
#     #     return redirect(url_for("login"))

#     # Get user from session
#     # user_identifier = session["user"]
#     current_user_id = session["user_id"]
    
#     # try:
#     #     user = User.query.filter_by(name=user_identifier).first()
#     # except Exception as e:
#     #     print(f"Database error: {e}")
#     #     flash("Database error. Please contact support.", "error")
#     #     return redirect(url_for("dashboard"))
#     try:
#         # 3. NAME KI JAGAH ID SE SEARCH KAREIN
#         user = User.query.get(current_user_id) 
#     except Exception as e:
#         print(f"Database error: {e}")
#         flash("Database error. Please contact support.", "error")
#         return redirect(url_for("dashboard"))
    
#     # if not user:
#     #     session.pop("user", None)  
#     #     return redirect(url_for("login"))
#     if not user:
#         session.clear()  
#         return redirect(url_for("login"))

#     # Check if profile exists
#     user_profile = Profile.query.filter_by(user_id=user.id).first()
    
#     if not user_profile:
#         user_profile = Profile(user_id=user.id)
#         db.session.add(user_profile)
#         db.session.commit()
#         print(f"✅ New profile created for user: {user.name}")

#     # Get user data safely
#     user_name = user.name
#     user_mobile = getattr(user, 'mobile', '')
#     user_resume = getattr(user, 'resume', None)
#     user_profile_pic = getattr(user, 'profile_pic', None)

#     # --- CV AUTO-FILL LOGIC ---
#     should_extract = False
    
#     # Check if user has uploaded resume
#     if user_resume:
#         UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
#         resume_path = os.path.join(UPLOAD_FOLDER, user_resume)
        
#         if os.path.exists(resume_path):
#             # Check if profile needs data
#             if not user_profile.skills or not user_profile.work_experience:
#                 should_extract = True
#                 print(f"📄 Found CV at: {resume_path}")
#         else:
#             print(f"❌ Resume file not found at: {resume_path}")
#             user.resume = None
#             db.session.commit()

#     # Extract CV data if needed
#     if should_extract:
#         extracted_data = extract_cv_with_gemini(resume_path)
        
#         if extracted_data:
#             # Update profile with extracted data
#             if extracted_data.get('about'):
#                 user_profile.about = extracted_data['about']
#                 print(f"✅ about added")

#             if extracted_data.get('skills'):
#                 user_profile.skills = ",".join(extracted_data['skills'])
#                 print(f"✅ Skills added: {len(extracted_data['skills'])} items")
            
#             if extracted_data.get('interests'):
#                 user_profile.interests = ",".join(extracted_data['interests'])
#                 print(f"✅ Interests added: {len(extracted_data['interests'])} items")
            
#             if extracted_data.get('languages'):
#                 user_profile.languages = ",".join(extracted_data['languages'])
#                 print(f"✅ languages added: {len(extracted_data['languages'])} items")

#             # if extracted_data.get('work_experience'):
#             #     user_profile.work_experience = extracted_data['work_experience']
#             #     print(f"✅ Work experience added")
#             if extracted_data.get('work_experience'):
#                 import json # Just in case top par missing ho
#                 user_profile.work_experience = json.dumps(extracted_data['work_experience'])
#                 print(f"✅ Work experience added as JSON string")
            
#             # if extracted_data.get('education'):
#             #     user_profile.education = extracted_data['education']
#             #     print(f"✅ Education added")
#             if extracted_data.get('education'):
#                 # Agar education bhi list format me aayi hai, to usme bhi dumps lagayein, 
#                 # warna join use karein (depends on your prompt format)
#                 if isinstance(extracted_data['education'], list):
#                     user_profile.education = json.dumps(extracted_data['education'])
#                 else:
#                     user_profile.education = extracted_data['education']
#                 print(f"✅ Education added")
            
#             # if extracted_data.get('certifications'):
#             #     user_profile.certifications = extracted_data['certifications']
#             #     print(f"✅ Certifications added")
#             if extracted_data.get('certifications'):
#                 if isinstance(extracted_data['certifications'], list):
#                      user_profile.certifications = ",".join(extracted_data['certifications'])
#                 else:
#                      user_profile.certifications = extracted_data['certifications']


#             # if extracted_data.get('projects'):
#             #     user_profile.projects = extracted_data['projects']
#             #     print(f"✅ Projects added")
#             if extracted_data.get('projects'):
#                 user_profile.projects = json.dumps(extracted_data['projects'])
#                 print(f"✅ Projects added as JSON string")

#             if extracted_data.get('achievements'):
#                 user_profile.achievements = extracted_data['achievements']
#                 print(f"✅ Achievements added")
            
#             if extracted_data.get('linkedin_url'):
#                 user_profile.linkedin_url = extracted_data['linkedin_url']
#                 print(f"✅ LinkedIn URL added")
            
#             if extracted_data.get('github_url'):
#                 user_profile.github_url = extracted_data['github_url']
#                 print(f"✅ GitHub URL added")
            
#             db.session.commit()
#             flash("✅ CV data extracted successfully! Your profile has been auto-filled.", "success")
#         else:
#             flash("⚠️ Could not extract data from CV. Please fill in manually.", "warning")

#     # Prepare data for template
#     profile_data = {
#         'about': user_profile.about or '',
#         'skills': user_profile.skills.split(',') if user_profile.skills else [],
#         'languages': user_profile.languages.split(',') if user_profile.languages else [],
#         'interests': user_profile.interests.split(',') if user_profile.interests else [],
#         'work_experience': user_profile.work_experience or '',
#         'education': user_profile.education or '',
#         'certifications': user_profile.certifications or '',
#         'projects': getattr(user_profile, 'projects', '') or '',
#         'achievements': getattr(user_profile, 'achievements', '') or '',
#         'linkedin_url': user_profile.linkedin_url or '',
#         'github_url': user_profile.github_url or ''
#     }

#     print(f"Backend sending about: {profile_data.get('about')}")
#     # Create a user object for template with safe attributes
#     class SafeUser:
#         def __init__(self, user, name, mobile, profile_pic):
#             self.id = user.id
#             self.name = name
#             self.mobile = mobile
#             self.profile_pic = profile_pic
#             self.resume = getattr(user, 'resume', None)
    
#     safe_user = SafeUser(user, user_name, user_mobile, user_profile_pic)

#     return render_template('profile.html', current_user=safe_user, profile=profile_data)




# @app.route('/upload-resume', methods=['POST'])
# def upload_resume():
#     """Endpoint to upload resume before profile page"""
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     if 'resume' not in request.files:
#         return jsonify({"error": "No file uploaded"}), 400
    
#     file = request.files['resume']
#     if file.filename == '':
#         return jsonify({"error": "No file selected"}), 400
    
#     if file and file.filename.lower().endswith('.pdf'):
        
        
#         # Save file with unique name
#         filename = secure_filename(f"user_{session['user']}_{file.filename}")
#         filepath = os.path.join(UPLOAD_FOLDER, filename)
#         file.save(filepath)
        
#         # Store in user model
#         user = User.query.filter_by(name=session["user"]).first()
#         if user:
#             # Delete old resume if exists
#             if user.resume:
#                 old_path = os.path.join(UPLOAD_FOLDER, user.resume)
#                 if os.path.exists(old_path):
#                     os.remove(old_path)
            
#             user.resume = filename
#             db.session.commit()
#             print(f"✅ Resume saved: {filename}")
            
#             return jsonify({
#                 "success": True, 
#                 "message": "Resume uploaded successfully! Refresh profile to auto-fill."
#             })
    
#     return jsonify({"error": "Invalid file type. Please upload PDF only."}), 400




# @app.route('/force-cv-extract', methods=['POST'])
# def force_cv_extract():
#     """Manually trigger CV extraction"""
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     user = User.query.filter_by(name=session["user"]).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     # Clear profile data to force re-extraction
#     profile = Profile.query.filter_by(user_id=user.id).first()
#     if profile:
#         profile.skills = None
#         profile.work_experience = None
#         db.session.commit()
#         print(f"🔄 Cleared profile data for re-extraction")
    
#     return jsonify({"success": True, "redirect": "/profile"})


# @app.route('/update-profile-data', methods=['POST'])
# def update_profile_data():
#     try:
#         data = request.get_json()
        
#         # Get user from session
#         user_identifier = session.get("user")
#         if not user_identifier:
#             return jsonify({"success": False, "error": "Please login"}), 401
        
#         user = User.query.filter_by(name=user_identifier).first()
#         if not user:
#             return jsonify({"success": False, "error": "User not found"}), 404
        
#         # Update mobile number if provided
#         if 'mobile' in data:
#             user.mobile = data['mobile']
        
#         # Get or create profile
#         profile = Profile.query.filter_by(user_id=user.id).first()
#         if not profile:
#             profile = Profile(user_id=user.id)
#             db.session.add(profile)
        
#         # Update all profile fields
#         if 'languages' in data:
#             profile.languages = data['languages'] if isinstance(data['languages'], str) else ",".join(data['languages'])
        
#         if 'about' in data:
#             profile.about = data['about']

#         if 'skills' in data:
#             profile.skills = data['skills'] if isinstance(data['skills'], str) else ",".join(data['skills'])
        
#         if 'interests' in data:
#             profile.interests = data['interests'] if isinstance(data['interests'], str) else ",".join(data['interests'])
        
#         if 'work_experience' in data:
#             profile.work_experience = data['work_experience']
        
#         if 'education' in data:
#             profile.education = data['education']
        
#         if 'certifications' in data:
#             profile.certifications = data['certifications']
        
#         if 'projects' in data:
#             profile.projects = data['projects']
        
#         if 'achievements' in data:
#             profile.achievements = data['achievements']
        
#         if 'linkedin_url' in data:
#             profile.linkedin_url = data['linkedin_url']
        
#         if 'github_url' in data:
#             profile.github_url = data['github_url']
        
#         db.session.commit()
#         return jsonify({"success": True, "message": "Profile updated successfully!"})
    
#     except Exception as e:
#         db.session.rollback()
#         print(f"Error: {e}")
#         return jsonify({"success": False, "error": str(e)}), 500


# @app.route('/check-cv-status')
# def check_cv_status():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     user = User.query.filter_by(name=session["user"]).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     profile = Profile.query.filter_by(user_id=user.id).first()
    
#     # Check if resume file exists
#     resume_exists = False
#     resume_path = None
#     if hasattr(user, 'resume') and user.resume:
#         UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
#         resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
#         resume_exists = os.path.exists(resume_path)
    
#     return jsonify({
#         "user_id": user.id,
#         "user_name": user.name,
#         "has_resume_column": hasattr(user, 'resume'),
#         "resume_filename": user.resume if hasattr(user, 'resume') else None,
#         "resume_path": resume_path,
#         "resume_file_exists": resume_exists,
#         "profile_exists": profile is not None,
#         "profile_has_data": {
#             "skills": bool(profile.skills) if profile else False,
#             "work_experience": bool(profile.work_experience) if profile else False,
#             "education": bool(profile.education) if profile else False
#         }
#     })

# @app.route('/debug-profile-data')
# def debug_profile_data():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     user = User.query.filter_by(name=session["user"]).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     profile = Profile.query.filter_by(user_id=user.id).first()
    
#     # Check resume file
#     resume_exists = False
#     resume_path = None
#     if hasattr(user, 'resume') and user.resume:
#         UPLOAD_FOLDER = os.path.join(current_app.root_path, 'uploads')
#         resume_path = os.path.join(UPLOAD_FOLDER, user.resume)
#         resume_exists = os.path.exists(resume_path)
        
#         # Try to read PDF and extract sample
#         pdf_sample = ""
#         if resume_exists and resume_path.endswith('.pdf'):
#             try:
#                 import PyPDF2
#                 with open(resume_path, 'rb') as f:
#                     reader = PyPDF2.PdfReader(f)
#                     if len(reader.pages) > 0:
#                         pdf_sample = reader.pages[0].extract_text()[:500]
#             except Exception as e:
#                 pdf_sample = f"Error reading PDF: {e}"
    
#     return jsonify({
#         "user_id": user.id,
#         "user_name": user.name,
#         "has_resume": hasattr(user, 'resume'),
#         "resume_filename": user.resume if hasattr(user, 'resume') else None,
#         "resume_path": resume_path,
#         "resume_exists": resume_exists,
#         "pdf_sample": pdf_sample,
#         "profile_exists": profile is not None,
#         "profile_data": {
#             "skills": profile.skills if profile else None,
#             "interests": profile.interests if profile else None,
#             "work_experience": profile.work_experience[:200] if profile and profile.work_experience else None,
#             "education": profile.education if profile else None
#         }
#     })

# @app.route('/debug-about')
# def debug_about():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     user = User.query.filter_by(name=session["user"]).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     profile = Profile.query.filter_by(user_id=user.id).first()
    
#     return jsonify({
#         "user_name": user.name,
#         "profile_exists": profile is not None,
#         "about_in_db": profile.about if profile else None,
#         "about_type": str(type(profile.about)) if profile else None,
#         "about_length": len(profile.about) if profile and profile.about else 0,
#         "all_profile_fields": {
#             "about": profile.about if profile else None,
#             "skills": profile.skills if profile else None,
#             "education": profile.education if profile else None
#         }
#     })


# @app.route('/check-profile-pic')
# def check_profile_pic():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     user = User.query.filter_by(name=session["user"]).first()
#     if not user:
#         return jsonify({"error": "User not found"}), 404
    
#     return jsonify({
#         "profile_pic": user.profile_pic,
#         "file_exists": os.path.exists(os.path.join(current_app.root_path, user.profile_pic.lstrip('/'))) if user.profile_pic else False
#     })

# @app.route('/upload-profile-picture', methods=['POST'])
# def upload_profile_picture():
#     """Upload profile picture"""
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401
    
#     if 'avatar' not in request.files:
#         return jsonify({"error": "No file provided"}), 400
    
#     file = request.files['avatar']
#     if file.filename == '':
#         return jsonify({"error": "No file selected"}), 400
    
#     # Check file type
#     allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
#     file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
#     if file_ext not in allowed_extensions:
#         return jsonify({"error": "Invalid file type. Use PNG, JPG, JPEG, GIF, or WEBP"}), 400
    
#     try:
#         # Get user
#         user = User.query.filter_by(name=session["user"]).first()
#         if not user:
#             return jsonify({"error": "User not found"}), 404
        
        
#         # Delete old profile picture if exists
#         if user.profile_pic:
#             old_pic_path = os.path.join(current_app.root_path, user.profile_pic.lstrip('/'))
#             if os.path.exists(old_pic_path):
#                 try:
#                     os.remove(old_pic_path)
#                 except:
#                     pass
        
#         # Save new profile picture
#         filename = secure_filename(f"user_{user.id}_{int(os.path.getmtime(file.filename) if hasattr(os.path, 'getmtime') else 1)}_{file.filename}")
#         filepath = os.path.join(UPLOAD_FOLDER, filename)
#         file.save(filepath)
        
#         # Update database
#         profile_pic_url = f"/static/profile_pics/{filename}"
#         user.profile_pic = profile_pic_url
#         db.session.commit()
        
#         print(f"✅ Profile picture uploaded: {profile_pic_url}")
        
#         return jsonify({
#             "success": True,
#             "url": profile_pic_url,
#             "message": "Profile picture updated successfully!"
#         })
        
#     except Exception as e:
#         print(f"❌ Upload error: {e}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500


@app.route("/user/courses")
def user_courses():
    # 1. Check if user is in session
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    # Your logs show this holds a name (like 'Akriti'), not an email
    user_identifier = session['user'] 
    
    # 2. FETCH THE CURRENT USER
    # FIX: Searching by 'username' instead of 'email'
    current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()

    # Handle "Ghost Users" 
    if not current_user:
        session.pop("user", None)  
        return redirect(url_for("login"))

    # 3. DYNAMIC FETCH: Use LEFT JOIN for performance and published check
    # 3. DYNAMIC FETCH: Use LEFT JOIN for performance (counting ALL chapters)
    courses = db.execute("""
        SELECT 
            c.id, 
            c.title, 
            c.description,
            COUNT(ch.id) as chapter_count
        FROM courses c
        LEFT JOIN chapters ch 
            ON c.id = ch.course_id 
        GROUP BY 
            c.id, c.title, c.description
    """).fetchall()

    # 4. PASS BOTH VARIABLES TO THE TEMPLATE
    return render_template("user_courses.html", courses=courses, current_user=current_user)




from bs4 import BeautifulSoup

def fix_broken_boxes(text):
    if not text: return text
    soup = BeautifulSoup(text, 'html.parser')
    
    # Find all the problematic divs
    for box in soup.find_all('div', class_='code-mirror'):
        code_text = ""
        
        # 1. Grab text from inside or above the box, preserving newlines
        if box.text.strip():
            # The 'separator' argument is the secret to keeping line breaks
            code_text = box.get_text(separator='\n').strip()
        else:
            prev = box.find_previous_sibling()
            while prev and not prev.text.strip():
                empty_space = prev
                prev = prev.find_previous_sibling()
                empty_space.decompose() 
                
            if prev and prev.text.strip():
                code_text = prev.get_text(separator='\n').strip()
                prev.decompose() 
                
        # 2. Convert to <pre> tags so your CSS styles them correctly
        new_pre = soup.new_tag('pre')
        new_code = soup.new_tag('code', attrs={'class': 'language-python'})
        new_code.string = code_text
        new_pre.append(new_code)
        
        # 3. Replace the old broken div with the new tag
        box.replace_with(new_pre)
                
    return str(soup)

# ==========================================
# USER: VIEW A SPECIFIC COURSE / CHAPTER
# ==========================================
@app.route("/user/courses/<int:course_id>")
def view_course(course_id):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    
    # 1. Fetch current user
    user_identifier = session['user']
    
    # ✅ FIX: Changed 'email' to 'name'
    # Kyunki session['user'] mein 'Akriti' (naam) aa raha hai, usko name column mein dhundhna hoga
    current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()

    # --- SAFETY CHECK ---
    if current_user is None:
        session.clear() # Clear the invalid session
        flash("Your session has expired. Please login again.", "error")
        return redirect(url_for("login"))
    # -----------------------------------------------

    # 2. Fetch the course
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("user_courses"))

    # 3. Fetch all published chapters for this course
    chapters = db.execute("SELECT * FROM chapters WHERE course_id = ? ORDER BY position ASC", (course_id,)).fetchall()

    # 4. Determine WHICH chapter to display
    requested_chapter_id = request.args.get('chapter_id', type=int)
    current_chapter = None

    if requested_chapter_id:
        current_chapter = next((c for c in chapters if c['id'] == requested_chapter_id), None)
    
    if not current_chapter and chapters:
        current_chapter = chapters[0]

    # 5. Fetch Quiz Questions for the current chapter
    quiz_questions = []
    if current_chapter:
        quiz_questions = db.execute("SELECT * FROM quiz_questions WHERE chapter_id = ?", (current_chapter['id'],)).fetchall()

    # 6. Fetch Progress
    progress_records = db.execute("SELECT chapter_id, status FROM user_progress WHERE user_id = ?", (current_user['id'],)).fetchall()
    progress_dict = {row['chapter_id']: row['status'] for row in progress_records}

    return render_template("view_course.html", 
                           course=course, 
                           chapters=chapters, 
                           current_chapter=current_chapter, 
                           quiz_questions=quiz_questions,
                           current_user=current_user,
                           progress_dict=progress_dict)


# ==========================================
# USER: START / VIEW A SPECIFIC CHAPTER
# ==========================================
import random # <--- Make sure this is at the top of your file

@app.route("/user/courses/<int:course_id>/read")
def lesson_course(course_id):
    if "user" not in session:
        return redirect(url_for("login"))

    db = get_db()
    
    # 1. Fetch current user
    user_identifier = session['user']
    
    # ✅ FIX: Changed 'email' to 'name' yahan bhi
    current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()

    # --- SAFETY CHECK ---
    if not current_user:
        session.clear() 
        return redirect(url_for("login"))

    # 2. Fetch the course
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for("user_courses"))

    # 3. Fetch all published chapters
    chapters = db.execute("SELECT * FROM chapters WHERE course_id = ? ORDER BY position ASC", (course_id,)).fetchall()

    # --- FETCH PROGRESS ---
    progress_records = db.execute("SELECT chapter_id, status FROM user_progress WHERE user_id = ?", (current_user['id'],)).fetchall()
    progress_dict = {row['chapter_id']: row['status'] for row in progress_records}

    # 4. Check the URL for a chapter_id
    requested_chapter_id = request.args.get('chapter_id', type=int)

    # --- BRANCH A: CURRICULUM VIEW ---
    if not requested_chapter_id:
        return render_template("view_course.html", 
                               course=course, 
                               chapters=chapters,
                               current_user=current_user,
                               progress_dict=progress_dict)

    # --- BRANCH B: DEDICATED LESSON VIEW ---
    else:
        current_chapter = next((c for c in chapters if c['id'] == requested_chapter_id), None)
        
        if not current_chapter:
            flash("Chapter not found.", "error")
            return redirect(url_for("lesson_course", course_id=course['id']))

        # --- MARK AS COMPLETED ---
        existing_progress = db.execute("SELECT id, status FROM user_progress WHERE user_id = ? AND chapter_id = ?", (current_user['id'], current_chapter['id'])).fetchone()
        
        if not existing_progress:
            db.execute("INSERT INTO user_progress (user_id, chapter_id, status) VALUES (?, ?, 'completed')", (current_user['id'], current_chapter['id']))
            db.commit()
        elif existing_progress['status'] != 'completed':
            db.execute("UPDATE user_progress SET status = 'completed' WHERE id = ?", (existing_progress['id'],))
            db.commit()

        progress_dict[current_chapter['id']] = 'completed'
        
        # 5. Fetch Quiz Questions (UPDATED LOGIC HERE)
        raw_questions = db.execute("SELECT * FROM quiz_questions WHERE chapter_id = ?", (current_chapter['id'],)).fetchall()
        
        quiz_questions = []
        for row in raw_questions:
            # Convert SQLite row to a mutable dictionary
            q_dict = dict(row) 
            
            # Combine the answers into a single list
            options = [q_dict['correct_answer'], q_dict['wrong_1'], q_dict['wrong_2'], q_dict['wrong_3']]
            
            # Shuffle the options list randomly
            random.shuffle(options)
            
            # Store the shuffled options back into the dictionary for the template
            q_dict['options'] = options 
            
            quiz_questions.append(q_dict)

        return render_template("lesson_course.html", 
                               course=course, 
                               chapters=chapters, 
                               current_chapter=current_chapter, 
                               quiz_questions=quiz_questions,
                               current_user=current_user,
                               progress_dict=progress_dict)


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
import pandas as pd
import sqlite3

# This code loads the database and uses the AI Learning Logic
def get_dynamic_prediction(user_input):
    try:
        # 1. Connect to the newly created career database
        db_name = 'career_database.db'
        conn = sqlite3.connect(db_name)
        
        # 2. Fetch the data from the SQL table instead of a CSV
        df = pd.read_sql("SELECT * FROM career_skills", conn)
        conn.close()

        # 3. Create and train the Machine Learning Model
        # TfidfVectorizer converts words to numbers, RandomForest makes the decision
        model = make_pipeline(
            TfidfVectorizer(stop_words='english'), 
            RandomForestClassifier(random_state=42)
        )
        
        # Train the model with the database data
        model.fit(df['skills'], df['role'])

        # 4. Predict the career based on user input
        prediction = model.predict([user_input])[0]
        
        # 5. Calculate the Confidence Score
        # predict_proba gets the probability of all roles, we take the highest one
        probabilities = model.predict_proba([user_input])[0]
        confidence = round(max(probabilities) * 100, 2)
        
        return prediction, confidence

    except sqlite3.OperationalError:
        return "Database missing. Run your initial python script first!", 0
    except Exception as e:
        print(f"Prediction Error: {e}")
        return "An error occurred with the AI model.", 0

@app.route("/predict", methods=["POST"])
def predict():
    skills = request.form.get("skills", "").lower()
    interests = request.form.get("interests", "").lower()
    user_input = f"{skills} {interests}"

    # Call our dynamic mapping function
    role, score = get_dynamic_prediction(user_input)

    return jsonify({
        "career": role,
        "confidence": score
    })



import os
from flask import request, jsonify, render_template, session
from datetime import datetime
from model import ats_score 
from extensions import db
from model import AtsLog  

# Create a temp folder for uploads if it doesn't exist
# UPLOAD_FOLDER = 'temp_uploads'
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

@app.route('/ats', methods=['GET', 'POST'])
def ats():
    # 1. Render the HTML page
    if request.method == 'GET':
        return render_template('ats.html')

    # 2. Validation
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Save the file temporarily
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        # Process the resume using your model
        result_data = ats_score(filepath)
        
        # Check if processing failed early
        if "error" in result_data:
            return jsonify({"error": result_data["error"]}), 400

        # --- DATABASE STORAGE LOGIC ---
        try:
            # THIS LINE HANDLES BOTH METHODS:
            # - Returns actual ID (e.g., 5) for logged-in users
            # - Returns None (which becomes NULL) for guests
            current_user_id = session.get('user_id')

            new_log = AtsLog(
                filename=file.filename,
                score=result_data.get('score', 0),
                
                # FIXED: replace(microsecond=0) keeps it as a DateTime object for SQLite
                # while removing the ugly decimals
                created_at=datetime.now().replace(microsecond=0), 
                
                user_id=current_user_id
            )
            db.session.add(new_log)
            db.session.commit()
            
        except Exception as db_error:
            db.session.rollback()
            print(f"Database Error: {db_error}") 
        # ------------------------------
            
        return jsonify(result_data)
        
    except Exception as e:
        print(f"Processing Error: {e}")
        return jsonify({"error": f"Failed to process document: {str(e)}"}), 500
        
    finally:
        # Cleanup: This ensures the file is deleted regardless of success or error
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/admin/register", methods=["GET", "POST"])
def admin_register():
    if request.method == "POST":
        # Added: Fetch first and last names from the form
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        
        # Kept your existing code
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        hashed_pw = generate_password_hash(password)
        
        # Updated: Insert the new name variables into the database
        db.execute(
            "INSERT INTO admins(first_name, last_name, email, password) VALUES (?, ?, ?, ?)", 
            (first_name, last_name, email, hashed_pw)
        )
        
        db.commit()
        return redirect(url_for("admin_login"))

    return render_template("admin_register.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE email=?", (email,)).fetchone()

        if admin and check_password_hash(admin['password'], password):
            session["admin"] = admin['email']
            return redirect(url_for("admin"))
        else:
            return "Invalid admin credentials"

    return render_template("admin_login.html")



@app.route("/admin")
def admin():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    try:
        # 1. Total Users Count
        total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        
        # 2. ATS Checks Count
        ats_count = db.execute("SELECT COUNT(*) FROM ats_logs").fetchone()[0]
        
        # 3. Predictions Count (Dynamic ✅)
        try:
            prediction_count = db.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
        except:
            prediction_count = 0
            
        # 4. Active Today Count (Dynamic ✅)
        # Assuming you have a column to track activity, otherwise it defaults to 0
        try:
            today = datetime.date.today().strftime('%Y-%m-%d')
            # Adjust the column name 'last_login' to match your actual database column
            active_today = db.execute("SELECT COUNT(*) FROM users WHERE last_login LIKE ?", (f"{today}%",)).fetchone()[0]
        except:
            active_today = 0
        
        # STATUS COLUMN RESTORED ✅
        users = db.execute("SELECT id, name, email, status FROM users").fetchall()

    except sqlite3.OperationalError as e:
        return f"Database Error: {e}. Run your database initialization script!"

    return render_template(
        "admin.html",
        total_users=total_users,
        ats_count=ats_count,
        predictions=prediction_count,  # Updated variable
        active_today=active_today,     # New dynamic variable
        users=users 
    )

@app.route("/toggle_user/<int:user_id>")
def toggle_user(user_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    
    # 1. Get the current status of the user
    user = db.execute("SELECT status FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user:
        current_status = user[0]
        
        # 2. Toggle logic: Flip the status
        if current_status == 'active':
            new_status = 'blocked'
        else:
            new_status = 'active'
            
        # 3. Update the database
        db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
        db.commit()
    
    # 4. Redirect back to the admin dashboard
    return redirect(url_for("admin"))


@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    # Check if admin is logged in
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    
    # Execute DELETE query for the specific user
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    
    # Redirect back to the admin dashboard after deletion
    return redirect(url_for("admin"))

@app.route("/admin/users")
def admin_users():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
        
    db = get_db()
    
    try:
        # 1. Fetch Regular Users
        users = db.execute("""
            SELECT 
                u.id, 
                u.name, 
                u.email, 
                u.status,
                (SELECT result FROM predictions WHERE user_id = u.id ORDER BY id DESC LIMIT 1),
                (SELECT COUNT(*) FROM ats_logs WHERE user_id = u.id)
            FROM users u
        """).fetchall()

        # 2. Fetch Administrators
        admins = db.execute("SELECT id, first_name, last_name, email, role FROM admins").fetchall()

        # 3. Calculate Stats for the Cards
        total_users = len(users)
        total_admins = len(admins) # Count the admins!
        
        predictions_row = db.execute("SELECT COUNT(*) FROM predictions").fetchone()
        predictions_total = predictions_row[0] if predictions_row else 0
        
        avg_score_row = db.execute("SELECT AVG(score) FROM ats_logs").fetchone()
        avg_score = round(avg_score_row[0], 1) if avg_score_row[0] else 0

    except Exception as e:
        print(f"Error in admin_users: {e}")
        total_users, total_admins, avg_score, predictions_total = 0, 0, 0, 0
        users, admins = [], []
    
    # Pass everything to the template
    return render_template(
        "users.html", 
        users=users, 
        admins=admins,
        total_users=total_users, 
        total_admins=total_admins,
        avg_score=avg_score, 
        predictions=predictions_total
    )

@app.route("/admin/ats_reports")
def ats_reports():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
        
    db = get_db()
    
    # Query: Get log details + the name of the user who uploaded it
    reports = db.execute("""
        SELECT 
            l.id, 
            u.name, 
            u.id as user_id, 
            l.filename, 
            l.score, 
            l.created_at 
        FROM ats_logs l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
    """).fetchall()
    
    return render_template("ats_reports.html", reports=reports)

@app.route("/admin/analytics")
def admin_analytics():
    if "admin" not in session:
        return redirect(url_for("admin_login"))
        
    db = get_db()
    
    # Simple count for the dashboard card
    total_scans = db.execute("SELECT COUNT(*) FROM ats_logs").fetchone()[0]
    
    return render_template("analytics.html", total_scans=total_scans)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ==========================================
# PASSWORD RESET LOGIC
# ==========================================
def send_reset_email(user_email, reset_link):
    sender_email = os.environ.get("EMAIL_USER")
    sender_password = os.environ.get("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        print("❌ Email credentials missing in .env!")
        return False

    msg = EmailMessage()
    msg['Subject'] = 'Admin Password Reset Request'
    msg['From'] = sender_email
    msg['To'] = user_email
    msg.set_content(f"Click the link to reset your password: {reset_link}")
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("✅ Email sent successfully!")
            return True
    except Exception as e:
        print(f"❌ SMTP Error: {e}")
        return False

@app.route('/admin/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', "").strip()
        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
        
        if admin:
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO reset_tokens (email, token) VALUES (?, ?)", (email, token))
            db.commit()
            
            reset_link = url_for('reset_password', token=token, _external=True)
            send_reset_email(email, reset_link)
            
        return render_template('forgot_password_done.html') # Suggested separate template
        
    return render_template('forgot_password.html')

@app.route('/admin/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    db = get_db()
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        
        # 1. Verify if the token exists in the database
        # We use record['email'] because of the RowFactory we added earlier
        record = db.execute("SELECT email FROM reset_tokens WHERE token = ?", (token,)).fetchone()
        
        if record:
            # 2. Hash the new password and update the admin table
            hashed_pw = generate_password_hash(new_password)
            db.execute("UPDATE admins SET password = ? WHERE email = ?", (hashed_pw, record['email']))
            
            # 3. Security: Delete the token so it cannot be used again
            db.execute("DELETE FROM reset_tokens WHERE token = ?", (token,))
            db.commit()
            
            # 4. Return "OK" so the JavaScript 'fetch' knows to show the success popup
            return "OK", 200
        else:
            # Return a 400 error so the JavaScript shows the error popup
            return "Invalid or expired token.", 400

    # GET request: Show the reset password page
    return render_template('reset_password.html', token=token)




@app.route('/admin/courses')
def admin_courses():
    # 1. Open the connection to your user database
    conn = sqlite3.connect('database.db')
    
    # This magic line lets us use column names (like course['title']) in our HTML template
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # 2. Fetch all courses (We don't need categories since they aren't in the table anymore)
    cursor.execute("SELECT * FROM courses")
    all_courses = cursor.fetchall()
    
    # 3. Always close the connection when done!
    conn.close()
    
    # 4. CRITICAL FIX: Make sure 'manage_courses.html' is the exact name of your file!
    return render_template('admin_courses.html', courses=all_courses)


from flask import Flask, render_template, request, redirect, url_for, flash
from model import db
from update_db import save_new_course_data


@app.route('/admin/courses/create', methods=['GET', 'POST'])
def create_course():
    # --- PATH 1: Handling Form Submission (POST) ---
    if request.method == 'POST':
        # We pass request.form directly to your save_new_course_data helper
        # It already looks for 'course_title', 'course_slug', and 'short_description'
        success, message = save_new_course_data(request.form)
        
        if success:
            # If the database save was successful, go back to the list
            # flash(message, "success") 
            return redirect(url_for('admin_courses'))
        else:
            # If there was a database error, stay on the page and show the error
            # flash(message, "danger")
            return redirect(url_for('create_course'))

    # --- PATH 2: Just loading the page (GET request) ---
    return render_template('create_course.html', is_edit=False)

# ==========================================
# EDIT COURSE ROUTE
# ==========================================
@app.route('/admin/courses/edit/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()

    # PATH 1: Handle Form Submission (Updating the database)
    if request.method == 'POST':
        title = request.form.get('course_title')
        slug = request.form.get('course_slug')
        description = request.form.get('short_description')

        db.execute('''
            UPDATE courses 
            SET title = ?, slug = ?, description = ? 
            WHERE id = ?
        ''', (title, slug, description, course_id))
        db.commit()

        flash("Course updated successfully!", "success")
        return redirect(url_for('admin_courses'))

    # PATH 2: Load the page (Fetch existing data)
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    
    if not course:
        flash("Course not found!", "error")
        return redirect(url_for('admin_courses'))

    # THE TRICK: Render create_course.html, but pass the 'course' data to it
    # We also pass an 'is_edit' variable so the HTML knows which mode it is in
    return render_template('create_course.html', course=course, is_edit=True)

# DELETE COURSE ROUTE
# ==========================================
@app.route('/admin/courses/delete/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    
    # Delete the specific course
    db.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    db.commit()

    flash("Course deleted successfully!", "success")
    return redirect(url_for('admin_courses'))

import os
from werkzeug.utils import secure_filename

@app.route('/admin/courses/<int:course_id>/manage', methods=['GET', 'POST'])
def manage_course(course_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()

    # --- PATH 1: FORM SUBMISSION (Save Chapter to Database) ---
    if request.method == 'POST':
        # 1. Get standard text fields
        title = request.form.get('chapter_title')
        position = request.form.get('position')
        
        # --- THE CLEANING ROBOT LOGIC STARTS HERE ---
        raw_content = request.form.get('content')          # Get the raw text from TinyMCE
        content = fix_broken_boxes(raw_content)            # Send it to the robot to fix
        # --- THE CLEANING ROBOT LOGIC ENDS HERE ---

        practice_set = request.form.get('practice_set')
        download_label = request.form.get('download_label')
        
        # Checkboxes return "1" if checked, None if unchecked
        is_premium = 1 if request.form.get('is_premium') else 0
        require_pass = 1 if request.form.get('require_pass') else 0

        # 2. Handle File Upload
        file_filename = None
        if 'download_file' in request.files:
            file = request.files['download_file']
            if file and file.filename != '':
                file_filename = secure_filename(file.filename)
                # Save to your uploads folder
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))

        # 3. Insert Chapter into Database
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO chapters (course_id, title, position, content, require_pass, is_premium, download_label, download_file, practice_set)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (course_id, title, position, content, require_pass, is_premium, download_label, file_filename, practice_set))
        
        # Get the ID of the chapter we just created so we can link the questions to it
        chapter_id = cursor.lastrowid 

        # 4. Handle Dynamic Quiz Questions (Using .getlist() to grab arrays)
        questions = request.form.getlist('quiz_question[]')
        corrects = request.form.getlist('quiz_correct[]')
        wrong1s = request.form.getlist('quiz_wrong1[]')
        wrong2s = request.form.getlist('quiz_wrong2[]')
        wrong3s = request.form.getlist('quiz_wrong3[]')

        # Zip loops through all arrays simultaneously. 
        # If the user added 3 questions, this loops 3 times.
        for q, c, w1, w2, w3 in zip(questions, corrects, wrong1s, wrong2s, wrong3s):
            # Only save if the question isn't completely blank
            if q.strip() != "":
                cursor.execute('''
                    INSERT INTO quiz_questions (chapter_id, question, correct_answer, wrong_1, wrong_2, wrong_3)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (chapter_id, q, c, w1, w2, w3))

        db.commit()
        flash("Chapter and Quiz saved successfully!", "success")
        return redirect(url_for('manage_course', course_id=course_id))

    # --- PATH 2: PAGE LOAD (Fetch data to show on screen) ---
    # Fetch the parent course
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    
    if not course:
        flash("Course not found!", "error")
        return redirect(url_for('admin_courses'))

    # Fetch all existing chapters for the Table of Contents sidebar
    chapters = db.execute("SELECT * FROM chapters WHERE course_id = ? ORDER BY position ASC", (course_id,)).fetchall()

    return render_template('manage_course.html', course=course, chapters=chapters, is_edit=False)



# ==========================================
# DELETE CHAPTER ROUTE
# ==========================================
@app.route('/admin/chapters/delete/<int:chapter_id>/<int:course_id>', methods=['POST'])
def delete_chapter(chapter_id, course_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()
    
    # Delete the specific chapter (Quiz questions will delete automatically due to ON DELETE CASCADE in your database setup!)
    db.execute("DELETE FROM chapters WHERE id = ?", (chapter_id,))
    db.commit()

    flash("Chapter deleted successfully!", "success")
    # Redirect back to the manage page for this specific course
    return redirect(url_for('manage_course', course_id=course_id))



  
@app.route('/admin/chapters/edit/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    db = get_db()

    # 1. Fetch the specific chapter you want to edit
    chapter = db.execute("SELECT * FROM chapters WHERE id = ?", (chapter_id,)).fetchone()
    if not chapter:
        flash("Chapter not found!", "error")
        return redirect(url_for('admin_courses'))

    course_id = chapter['course_id']

    # --- PATH 1: FORM SUBMISSION (Save Updates) ---
    if request.method == 'POST':
        title = request.form.get('chapter_title')
        position = request.form.get('position')
        
        # --- THE CLEANING ROBOT LOGIC STARTS HERE ---
        raw_content = request.form.get('content')
        content = fix_broken_boxes(raw_content)
        # --- THE CLEANING ROBOT LOGIC ENDS HERE ---
        
        practice_set = request.form.get('practice_set')
        download_label = request.form.get('download_label')
        is_premium = 1 if request.form.get('is_premium') else 0
        require_pass = 1 if request.form.get('require_pass') else 0

        # File upload: Keep old file if a new one isn't uploaded
        file_filename = chapter['download_file']
        if 'download_file' in request.files:
            file = request.files['download_file']
            if file and file.filename != '':
                file_filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))

        # Update the Chapters table
        db.execute('''
            UPDATE chapters 
            SET title = ?, position = ?, content = ?, require_pass = ?, is_premium = ?, download_label = ?, download_file = ?, practice_set = ?
            WHERE id = ?
        ''', (title, position, content, require_pass, is_premium, download_label, file_filename, practice_set, chapter_id))

        # Update Quiz Questions: Easiest way is to delete old ones and insert the newly submitted ones
        db.execute("DELETE FROM quiz_questions WHERE chapter_id = ?", (chapter_id,))
        
        questions = request.form.getlist('quiz_question[]')
        corrects = request.form.getlist('quiz_correct[]')
        wrong1s = request.form.getlist('quiz_wrong1[]')
        wrong2s = request.form.getlist('quiz_wrong2[]')
        wrong3s = request.form.getlist('quiz_wrong3[]')

        for q, c, w1, w2, w3 in zip(questions, corrects, wrong1s, wrong2s, wrong3s):
            if q.strip() != "":
                db.execute('''
                    INSERT INTO quiz_questions (chapter_id, question, correct_answer, wrong_1, wrong_2, wrong_3)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (chapter_id, q, c, w1, w2, w3))

        db.commit()
        flash("Chapter updated successfully!", "success")
        return redirect(url_for('manage_course', course_id=course_id))

    # --- PATH 2: PAGE LOAD (Fetch data to pre-fill the form) ---
    course = db.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    chapters = db.execute("SELECT * FROM chapters WHERE course_id = ? ORDER BY position ASC", (course_id,)).fetchall()
    quiz_questions = db.execute("SELECT * FROM quiz_questions WHERE chapter_id = ?", (chapter_id,)).fetchall()

    # Pass the data to the template and flip the 'is_edit' switch to True!
    return render_template('manage_course.html', 
                           course=course, 
                           chapters=chapters, 
                           edit_chapter=chapter, # We call it edit_chapter so it doesn't conflict with the chapters list
                           quiz_questions=quiz_questions, 
                           is_edit=True)

@app.route('/faq')
def faq():
    current_user = None
    if "user" in session:
        db = get_db()
        user_identifier = session['user']
        current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()
        
    return render_template('faqs.html', current_user=current_user)

@app.route('/terms')
def terms():
    current_user = None
    if "user" in session:
        db = get_db()
        user_identifier = session['user']
        current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()
        
    return render_template('terms.html', current_user=current_user)

@app.route('/privacy')
def privacy():
    current_user = None
    if "user" in session:
        db = get_db()
        user_identifier = session['user']
        current_user = db.execute("SELECT * FROM users WHERE LOWER(name) = LOWER(?)", (user_identifier,)).fetchone()
        
    return render_template('privacy.html', current_user=current_user)




if __name__ == "__main__":
    app.run(debug=True)

