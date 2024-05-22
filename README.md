**NetworkAuto**

This project contains a script to monitor and handle chassis alarms from juniper routers and write them to a txt file. The script is scheduled to run twice a day using a cron job.

## Project Structure

- `chassisAlarms.py`: The main Python script that performs the chassis alarm monitoring.
- `chassisAlarms.sh`: A bash script to execute the Python script.
- `README.md`: This readme file.

## Requirements

- Python 3
- cron

## Setup

1. Ensure Python 3 is installed on your system.

2. Make the bash script executable:
   ```bash
   chmod +x / `{path}`/cron_shell.sh
3. Cron job:
    ```bash
    crontab -e 
    # Run the chassisAlarms.sh script at 07:00 UTC every day
    0 7 * * * /`{path}`/cron_shell.sh



