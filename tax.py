# /opt/anaconda/bin/ipython

import os
import random
import re
from copy import deepcopy
from lxml import etree
from functools import partial 

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
    fields990 = ["ActivityOrMissionDesc", "MissionDesc", "TotalEmployeeCnt", "TotalAssetsEOYAmt", "TotalContributionsAmt", "CYTotalRevenueAmt" , "TotalVolunteersCnt"]

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
    #patterns = [r"immigration"]
    value = result["ActivityOrMissionDesc"]

    
    if value and re.search(r"immigration", value, re.IGNORECASE):
            return result
    return None

    #once we have found which non profits were of interest to us, we search now if the xml file contains that EIN
    #EINList = [r"842322254", r"770487468", r"800267674", r"263547740", r"113299408"]

    #get the EIN for our XML result dictionary
    #target = result["EIN"]

    #for ein in EINList:
    #    if target and re.search(ein, target):
    #        return result
    #return None


def printData(xmlResults):
    """
    print the data in csv format. need to check for null values.
    """
    #we only want to print these keys
    keys = ["EIN","BusinessName" ,"returnDateStamp", "TotalEmployeeCnt","TotalVolunteersCnt", "TotalContributionsAmt" , "CYTotalRevenueAmt"]

    #print each key so that it will be our header for our dataset
    for k in keys:
        print(k +"," ,end ="")
    print("")

    #for each documnent in our list of xmlResults
    for doc in xmlResults:
        if doc is not None:
        #check for each key per documnet
            for key in keys:
                #check if value is null. if so print blank
                if doc[key] is not None:
                    print(doc[key] , end = ", ")
                else:
                    print("" ,end = ", ")
            #prints a new line
            print("")


def convertToInt(result):
    """
    converts all integers values to actual integers in our xml results
    """

    for x in result:
        for k,v in x.items():
            if k in {"TotalEmployeeCnt", "TotalVolunteersCnt", "TotalContributionsAmt", "CYTotalRevenueAmt"} and v is not None:
                x[k] = int(v) #convert to integer
    return result

def sortByKey(data ,key):
    """
    function to sort by key
    necessary because some keys have None values. Cant sort a None value so we replace it with +-Infinity
    """
    #define a custom key function to handle None values
    def keyNoneHandler(item):
        value = item.get(key)
        return value if value is not None else float('-inf')

    return data.sort(key = keyNoneHandler, reverse = True)

def xmlContainsEIN(xmlFiles, nums):
    """
    Given a xmlFile of dictionaries, this method will use set lookups to see if the xml File is of our particular interest by seeing if it has an EIN that matches our set. 
    """
    if xmlFiles["EIN"] in nums:
        return xmlFiles
    else:
        return None

# Apply our function to many files
rn = map(extract, s990)

# Convert it to a list, because map is lazy
#if it has None value, filter it out because we dont care about it

#rn = list(filter(None,rn))
#printData(rn)

#print("\n\nprinting2022")

#copy rn into d2
#d2 = deepcopy(rn)
#d2 = convertToInt(d2)


#get non profits from 2022
#d22 = [x for x in d2 if "2022" in x["returnDateStamp"]]
#printData(d22)
#get 5 biggest non profits based on our idea of importance of 2022
#d22.sort(key = lambda x: x["TotalContributionsAmt"])
#sortByKey(d22, "TotalContributionsAmt")
#printData(d22)

#after sorting, the 5 highest importance will be at the top of my list
#top5MostImportant = {result["EIN"] for result in d22[:5]}
#print(top5MostImportant)

# Now run it on... EVERYTHING ALL AT ONCE IN PARALLEL!
# See https://docs.python.org/3/library/multiprocessing.html
from multiprocessing import Pool

# 10 parallel workers
with Pool(10) as p:
    r = p.map(extract, all990)
    out = list(filter(None,r))

#make copy of output to edit the copy
outCopy = deepcopy(out)

#convert all strings to ints
outCopy = convertToInt(out)

#get subset by year. Im picking 2022
out22 = [x for x in outCopy if "2022" in x["returnDateStamp"]]

#sort by most important factor
sortByKey(out22, "TotalContributionsAmt")

#get a set of the top 5 non profits based on my most important factor
top5MostImportantEIN = {file["EIN"] for file in out22[:5]}

#grep for these EIN in our orginal output
with Pool(10) as p:
    xmlContainsEINPartial = partial(xmlContainsEIN, nums = top5MostImportantEIN)
    output = p.map(xmlContainsEINPartial, out)
    outputFiltered = list(filter(None,output))
    printData(outputFiltered)


#print out our desired fields from the ouput of 2.3 million xml files
#our output wont be 2.3 million in size bc we reduced it using REGEX and filtering
#for doc in out:
#    print(doc["EIN"][0] + ","+doc["returnDateStamp"] + "," + doc["totalEmployeeCnt"] +","+ doc["TotalContributionsAmt"] + "," + doc["CYTotalRevenueAmt"])


# Nice, it was faster than I expected:
#
#    In [57]: %time %run tax.py
#    CPU times: user 14.8 s, sys: 1.31 s, total: 16.1 s
#    Wall time: 1min 42s
