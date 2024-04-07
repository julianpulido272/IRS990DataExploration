# /opt/anaconda/bin/ipython

import os
import random
import re

from lxml import etree

datadir = "/stat129/all990files/"

all990 = [datadir + p for p in os.listdir(datadir)]
# Has 2.3 million files

# Working with a small sample is easier
n = 10000
#random.seed(2089) # Same random sample
s990 = random.sample(all990, n)

#Method to extract the xpath information given an xmlfile
def extract(xmlfile):
    """
    Extract a dictionary containing the elements of interest
    """
    tree = etree.parse(xmlfile)
    fields990 = ["ActivityOrMissionDesc", "MissionDesc", "TotalEmployeeCnt", "TotalAssetsEOYAmt", "TotalContributionsAmt", "CYTotalRevenueAmt"]

    # Hold all the results
    result = {}
    for f in fields990:
        # Won't always be there
        try:
            result[f] = tree.xpath("/Return/ReturnData/IRS990/" + f + "/text()")[0]
        except:
            # didn't work!
            # There are certainly better ways to handle this.
            result[f] = None
    
    #business Filer Info (different fields)

    #get the date for which the tax file was created
    try:
        result["returnDateStamp"] = tree.xpath("/Return/ReturnHeader/ReturnTs/text()")[0]
    except:
        result["returnDateStamp"]= None

    try:
        result["EIN"] = tree.xpath("/Return/ReturnHeader/Filer/EIN/text()")[0]
    except:
        result["EIN"] = None
    try:
        result["BusinessName"] = tree.xpath("/Return/ReturnHeader/Filer/BusinessName/BusinessNameLine1Txt/text()")[0]
    except:
        result["BusinessName"] = None
    
    #patterns to find regex in 
    #patterns = [r"water"]
    #value = result["ActivityOrMissionDesc"]

    #for p in patterns:
    #    if  value and re.search(p, value, re.IGNORECASE):
    #        return result
    #return None

    #once we have found which non profits were of interest to us, we search now if the xml file contains that EIN
    EINList = [r"842322254", r"770487468", r"800267674", r"263547740", r"113299408"]

    #get the EIN for our XML result dictionary
    target = result["EIN"]

    for ein in EINList:
        if target and re.search(ein, target):
            return result
    return None

def extract_Regex(xmlfile, regex):
    """
    Extract a dictionary containing the elements of interest. if the xml file contains the regex expression in the description, return the xml. if not, return null
    """
    tree = etree.parse(xmlfile)
    fields990 = ["ActivityOrMissionDesc", "MissionDesc", "TotalEmployeeCnt", "TotalAssetsEOYAmt", "TotalContributionsAmt", "CYTotalRevenueAmt"]

    # Hold all the results
    result = {}
    for f in fields990:
        # Won't always be there
        try:
            result[f] = tree.xpath("/Return/ReturnData/IRS990/" + f + "/text()")[0]
        except:
            # didn't work!
            # There are certainly better ways to handle this.
            result[f] = None

    #get the date for which the tax file was created. has a different xpath
    try:
        result["returnDateStamp"] = tree.xpath("/Return/ReturnHeader/ReturnTs/text()")[0]
    except:
        result["returnDateStamp"]= None

    #check if our regex is in our xmlfile, if not return null since we don't care about it
    value = result["ActivityOrMissionDesc"]
    
    #check if value exists and search for it
    if  value and re.search(regex, value, re.IGNORECASE):
        return result
    else:
        return None

def printData(xmlResults):
    """
    print the data in csv format. need to check for null values.
    """
    #we only want to print these keys
    keys = ["EIN", "returnDateStamp", "TotalEmployeeCnt", "TotalContributionsAmt" , "CYTotalRevenueAmt"]

    #print each key so that it will be our header for our dataset
    for k in keys:
        print(k +"," ,end ="")
    print("")

    #for each documnent in our list of xmlResults
    for doc in xmlResults:
        #check for each key per documnet
        for key in keys:
            #check if value is null. if so print blank
            if doc[key] is not None:
                print(doc[key] + ",", end = "")
            else:
                print("" + ",", end = "")
        #prints a new line
        print("")




# Test our function
r3 = extract(s990[3])
#print(r3)

# Apply our function to many files
#pattern = r"water"
#rn = list(map(lambda filename: extract_Regex(filename,pattern),s990))
rn = map(extract, s990)

# Convert it to a list, because map is lazy
#if it has None value, filter it out because we dont care about it

#rn = list(filter(None,rn))
#printData(rn)


#print(rn)
# Now run it on... EVERYTHING ALL AT ONCE IN PARALLEL!
# See https://docs.python.org/3/library/multiprocessing.html
from multiprocessing import Pool

# 10 parallel workers
with Pool(10) as p:
    r = p.map(extract, all990)
    out = list(filter(None,r))
    printData(out)

#print out our desired fields from the ouput of 2.3 million xml files
#our output wont be 2.3 million in size bc we reduced it using REGEX and filtering
#for doc in out:
#    print(doc["EIN"][0] + ","+doc["returnDateStamp"] + "," + doc["totalEmployeeCnt"] +","+ doc["TotalContributionsAmt"] + "," + doc["CYTotalRevenueAmt"])


# Nice, it was faster than I expected:
#
#    In [57]: %time %run tax.py
#    CPU times: user 14.8 s, sys: 1.31 s, total: 16.1 s
#    Wall time: 1min 42s
