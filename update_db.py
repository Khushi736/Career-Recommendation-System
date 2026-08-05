# import sqlite3
# import os
# from werkzeug.utils import secure_filename
# from extensions import db
# from model import Course, CourseObjective, Module, Lesson, FAQ

# # ... rest of your code ...
# # import sqlite3
# # import os
# # from werkzeug.utils import secure_filename
# # from model import db, Course, CourseObjective, Module, Lesson, FAQ

# # 1. Connect to the database that stores USER info
# # Based on your setup, "database.db" is where the 'users' table lives.
# conn = sqlite3.connect("database.db")
# cursor = conn.cursor()

# print("Updating user database (database.db) without losing data...")

# # --- NEW SECTION: CREATE COURSES & CATEGORIES TABLES ---
# print("\nChecking and creating new tables...")

# new_tables = {
#     "categories": """
#         CREATE TABLE IF NOT EXISTS categories (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT NOT NULL
#         )
#     """,
#     "courses": """
#         CREATE TABLE IF NOT EXISTS courses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             title TEXT NOT NULL,
#             description TEXT NOT NULL,
#             instructor TEXT NOT NULL,
#             duration TEXT,
#             thumbnail_url TEXT,
#             category_id INTEGER,
#             FOREIGN KEY(category_id) REFERENCES categories(id)
#         )
#     """
# }

# for table_name, query in new_tables.items():
#     try:
#         cursor.execute(query)
#         print(f"✅ Table '{table_name}' is ready.")
#     except Exception as e:
#         print(f"❌ Error creating table '{table_name}': {e}")


# # --- EXISTING SECTION: ALTER TABLES ---
# print("\nChecking and updating existing table columns...")

# # 2. Complete list of columns (Keeping all your existing ones + matching dashboard requirements)
# updates = [
#     "ALTER TABLE users ADD COLUMN mobile TEXT",
#     "ALTER TABLE users ADD COLUMN resume TEXT",
#     "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'",
#     "ALTER TABLE users ADD COLUMN last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
#     "ALTER TABLE users ADD COLUMN cv_path TEXT",           # Added for CV reading logic
#     "ALTER TABLE users ADD COLUMN profile_pic TEXT",       # Added for profile logic
#     "ALTER TABLE ats_logs ADD COLUMN user_id INTEGER",
#     "ALTER TABLE predictions ADD COLUMN user_id INTEGER",
#     "ALTER TABLE predictions ADD COLUMN confidence REAL",
#     "ALTER TABLE users ADD COLUMN about TEXT",
#     "ALTER TABLE users ADD COLUMN projects TEXT",
#     "ALTER TABLE users ADD COLUMN skills TEXT"
# ]

# # 3. Try to add each column
# for query in updates:
#     try:
#         cursor.execute(query)
#         # Extract the column name for the success message
#         col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
#         print(f"✅ Added '{col_name}' column successfully.")
        
#     except sqlite3.OperationalError as e:
#         # SQLite throws an error if the column is already there. We can safely ignore it.
#         error_msg = str(e).lower()
#         if "duplicate column name" in error_msg:
#             col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
#             print(f"⏩ Column '{col_name}' already exists. Skipping.")
#         elif "no such table" in error_msg:
#             table_name = query.split("TABLE ")[1].split(" ")[0]
#             print(f"❌ Table '{table_name}' does not exist in database.db. Run init_database.py first.")
#         else:
#             print(f"❌ Error with query '{query}': {e}")



# # Define where you want files saved (e.g., 'static/uploads/')
# UPLOAD_FOLDER = 'static/uploads/courses/'

# def save_file(file_obj):
#     """Helper function to save a file and return its path."""
#     if file_obj and file_obj.filename != '':
#         filename = secure_filename(file_obj.filename)
#         # Ensure directory exists
#         os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#         file_path = os.path.join(UPLOAD_FOLDER, filename)
#         file_obj.save(file_path)
#         return file_path
#     return None

# def save_new_course_data(form_data, files_data):
#     try:
#         # --- STEP 1: Process Files & Basic Course Details ---
#         cover_path = save_file(files_data.get('cover_photo'))
#         promo_path = save_file(files_data.get('promo_video'))

#         new_course = Course(
#             title=form_data.get('title'),
#             subtitle=form_data.get('subtitle'),
#             category_id=form_data.get('category_id'),
#             subcategory_id=form_data.get('subcategory_id'),
#             level=form_data.get('level'),
#             price=form_data.get('price'),
#             instructor=form_data.get('instructor'),
#             description=form_data.get('description'),
#             cover_photo=cover_path,
#             promo_video=promo_path
#         )
#         db.session.add(new_course)
#         db.session.flush() # Flushes to DB to generate course ID

#         # --- STEP 1 (Cont): Save Dynamic Objectives ---
#         for obj_text in form_data.getlist('objectives[]'):
#             if obj_text.strip():
#                 db.session.add(CourseObjective(objective_text=obj_text, course_id=new_course.id))

#         # --- STEP 2: Save Modules and Lessons ---
#         module_index = 1
#         while f'module_{module_index}_title' in form_data:
#             mod_title = form_data.get(f'module_{module_index}_title')
            
#             if mod_title.strip():
#                 new_module = Module(title=mod_title, course_id=new_course.id)
#                 db.session.add(new_module)
#                 db.session.flush() # Get the Module ID

#                 # Fetch lessons for this specific module
#                 lesson_titles = form_data.getlist(f'module_{module_index}_lesson_titles[]')
#                 lesson_files = files_data.getlist(f'module_{module_index}_lesson_files[]')
                
#                 for i in range(len(lesson_titles)):
#                     if lesson_titles[i].strip():
#                         # Save the lesson file if one was uploaded
#                         lesson_file_path = None
#                         if i < len(lesson_files):
#                             lesson_file_path = save_file(lesson_files[i])

#                         db.session.add(Lesson(
#                             title=lesson_titles[i], 
#                             file_path=lesson_file_path, 
#                             module_id=new_module.id
#                         ))
            
#             module_index += 1

#         # --- STEP 3: Save FAQs ---
#         faq_questions = form_data.getlist('faq_questions[]')
#         faq_answers = form_data.getlist('faq_answers[]')
        
#         for q, a in zip(faq_questions, faq_answers):
#             if q.strip() and a.strip():
#                 db.session.add(FAQ(question=q, answer=a, course_id=new_course.id))

#         # --- COMMIT TRANSACTION ---
#         db.session.commit()
#         return True, "Course successfully created and saved!"

#     except Exception as e:
#         db.session.rollback() # Abort everything if a single error occurs
#         return False, f"Error saving course: {str(e)}"
    
# import os
# from werkzeug.utils import secure_filename
# from extensions import db
# from model import Module, Lesson

# UPLOAD_FOLDER = 'static/uploads/lessons/'

# def save_lesson_file(file_obj):
#     """Saves video/pdf files for lessons."""
#     if file_obj and file_obj.filename != '':
#         filename = secure_filename(file_obj.filename)
#         os.makedirs(UPLOAD_FOLDER, exist_ok=True)
#         file_path = os.path.join(UPLOAD_FOLDER, filename)
#         file_obj.save(file_path)
#         return file_path
#     return None

# def save_course_curriculum(course_id, form_data, files_data):
#     """Saves an infinite amount of dynamic modules and lessons to a specific course."""
#     try:
#         module_index = 1
        
#         # Loop as long as the HTML form is sending 'module_X_title'
#         while f'module_{module_index}_title' in form_data:
#             mod_title = form_data.get(f'module_{module_index}_title')
            
#             if mod_title and mod_title.strip():
#                 # 1. Create the Module
#                 new_module = Module(title=mod_title, course_id=course_id)
#                 db.session.add(new_module)
#                 db.session.flush() # Get the new module.id immediately

#                 # 2. Fetch the Lessons attached to THIS specific module
#                 lesson_titles = form_data.getlist(f'module_{module_index}_lesson_titles[]')
#                 lesson_files = files_data.getlist(f'module_{module_index}_lesson_files[]')
                
#                 # 3. Save the Lessons
#                 for i in range(len(lesson_titles)):
#                     if lesson_titles[i].strip():
#                         lesson_file_path = None
#                         # Check if a file was actually uploaded for this specific lesson
#                         if i < len(lesson_files) and lesson_files[i].filename != '':
#                             lesson_file_path = save_lesson_file(lesson_files[i])

#                         new_lesson = Lesson(
#                             title=lesson_titles[i], 
#                             file_path=lesson_file_path, 
#                             module_id=new_module.id
#                         )
#                         db.session.add(new_lesson)
            
#             module_index += 1

#         db.session.commit()
#         return True, "Curriculum saved successfully!"

#     except Exception as e:
#         db.session.rollback()
#         return False, f"Error saving curriculum: {str(e)}"

# # Save changes and close
# conn.commit()
# conn.close()

# print("\nDatabase update complete! Your user data in 'database.db' is now updated.")



# import sqlite3


# # --- CONFIGURATION ---
# UPLOAD_FOLDER = 'static/uploads/courses/'
# LESSON_UPLOAD_FOLDER = 'static/uploads/lessons/'


# # =====================================================================
# # DATABASE UPDATE SCRIPT
# # This ONLY runs if you type `python update_db.py` in the terminal
# # =====================================================================
# if __name__ == "__main__":
#     # Import app here so we can use its context for SQLAlchemy
#     from app import app
    
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()

#     print("Updating user database (database.db) without losing data...")

#     # --- NEW SECTION: CREATE COURSES & CATEGORIES TABLES ---
#     print("\nChecking and creating new tables...")

#     new_tables = {
#         "categories": """
#             CREATE TABLE IF NOT EXISTS categories (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT NOT NULL
#             )
#         """,
#         "courses": """
#             CREATE TABLE IF NOT EXISTS courses (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 title TEXT NOT NULL,
#                 subtitle TEXT,
#                 level TEXT,
#                 price TEXT,
#                 instructor TEXT,
#                 description TEXT,
#                 cover_photo TEXT,
#                 promo_video TEXT,
#                 category_id INTEGER,
#                 subcategory_id INTEGER,
#                 FOREIGN KEY(category_id) REFERENCES categories(id)
#             )
#         """
#     }

#     for table_name, query in new_tables.items():
#         try:
#             cursor.execute(query)
#             print(f"✅ Table '{table_name}' is ready.")
#         except Exception as e:
#             print(f"❌ Error creating table '{table_name}': {e}")


#     # --- EXISTING SECTION: ALTER TABLES ---
#     print("\nChecking and updating existing table columns...")

#     # Removed DEFAULT CURRENT_TIMESTAMP from last_login to fix the SQLite error
#     updates = [
#         "ALTER TABLE users ADD COLUMN mobile TEXT",
#         "ALTER TABLE users ADD COLUMN resume TEXT",
#         "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'",
#         "ALTER TABLE users ADD COLUMN last_login TIMESTAMP", 
#         "ALTER TABLE users ADD COLUMN cv_path TEXT",           
#         "ALTER TABLE users ADD COLUMN profile_pic TEXT",       
#         "ALTER TABLE ats_logs ADD COLUMN user_id INTEGER",
#         "ALTER TABLE predictions ADD COLUMN user_id INTEGER",
#         "ALTER TABLE predictions ADD COLUMN confidence REAL",
#         "ALTER TABLE users ADD COLUMN about TEXT",
#         "ALTER TABLE users ADD COLUMN projects TEXT",
#         "ALTER TABLE users ADD COLUMN skills TEXT"
#     ]

#     for query in updates:
#         try:
#             cursor.execute(query)
#             col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
#             print(f"✅ Added '{col_name}' column successfully.")
            
#         except sqlite3.OperationalError as e:
#             error_msg = str(e).lower()
#             if "duplicate column name" in error_msg:
#                 col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
#                 print(f"⏩ Column '{col_name}' already exists. Skipping.")
#             elif "no such table" in error_msg:
#                 table_name = query.split("TABLE ")[1].split(" ")[0]
#                 print(f"❌ Table '{table_name}' does not exist in database.db. Run init_database.py first.")
#             else:
#                 print(f"❌ Error with query '{query}': {e}")

#     # Save changes and close
#     conn.commit()
#     conn.close()
    
#     # Sync SQLAlchemy Models
#     print("\nSyncing SQLAlchemy tables...")
#     with app.app_context():
#         db.create_all()

#     print("\nDatabase update complete! Your user data in 'database.db' is now updated.")

# import sqlite3
# import os
# from extensions import db
# from model import Course

# # =====================================================================
# # HELPER FUNCTIONS (Used by app.py)
# # =====================================================================

# def save_new_course_data(form_data):
#     """
#     Saves Course Details from the single-page 'Create Course' form.
#     Matches the frontend fields: course_title, course_slug, short_description.
#     """
#     try:
#         # Extract exactly what is in your current frontend
#         new_course = Course(
#             title=form_data.get('course_title'),
#             slug=form_data.get('course_slug'),
#             description=form_data.get('short_description')
#         )
        
#         db.session.add(new_course)
#         db.session.commit()
        
#         return True, "Course created successfully!"

#     except Exception as e:
#         db.session.rollback()
#         return False, f"Error saving course: {str(e)}"


# # =====================================================================
# # DATABASE UPDATE SCRIPT
# # This runs if you type `python update_db.py` in the terminal
# # =====================================================================
# if __name__ == "__main__":
#     from app import app
    
#     conn = sqlite3.connect("database.db")
#     cursor = conn.cursor()

#     print("Checking and updating database tables...")

#     # Ensure the courses table has the columns matching your frontend
#     # Note: Using 'description' as the column name to match your SQLAlchemy model
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS courses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             title TEXT NOT NULL,
#             slug TEXT NOT NULL,
#             description TEXT
#         )
#     """)
#     print("✅ Table 'courses' is ready.")

#     # --- UPDATING EXISTING USERS TABLE ---
#     # This keeps your existing user column updates in case you need them
#     updates = [
#         "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'",
#         "ALTER TABLE users ADD COLUMN last_login TIMESTAMP",
#         "ALTER TABLE users ADD COLUMN profile_pic TEXT",
#         "ALTER TABLE users ADD COLUMN about TEXT",
#         "ALTER TABLE users ADD COLUMN skills TEXT"
#     ]

#     for query in updates:
#         try:
#             cursor.execute(query)
#             col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
#             print(f"✅ Added '{col_name}' column.")
#         except sqlite3.OperationalError:
#             # Column already exists
#             pass

#     conn.commit()
#     conn.close()
    
#     # Sync SQLAlchemy Models
#     with app.app_context():
#         db.create_all()

#     print("\nDatabase update complete!")
import sqlite3
import os
from extensions import db
from model import Course, UserProgress, Profile  # <-- Added UserProgress here

# =====================================================================
# HELPER FUNCTIONS (Used by app.py)
# =====================================================================

def save_new_course_data(form_data):
    try:
        new_course = Course(
            title=form_data.get('course_title'),
            slug=form_data.get('course_slug'),
            description=form_data.get('short_description')
        )
        db.session.add(new_course)
        db.session.commit()
        print("✅ Course saved to DB successfully!") 
        return True, "Success"
    except Exception as e:
        db.session.rollback()
        print(f"❌ DATABASE ERROR: {e}") 
        return False, str(e)


# =====================================================================
# DATABASE UPDATE SCRIPT
# This runs if you type `python update_db.py` in the terminal
# =====================================================================
if __name__ == "__main__":
    # Import app inside the block to avoid circular import issues
    from app import app
    
    # 1. RAW SQLITE UPDATES (For structural changes)
    
    # --- UNIFIED DATABASE PATH ---
    # Get the exact path to the folder where this script lives
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Point directly to the database.db in the main folder
    db_path = os.path.join(basedir, "database.db")
    
    # Connect to the database inside the instance folder!
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # -----------------------

    print(f"Checking and updating database at: {db_path}")

    # Ensure the courses table exists with columns matching your frontend
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL,
            description TEXT
        )
    """)
    print("✅ Table 'courses' is ready.")

    # --- NEW TABLES FOR MANAGE CHAPTERS ---
    # Ensure the chapters table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            position INTEGER NOT NULL,
            content TEXT,
            require_pass BOOLEAN DEFAULT 0,
            is_premium BOOLEAN DEFAULT 0,
            download_label TEXT,
            download_file TEXT,
            practice_set TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    print("✅ Table 'chapters' is ready.")

    # Ensure the quiz questions table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            wrong_1 TEXT NOT NULL,
            wrong_2 TEXT NOT NULL,
            wrong_3 TEXT NOT NULL,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
        )
    """)
    print("✅ Table 'quiz_questions' is ready.")
    # --------------------------------------
    
    # --- NEW TABLE FOR USER PROGRESS ---
    # Ensure the user progress table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chapter_id INTEGER NOT NULL,
            status TEXT DEFAULT 'not_started',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE,
            CONSTRAINT _user_chapter_uc UNIQUE (user_id, chapter_id)
        )
    """)
    print("✅ Table 'user_progress' is ready.")
    # --------------------------------------

    # --- NEW TABLE FOR PROFILES (CV PARSING DATA) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            about TEXT,
            work_experience TEXT,
            education TEXT,
            certifications TEXT,
            skills TEXT,
            interests TEXT,
            languages TEXT,
            projects TEXT,
            achievements TEXT,
            linkedin_url TEXT,
            github_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    print("✅ Table 'profiles' is ready.")

    # --- UPDATING EXISTING USERS TABLE ---
    updates = [
        "ALTER TABLE users ADD COLUMN mobile TEXT",
        "ALTER TABLE users ADD COLUMN resume TEXT",
        "ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'",
        "ALTER TABLE users ADD COLUMN last_login TIMESTAMP",
        "ALTER TABLE users ADD COLUMN profile_pic TEXT",
        "ALTER TABLE users ADD COLUMN about TEXT",
        "ALTER TABLE users ADD COLUMN skills TEXT",
        "ALTER TABLE profiles ADD COLUMN languages TEXT"
    ]

    for query in updates:
        try:
            cursor.execute(query)
            col_name = query.split("ADD COLUMN ")[1].split(" ")[0]
            print(f"✅ Added '{col_name}' column.")
        except sqlite3.OperationalError as e:
            # Skip if column already exists
            if "duplicate column name" in str(e).lower():
                continue
            # Skip if users table doesn't exist yet
            if "no such table: users" in str(e).lower():
                print("⏩ Users table doesn't exist yet, skipping column updates.")
                break
            print(f"❌ Error with query: {e}")

    conn.commit()
    conn.close()
    
    # 2. SYNC SQLALCHEMY MODELS
    print("\nSyncing SQLAlchemy tables...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ SQLAlchemy models synced successfully.")
        except Exception as e:
            print(f"❌ Error syncing models: {e}")

    print("\nDatabase update complete!")