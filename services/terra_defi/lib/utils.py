# -*- coding: utf-8 -*-
"""
Created on 2022/04/12
@author: schengatto@gmail.com
"""
import telegram_send
import pandas as pd
import smtplib
import os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def load_prices(ticker, depth):
    filename = '../data/' + ticker + '.csv'
    data = pd.read_csv(filename, parse_dates=['Date'])
    data.set_index('Date', inplace=True)
    return data.iloc[-depth:]


def send_email(receivers, subject, text, html=None):
    sender = "schengatto@gmail.com"
    server = smtplib.SMTP('smtp.gmail.com', 587)  # use gmail with port
    server.starttls()
    server.login(sender, os.getenv("EMAIL_PASSWORD", ""))
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ", ".join(receivers)

    if text is not None:
        text = MIMEText(text)
        msg.attach(text)

    if html is not None:
        html_part = MIMEText(html, "html")
        msg.attach(html_part)

    server.sendmail(sender, receivers, msg.as_string())
    server.quit()
    print(f"Email sent to {receivers}")


def send_telegram_msg(messages=[], images=[], files=[], conf="/var/telegram_conf/group1.conf"):
    if conf is None:
        conf = "/var/telegram_conf/group1.conf"

    if not os.path.exists(conf):
        conf = "./lib/telegram_conf/group1.conf"

    telegram_send.send(messages=messages, conf=conf)

    for image in images:
        with open(image, "rb") as f:
            telegram_send.send(conf=conf, images=[f])
            f.close()

    for file in files:
        with open(file, "rb") as f:
            telegram_send.send(conf=conf, files=[f])
            f.close()
