import requests
from bs4 import BeautifulSoup
import sqlite3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import time
from dotenv import load_dotenv
import os

load_dotenv()
SESSION_KEY = os.environ.get("SESSION_KEY")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

classes = [
    (3131, "CSC 226"),
    (5058, "E 115"),
    (2762, "ECE 109"),
    (1958, "E 201"),
]

s = requests.Session()
s.cookies.set('MoodleSession', SESSION_KEY)
connection = sqlite3.connect("grades.db")
connection.execute('''
   CREATE TABLE IF NOT EXISTS grades (id integer primary key, class_name text, grades text)
''')

sg = SendGridAPIClient(SENDGRID_API_KEY)

while (True):
    for id, name in classes:
        connection.execute(f"INSERT OR IGNORE INTO grades(id, class_name) VALUES({id}, '{name}')")
        previous = connection.execute(f"SELECT grades FROM grades WHERE id = {id}").fetchone()[0]

        r = s.get(f"https://moodle-courses2324.wolfware.ncsu.edu/grade/report/user/index.php?id={id}")
        soup = BeautifulSoup(r.content, "html.parser")
        results = soup.find_all(class_="gradeitemheader")

        text = []
        for r in results:
            row = r.find_parent("tr")
            text.append(" ".join(row.text.strip().split("\n")))

        text = "\n".join(text)
        if(len(text) == 0):
            message = Mail(
                from_email='joe@joejackson.me',
                to_emails='joe@joejackson.me',
                subject=f"Something went wrong importing from: {name}",
                html_content="can't import grades")

            try:
                sg.send(message)
            except Exception as e:
                print(e.message)
        else:
            if (text != previous):
                message = Mail(
                    from_email='joe@joejackson.me',
                    to_emails='joe@joejackson.me',
                    subject=f"Updated grade from class: {name}",
                    html_content='<strong>There is a change in the grade for this class</strong>')

                try:
                    sg.send(message)
                except Exception as e:
                    print(e.message)

            connection.execute(f"UPDATE grades SET grades = '{text}' WHERE id = {id}")

    connection.commit()
    time.sleep(300)
