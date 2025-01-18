from datetime import datetime, timedelta
from datetime import timezone
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
import time
import pytz
import pandas as pd
import csv
import logging
from metpy.plots import SkewT
from metpy.units import units
import sqlite3
import os

logging.getLogger('matplotlib').setLevel(logging.WARNING) #prevents matplotlib debug stuff
logging.basicConfig(level=logging.NOTSET)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL + 1)

#data import & setup
kestrel_log = pd.read_csv(r"C:\Users\train\Documents\drone data\data_june16.csv", on_bad_lines='skip', skiprows=4, index_col=False)
kestrel_temp = kestrel_log['°F'].tolist()
kestrel_time = kestrel_log['yyyy-MM-dd hh:mm:ss a'].tolist()
kestrel_dew = kestrel_log['ft'].tolist() #for whatever reason, this is the column the dews are logged in
uav_log = pd.read_csv(r"C:\Users\train\Documents\drone data\drone_june16.csv", on_bad_lines='skip')
uav_time = uav_log['datetime(utc)'].tolist()
uav_height = uav_log['height_above_takeoff(feet)'].tolist()
uav_time_reduced = []
kestrel_time_reduced = []
kestrel_time_utc = []


#returns 1 if DST is active, 0 if DST is not active (insane)
isDST = time.daylight

#removing datestamp from data because it is irrelevent
for x in uav_time:
    placeholder1 = x[11:]
    uav_time_reduced.append(placeholder1)
for x in kestrel_time:
    placeholder2 = x[11:]
    kestrel_time_reduced.append(placeholder2)
dateOfData = kestrel_time[1]
dateOfData = dateOfData[:10]
print(dateOfData)
#needed for lists, dictionaries do this already
#remove duplicate timestamps
uav_time_shortened = []
uavTime = (uav_time_reduced[0])
uavTime = int(uavTime[6:9])
    
for y in uav_time_reduced:
    v = int(y[6:9])
    deltaSecond = v - uavTime
    if deltaSecond != 0:
        uav_time_shortened.append(y)
        uavTime = v

#convert to 24 hour format (relatively obvious)
def convert24(str1): 
    if str1[-2:] == "AM" and str1[:2] == "12": 
        return "00" + str1[2:-2] 
    elif str1[-2:] == "AM": 
        return str1[:-2]  
    elif str1[-2:] == "PM" and str1[:2] == "12": 
        return str1[:-2] 
    else:
        return str(int(str1[:2]) + 12) + str1[2:8]      
base_time = convert24("02:20:12 PM")
final_time = 'null'

#convert to UTC function, who woulda guessed based on that function name
def convert_to_utc(timestamp):
    timestamp = timestamp.strip() #removes white space that was throwing errors
    timestamp = datetime.strptime(timestamp, "%H:%M:%S")
    local_tz = pytz.timezone("EST")
    utcOffset = pytz.timezone("GMT")
    local_dt = local_tz.localize(timestamp) 
    utc_dt = local_dt.astimezone(utcOffset)
    if isDST == 1:
        utc_dt = utc_dt - timedelta(hours=1)
    utc_dt = utc_dt.strftime("%H:%M:%S")
    return utc_dt

#gain user inputted start and end times
startTime = "4:33:00" #input("Input start time (hh:mm:ss): ")
endTime = "4:38:45" #input("Input end time (hh:mm:ss): ")
#converting start time to datetime object
startTimeDT = datetime.strptime(startTime, "%H:%M:%S")
startTimeDT = datetime.strftime(startTimeDT, "%H:%M:%S")
#converting to 24 hour UTC time
startTimeDT = convert24(startTimeDT)
startTimeDT = convert_to_utc(startTimeDT)
#converting end time to datetime object
endTimeDT = datetime.strptime(endTime, "%H:%M:%S")
endTimeDT = datetime.strftime(endTimeDT, "%H:%M:%S")
#converting to 24 hour UTC time
endTimeDT = convert24(endTimeDT)
endTimeDT = convert_to_utc(endTimeDT)


#converting kestrel timestamps to UTC
for x in kestrel_time_reduced:
    base_time_reduced = convert24(x)
    final_time = convert_to_utc(base_time_reduced)
    kestrel_time_utc.append(final_time)

kestrel_time_utc_2 = []
kestrel_temp2 = []
kestrel_dew2 = []
for x in kestrel_time_utc:
    if x >= startTimeDT and x <= endTimeDT:
        index = kestrel_time_utc.index(x)
        kestrel_time_utc_2.append(x)
        addTemp = kestrel_temp[index]
        kestrel_temp2.append(addTemp)
        addDew = kestrel_dew[index]
        kestrel_dew2.append(addDew)

#making dicts to store values
kestrelTemp = {}
for key in kestrel_time_utc_2:
    for value in kestrel_temp2:
        kestrelTemp[key] = value
        kestrel_temp2.remove(value)
        break

kestrelDew = {}
for key in kestrel_time_utc_2:
    for value in kestrel_dew2:
        kestrelDew[key] = value
        kestrel_dew2.remove(value)
        break 

# to convert lists to dictionary
timeHeight = {}
for key in uav_time_reduced:
    for value in uav_height:
        timeHeight[key] = value
        uav_height.remove(value)
        break

#comparing lists to only have same times
uav_time_final = []
kestrel_time_final = []
for x in uav_time_shortened:
    if x in kestrel_time_utc:
        uav_time_final.append(x)
for x in kestrel_time_utc:
    if x in uav_time_final:
        kestrel_time_final.append(x)
df = pd.DataFrame(list(zip(kestrel_time_final, uav_time_final)),
                   columns =['kestrel', 'uav'])

#rduce dicts to only neccesary values
timeHeight2 = {}
for key, value in timeHeight.items():
    x = key
    y = value
    if x in uav_time_final:
        timeHeight2[x] = y

kestrelTemp2 = {}
for key, value in kestrelTemp.items():
    x = key
    y = value
    if x in kestrel_time_final:
        kestrelTemp2[x] = y

kestrelDew2 = {}
for key, value in kestrelDew.items():
    x = key
    y = value
    if x in kestrel_time_final:
        kestrelDew2[x] = y

#make a list from dict for df
timeHeightList = list(timeHeight2.items())
kestrelTempList = list(kestrelTemp2.items())
kestrelDewList = list(kestrelDew2.items())

#make df
df2 = pd.DataFrame(timeHeightList, columns=['time', 'height'])
df3 = pd.DataFrame(kestrelTempList, columns=['time', 'temperature'])
df4 = pd.DataFrame(kestrelDewList, columns=['time', 'dew'])
df5 = pd.merge(df2, df3, on = "time")
df6 = pd.merge(df5, df4, on='time')
temp = df6['temperature'].tolist()
height = df6['height'].tolist()
dew = df6['dew'].tolist()

plt.figure(figsize=(6,4))
plt.subplot(1, 2, 2)
plt.plot(temp, height, color='r')
plt.title("Temperature w/ Height")
plt.xlabel("Temperature")
plt.ylabel("Height (ft)")
plt.grid(axis = "y", linestyle = '--')
plt.subplot(1, 2, 1)
plt.plot(dew, height, color='g')
plt.title("Dewpoint w/ Height")
plt.xlabel("Dewpoint")
plt.ylabel("Height (ft)")
plt.grid(axis = "y", linestyle = '--')
save_results_to = 'C:/Users/train\Documents/python generated skew-T/'
fileName = str(uav_time[0])
fileName = fileName.replace(':', ' ')
plt.savefig(save_results_to + fileName + '.png')
plt.show()
logging.debug('plot "shown"')

#calulating lapse rates
maxHeight = height[-1]
maxHeightMeters = maxHeight * 0.3048
tempRange = ((temp[0] - 32) / 1.8) - ((temp[-1] - 32) / 1.8)
lapseRate = tempRange / maxHeightMeters
lapserateKm = lapseRate * 1000
print("Lapse Rate 0 -", round(maxHeightMeters), "m : ", round(lapserateKm, 1), "c/km")

# Connect to DB and create a cursor
sqliteConnection = sqlite3.connect('droneData.db')
cursor = sqliteConnection.cursor()
data=cursor.execute('''SELECT * FROM weatherData''') 
#for row in data: 
    #print(row) 

'''#for whatever reason if the table needs to be recreated
# Creating table
table = """ CREATE TABLE weatherData (
            date TEXT,
            timestamp TEXT,
            height REAL,
            temperature REAL,
            dewpoint REAL,
            unique (timestamp, height, temperature, dewpoint)
        ); """
cursor.execute(table)
print("Table created")'''
try:
    for time3, height3, temp3, dew3 in zip(kestrel_time_utc_2, height, temp, dew):
        query = "INSERT INTO weatherData (date, timestamp, height, temperature, dewpoint) VALUES ('" + dateOfData + "', '" + str(time3) + "', '" + str(height3) + "','" + str(temp3) + "','" + str(dew3) + "' ) "
        cursor.execute(query)
        data=cursor.execute('''SELECT * FROM weatherData''') 
    print('data added succesfully!')
    #for row in data: 
    #    print(row) 
except:
    print('query failed (likely duplicate data)')

sqliteConnection.commit()

# Close the connection
sqliteConnection.close()








