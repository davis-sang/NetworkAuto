#!/usr/bin/python3
import datetime
import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from netmiko import ConnectHandler

# Function to connect to Juniper router and retrieve chassis alarms
def get_chassis_alarms(router_name, router_ip, username, password, alarms_dict):
    try:
        net_connect = ConnectHandler(device_type='juniper', ip=router_ip, username=username, password=password)
        alarms = net_connect.send_command("show chassis alarms")
        with lock:
            alarms_dict[router_name] = alarms
        net_connect.disconnect()
        print(f"[{timestamp}]: Alarms for {router_name} retrieved successfully.")
    except Exception as e:
        print(f"[{timestamp}]: Failed to retrieve alarms for {router_name}. {str(e)}")
        alarms_dict[router_name] = "Connection failed !!!"

# Function to send email with the alarms attached
def send_email(sender_email, sender_password, receiver_email, subject, body, filename):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    part.add_header('Content-Disposition', f'attachment; filename= {filename}')

    msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
# Create a timestamp for the file name
timestamp = datetime.datetime.utcnow().strftime("%d-%m-%Y, %H:%M:%S")
# Define the router credentials and email details
router_credentials = {}

# Read the /etc/hosts file
with  open('/etc/hosts', 'r') as file:
    lines = file.readlines()

# Read and extract router credentials
for line in lines:
    # Ignore commented lines and empty lines
    if line.startswith('#') or line.strip() == '':
        continue

    # Split the line into hostname and IP address
    parts = line.split()
    hostname = parts[1]
    ip_address = parts[0]

    # Extract router name from hostname
    match = re.match(r'([A-Za-z0-9-]+)', hostname)
    if match:
        router_name = match.group(1)
        router_credentials[router_name] = ip_address

sender_email = ""
sender_password = ""
adrlst = ['']
receiver_email = ', '.join(adrlst)
subject = "Critical !!! Chassis Alarms : " + timestamp + "UTC"
body = "Hi Team, \n\nPlease find attached the chassis alarms for juniper routers/switches as of " + timestamp + "UTC.\n\nRegards,\nJuniper Alarm Monitor"

# Dictionary to store alarms for each router
alarms_dict = {}

#List to store threads
threads = []

#Lock object for thread sync.
lock = threading.Lock()

# Iterate over the router credentials and retrieve the alarms
for router_name, router_ip in router_credentials.items():
    username = ""
    password = ""
    t = threading.Thread(target=get_chassis_alarms, args=(router_name, router_ip, username, password, alarms_dict))
    threads.append(t)
    t.start()

# Wait for all threads to complete
for t in threads:
    t.join()

# Write alarms to a text file
filename = "chassis_alarms.txt"
with open(filename, 'w') as f:
    for router, alarms in alarms_dict.items():
           f.write(f"-----------------Equipment: {router}-----------------\n")
           f.write(alarms)
           f.write('\n\n')

# Send the email with the alarms file attached
send_email(sender_email, sender_password, receiver_email,subject, body, filename)