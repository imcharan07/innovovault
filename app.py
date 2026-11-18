from flask import Flask, render_template, request, redirect, url_for,session
from db import get_connection
from flask import flash
import mysql.connector
import secrets
import string
import os
from werkzeug.utils import secure_filename
from similarity import calculate_similarity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "innovovault@123"
app.config["REPORT_FOLDER"] = "uploads/reports"
app.config["SOURCE_FOLDER"] = "uploads/source_code"
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        admin_id = request.form["admin_id"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
      "SELECT * FROM innovovault_auth.admin WHERE admin_id=%s AND password=%s",
    (admin_id, password)
)

        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin:
            return redirect(url_for("admin_dashboard"))
        else:
            return "Invalid Admin ID or Password"

    return render_template("admin_login.html")


@app.route("/team-login", methods=["GET", "POST"])
def team_login():

    if request.method == "POST":

        team_id = request.form.get("team_id", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                team_id,
                password,
                first_login
            FROM innovovault_teams.teams
            WHERE team_id = %s
        """, (team_id,))

        team = cursor.fetchone()

        cursor.close()
        conn.close()

        # Invalid Team ID
        if not team:
            return render_template(
                "login.html",
                message="Invalid Team ID or Password"
            )

        # Invalid Password
        if team["password"] != password:
            return render_template(
                "login.html",
                message="Invalid Team ID or Password"
            )

        # Login successful
        session["team_id"] = team["team_id"]

        # First login -> complete team details
        if team["first_login"] == 1:
            return redirect(url_for("team_details"))

        # Normal login -> dashboard
        return redirect(url_for("team_dashboard"))

    return render_template(
        "login.html",
        message=None
    )


@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "team_id" not in session:
        return redirect(url_for("team_login"))

    team_id = session["team_id"]

    message = None
    success = False

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:

            return render_template(
                "change_password.html",
                message="New passwords do not match.",
                success=False
            )

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT password
            FROM innovovault_teams.teams
            WHERE team_id=%s
        """, (team_id,))

        team = cursor.fetchone()

        if not team:

            cursor.close()
            conn.close()

            session.clear()

            return redirect(url_for("team_login"))

        if team["password"] != current_password:

            cursor.close()
            conn.close()

            return render_template(
                "change_password.html",
                message="Current password is incorrect.",
                success=False
            )

        cursor.execute("""
            UPDATE innovovault_teams.teams
            SET password=%s,
                first_login=0
            WHERE team_id=%s
        """, (
            new_password,
            team_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return render_template(
            "change_password.html",
            message="Password changed successfully!",
            success=True
        )

    return render_template(
        "change_password.html",
        message=message,
        success=success
    )


@app.route("/save-team-details", methods=["POST"])
def save_team_details():

    team_id = session.get("team_id")

    if not team_id:
        return redirect(url_for("team_login"))

    leader_name = request.form.get("leader_name")
    leader_roll = request.form.get("leader_roll")

    member2_name = request.form.get("member2_name")
    member2_roll = request.form.get("member2_roll")

    member3_name = request.form.get("member3_name")
    member3_roll = request.form.get("member3_roll")

    member4_name = request.form.get("member4_name")
    member4_roll = request.form.get("member4_roll")

    guide_name = request.form.get("guide_name")

    conn = get_connection()
    cursor = conn.cursor()

    # Save complete team details
    cursor.execute("""
        INSERT INTO innovovault_teams.team_details (
            team_id,
            leader_name,
            leader_roll,
            member2_name,
            member2_roll,
            member3_name,
            member3_roll,
            member4_name,
            member4_roll,
            guide_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        team_id,
        leader_name,
        leader_roll,
        member2_name,
        member2_roll,
        member3_name,
        member3_roll,
        member4_name,
        member4_roll,
        guide_name
    ))

    # First login completed
    cursor.execute("""
        UPDATE innovovault_teams.teams
        SET first_login = 0
        WHERE team_id = %s
    """, (team_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("team_dashboard"))

@app.route("/team-dashboard")
def team_dashboard():

    if "team_id" not in session:
        return redirect(url_for("team_login"))

    team_id = session["team_id"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            leader_name,
            leader_roll,
            member2_name,
            member2_roll,
            member3_name,
            member3_roll,
            member4_name,
            member4_roll,
            guide_name
        FROM innovovault_teams.team_details
        WHERE team_id=%s
    """, (team_id,))

    team = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "team_dashboard.html",
        team_id=team_id,
        team=team
    )


@app.route("/team-details")
def team_details():

    if "team_id" not in session:
        return redirect(url_for("team_login"))

    return render_template("team_details.html")

@app.route("/submit-project", methods=["GET", "POST"])
def submit_project():

    if "team_id" not in session:
        return redirect(url_for("team_login"))

    if request.method == "POST":

        conn = get_connection()
        cursor = conn.cursor()

        # Team ID
        team_id = session["team_id"]

        # Get Academic Year
        cursor.execute("""
            SELECT academic_year_id
            FROM innovovault_teams.teams
            WHERE team_id=%s
        """, (team_id,))

        academic_year = cursor.fetchone()
        academic_year_id = academic_year[0]

        # Form Data
        project_title = request.form["project_title"]
        domain = request.form["domain"]
        technologies = request.form["technologies"]
        abstract = request.form["abstract"]
        problem_statement = request.form["problem_statement"]
        proposed_solution = request.form["proposed_solution"]
        expected_impact = request.form["expected_impact"]
        detailed_description = request.form["detailed_description"]
        tags = request.form["tags"]

        report_name = ""
        source_name = ""

        

        # ==========================
        # Calculate Similarity
        # ==========================

        new_project = project_title + " " + abstract

        cursor.execute("""
SELECT title, abstract
FROM innovovault_repository.previous_projects
WHERE status='Approved'
""")

        rows = cursor.fetchall()

        old_projects = []

        for row in rows:
            title = row[0] if row[0] else ""
            abs_text = row[1] if row[1] else ""
            old_projects.append(title + " " + abs_text)

        similarity_score = calculate_similarity(new_project, old_projects)
        novelty_score = round(100 - similarity_score, 2)

        # ==========================
        # Save into Database
        # ==========================

        cursor.execute("""
INSERT INTO innovovault_submission.submitted_projects
(
    academic_year_id,
    team_id,
    project_title,
    domain,
    technologies,
    abstract,
    problem_statement,
    proposed_solution,
    expected_impact,
    detailed_description,
    tags,
    similarity_score,
    novelty_score,
    status
)
VALUES
(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
""",
(
    academic_year_id,
    team_id,
    project_title,
    domain,
    technologies,
    abstract,
    problem_statement,
    proposed_solution,
    expected_impact,
    detailed_description,
    tags,
    similarity_score,
    novelty_score,
    "Pending"
))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("team_dashboard"))
    flash("Project proposal submitted successfully!Wait for the faculty approval.")
    return render_template("submit_project.html")

@app.route("/project-proposals")
def project_proposals():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT *
    FROM innovovault_submission.submitted_projects
    WHERE status = 'Pending'
    ORDER BY submitted_on DESC
""")

    proposals = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "project_proposals.html",
        proposals=proposals
    )


@app.route("/create-team", methods=["GET", "POST"])
def create_team():

    if request.method == "POST":

        academic_year = request.form["academic_year"]
        team_id = request.form["team_id"]

        # Generate Temporary Password
        characters = string.ascii_letters + string.digits + "@#$"

        password = "".join(
            secrets.choice(characters)
            for _ in range(8)
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
    "SELECT id FROM innovovault_teams.academic_years WHERE year=%s",
    (academic_year,)
)

        year = cursor.fetchone()

        if year is None:

            conn.close()

            return render_template(
                "create_team.html",
                message="Academic Year Not Found!"
            )

        academic_year_id = year[0]

        try:

            cursor.execute("""
            INSERT INTO innovovault_teams.teams
            (academic_year_id, team_id, password)
            VALUES (%s, %s, %s)
            """,
            (academic_year_id, team_id, password))

            conn.commit()
            cursor.close()
            conn.close()

            return render_template(
                "create_team.html",
                success=True,
                team_id=team_id,
                password=password
            )

        except mysql.connector.IntegrityError:

            conn.close()

            return render_template(
                "create_team.html",
                message="Team ID already exists!"
            )

    return render_template("create_team.html")

@app.route("/explore-projects")
def explore_projects():

    search = request.args.get("search", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute("""
            SELECT
                title,
                abstract,
                domain,
                technology,
                status
            FROM innovovault_repository.previous_projects
            WHERE
                title LIKE %s
                OR abstract LIKE %s
                OR domain LIKE %s
                OR technology LIKE %s
        """,
        (
            "%"+search+"%",
            "%"+search+"%",
            "%"+search+"%",
            "%"+search+"%"
        ))

    else:

        cursor.execute("""
            SELECT
                title,
                abstract,
                domain,
                technology,
                status
            FROM innovovault_repository.previous_projects
        """)

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "explore.html",
        projects=projects
    )

@app.route("/admin-review")
def admin_review():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM innovovault_submission.submitted_projects
        WHERE status='Pending'
    """)

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_review.html",
        projects=projects
    )

@app.route("/view-project/<int:id>")
def view_project(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.project_title,
            sp.domain,
            sp.technologies,
            sp.abstract,
            sp.problem_statement,
            sp.proposed_solution,
            sp.expected_impact,
            sp.detailed_description,
            sp.tags,
            ay.year AS academic_year
        FROM innovovault_submission.submitted_projects sp
        JOIN innovovault_teams.academic_years ay
        ON sp.academic_year_id = ay.id
        WHERE sp.id=%s
    """, (id,))

    project = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "view_project.html",
        project=project
    )

@app.route("/review-project/<int:id>")
def review_project(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            sp.*,
            ay.year AS academic_year
        FROM innovovault_submission.submitted_projects sp
        JOIN innovovault_teams.academic_years ay
        ON sp.academic_year_id = ay.id
        WHERE sp.id=%s
    """, (id,))

    project = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "review_project.html",
        project=project
    )

@app.route("/approve-project/<int:id>")
def approve_project(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get project details
    cursor.execute("""
        SELECT
            project_title,
            abstract,
            domain,
            technologies
        FROM innovovault_submission.submitted_projects
        WHERE id=%s
    """, (id,))

    project = cursor.fetchone()

    if project:

        # Update proposal status
        cursor.execute("""
            UPDATE innovovault_submission.submitted_projects
            SET status='Approved'
            WHERE id=%s
        """, (id,))

        # Store only required fields in previous_projects
        cursor.execute("""
            INSERT INTO innovovault_repository.previous_projects
            (
                title,
                abstract,
                domain,
                technology,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s)
        """,
        (
            project["project_title"],
            project["abstract"],
            project["domain"],
            project["technologies"],
            "Approved"
        ))

        conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("admin_review"))
    
@app.route("/reject-project/<int:id>", methods=["POST"])
def reject_project(id):

    reason = request.form["reason"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE innovovault_submission.submitted_projects
        SET
            status='Rejected',
            rejection_reason=%s
        WHERE id=%s
    """, (reason, id))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("admin_review"))


@app.route("/my-project")
def my_project():

    if "team_id" not in session:
        return redirect(url_for("team_login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            project_title,
            domain,
            similarity_score,
            novelty_score,
            status,
            rejection_reason,
            submitted_on
        FROM innovovault_submission.submitted_projects
        WHERE team_id=%s
        ORDER BY submitted_on DESC
        LIMIT 1
    """, (session["team_id"],))

    project = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "my_project.html",
        project=project
    )
@app.route("/analytics")
def analytics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM innovovault_submission.submitted_projects")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM innovovault_submission.submitted_projects WHERE status='Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM innovovault_submission.submitted_projects WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM innovovault_submission.submitted_projects WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "analytics.html",
        total=total,
        approved=approved,
        pending=pending,
        rejected=rejected
    )
@app.route("/add-academic-year", methods=["POST"])
def add_academic_year():

    academic_year = request.form["academic_year"].strip()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # Make the new year Active
        cursor.execute("""
            UPDATE innovovault_teams.academic_years
            SET status='Inactive'
        """)

        # Insert new academic year
        cursor.execute("""
            INSERT INTO innovovault_teams.academic_years (year, status)
            VALUES (%s, 'Active')
        """, (academic_year,))

        conn.commit()

        flash("Academic Year added successfully!")

    except mysql.connector.IntegrityError:

        conn.rollback()

        flash("Academic Year already exists!")

    finally:

        cursor.close()
        conn.close()

    return redirect(url_for("admin_dashboard"))
@app.route("/admin-dashboard")
def admin_dashboard():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all Academic Years
    cursor.execute("""
        SELECT id, year
        FROM innovovault_teams.academic_years
        ORDER BY year DESC
    """)

    academic_years = cursor.fetchall()

    # Get selected Academic Year
    selected_year_id = request.args.get("year_id", type=int)

    # If no year is selected, use the Active Academic Year
    if selected_year_id:
        cursor.execute("""
            SELECT id, year
            FROM innovovault_teams.academic_years
            WHERE id=%s
        """, (selected_year_id,))

        current_year = cursor.fetchone()

    else:
        cursor.execute("""
            SELECT id, year
            FROM innovovault_teams.academic_years
            WHERE status='Active'
            LIMIT 1
        """)

        current_year = cursor.fetchone()

    # If selected year does not exist, use Active Year
    if not current_year:
        cursor.execute("""
            SELECT id, year
            FROM innovovault_teams.academic_years
            WHERE status='Active'
            LIMIT 1
        """)

        current_year = cursor.fetchone()

    # Academic Year ID used for dashboard counts
    academic_year_id = current_year["id"] if current_year else None

    # Total Teams
    if academic_year_id:
        cursor.execute("""
            SELECT COUNT(*) AS total_teams
            FROM innovovault_teams.teams
            WHERE academic_year_id=%s
        """, (academic_year_id,))
    else:
        total_teams = 0

    if academic_year_id:
        total_teams = cursor.fetchone()["total_teams"]

    # Pending Proposals
    if academic_year_id:
        cursor.execute("""
            SELECT COUNT(*) AS pending
            FROM innovovault_submission.submitted_projects
            WHERE status='Pending'
            AND academic_year_id=%s
        """, (academic_year_id,))
    else:
        pending = 0

    if academic_year_id:
        pending = cursor.fetchone()["pending"]

    # Approved Projects
    if academic_year_id:
        cursor.execute("""
            SELECT COUNT(*) AS approved
            FROM innovovault_submission.submitted_projects
            WHERE status='Approved'
            AND academic_year_id=%s
        """, (academic_year_id,))
    else:
        approved = 0

    if academic_year_id:
        approved = cursor.fetchone()["approved"]

    # Final Submissions
    if academic_year_id:
        cursor.execute("""
            SELECT COUNT(*) AS submitted
            FROM innovovault_submission.submitted_projects
            WHERE academic_year_id=%s
        """, (academic_year_id,))
    else:
        submitted = 0

    if academic_year_id:
        submitted = cursor.fetchone()["submitted"]

    cursor.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_teams=total_teams,
        pending=pending,
        approved=approved,
        submitted=submitted,
        current_year=current_year,
        academic_years=academic_years
    )


@app.route("/view-teams")
def view_teams():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.team_id,
            td.leader_name,
            td.leader_roll,
            td.member2_name,
            td.member2_roll,
            td.member3_name,
            td.member3_roll,
            td.member4_name,
            td.member4_roll,
            td.guide_name
        FROM innovovault_teams.teams t
        LEFT JOIN innovovault_teams.team_details td
        ON t.team_id = td.team_id
        ORDER BY t.team_id
    """)

    teams = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("view_teams.html", teams=teams)

@app.route("/view-team/<team_id>")
def view_team(team_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            t.team_id,
            td.leader_name,
            td.leader_roll,
            td.member2_name,
            td.member2_roll,
            td.member3_name,
            td.member3_roll,
            td.member4_name,
            td.member4_roll,
            td.guide_name
        FROM innovovault_teams.teams t
        LEFT JOIN innovovault_teams.team_details td
        ON t.team_id = td.team_id
        WHERE t.team_id = %s
    """, (team_id,))

    team = cursor.fetchone()

    cursor.close()
    conn.close()

    if not team:
        return "Team not found", 404

    return render_template(
        "view_team.html",
        team=team
    )

@app.route("/delete-team/<team_id>")
def delete_team(team_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM innovovault_teams.team_details WHERE team_id=%s",
        (team_id,)
    )

    cursor.execute(
        "DELETE FROM innovovault_teams.teams WHERE team_id=%s",
        (team_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for("view_teams"))

@app.route("/submitted-projects")
def submitted_projects():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            team_id,
            project_title,
            domain,
            technologies,
            abstract,
            similarity_score,
            novelty_score,
            status,
            rejection_reason,
            submitted_on
        FROM innovovault_submission.submitted_projects
        ORDER BY submitted_on DESC
    """)

    projects = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "submitted_projects.html",
        projects=projects
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)  
