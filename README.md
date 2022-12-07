# spoke_campaign_automation
Documentation and Python code for automation of texting campaigns in Spoke with Spoke API

**Background / Problem Statement**

On the Beto for Texas campaign, we used Scale to Win’s Spoke tool for our text messaging campaigns. In the beginning of the campaign, we would create each campaign individually and manually upload the contact list as a csv. Once Spoke released their API, we used a Google Cloud Function to automate the creation and list upload for our regular campaigns. This saved our team at least 7 hours of work related to text messaging campaigns each week.

Before the Spoke API came out, we had already automated out the creation of contact lists for our regular campaigns. We did this through scheduled queries in our BigQuery instance which ran daily and deposited a csv of contacts for each campaign in a Google Cloud Storage bucket. Once the Spoke API was released, we simply had to write the code which would grab each list from the bucket and upload it into Spoke. 

**Quickstart**

You can quickly set-up and begin using the program to automate campaign production for daily lists with the following steps:

\1.   Download the file spoke_campaign_automation.zip from GitHub.

\2.   Create a Pub/Sub trigger Google Cloud Function.

\3.   Upload this file into a Google Cloud Function. There should be an option to upload a zip file.

\4.   In Google Secret Manager, create two secrets.

a.   The first should contain the JSON key for your Google Cloud service account. This account should belong to the GCS bucket with your contact list csvs.

b.   The second should contain your Spoke API key.

\5.   Once the zip file has been uploaded, customize the following variables:

a.   In the program editor in GCF, change the project and bucket variables to the Google Cloud project you’re working out of and the name of the Google Cloud Storage where your contact lists are located, respectively.

**b.**   Under the **Runtime, build and connections settings** **header in the set-up page of the GCF, click security and** **Reference a secret****. Set your service account JSON key as an exposed environmental variable named ‘SERVICE_ACCOUNT’ and your Spoke API key as ‘SPOKE_API_KEY’.** 

c.   Edit the data in campaign_templates_data and gcs_object_names variables to match the template ID and name of your Spoke campaigns and the names of the csv files containing the contact list you’d like to upload. There are further instructions in the program itself.

\6.   Deploy your function.

\7.   Set up a Cloud Scheduler trigger attached to the GCF’s pub/sub topic.

\8.   Done! You can check the [official Google documentation](https://cloud.google.com/functions/docs/create-deploy-gcloud-1st-gen) for further help.

**Additional Features**

There is a second version of the main.py file called main_additional_features.py. This version contains heavily commented code which thoroughly explains how each step of the program works. It also contains code for additional features, such as modifying the program to only create and upload a campaign on a specific day of the week or a specific set of days. This version is intended to help a proficient Python coder edit the program to perform more complex things.

 

 

 
