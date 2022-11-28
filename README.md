────────────────────────────────────────────       
╔════╗────────────╔═══╗─────╔╗──────╔╗                          
║╔╗╔╗║────────────║╔══╝─────║║─────╔╝╚╗                        
╚╝║║╠╩╦╦══╦══╦══╦═╣╚══╦╗╔╦══╣║╔╗╔╦═╩╗╔╬══╦═╗                            
──║║║╔╬╣╔╗║╔╗║║═╣╔╣╔══╣╚╝║╔╗║║║║║║╔╗║║║╔╗║╔╝                    
──║║║║║║╚╝║╚╝║║═╣║║╚══╬╗╔╣╔╗║╚╣╚╝║╔╗║╚╣╚╝║║                      
──╚╝╚╝╚╩═╗╠═╗╠══╩╝╚═══╝╚╝╚╝╚╩═╩══╩╝╚╩═╩══╩╝                          
───────╔═╝╠═╝║                                                  
───────╚══╩══╝                                  
────────────────────────────────────────────

#TriggerEvaluator
The TriggerEvaluator is a framework to compare trigger-mechanisms.
A trigger is a condition that determines whether an application behaves maliciously or not.
A trigger-mechanism is an implemented method to automatically fulfill this condition and activate hidden behaviour.

The _TriggerEvaluator_ was build as part of my Bachelor-Thesis.

#Getting Started
These instructions will get a copy of the project up and running on your local machine for development and testing purposes.

## Installing

### Step 1 - Install Android Development Kit (ADK)
Download and install [AndroidStudio](https://developer.android.com/studio) from its homepage.

Go to _Tools > SDK Manager > SDK Tools_

And install _Android SDK Command-line Tools (latest)_

### Step 2 - Download Android API Versions
The current version of the TriggerEvaluator needs Android API 31, 23, 21.

Install API 31 with the following commands
The sdkmanager is located in _AndrodSDK-Folder > tools > bin_
```
sdkmanager "platform-tools" "platforms;android-31"

sdkmanager "system-images;android-31;default;x86_64"

sdkmanager --licenses
```
Change the 31 to 23 and 21

### Step 3 - Clone this repo
```
git clone https://github.com/jflier2s/TriggerEvaluation
```

### Step 4 - Install requirements
```
pip install -r requirements.txt
```

### Step 5 - Edit config.ini
Change paths in _config.ini_ - file

## Run - Execute Code
```
python3 main.py
```
More information with _--help_ or _-h_

# Build With
 - [Curious Monkey](https://github.com/hayyanHasan/Curious-Monkey/) - Triggering method by hayyanHasan
 - [Exerciser Monkey](https://developer.android.com/studio/test/other-testing-tools/monkey) - Official Tool by Google
 - [DroidBot](https://github.com/honeynet/droidbot) - Triggering method by Yuanchun Li
 - [Evadroid Suite](https://ibmmobile.bitbucket.io/) - Framework with implemented trigger

#Contributing
If you want to contribute you can simply create a pull request. Feel free to contact me
