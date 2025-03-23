#a large quantity of imports
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
import math

#debug setup
logging.getLogger('matplotlib').setLevel(logging.WARNING) #prevents matplotlib debug stuff
logging.basicConfig(level=logging.NOTSET)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL + 1)

dateOfData = "feb10" #as written in the file name (probably not standardized so good luck)
timeOfData = "2049z" #as written in the file name
timeOfKestrel = "20z" #because multiple datasets rely on the same kestrel timestamp
startTime ="3:49:15 PM" #input("Input start time (hh:mm:ss): ")
endTime = "3:57:15 PM" #input("Input end time (hh:mm:ss): ")
saveDataToFile = True #does this even do anything anymore

#data import & setup
kestrel_log = pd.read_csv(r"C:\Users\train\Documents\drone data\data_"  + dateOfData + "_" + timeOfKestrel + ".csv", on_bad_lines='skip', skiprows=4, index_col=False)
#kestrel_log = pd.read_csv(r"C:\Users\train\Documents\drone data\data_"  + dateOfData + ".csv", on_bad_lines='skip', skiprows=4, index_col=False)
#kestrel_log = pd.read_csv(r"C:\Users\train\Documents\drone data\data_nov1.csv", on_bad_lines='skip', skiprows=4, index_col=False)
kestrel_temp = kestrel_log['°F'].tolist()
kestrel_time = kestrel_log['yyyy-MM-dd hh:mm:ss a'].tolist()
kestrel_dew = kestrel_log['ft'].tolist() #for whatever reason, this is the column the dews are logged in
kestrel_rh = kestrel_log['%'].tolist()
uav_log = pd.read_csv(r"C:\Users\train\Documents\drone data\drone_" + dateOfData + "_" + timeOfData + ".csv", on_bad_lines='skip')
#uav_log = pd.read_csv(r"C:\Users\train\Documents\drone data\drone_" + dateOfData + ".csv", on_bad_lines='skip')
#uav_log = pd.read_csv(r"C:\Users\train\Documents\drone data\drone_nov1.csv", on_bad_lines='skip')
uav_time = uav_log['datetime(utc)'].tolist()
uav_height = uav_log['height_above_takeoff(feet)'].tolist()
kestrel_log_v2 = pd.read_csv(r"C:\Users\train\Documents\drone data\data_" + dateOfData + "_" + timeOfKestrel + ".csv", on_bad_lines='skip', skiprows=4, index_col=False)
#kestrel_log_v2 = pd.read_csv(r"C:\Users\train\Documents\drone data\data_" + dateOfData + ".csv", on_bad_lines='skip', skiprows=4, index_col=False)
#kestrel_log_v2 = pd.read_csv(r"C:\Users\train\Documents\drone data\data_nov1.csv", on_bad_lines='skip', skiprows=4, index_col=False)
uav_time_reduced = []
kestrel_time_reduced = []
kestrel_time_utc = []
dew_from_rh = []
kestrel_pressure_2 = []

#gain user inputted start and end times
AmPm = kestrel_time[0]
AmPm = AmPm[20:]

# Rename duplicate columns
def rename_duplicates(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

df = rename_duplicates(kestrel_log_v2)
kestrel_pressure = df["°F.1"].tolist()

#rudementary method for finding the correct dewpoint data column
#this definately is not used anymore
dewValue = float(kestrel_dew[20])

if dewValue < 0 or dewValue > 100:
    kestrel_dew = kestrel_log['°F.2'].tolist()

for x in kestrel_pressure:
    x = x * 33.864
    kestrel_pressure_2.append(x)

#returns 1 if DST is active, 0 if DST is not active (insane)
#isDST = time.daylight
isDST = 0 #daylight time manual override because the automatic one doesnt work for some unknown reason

#removing datestamp from data because it is irrelevent
for x in uav_time:
    placeholder1 = x[11:]
    uav_time_reduced.append(placeholder1)
for x in kestrel_time:
    placeholder2 = x[11:]
    kestrel_time_reduced.append(placeholder2)
dateOfData = kestrel_time[1]
dateOfData = dateOfData[:10]

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

#converts time to UTC, who woulda guessed based on that function name
def convert_to_utc(timestamp):
    timestamp = timestamp.strip() #removes white space that was throwing errors
    timestamp = datetime.strptime(timestamp, "%H:%M:%S")
    local_tz = pytz.timezone("EST")
    utcOffset = pytz.timezone("GMT")
    local_dt = local_tz.localize(timestamp) 
    utc_dt = local_dt.astimezone(utcOffset)
    #this daylight time code should work now
    if isDST == 1:
        utc_dt = utc_dt + timedelta(hours=-1) 
    utc_dt = utc_dt.strftime("%H:%M:%S")
    return utc_dt



#converting start time to datetime object
startTimeDT = datetime.strptime(startTime, "%I:%M:%S %p")
startTimeDT = datetime.strftime(startTimeDT, "%I:%M:%S %p")
#converting to 24 hour UTC time
startTimeDT = convert24(startTimeDT)
startTimeDT = convert_to_utc(startTimeDT)
#converting end time to datetime object
endTimeDT = datetime.strptime(endTime, "%I:%M:%S %p")
endTimeDT = datetime.strftime(endTimeDT, "%I:%M:%S %p")
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

#removes data outside of specified time?
#fixed this with absolutely diabolical nested statements, sorry to whoever reads the following code
for x in kestrel_time_utc:
    if startTimeDT[:2] == '23' and endTimeDT[:2] == '00': #checking to see if times cross between days
        if x[:2] == '23': 
            if x >= startTimeDT:
                index = kestrel_time_utc.index(x)
                kestrel_time_utc_2.append(x)
                addTemp = kestrel_temp[index]
                kestrel_temp2.append(addTemp)
                addDew = kestrel_dew[index]
                kestrel_dew2.append(addDew)
        elif x[:2] == '00':
            if x <= endTimeDT:
                index = kestrel_time_utc.index(x)
                kestrel_time_utc_2.append(x)
                addTemp = kestrel_temp[index]
                kestrel_temp2.append(addTemp)
                addDew = kestrel_dew[index]
                kestrel_dew2.append(addDew)
        else:
            print('error')
    else:
        if x >= startTimeDT and x <= endTimeDT:
            index = kestrel_time_utc.index(x)
            kestrel_time_utc_2.append(x)
            addTemp = kestrel_temp[index]
            kestrel_temp2.append(addTemp)
            addDew = kestrel_dew[index]
            kestrel_dew2.append(addDew)
#lets never discuss the above code again

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

#reduce dicts to only neccesary values
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

#make df for plotting
df2 = pd.DataFrame(timeHeightList, columns=['time', 'height'])
df3 = pd.DataFrame(kestrelTempList, columns=['time', 'temperature'])
df4 = pd.DataFrame(kestrelDewList, columns=['time', 'dew'])
df5 = pd.merge(df2, df3, on = "time")
df6 = pd.merge(df5, df4, on='time')
temp = df6['temperature'].tolist()
height = df6['height'].tolist()
dew = df6['dew'].tolist()

#plotting the data
plt.figure(figsize=(6,4))
plt.subplot(1, 2, 2)
plt.plot(temp, height, color='r')
plt.suptitle("Sounding MILT " + dateOfData + " " + endTimeDT[:2] + "z")
#plt.title("Tempreature w/ Height")
plt.xlabel("Temperature")
plt.ylabel("Height (ft)")
plt.grid(axis = "y", linestyle = '--')
plt.subplot(1, 2, 1)
plt.plot(dew, height, color='g')
#plt.title("Dewpoint w/ Height")
plt.xlabel("Dewpoint")
plt.ylabel("Height (ft)")
plt.grid(axis = "y", linestyle = '--')
#plt.xticks(np.arange(10, 20, 5)) 
#saving the plot
save_results_to = 'C:/Users/train\Documents/python generated skew-T/'
fileName = str(uav_time[0])
fileName = fileName.replace(':', '_')
plt.savefig(save_results_to + fileName + '.png')
plt.show()
logging.debug('plot "shown"')


saveFilePath = r"C:\Users\train\Documents\programs\droneDataWebpage\data"
saveFileName = fileName + "z.csv"
full_path = f"{saveFilePath}/{saveFileName}"

# Check if the file exists
if os.path.exists(full_path):
    # Prompt the user to choose whether to replace the file
    user_choice = input(f"The file '{full_path}' already exists. Do you want to replace it? (yes/no): ").strip().lower()
    if user_choice == 'yes':
        # Overwrite the existing file
        df6.to_csv(full_path, index=False)
        print(f"File has been replaced.")
    elif user_choice == 'no':
        print(f"File was not replaced. Existing data will be preserved.")
    else:
        print("Invalid choice. File will not be replaced by default.")
else:
    # Save the DataFrame to a new CSV file
    df6.to_csv(full_path, index=False)
    print(f"File '{full_path}' has been created.")

#oh that's where that variable was used
#if saveDataToFile == True:
#    df6.to_csv(full_path, index=False)
#think this might be depreciated

#calulating lapse rates
maxHeight = height[-1]
maxHeightMeters = maxHeight * 0.3048
tempRange = ((temp[0] - 32) / 1.8) - ((temp[-1] - 32) / 1.8)
lapseRate = tempRange / maxHeightMeters
lapserateKm = lapseRate * 1000
print("Lapse Rate 0 -", round(maxHeightMeters), "m : ", round(lapserateKm, 1), "c/km")
derivedLapseRate = "Lapse Rate 0-" + str(round(maxHeightMeters)) + "m: " + str(round(lapserateKm, 1)) + "c/km"

# Derived data to append
derived_data = [
    "",
    "# Derived Data",
    str(derivedLapseRate),
]

# Function to check and append derived data
def append_derived_data(file_path, derived_data):
    derived_data_exists = False

    # Check if file exists
    if os.path.exists(file_path):
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Check if all lines of derived data already exist in the file
        derived_data_exists = all(line in content for line in derived_data if line)  # Ignore empty lines

    # Append the derived data only if it doesn't already exist
    if not derived_data_exists:
        with open(file_path, 'a') as file:
            file.writelines('\n'.join(derived_data) + '\n')
        print("Derived data appended successfully.")
    else:
        print("No changes made. Derived data already exists in the file.")

# Call the function to append derived data
append_derived_data(full_path, derived_data)

print(f"Data written to {full_path}")

# there used to be broken sqlite code here.  It is gone now, and it is in the programs folder if you ever need it again.
















