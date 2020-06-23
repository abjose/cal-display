# code initially copied from https://developers.google.com/calendar/quickstart/python
from datetime import datetime, timezone
from dateutil.parser import parse
import pickle
import os, os.path
from PIL import Image
from cairosvg import svg2png
from io import BytesIO
from inky import InkyWHAT
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def hours_and_minutes(duration):
    seconds = duration.total_seconds()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours == 0: minutes = max(minutes, 1)
    return f"{hours:02d}:{minutes:02d}"

# Return true if there have been changes to the svg since last time.
def save_svg(current_task, remaining, next_task, next_task_date, next_task_duration):
    with open("template.svg", "r") as template:
        data = template.read()
        data = data.replace("thing1", current_task)
        if current_task == "free":
            data = data.replace("time1 remaining", "")
        else:
            data = data.replace("time1", hours_and_minutes(remaining))
        data = data.replace("thing2", next_task)
        # only show date if not today
        if next_task_date.date() == datetime.today().date():
            datestring = " " + str(next_task_date.time())[:-3]
            data = data.replace("date2", datestring)
        else:
            datestring = str(next_task_date.date())[6:]  # date without year
            datestring += " " + str(next_task_date.time())[:-3]
            data = data.replace("date2", datestring)
        data = data.replace("duration2", hours_and_minutes(next_task_duration))
        if os.path.exists("output.svg"):
            with open("output.svg", "r") as old_svg:
                # check if something has changed
                # bit hacky - compare to saved svg
                old_data = old_svg.read()
                if data == old_data:
                    print("Aborting, no changes have occurred")
                    return False
        with open("output.svg", "w") as output:
            output.write(data)
        return True

def send_to_display():


    # TODO: do only in python... was having some issues with svg2png
    os.system("inkscape -z -w 400 -h 300 output.svg -e output.png")
    img = Image.open("output.png")
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette((255, 255, 255, 0, 0, 0, 255, 0, 0) + (0, 0, 0) * 252)
    img = img.convert("RGB").quantize(palette=pal_img)

    # send
    inky_display = InkyWHAT("red")
    inky_display.set_border(inky_display.RED)
    inky_display.set_image(img)
    inky_display.show()

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    print("getting calendar data")
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    cal_id = "primary"
    with open("calendar_id.txt", "r") as cal_config:
        cal_id = cal_config.read().strip()
    events_result = service.events().list(calendarId=cal_id, timeMin=now,
                                          maxResults=2, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    print("generating image")
    now = datetime.now(timezone.utc)
    should_send = True
    if not events:
        should_send = save_svg("no events found", now-now, "nothing", now-now, now-now)
        print('No upcoming events found.')
    else:
        start1 = parse(events[0]['start'].get('dateTime', events[0]['start'].get('date')))
        end1 = parse(events[0]['end'].get('dateTime', events[0]['end'].get('date')))
        summary1 = events[0]['summary']

        start2 = now
        end2 = now
        summary2 = "free"
        if len(events) > 1:
            start2 = parse(events[1]['start'].get('dateTime', events[1]['start'].get('date')))
            end2 = parse(events[1]['end'].get('dateTime', events[1]['end'].get('date')))
            summary2 = events[1]['summary']

        if start1 <= now <= end1:
            # first event is currently happening
            shoudl_send = save_svg(summary1, end1-now, summary2, start2, end2-start2)
        else:
            # first event is yet to happen
            should_send = save_svg("free", start1-now, summary1, start1, end1-start1)

    if should_send:
        print("sending to display")
        send_to_display()

    print("done")


if __name__ == '__main__':
    main()
