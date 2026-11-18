import mysql.connector

# ==========================================
# CONNECT TO MYSQL
# ==========================================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="innovovault"
)

cursor = conn.cursor()

# ==========================================
# REMOVE OLD EMPTY PROJECT TABLES
# ==========================================

cursor.execute("DROP TABLE IF EXISTS previous_projects")
cursor.execute("DROP TABLE IF EXISTS submitted_projects")
cursor.execute("DROP TABLE IF EXISTS project_proposals")

# ADMIN TABLE


cursor.execute("""
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL
)
""")


# ACADEMIC YEARS TABLE


cursor.execute("""
CREATE TABLE IF NOT EXISTS academic_years (
    id INT AUTO_INCREMENT PRIMARY KEY,
    year VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'Inactive'
)
""")


# TEAMS TABLE


cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    academic_year_id INT NOT NULL,
    team_id VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    first_login BOOLEAN DEFAULT TRUE,

    UNIQUE (team_id),
    UNIQUE (academic_year_id, team_id),

    FOREIGN KEY (academic_year_id)
        REFERENCES academic_years(id)
        ON DELETE CASCADE
)
""")


# TEAM DETAILS TABLE


cursor.execute("""
CREATE TABLE IF NOT EXISTS team_details (
    id INT AUTO_INCREMENT PRIMARY KEY,

    team_id VARCHAR(50) UNIQUE NOT NULL,

    leader_name VARCHAR(100) NOT NULL,
    leader_roll VARCHAR(30) UNIQUE NOT NULL,

    member2_name VARCHAR(100),
    member2_roll VARCHAR(30),

    member3_name VARCHAR(100),
    member3_roll VARCHAR(30),

    member4_name VARCHAR(100),
    member4_roll VARCHAR(30),

    guide_name VARCHAR(100),

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON DELETE CASCADE
)
""")


# PROJECT PROPOSALS TABLE


cursor.execute("""
CREATE TABLE IF NOT EXISTS project_proposals (
    id INT AUTO_INCREMENT PRIMARY KEY,

    team_id VARCHAR(50) NOT NULL,

    proposal_number INT NOT NULL,

    title VARCHAR(255) NOT NULL,

    domain VARCHAR(100),

    abstract TEXT NOT NULL,

    status VARCHAR(20) DEFAULT 'Pending',

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON DELETE CASCADE
)
""")

# SUBMITTED PROJECTS TABLE



cursor.execute("""
CREATE TABLE submitted_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,

    academic_year_id INT NOT NULL,

    team_id VARCHAR(50) NOT NULL,

    project_title VARCHAR(255) NOT NULL,

    domain VARCHAR(100),

    technologies VARCHAR(255),

    abstract TEXT,

    problem_statement TEXT,

    proposed_solution TEXT,

    expected_impact TEXT,

    detailed_description TEXT,

    tags VARCHAR(255),

    similarity_score DECIMAL(5,2) DEFAULT 0,

    novelty_score DECIMAL(5,2) DEFAULT 0,

    status VARCHAR(20) DEFAULT 'Pending',

    rejection_reason TEXT,

    report_file VARCHAR(255),

    source_code_zip VARCHAR(255),

    demo_link VARCHAR(255),

    submitted_on DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (academic_year_id)
        REFERENCES academic_years(id)
        ON DELETE CASCADE,

    FOREIGN KEY (team_id)
        REFERENCES teams(team_id)
        ON DELETE CASCADE
)
""")

# ==========================================
# PREVIOUS PROJECTS TABLE
# ==========================================
# Used by similarity checking and Explore Projects

cursor.execute("""
CREATE TABLE previous_projects (
    id INT AUTO_INCREMENT PRIMARY KEY,

    title VARCHAR(255) NOT NULL,

    abstract TEXT,

    domain VARCHAR(100),

    technology VARCHAR(255),

    status VARCHAR(20) DEFAULT 'Approved',

    created_on DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

# ==========================================
# SAVE CHANGES
# ==========================================

conn.commit()

print("==========================================")
print("INNOVOVAULT DATABASE SETUP SUCCESSFUL!")
print("==========================================")
print("Tables created:")
print("1. admin")
print("2. academic_years")
print("3. teams")
print("4. team_details")
print("5. project_proposals")
print("6. submitted_projects")
print("7. previous_projects")
print("==========================================")

cursor.close()
conn.close()