import datetime
import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from netmiko import ConnectHandler


# Connect to router and retrieve chassis alarms.
def get_chassis_alarms(router_name, router_ip, username, password, alarm_dict):
    try:
        net_connect = ConnectHandler(
            device_type="", ip=router_ip, username=username, password=password
        )
        alarms = net_connect.send_command("show chassis alarms")
        with lock:
            alarm_dict[router_name] = alarms
        net_connect.disconnect()
        print(f"[{timestamp}]: Alarms for {router_name} retrieved successfully.")
    except Exception as e:
        print(f"[{timestamp}]: Failed to retrieve alarms for {router_name}.{str(e)}")
        with lock:
            alarm_dict[router_name] = "Connection failed !!!"


# Function to send email with the alarms attached.
def send_email(sender_email, sender_password, receiver_email, subject, body, filename):
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    part.add_header("Content-Disposition", f"attachment; filename= {filename}")

    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()


# Create a timestamp for the file name
timestamp = datetime.datetime.utcnow().strftime("%d-%m-%Y, %H:%M:%S")

#
device_credentials = [{"Routers": {}}, {"Switches": {}}]


def fetch_devices():
    pass
    # fetch devices


# Dict to store fetched alarms for each device
alarms_dict = {}
lock = threading.Lock()

# Email body and details
sender_email = ""
sender_password = ""
adrlst = [""]
receiver_email = ", ".join(adrlst)
subject = "Critical !!! Chassis Alarms : " + timestamp + "UTC"
body = (
    "Hi Team, \n\nPlease find attached the chassis alarms for equipment as of "
    + timestamp
    + "UTC.\n\nRegards,\n"
)


# Fetch device alarms concurrently
def fetch_alarms():
    fetch_devices()
    threads = []
    for device_type in device_credentials:
        for device_dict in device_type.values():
            for device_name, device_ip in device_dict.items():
                username = ""
                password = ""
                t = threading.Thread(
                    target=get_chassis_alarms,
                    args=(device_name, device_ip, username, password, alarms_dict),
                )
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
            "+" + "-" * 88 + "+",
            "|                                                                                        |",
            f"|{('**' + section_name + '**').center(88)}|",
            "|                                                                                        |",
            "+" + "-" * 88 + "+",
        ]
        for line in header:
            f.write(line + "\n")

    # Function to write the device section
    def write_device_section(f, devices):
        for device_name, device_ip in devices.items():
            if device_name in alarms_dict:
                device_section = [
                    "+" + "-" * 71 + "+",
                    f"|{'Equipment: ' + device_name.ljust(60)}|",
                    "+" + "-" * 71 + "+",
                ]
                for line in device_section:
                    f.write(line + "\n")
                f.write(alarms_dict[device_name] + "\n\n")

    with open(filename, "w") as f:
        # Writing Routers section
        write_header(f, "ROUTERS")
        write_device_section(f, device_credentials[0]["Routers"])

        # Writing Switches section
        write_header(f, "SWITCHES")
        write_device_section(f, device_credentials[1]["Switches"])

    return filename


# Send the email with the alarms file attached
send_email(sender_email, sender_password, receiver_email, subject, body, file_name())
