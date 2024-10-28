# Build-master

## Description
  This is a telegram bot that let's the relevant people in a group know that they are the build master for the week. It has a scheduler that sends the message every Monday at 08:00. 

## What you will need:
  - Python v3.7.7 and higher
  - ```pip install python-dotenv, python-telegram-bot, APScheduler, pytz```

## To run it:
  - ```python path/to/dest/build_dev6.py```

## To run it in the background:
  - ```nohup python path/to/dest/build_dev6.py &```
  - If you want to end the process you need to see if it is running first:
    - ```ps -ef```
  - To kill the process:
    - ```kill -9 $(ps aux | grep build_dev6.py | grep -v grep | awk '{print $2}')```
  - Please check if the above killed the process, by using:
    - ```ps -ef``` 