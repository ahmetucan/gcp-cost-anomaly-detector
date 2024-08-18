import json
import os
from datetime import datetime, date, timedelta
import requests
import time


print(os.getcwd())


def load_config(file_path):
    with open("config.json", 'r') as file:
        config = json.load(file)
    return config

def login(date_str):
    login = f"bq show --project_id=<random_project_name_in_your_account>"
    os.system(f"{login}")
    return login

def get_project_cost(project_name, project_id, billing_account_id, billing_table_name, billing_dataset_name, date_str):

    date_fix= ((datetime.strptime(date_str, "%Y-%m-%d")) + timedelta(days=1)).strftime("%Y-%m-%d")
    query = f"bq query --format=prettyjson --max_rows 100000 --nouse_legacy_sql 'SELECT * FROM `{billing_account_id}.{billing_dataset_name}.{billing_table_name}` WHERE project.id = \"{project_id}\" AND DATE(_PARTITIONTIME) IN (\"{date_str}\", \"{date_fix}\") AND DATE (usage_start_time) = \"{date_str}\" AND DATE(usage_end_time) = \"{date_str}\"'"
    print(query)
    os.system(f"{query} > costtable.json")
    with open("costtable.json", "r") as f:
        table_data = f.read()

    table = json.loads(table_data)
    project_cost = 0
    for item in table:
        if item["project"]["name"] == project_name:
            project_cost += float(item["cost"])
    
    return project_cost


def get_cost_details(project_id, billing_account_id, billing_table_name, billing_dataset_name, date1, date2):
    for date in [date1, date2]:
        date_fix= ((datetime.strptime(date, "%Y-%m-%d")) + timedelta(days=1)).strftime("%Y-%m-%d")
        query = f"bq query --format=prettyjson --max_rows 100000 --nouse_legacy_sql 'SELECT service.description, ROUND(SUM(cost), 2) as total_cost FROM `{billing_account_id}.{billing_dataset_name}.{billing_table_name}` WHERE project.id = \"{project_id}\" AND DATE(_PARTITIONTIME) IN (\"{date}\", \"{date_fix}\") AND DATE (usage_start_time) = \"{date}\" AND DATE(usage_end_time) = \"{date}\" GROUP By service.description ORDER BY total_cost DESC '"
        print(query)
        os.system(f"{query} > cost_{date}.json")


def generate_report(config, project_name, project_id, billing_account_id, billing_table_name, date1, date2, webhook_url, channel):

    d1_project_cost = float(format(get_project_cost(project_name, project_id, billing_account_id, billing_table_name, billing_dataset_name, date1), '.2f'))
    d2_project_cost = float(format(get_project_cost(project_name, project_id, billing_account_id, billing_table_name, billing_dataset_name, date2), '.2f'))
    if d2_project_cost == 0:
        print(project_name + "Project usage not exist!!!")
        return None
    if d1_project_cost < 1000:
        print(project_name + "Project usage low")
        return None
    cost_difference = format((d1_project_cost - d2_project_cost), '.2f')
    print(d1_project_cost)
    print(d2_project_cost)

    percentage_change = (((d1_project_cost - d2_project_cost) / d2_project_cost)* 100)
    print(percentage_change)
    if abs(percentage_change) <= 15.0:

        data = {
            "channel": f"#{channel}",
            "icon_emoji": ":pinched_fingers::skin-tone-2:",
            "username": "GCP Cost Normal Webhook",
            "text": "*In " + project_name + " everything all right !!!*"
        }
        response = requests.post(
            webhook_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        return None

    if percentage_change >= 15:
        color="#ff2701"
    else:
        color="#008000"

    percentage_change = float(format((((d1_project_cost - d2_project_cost) / d2_project_cost)* 100), '.2f'))
    if percentage_change > 15.0 and (d1_project_cost  > 20000.0 or d2_project_cost > 20000.0):
        channel = "gcp-critical-cost-anomaly-detector"
        data = {
            "channel": f"#{channel}",
            "text": "*Devops Cost Anomaly Detector*",
            "icon_emoji": ":gcp:",
            "username": "GCP Cost Anomaly Detector Webhook",
            "attachments": [
            {
                "color": color,    
                "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": project_name + " (" + date1 + ")"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*" + date1 + " Total Cost:* " + str(d1_project_cost) + " TL"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*" + date2 + " Total Cost:* " + str(d2_project_cost) + " TL"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Cost Differcence:* " + str(cost_difference) + "TL"
                        },
                                            {
                            "type": "mrkdwn",
                            "text": "*Change Percentage* : %" + str(percentage_change)
                        }
                    ]
                }
                    ]
                }
            ]
        }
    else:
        data = {
            "channel": f"#{channel}",
            "text": "*Devops Cost Anomaly Detector*",
            "icon_emoji": ":gcp:",
            "username": "GCP Cost Anomaly Detector Webhook",
            "attachments": [
            {
                "color": color,    
                "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": project_name + " (" + date1 + ")"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*" + date1 + " Total Cost:* " + str(d1_project_cost) + " TL"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*" + date2 + " Total Cost:* " + str(d2_project_cost) + " TL"
                        }
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": "*Cost Differcence:* " + str(cost_difference) + "TL"
                        },
                                            {
                            "type": "mrkdwn",
                            "text": "*Change Percentage* : %" + str(percentage_change)
                        }
                    ]
                }
                    ]
                }
            ]
        }


    get_cost_details(project_id,  billing_account_id, billing_table_name, billing_dataset_name, date1, date2)

    with open(f"cost_{date1}.json", "r") as file:
        cost_data_date1 = json.load(file)
    
    with open(f"cost_{date2}.json", "r") as file:
        cost_data_date2 = json.load(file)

    service_cost_blocks = [{
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Daily Service Cost Usages:"
        }
    },
    { 
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": f"*Detail Cost for {date1}*"
            },
            {
                "type": "mrkdwn",
                "text": f"*Detail Cost for {date2}*"
            }
        ]
    }]

    os.remove("cost_" + date1 + ".json")
    os.remove("cost_" + date2 + ".json")

    for service_date1, service_date2 in zip(cost_data_date1, cost_data_date2):
        description = service_date1['description']  # Assuming same order; might need adjustment
        total_cost_date1 = service_date1['total_cost']
        total_cost_date2 = service_date2['total_cost']
        service_cost_blocks.append({
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*{description}:* {total_cost_date1} TL for {date1} "
                },
                                {
                    "type": "mrkdwn",
                    "text": f"*{description}:* {total_cost_date2} TL for {date2}"
                }
            ]
        })

    # Other existing code to construct the full message payload...

    data['attachments'][0]['blocks'] += service_cost_blocks

    return data

def send_slack_message(url, channel, data):

    d1_project_cost = float(format(get_project_cost(project_name, project_id, billing_account_id, billing_table_name, billing_dataset_name, date1), '.2f'))
    d2_project_cost = float(format(get_project_cost(project_name, project_id, billing_account_id, billing_table_name, billing_dataset_name, date2), '.2f'))
    percentage_change = float(format((((d1_project_cost - d2_project_cost) / d2_project_cost)* 100), '.2f'))
    if percentage_change > 15.0 and (d1_project_cost  > 20000.0 or d2_project_cost > 20000.0):
        url = "<slack_webhook_url>"
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        if response.status_code != 200:
            raise ValueError(f"Request to slack returned an error {response.status_code}, the response is: {response.text}")
        return True
    else:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )
        if response.status_code != 200:
            raise ValueError(f"Request to slack returned an error {response.status_code}, the response is: {response.text}")
        return True

if __name__ == "__main__":
    config = load_config('config.json')

    today = date.today()
    date1 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    date2 = (today - timedelta(days=3)).strftime("%Y-%m-%d")

    webhook_url = "<slack_webhook_url>"
    channel = "<slack_channel_name>"

    login = login(date1)
    for project_key, project_info in config["projects"].items():
        project_name = project_info["name"]
        print(project_name)
        project_id = project_info["id"]
        billing_account_id = project_info["billing_account_id"]
        billing_table_name = project_info["billing_table_name"]
        billing_dataset_name = project_info["billing_dataset_name"]
        data = generate_report(config, project_name, project_id, billing_account_id, billing_table_name, date1, date2, webhook_url, channel)
        if data:
            send_slack_message(webhook_url,channel, data)
