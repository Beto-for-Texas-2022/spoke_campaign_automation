from google.oauth2 import service_account
from google.cloud import storage
from datetime import date, timedelta
import datetime
import requests
import pandas as pd
import os
import json
from time import sleep


def main(event, context):
    # input your google project name here
    project = '1234567890000000'
    # input your google cloud storage bucket name here
    bucket = 'bft_contact_lists'

    # input the name of the environmental variable which contains your service account json key
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.environ.get('SERVICE_ACCOUNT')))
    client = storage.Client(project=project, credentials=credentials)

    # input the name of the environmental variable which contains your spoke api key
    spoke_api_key = str(os.environ.get('SPOKE_API_KEY'))

    campaign_templates_data = [
        {'id': 4538, 'title': 'Block Walk Recruitment'},
        {'id': 4665, 'title': 'In-Person Phone Bank Recruitment'},
        {'id': 5091, 'title': 'Mobilize Hosts Recently Approved Block Walks'},
        {'id': 5729, 'title': 'Short Lead Block Walk Recruitment'}
        # sample row
        # you would insert new campaigns you want to automate creation and upload of below in the following format
        # , {'id': 0000, 'title': 'SAMPLE CAMPAIGN NAME'}
    ]

    blobs = client.list_blobs(bucket_or_name=bucket)
    blob_names = [blob.name for blob in blobs]

    # IT IS VERY IMPORTANT THAT THE ORDER OF EACH FILE NAMES LIST IS THE SAME ORDER AS THE
    # ID AND TITLE ARRAYS IN CAMPAIGN_TEMPLATE_DATA
    # for example, if the first row in campaign_templates_data is your block walk campaign,
    # the first row in gcs_object_names must be the name of the csv containing your block walk recruitment list
    # if the third row is your phone bank campaign in campaign_templates_data, the third
    # row in gcs_object_names must be the name of the csv containing your phone bank recruitment list
    # the names of the csvs must also be standardized
    gcs_object_names = [
        [name for name in blob_names if 'gotv_block_walk' in name],
        [name for name in blob_names if 'gotv_phone_bank' in name],
        [name for name in blob_names if 'mobilize_hosts_recently_approved_block_walks' in name],
        [name for name in blob_names if 'short_lead_block_walk' in name]
        # sample row
        # you would insert the standardized name of the csv files to be uploaded in the following format
        # , [name for name in blob_names if 'CSV_FILE_NAME' in name]
    ]

    df = pd.DataFrame(campaign_templates_data)
    df['gcs_object_names'] = gcs_object_names

    copy_count = 0
    campaign_ids = []

    for index, row in df.iterrows():
        template_campaign_id = row.id
        campaign_title = row.title
        gcs_object_names = row.gcs_object_names
        campaign_ids_row = []

        for list_ in gcs_object_names:
            copy_count = copy_count + 1

            response = requests.request(
                'POST',
                'https://betofortexas.text.scaletowin.com/api/copy-campaign',
                json={"campaignId": template_campaign_id,
                      "title": campaign_date + " " + campaign_title + " Part " + str(copy_count) + "/" + str(
                          len(gcs_object_names))},
                headers={"STW-Api-Key": spoke_api_key})

            print("Response for " + campaign_date + " " + campaign_title + " " + str(copy_count))
            print(response)

            campaign_id = response.json()['campaignId']
            campaign_ids_row.append(campaign_id)

        copy_count = 0
        campaign_ids.append(campaign_ids_row)

    df['campaign_ids'] = campaign_ids

    for index, row in df.iterrows():
        gcs_object_names = row.gcs_object_names
        campaign_ids = row.campaign_ids
        name_id_pairs = zip(gcs_object_names, campaign_ids)

        for name, campaign_id in name_id_pairs:
            response = requests.request(
                'POST',
                'https://betofortexas.text.scaletowin.com/api/campaigns/{id}/contacts'.format(id=campaign_id),
                json={"type": "csv-gcs-upload", "gcsBucket": bucket, "gcsObjectName": name},
                headers={"STW-Api-Key": spoke_api_key})

            print(path + ' has been attempted to be uploaded to Spoke.')
            print(response)

            sleep(40)
