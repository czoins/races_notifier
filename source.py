import requests, time, re
from bs4 import BeautifulSoup as bs
from datetime import datetime, date, timedelta
from mailjet_rest import Client

def main():
    with open("config.txt") as conf:
        config = conf.read().splitlines()
        keywords = [key.strip() for key in config[1].replace("Races:", "").split(",")]
        emails = [key.strip() for key in config[2].replace("Emails:", "").split(",")]
    
    try:
        with open("notified") as ntf:
            notified = ntf.read().splitlines()
    except FileNotFoundError:
        open("notified", "w").close()    
    
    success = False
    while not success:
        try:
            content = requests.get("https://dubairacingclub.com/visit/calendar/racing-calendar")
            success = True
        except:
            time.sleep(5)
    
    soup = bs(content.content, "html.parser")
    dates, titles, times = [], [], []
    for k in soup.find_all("span", {"class": "date-display-single"}):
        dates.append(k.text.strip().split(", ", 1))
        
    for k in soup.find_all("td", {"class": "views-field views-field-title"}):
        titles.append(k.text.strip())
        
    for k in soup.find_all("td", {"class": "views-field views-field-field-event-post-time-value"}):
        times.append(k.text.strip())
    
    races = [list(l) for l in zip(dates, titles, times)]
    
    races = [l for l in races if any([bool(re.search(k, l[1], re.I)) for k in keywords])]
    
    MONTHS = {"January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06", "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"}
    today = []
    tomorrow = []
    
    for race in races:
        race[0][1] = race[0][1].replace(",", "").split()
        race[0][1][1] = MONTHS[race[0][1][1]]
        if len(race[0][1][0]) < 2:
            race[0][1][0] = "0" + race[0][1][0]
        race[0][1] = " ".join(race[0][1])
        
        race[2] = race[2].lower()
        if "pm" in race[2]:
            race[2] = race[2].replace("pm", "").split(":")
            race[2][0] = str(int(race[2][0]) + 12)
            race[2] = ":".join(race[2])
        elif "am" in race[2]:
            race[2] = race[2].replace("am", "")
            if len(race[2].split(":")[0]) < 2:
                race[2] = race[2].split(":")
                race[2][0] = "0" + race[2][0]
                race[2] = ":".join(race[2])
        race[0][1] = race[0][1] + " "  + race[2]
        
        fd = datetime.strptime(race[0][1], '%d %m %Y %H:%M')
        raceDate = str(fd.date())
        raceTimestamp = fd.timestamp()
        
        if raceDate == str(date.today()) and raceTimestamp > time.time() and not race[0][1] in notified:
            today.append([race[1], race[0][0], race[2], race[0][1]])
        if raceDate == str(date.today() +timedelta(days=1)) and not race[0][1] in notified:
            tomorrow.append([race[1], race[0][0], race[2], race[0][1]])
    
    body = ""
    body += "<strong>Today:</strong><br/>"
    if today:
        for race in today:
            body += f"{race[0]} on {race[1]} at {race[2]}<br/>"
    else:
        body += "None<br/>"
        
    body += "<br/><strong>Tomorrow:</strong><br/>"
    if tomorrow:
        for race in tomorrow:
            body += f"{race[0]} on {race[1]} at {race[2]}<br/>"
    else:
        body += "None<br/>"
    
    mailjet = Client(auth=('bfa36871ec035cbe8798ae723dd268d2', 'ef38eca3a518901be8379222827e5c64'), version='v3.1')
    
    if today or tomorrow:
        for email in emails:
            data = {
              'Messages': [
                {
                  "From": {
                    "Email": "racesremainderpy@mozej.com",
                    "Name": "Races notifier"
                  },
                  "To": [
                    {
                      "Email": email,
                    }
                  ],
                  "Subject": f"Races notifier {date.today()}",
                  "TextPart": "Races notifier",
                  "HTMLPart": "<h3>These are the races for today and tomorrow</h3><br/>" + body
                  
                }
              ]
            }
            result = mailjet.send.create(data=data)
            time.sleep(5)
            
        if result.status_code == 200:
            with open("notified", "a") as ntf:
                if today:
                    for race in today:
                        ntf.write(race[3] + "\n")
                if tomorrow:
                    for race in tomorrow:
                        ntf.write(race[3] + "\n")
                        
if __name__ == "__main__":
    main()