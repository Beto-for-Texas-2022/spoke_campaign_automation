from google.oauth2 import service_account
from google.cloud import storage
from datetime import date, timedelta
import datetime
import requests
import pandas as pd
import os
import json
from time import sleep


# event, context input parameters required for pub/sub trigger on cloud function
def main(event, context):
    # input your google project name here
    project = '166318991862'
    # input your google cloud storage bucket name here
    # this bucket should contain the contact lists you are trying to upload to spoke in csv format
    bucket = 'bft_contact_lists'

    # input the name of the environmental variable which contains your service account json key
    # you can input this data in the secret manager tool and set it as an environmental variable in the cloud function during initial set-up of the cloud function
    credentials = service_account.Credentials.from_service_account_info(json.loads(os.environ.get('SERVICE_ACCOUNT')))
    client = storage.Client(project=project, credentials=credentials)

    # input the name of the environmental variable which contains your spoke api key
    # set up is the same as the credentials variable
    spoke_api_key = str(os.environ.get('SPOKE_API_KEY'))

    # creating df with template campaign id and new campaign title data for daily campaigns
    # each row is a unique campaign

    campaign_templates_data = [
                                 {'id': 4538, 'title': 'Block Walk Recruitment'},
                                 {'id': 4665, 'title': 'In-Person Phone Bank Recruitment'},
                                 {'id': 5091, 'title': 'Mobilize Hosts Recently Approved Block Walks'},
                                 {'id': 5729, 'title': 'Short Lead Block Walk Recruitment'}
                                 # sample row
                                 # you would insert new campaigns you want to automate creation and upload of below in the following format
                                 # , {'id': 0000, 'title': 'SAMPLE CAMPAIGN NAME'}
                              ]

    # code below creates a list of blobs (files) in google cloud storage bucket
    # if file name begins with today's date; this was purely due to our naming convention
    blobs = client.list_blobs(bucket_or_name = bucket, prefix='Lists_Texting/{month}_{day}'.format(month = date.today().strftime('%m'), day  = date.today().strftime('%d')))
    # creates list of names of blobs in blobs
    blob_names = [blob.name for blob in blobs]
    # gcs_object_names is a list of lists
    # if a blob name in blob_names contains the string in the if condition for each list, it gets pulled into the list
    # this structure is meant to match our csvs to the correct template campaign id and campaign title
    # note, if there are multiple csvs for a single campaign type (because the csv had to be split up due to
    # spoke's 500k row limit), this will capture all the csvs associated with the campaign and match it to
    # the correct template / title, as long as the csv name is standardized

    #change name of gcs_object_names
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

    # the if conditions below generate data for our non-daily spoke campaigns
    # the condition below adds data for a campaign that only goes out on mondays
    if date.today().weekday() == 0: # if monday
      campaign_templates_data.append({'id': 4664, 'title': 'Virtual Phone Bank Recruitment'})
      gcs_object_names.append([name for name in blob_names if 'gotv_virtual_phone_bank' in name])

    # the condition below adds data for a campaign that ran every day but only between october 23rd and november 2nd
    if datetime.date(2022, 10, 23) <= date.today() <= datetime.date(2022, 11, 2):
      campaign_templates_data.append({'id': 5745, 'title': 'Vote Early with Beto'})
      gcs_object_names.append([name for name in blob_names if 'betopolls' in name])


    # the code below was for a campaign that we sent at 3 pm everyday instead of the usual 9 am
    # if the function was triggered at 9 am, the program sets the dataframe to loop through as the data contained above, in the else condition
    # if the function was triggered at 3 pm, the program sets the dataframe to loop throough as a single row dataframe containing 'GOTV E-Day'
    if (datetime.datetime.now().time().strftime("%H") == datetime.time(19, 00, 00).strftime("%H")) == True:
      df = pd.DataFrame([{'id': 6100 , 'title': 'GOTV E-Day'}])
      df['gcs_object_names'] = [[name for name in blob_names if 'gotv_eday' in name]]
    else:
      df = pd.DataFrame(campaign_templates_data)
      df['gcs_object_names'] = gcs_object_names

    copy_count = 0
    campaign_ids = []

    #the for loop below creates new campaigns based on the campaign template ids
    # looping through dataframe created in the above code
    for index, row in df.iterrows():
        template_campaign_id = row.id
        campaign_title = row.title
        gcs_object_names = row.gcs_object_names
        campaign_ids_row = []
        campaign_date = ''

        # a minor name convention change for a weekly campaign that was uploaded the day before it was sent
        # rather than the day of
        if campaign_title in 'Virtual Phone Bank Recruitment':
          campaign_date = str((date.today() + timedelta(days=1)).strftime("%m/%d"))
        else:
          campaign_date = str(date.today().strftime("%m/%d"))

    # looping through all blob names (csv files) in a given list in gcs_object_names
        for list_ in gcs_object_names:
            #for campaigns that had to be split due to the 500k row limit
            copy_count = copy_count + 1
            #api request to copy the template campaign and create new campaign
            response = requests.request(
                'POST',
                'https://betofortexas.text.scaletowin.com/api/copy-campaign',
                json={"campaignId": template_campaign_id,
                      "title": campaign_date + " " + campaign_title + " Part " + str(copy_count) + "/" + str(len(gcs_object_names))},
                headers={"STW-Api-Key": spoke_api_key})

            # logging
            print("Response for " + campaign_date + " " + campaign_title + " " + str(copy_count))
            print(response)

            # returning the id of the newly created campaign
            campaign_id = response.json()['campaignId']
            # storing id of newly created campaign to a list
            # list of ids to be accessed later in order to upload csv of contacts to campaign
            campaign_ids_row.append(campaign_id)

        copy_count = 0
        campaign_ids.append(campaign_ids_row)

    # creates new column in dataframe with newly created campaign ids
    df['campaign_ids'] = campaign_ids

    # the for loop below uploads csvs to the campaigns newly created in the prior for loop
    for index, row in df.iterrows():
        gcs_object_names = row.gcs_object_names
        campaign_ids = row.campaign_ids
        # zipping together to pair the blob name and newly created campaign id
        name_id_pairs = zip(gcs_object_names, campaign_ids)

        # looping through the blob name - newly created campaign id pairs
        for name, campaign_id in name_id_pairs:
            # api call to upload csv file of contacts to a campaign
            response = requests.request(
                'POST',
                'https://betofortexas.text.scaletowin.com/api/campaigns/{id}/contacts'.format(id=campaign_id),
                json={"type": "csv-gcs-upload", "gcsBucket": bucket, "gcsObjectName": name},
                headers={"STW-Api-Key": spoke_api_key})

            print(path + ' has been attempted to be uploaded to Spoke.')
            print(response)

            # sleep function to prevent more than 3 contact lists being uploaded at the same time
            # due to spoke limitation; to prevent spoke from crashing
            sleep(40)   
