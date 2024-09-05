import smtplib
from email.mime.text import MIMEText


sender_email = "<YOUR_EMAIL_GOES_HERE>"
sender_password = "<YOUR_PASSWORD_HERE>"


def send_invite_email(email: str, invite_link: str):
    try:
        body = """
        <html>
          <body>
            Click <a href={{invite_link}}>here</a> to join.
          </body>
        </html>
        """
        html_message = MIMEText(body, 'html')
        html_message['Subject'] = "Invite"
        html_message['From'] = sender_email
        html_message['To'] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, html_message.as_string())
    except:
        raise Exception("Some issue occurred")


def login_alert(email: str):
    try:
        body = "There has been a login attempt made using your mail id"
        msg = MIMEText(body)
        msg['Subject'] = "Login Attempt Alert"
        msg['From'] = sender_email
        msg['To'] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
    except:
        raise Exception("Some issue occurred")


def password_change_alert(email: str):
    try:
        body = "Password has been updated"
        msg = MIMEText(body)
        msg['Subject'] = "Password update Alert"
        msg['From'] = sender_email
        msg['To'] = email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
    except:
        raise Exception("Some issue occurred")
