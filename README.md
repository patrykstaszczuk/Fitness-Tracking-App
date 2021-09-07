# Fitness Tracking App

Manage you food recipes, track your health statistics, activities and more.

## Status

Application is in continuous developement as we planning to use it daily for health and sport activities analysis. 
Frontend for this app is being developing by other person. 

## General info

Key features:
 - Create and manage your recipes
 - Send recipe ingredients to nozbe as shopping list via Nozbe API
 - Invite and join to groups to share your recipes with others
 - Track your health statistics (weight, sleep length, mood and more) in daily dashboard
 - Calculate BMI based on current health condition 
 - Analysis your health progess with statistics history, weekly summaries and detailed information about your tracked stats
 - Get your recent activities from Strava via Strava API
 - Track your daily calories intake and calories delta, based on what you eat and your activities. Intake calories are auto calculated.
 
 To be implemented:
 - More traning features based on data from StravaApi
 - Sub App for daily food quallity calculator. Get points for eating healthy food and lose point for eating junk food! (some junk food allowed, as one of the main athlete rule is EAT EVERYTHING :) ) 
 - Weekly menu planner 
 - Workout planner with google calendar API support
 - Weather checker for location where we usually do cycling training 
  

## Technologies

- Python 3.9.4
- Django REST Framework
- Docker

Detailed information in requirements.txt file

## Setup

To run this project, few files neeed to be prepared:

* .env (file with enviromental variables used by docker container to connect to db, retrieve secret key and more). Inside the file you should include:

SECRET_KEY = yoursecretkey <br>
DB_NAME = yourdbname <br>
DB_USER = yourdbuser <br>
DB_PASS = yourdbpass <br>
DB_HOST = 'db' # database service name from docker-compose.yml <br>

Additionally you can specify nozbe information in order to connect your app with specific nozbe project. Information how to obtain this data can be found in official nozbe API docs: https://files.nozbe.com/rest_api/nozbe_restapi01.pdf

NOZBE_CLIENT_ID = yournozbeclientid <br>
NOZBE_SECRET = nozbesecretkey <br>
NOZBE_PROJECT_ID = nozbeprojectid <br>

For strava connection:
STRAVA_CLIENT_ID= yourstravaclientid
STRAVA_CLIENT_SECRET= yourstravasecret
  

* .env.db (information needed for mysql to startup): <br /> 
 
MYSQL_ROOT_PASSWORD= yourmysqlrootpassword <br>
MYSQL_DATABASE= yourdbname <br>
MYSQL_USER= yourdbuser <br>
MYSQL_PASSWORD= yourdbpassword <br>

Important:
  - Keep this files in .gitignore as it may contains sensitive information
  - media files are store in media/ folder located in main folder. This folder should also be keep in gitignore since it may contains many MBs of data 
  - mysql database is stored in mysql/ folder. It is recomended to store this file locally.

