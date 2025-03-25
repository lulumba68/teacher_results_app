from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import openpyxl
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "Bmcsp68955.")

DATABASE = 'teachers.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    # Login logic here...
    if request.method == 'POST':
        cheki_namba = request.form['cheki_namba']
        conn = get_db_connection()
        teacher = conn.execute('SELECT * FROM teachers WHERE cheki_namba = ?', (cheki_namba,)).fetchone()
        conn.close()

        if teacher:
            session['cheki_namba'] = cheki_namba
            return redirect(url_for('upload_results'))
        else:
            flash('Namba ya cheki si sahihi.', 'error')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_results():
    # Upload results logic here...
    if 'cheki_namba' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    teacher = conn.execute('SELECT * FROM teachers WHERE cheki_namba = ?', (session['cheki_namba'],)).fetchone()
    conn.close()

    if not teacher:
        return 'Mwalimu hakupatikana.'

    if request.method == 'POST':
        try:
            student_names = request.form.getlist('student_name[]')
            paper1_marks = [float(x) for x in request.form.getlist('paper1[]')]
            paper2_marks = [float(x) for x in request.form.getlist('paper2[]')]
            paper3_marks = [float(x) for x in request.form.getlist('paper3[]')]

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.append(['Student Name', 'Paper 1 Marks', 'Paper 2 Marks', 'Paper 3 Marks', 'Average Marks'])

            for i in range(len(student_names)):
                avg = (paper1_marks[i] + paper2_marks[i] + paper3_marks[i]) / 3
                sheet.append([student_names[i], paper1_marks[i], paper2_marks[i], paper3_marks[i], avg])

            excel_file = BytesIO()
            workbook.save(excel_file)
            excel_file.seek(0)

            sender_email = os.environ.get("SENDER_EMAIL")
            sender_password = os.environ.get("SENDER_PASSWORD")
            receiver_email = "denismagesa67@gmail.com"
            subject = f"Student Results - {teacher['jina']}"
            body = f"Results for students taught by {teacher['jina']} are attached."

            if send_email_with_excel(sender_email, sender_password, receiver_email, subject, body, excel_file):
                flash('Results sent successfully!', 'success')
            else:
                flash('Failed to send results.', 'error')

        except Exception as e:
            flash(f'Error processing results: {e}', 'error')

    return render_template('upload_results.html', teacher=teacher)

def send_email_with_excel(sender_email, sender_password, receiver_email, subject, body, excel_file):
    # Email sending logic here...
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', "octet-stream")
    part.set_payload(excel_file.getvalue())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename="student_results.xlsx")
    msg.attach(part)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
