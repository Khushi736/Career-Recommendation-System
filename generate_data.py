import pandas as pd
import random
import sqlite3
import os

DB_NAME = 'career_database.db'
TABLE_NAME = 'career_skills'

def create_upgraded_database():
    print("🌱 Generating Upgraded AI Training Data for 19 Categories...")
    
    data_map = {
        "Excel/Spreadsheet Expert": {
            "skills": ["vlookup", "xlookup", "index-match", "pivot tables", "macros", "vba", "data cleaning", "reporting", "google sheets"],
            "interests": ["organization", "efficiency", "automation", "data management", "financial tracking"]
        },
        "Content Creator": {
            "skills": ["writing", "seo", "copywriting", "script writing", "storytelling", "canva", "research", "editing"],
            "interests": ["social media", "blogging", "creative writing", "audience engagement", "influencing"]
        },
        "Graphic Designer": {
            "skills": ["photoshop", "illustrator", "typography", "color theory", "branding", "layout design", "canva"],
            "interests": ["arts", "visual design", "creativity", "drawing", "photography"]
        },
        "Video Editor": {
            "skills": ["adobe premiere pro", "after effects", "audio syncing", "color grading", "motion graphics", "storyboarding"],
            "interests": ["filmmaking", "youtube content", "animation", "visual effects", "media production"]
        },
        "Software Developer": {
            "skills": ["python", "java", "javascript", "c++", "git", "algorithms", "data structures", "django", "react", "oop"],
            "interests": ["technology", "coding", "problem solving", "ai", "building apps", "logic"]
        },
        "Web Developer": {
            "skills": ["html", "css", "javascript", "sql", "databases", "hosting", "wordpress", "php", "backend logic"],
            "interests": ["internet technology", "building websites", "ui components", "web security"]
        },
        "Data Analyst": {
            "skills": ["excel", "sql", "tableau", "power bi", "statistics", "pandas", "data visualization", "reporting"],
            "interests": ["data science", "mathematics", "business strategy", "puzzles", "research"]
        },
        "AI/ML Engineer": {
            "skills": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "statistics", "neural networks"],
            "interests": ["automation", "artificial intelligence", "math", "robotics", "future tech"]
        },
        "Finance Professional": {
            "skills": ["accounting", "taxation", "financial modeling", "auditing", "compliance", "tally", "excel"],
            "interests": ["money management", "economics", "investments", "corporate strategy", "banking"]
        },
        "Digital Marketer": {
            "skills": ["seo", "google ads", "google analytics", "ppc", "content marketing", "social media marketing", "email marketing"],
            "interests": ["online growth", "advertising", "consumer behavior", "branding", "market trends"]
        },
        "Sales Executive": {
            "skills": ["communication", "negotiation", "lead generation", "crm", "presentation", "closing deals"],
            "interests": ["networking", "persuasion", "business growth", "traveling", "meeting people"]
        },
        "Human Resource (HR)": {
            "skills": ["hiring", "recruitment", "employee engagement", "payroll", "labor law", "conflict resolution"],
            "interests": ["people management", "organizational culture", "psychology", "mentoring"]
        },
        "Cybersecurity Analyst": {
            "skills": ["networking", "linux", "penetration testing", "ethical hacking", "firewalls", "cryptography"],
            "interests": ["online security", "investigation", "hacking", "digital forensics", "privacy"]
        },
        "Cloud Engineer": {
            "skills": ["aws", "azure", "devops", "linux", "ci/cd", "docker", "kubernetes", "cloud security"],
            "interests": ["server management", "infrastructure", "scaling systems", "automation"]
        },
        "Teacher/Trainer": {
            "skills": ["subject expertise", "public speaking", "curriculum design", "mentorship", "patience", "presentation"],
            "interests": ["education", "helping others", "knowledge sharing", "public service"]
        },
        "Customer Support": {
            "skills": ["communication", "troubleshooting", "patience", "crm tools", "active listening", "technical support"],
            "interests": ["problem solving", "helping people", "client satisfaction", "service"]
        },
        "UI/UX Designer": {
            "skills": ["figma", "wireframing", "prototyping", "user research", "adobe xd", "visual design", "interaction design"],
            "interests": ["user psychology", "app design", "human behavior", "web aesthetics"]
        },
        "Government/Civil Servant": {
            "skills": ["aptitude", "general knowledge", "reasoning", "policy analysis", "public administration"],
            "interests": ["stability", "public service", "governance", "social welfare"]
        },
        "Entrepreneur/Freelancer": {
            "skills": ["leadership", "strategic planning", "marketing", "financial management", "risk assessment", "sales"],
            "interests": ["business ownership", "risk taking", "innovation", "independence"]
        }
    }

    educations = ["High School", "Bachelor's", "Master's", "PhD", "Diploma"]
    expanded_data = []

    for career, attributes in data_map.items():
        print(f"🚀 Generating data for: {career}...")
        unique_combinations = set()
        attempts = 0 # Safety counter
        
        # Determine sampling limits based on available data
        max_s = min(len(attributes["skills"]), 5)
        max_i = min(len(attributes["interests"]), 3)

        while len(unique_combinations) < 200 and attempts < 1000:
            attempts += 1
            
            # Use random.randint with safe ranges
            num_s = random.randint(min(3, len(attributes["skills"])), max_s)
            num_i = random.randint(min(2, len(attributes["interests"])), max_i)
            
            sample_skills = tuple(sorted(random.sample(attributes["skills"], num_s)))
            sample_interests = tuple(sorted(random.sample(attributes["interests"], num_i)))
            
            combined_hash = (sample_skills, sample_interests)
            
            if combined_hash not in unique_combinations:
                unique_combinations.add(combined_hash)
                
                edu = random.choice(educations)
                if edu in ["High School", "Diploma"]: age = random.randint(18, 25)
                elif edu == "Bachelor's": age = random.randint(22, 35)
                else: age = random.randint(25, 50)

                expanded_data.append({
                    "age": age,
                    "education": edu,
                    "skills": ", ".join(sample_skills),
                    "interests": ", ".join(sample_interests),
                    "role": career
                })

    df = pd.DataFrame(expanded_data)
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"\n✅ Success! {len(df)} rows generated across {len(data_map)} categories.")

if __name__ == "__main__":
    create_upgraded_database()