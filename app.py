from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

students = {}

def send_email(sender_email, sender_password, receiver_email, subject, body):
    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        student_name = request.form["student_name"]
        subject = request.form["subject"]
        result = request.form["result"]
        parent_email = request.form["parent_email"]

        students[student_name] = {"subject": subject, "result": result, "parent_email": parent_email}

        sender_email = os.environ.get("SENDER_EMAIL")
        sender_password = os.environ.get("SENDER_PASSWORD")
        receiver_email = "lulumba68@gmail.com"
        subject_email = f"Result for {student_name} in {subject}"
        body = f"Dear Parent,\n\nYour child, {student_name}, received a result of {result} in {subject}."

        if send_email(sender_email, sender_password, receiver_email, subject_email, body):
            flash(f"Result for {student_name} sent to {receiver_email}", "success")
        else:
            flash(f"Failed to send result for {student_name}. Please check your email configuration.", "danger")

        return redirect(url_for("index"))

    return render_template("index.html", students=students)

if __name__ == "__main__":
    app.run(debug=False)