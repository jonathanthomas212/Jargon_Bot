import slack
import os
import csv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

#maybe store this in an .env file
slackToken="xoxb-4810031156-1950093251250-law6pgudYLJfqhfMReOXVr54"
signingSecret="628ab17b0599b2c5776d9d725fe6b3ce"



#read in csv dict and add it to a python dict
filename ="jargonDict.csv"
jargonDict={}

with open(filename, 'r') as data:

    next(csv.reader(data)) # skip header line  
    for line in csv.reader(data):
        key = line[0]
        value = line[1]

        #format key
        key = key.lower()
        formattedKeyArray = []
        
        for i in list(key):
            if i.isalnum():
                formattedKeyArray.append(i)

        formattedKey = "".join(formattedKeyArray)
        #add to dict
        jargonDict[formattedKey] = value



#read in users.csv
users=[]
with open("users.csv", 'r') as data:
 
    for line in csv.reader(data):
        users.append(line[0])



#read in badWords.csv
badWords={}
with open("badWords.csv", 'r') as data:
 
    for line in csv.reader(data):
        word = line[1].strip(",")
        badWords[word] = ""



app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(signingSecret, '/slack/events', app)

client = slack.WebClient(slackToken)
BOT_ID = client.api_call("auth.test")['user_id']



#message event recieved
@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    #only reply to user messages
    if (user_id != None) and (BOT_ID != user_id): 

        #parse message and return term/acronym
        term = parseMessage(text)

        #find defention
        response = getResponse(term)

        #send a message to same channel (dm)
        client.chat_postMessage(channel=channel_id, text=response)



#slash command received
@app.route('/slash', methods=['POST'])
def slash_command():
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')

    #add to dict and return response
    response = addToDict(text)

    #send a message to same channel (dm)
    client.chat_postMessage(channel=channel_id, text=response)
    
    return Response(), 200



#app_home_opened event recieved
@slack_event_adapter.on('app_home_opened')
def greeting(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    
    initial_greeting = "Hi I'm Jargon Bot :wave: you can message me to define any terms or acronyms you don't know. Just type the word or ask me what it means (I'm a very good reader). You can also add a new term to my dictionary with the command */add_entry*"

    #send initial greeting and add to known users
    if user_id not in users:
        client.chat_postMessage(channel=channel_id, text=initial_greeting)

        users.append(user_id)
        newRow = [user_id]

        with open("users.csv",'a',newline='\n') as data:
            writer = csv.writer(data)
            writer.writerow(newRow)

    



#return term/acronym        
def parseMessage(text):

    #remove upper case
    text = text.lower()

    if "what does " in text:
        if " mean" in text:
            term = (text.split("what does ")[1]).split(" mean")[0]
        elif " stand for" in text:
            term = (text.split("what does ")[1]).split(" stand for")[0]
        else:
            term = text

    elif "what" in text:   
        if "what is an " in text:
            term = text.split("what is an ")[1]
        elif "what is a " in text:
            term = text.split("what is a ")[1]
        elif "whats an " in text:
            term = text.split("whats an ")[1]
        elif "whats a " in text:
            term = text.split("whats a ")[1]
        elif "what's an " in text:
            term = text.split("what's an ")[1]
        elif "what's a " in text:
            term = text.split("what's a ")[1]
        elif "what is " in text:
            term = text.split("what is ")[1]
        elif "whats " in text:
            term = text.split("whats ")[1]
        elif "what's " in text:
            term = text.split("what's ")[1]
        else:
            term = text

    elif "define " in text:
        term = text.split("define ")[1]

    else:
        term = text


    #remove spaces and special characters
    formattedTermArray = []
    
    for i in list(term):
        if i.isalnum():
            formattedTermArray.append(i)

    formattedTerm = "".join(formattedTermArray)
    return formattedTerm
    

#return dictionary value or error message
def getResponse(term):

    if term in jargonDict:
        return jargonDict[term]
    else:
        notFound = "Sorry, I don't know that one"
        return notFound



def addToDict(text):

    #split key and value
    if ":" in text:
        key = text.split(":")[0]
        value = text.split(":")[1]
    else:
        return "Oops something went wrong, make sure you use the format */add_entry term:definition*"

    #check for profanity
    if containsBadWord(key,value):
        return "Hey that's a bad word :rage:"

    #format key
    key = key.lower()
    formattedKeyArray = []

    for i in list(key):
        if i.isalnum():
            formattedKeyArray.append(i)

    formattedKey = "".join(formattedKeyArray)

    #add to python dict and csv
    jargonDict[formattedKey] = value
    updateCSV(formattedKey,value)
    return "I added it to my dictionary, thanks!"



#add a line to the bottom of the csv
def updateCSV(key,value):

    newRow = [key,value]

    with open(filename,'a',newline='\n') as data:
        writer = csv.writer(data)
        writer.writerow(newRow)

    print("CSV updated")



#check for bad words in entry
def containsBadWord(key,value):

    if key.lower() in badWords:
        return True

    valueList = value.split(" ")
    for word in valueList:
        if word.lower() in badWords:
            return True

    return False



if __name__ == "__main__":
    
    app.run(debug=True)









