import datetime
import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from netmiko import ConnectHandler

#Connect to Juniper router and retrieve chassis alarms.
def get_chassis_alarms(router_name, router_ip, username, password, alarm_dict):
    try:
        net_connect = ConnectHandler(device_type='juniper', ip=router_ip, username=username, password=password)
        alarms = net_connect.send_command("show chassis alarms")
        with lock:
            alarm_dict[router_name] = alarms
        net_connect.disconnect()
        print(f"[{timestamp}]: Alarms for {router_name} retrieved successfully.")
    except Exception as e:
        print(f"[{timestamp}]: Failed to retrieve alarms for {router_name}.{str(e)}")
        with lock:
            alarm_dict[router_name]= "Connection failed !!!"

# Function to send email with the alarms attached.
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

#
device_credentials = [
    {'Routers': {}},
    {'Switches':{}}
]

# Read the /etc/hosts file
def fetch_devices():
    
    with  open('/etc/hosts', 'r') as file:
        lines = file.readlines()

# Read and extract router credentials
    for line in lines:

    # Split the line into hostname and IP address
        parts = line.split()
        if len(parts) < 2:
            continue
        hostname = parts[1]
        ip_address = parts[0]

    # Extract router name from hostname
        for hostname in parts[1:]:
            if is_router(hostname):
                router_name = is_router(hostname).group(1)
                device_credentials[0]['Routers'][router_name] = ip_address
            elif is_switch(hostname):
                switch_name = is_switch(hostname).group(1)
                device_credentials[1]['Switches'][switch_name] = ip_address
            else:
                print(f"No match found for hostname: {hostname}")

#Function to match router from hosts file.
def is_router(hostname):
    return re.match(r'([A-Z]{3}[0-9]{2}-[R]{1}[0-9]{2})', hostname.upper())

#Function to match switch from hosts file.    
def is_switch(hostname):
    return re.match(r'([A-Z]{3}[0-9]{2}-[AS]{2}[0-9]{2})', hostname.upper()) or \
    re.match(r'([A-Z]{3}[0-9]{2}-[EX]{2}[0-9]{2})', hostname.upper()) or \
    re.match(r'(srx-ubx-.*)', hostname.lower()) or \
    re.match(r'([a-zA-Z0-9-]+)', hostname.lower())

#Dict to store fetched alarms for each device
alarms_dict={}
lock = threading.Lock()

#Email body and details
sender_email = ""
sender_password = ""
adrlst = ['']
receiver_email = ', '.join(adrlst)
subject = "Critical !!! Chassis Alarms : " + timestamp + "UTC"
body = "Hi Team, \n\nPlease find attached the chassis alarms for juniper routers/switches as of " + timestamp + "UTC.\n\nRegards,\nJuniper Alarm Monitor"

# Fetch device alarms concurrently
def fetch_alarms():
    fetch_devices()
    threads = []
    for device_type in device_credentials:
        for device_dict in device_type.values():
            for device_name, device_ip in device_dict.items():
                username = ""
                password = ""
                t = threading.Thread(target=get_chassis_alarms, args=(device_name, device_ip, username, password, alarms_dict))
                threads.append(t)
                t.start()

    for t in threads:
        t.join()

# Write alarms to a text file
def file_name():
    fetch_alarms()
    filename = "chassis_alarms.txt"

    # Function to write the header for each section
    def write_header(f, section_name):
        header = [
            "+" + "-"*88 + "+",
            "|                                                                                        |",
            f"|{('**' + section_name + '**').center(88)}|",
            "|                                                                                        |",
            "+" + "-"*88 + "+"
        ]
        for line in header:
            f.write(line + "\n")

    # Function to write the device section
    def write_device_section(f, devices):
        for device_name, device_ip in devices.items():
            if device_name in alarms_dict:
                device_section = [
                    "+" + "-"*71 + "+",
                    f"|{'Equipment: ' + device_name.ljust(60)}|",
                    "+" + "-"*71 + "+"
                ]
                for line in device_section:
                    f.write(line + "\n")
                f.write(alarms_dict[device_name] + '\n\n')

    with open(filename, 'w') as f:
        # Writing Routers section
        write_header(f, "ROUTERS")
        write_device_section(f, device_credentials[0]['Routers'])

        # Writing Switches section
        write_header(f, "SWITCHES")
        write_device_section(f, device_credentials[1]['Switches'])

    return filename


# Send the email with the alarms file attached
send_email(sender_email, sender_password, receiver_email,subject, body, file_name())