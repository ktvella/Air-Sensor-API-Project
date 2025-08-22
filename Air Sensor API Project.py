# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 11:27:45 2025

@author: kvella
"""

import requests
import pandas as pd
from io import StringIO
import datetime


def location_to_sensor(loc):
    #translate entry to sensor number
    #return not valid if invalid input is entered
    if loc =="1": 
        #sensor for boston
        return "158773"
    elif loc =="2":
        #sensor for Toronto
        return  "79359"
    elif loc == "3":
        #sensor for Chicago
        return "87741"
    elif loc == "4": 
        #sensor for NYC
        return  "103518"
    elif loc == "5":
        #sensor for Orlando
        return  "101786"
    else: 
        return "Not Valid"


def connect_to_api(sensor_num):
    '''
    Connect to PurpleAir API for sensor

    Pull history csv for selected parameters
    Convert to DataFrame

    Parameters: 
        average: inverval over which to average data, 1440 input averages over a day
        pm2.5_atm: air quality indicator, the estimated mass concentration of fine particles with a diameter of fewer than 2.5 microns. 
            higher value indicates worse air quality
            humidity: relative humidity %
            temperature: temperature in F
            scattering_coefficient: measurement of light scatterning, used to indicate haze levels. Higher number means more haze
    '''


    '''
    Finding the latest weather conditions
    '''

    url = "https://api.purpleair.com/v1/sensors/"+sensor_num+"/history/csv"
    headers = {"X-API-Key": "your api key here"}

    params = {"fields": "pm2.5_atm,humidity,temperature,scattering_coefficient" }

    response = requests.get(url, headers=headers, params=params)


    latest_conditions = pd.read_csv(StringIO(response.text))
    latest_conditions = latest_conditions.sort_values(by="time_stamp", ascending = False).reset_index(drop = True)
    return latest_conditions


def print_data_time_range(df):
    #find the time span of the data pulled
    range_seconds = df["time_stamp"].max()-df["time_stamp"].min()
    range_minutes = round(range_seconds/60, 1)
    range_hours = round(range_seconds/60/60, 1)
    range_days = round(range_seconds/60/60/24, 1)
    print("\033[1mData Size\033[0m")
    print(f"Time range in minutes: {range_minutes} \nTime range in hours: {range_hours} \nTime range in days: {range_days}")


def get_air_quality(pm25):
    #indicate quality of air based on pm2.5 measurement
    if pm25<=50: 
        air_quality = "Good"
    elif pm25<=100: 
        air_quality = "Moderate"
    else: 
        air_quality = "Unhealthy"
    return air_quality

def past_weeks_data(df): 
    '''
    Finding data from last week days to compare todays weather to
    '''

    #finding the unix range for the latest week of data
    latest_time_unix = df["time_stamp"].max()
    last_week_range_unix = latest_time_unix - 604800

    #selecting only latest week of data, add time column
    latest_week_data = df[df["time_stamp"].between(last_week_range_unix, latest_time_unix)].copy()
    latest_week_data["date_time"] =latest_week_data["time_stamp"].apply(lambda x: datetime.datetime.fromtimestamp(x).time())

    #select only data at current time
    current_time_latest = latest_week_data[latest_week_data["date_time"] == timestamp.time()]


    #find average values for this time in the last week
    avg_time_temp = current_time_latest["temperature"].mean()
    avg_time_hum = current_time_latest["humidity"].mean()
    
    return avg_time_temp, avg_time_hum


def find_60_30_7_day_avgs(df,column, latest_time_unix):
    '''
    finding past data to compare air quality to
    past 60 days, 30 days and 7 days
    '''
    av60day = df[column].mean()
    latest30day_conditions = df[latest_conditions["time_stamp"].between(latest_time_unix-2592000, latest_time_unix)].copy()
    av30day = latest30day_conditions[column].mean()
    latest7day_conditions = df[latest_conditions["time_stamp"].between(latest_time_unix-604800, latest_time_unix)].copy()
    av7day = latest7day_conditions[column].mean()
    return av60day, av30day, av7day

def higher_lower(todays, prev): 
    #returns if a value is higher, lower, or similar to a previous value
    if todays < prev-2: 
        string = "lower than"
    elif prev-2 < todays < prev+1: 
        string = "similar to"
    else: 
        string = "higher than" 
    return string


additional_location = "Y"
print("Welcome to Katie's weather app, build using data from PurpleAir sensors\n")
while additional_location =="Y": 
    sensor = "Not Valid"
    while sensor == "Not Valid": 
        location = input("What is your location? \nEnter a number:\n1 for Boston\n2 for Toronto \n3 for Chicago \n4 for New York City\n5 for Orlando.\n")
        sensor = location_to_sensor(location)
        if sensor == "Not Valid": 
            print("\nLocation not valid.")
    print(sensor)
    #connect to sensor and pull data
    latest_conditions = connect_to_api(sensor)
    #current time and weather conditions
    latest_time_unix = latest_conditions.iloc[0, 0]
    timestamp = datetime.datetime.fromtimestamp(latest_time_unix)
    humidity = latest_conditions.iloc[0, 2]
    temperature = latest_conditions.iloc[0, 3]
    scattering_coefficient = latest_conditions.iloc[0,4]
    pm2_5 = latest_conditions.iloc[0, 5]
    #print_data_time_range(latest_conditions)
    air_quality = get_air_quality(pm2_5)
    print(f"\033[1mReport for the Day\033[0m \nLatest data at {timestamp} \nTemperature is {temperature}\u00b0F \nRelative Humidity is {humidity} \nAir quality is {air_quality} with a PM2.5 of {pm2_5}\n")
    #finding past data to compare today's conditions to
    avg_time_temp, avg_time_hum = past_weeks_data(latest_conditions)
    av60day_aq, av30day_aq, av7day_aq = find_60_30_7_day_avgs(latest_conditions, "pm2.5_atm", latest_time_unix)
    #comparing todays data to previous week's data
    print(f"The temperature is {higher_lower(temperature, avg_time_temp)} average for this past week at this time.")
    print(f"The humidity is {higher_lower(humidity, avg_time_hum)} average for this past week at this time.")
    print(f"The air pollution is {higher_lower(pm2_5, av7day_aq)} average levels this past week, and {higher_lower(pm2_5, av30day_aq)} average levels this past month.\n")
    additional_location = input("Would you like to look at another location? Enter Y/N\n")


