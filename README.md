# InternetOfFish2.0

## Motivation
Understanding the biological mechanisms that lead to complex behavior is a core goal of neuroscience. When studying this
link, experimenters often need to collect samples soon after a behavior occurs. This was the case for a recent joint
project of the Streelman and McGrath Labs at Georgia Tech. In this project, we needed to collect samples from 
*Pseudotrophus demasoni* (a species of cichlid fish) soon after they had performed a courtship behavior. This posed a 
challenge, because the behavior was rare and unpredictable. This motivated us to develop a low-cost automated system 
that uses computer-vision to detect courtship behavior in real-time and notifies researchers via email, the code 
for which is found in this repository. While we developed this code primarily for internal use, it may serve as a 
useful resource for others seeking to develop similar real-time behavior detection systems. 

## Conceptual Overview
The system is designed to switch between two modes: an "active mode", during which data is collected and continuously 
analyzed for courtship behavior, and a "passive mode", during which data is moved to DropBox for long-term storage. 
Active mode starts by instructing the Raspberry Pi Camera to begin recording video to a file. Soon after, a frame is
copied from the video stream to be analyzed as an image. First, an EfficientDet-Lite0 network is used to detect the 
ROI within the image. Next, the frame is cropped to the ROI area and passed to another EfficientDet-Lite0 network 
which detects fish within the ROI. The number of high-confidence fish detections is interpreted as the 
current ROI occupancy. Since the ROI location is relatively static, it is only updated once every few minutes. 
But because the fish constantly move in and out of the ROI, their positions (and in turn the occupancy) is 
estimated multiple times per second. Periodically, (by default, once every thirty seconds) the system 
analyzes the most recent occupancy data (by default, the most recent minute of data) to infer whether 
courtship is occurring. If so, it uses SendGrid to notify a researcher via email. This continues until a set
time (by default, 7pm) when the system switches to passive mode. Passive mode is relatively simple; 
stored data, in the form of H264 videos, is converted to MP4 format for better accessibility then 
uploaded to Dropbox using rclone. The system then idles until the time when active mode is scheduled to enter 
active mode again (by default, 7am the next day). This cycle continues until a user terminates the program.


## Installation:

1) follow instructions from https://aiyprojects.withgoogle.com/maker/ for the initial setup.
While we will not use the AIY Maker Kit API directly, using their prebuilt image ensures
that finicky dependencies (like pycoral) are installed correctly
2) enable the camera in raspi-config
3) Clone this repo to your pi using:
```
cd ~
git clone https://github.com/tlancaster6/InternetOfFish2.0
```
4) Open the terminal and install the remaining dependencies. Note building numpy can take
a long time.
```
sudo apt install screen
sudo pip3 install --upgrade pip
sudo pip3 install pandas
sudo pip3 install pause
sudo pip3 install PyYAML
sudo pip3 install sendgrid
sudo pip3 install --upgrade numpy
```

## Basic Usage
1) It is recommended to run the program within a screen session to ensure continuous operation and make interaction
via ssh easier. To start a screen session, open the terminal and use the command 
```
screen -S <session_name>
```
replacing <session_name> with a name of your choice. This will create a new screen session and attach to it.

2) While still within your screen session, move into the InternetOfFish2.0 directory
```
cd ~/InternetOfFish2.0
```
3) Generate a new project (replace "your_project_id" with a unique project ID of your choosing)
```
main.py --pid your_project_id
```
4) Once the default config has been generated, the program will exit. This is your opportunity to
edit the config.yaml file with custom values, such as your Sendgrid credentials or dropbox upload 
location (see  additional setup instructions below)
5) Rerun the command 
```
main.py --pid your_project_id
```
using the same project ID as before. You'll see some information print to the screen as the program starts up.
Depending on whether it is currently inside the recording hours you set in the config file, the program will enter 
either active or passive mode.
6) At this point the program should be running, and you can detach from the screen with the two following keyboard 
shortcuts:
```
Ctrl+a
Ctrl+d
```
You will be returned to the terminal where you first attached to the screen. You can close this terminal,
or close you ssh connection if you connected remotely, and the screen session you created will persist. To check on it,
open the terminal and use the command 
```
screen -r
```

## Sendgrid Setup for email notifications
Though this section is technically optional, omitting prevents the program from sending emails when a possible
behavioral event is detected, which in turn largely defeats the purpose of this program as it is currently written. 

1) create a free-tier sendgrid account (https://sendgrid.com/en-us) and create a full-access API key 
(https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys).
2) To enable email notifications for a project, first create a new project by running the following command
   (but with a unique project id of your choosing)
```
main.py --pid your_project_id
```
3) when prompted, open the config.yaml file and fill in the following variables:

   - user_email: the email which will receive notifications

   - sendgrid_from_email: the email address you used to set up the sendgrid account

   - sendgrid_api_key: the api key from the first step

5) Save and close the config file. Now when you rerun main.py (with the same project id ) to initiate data collection. 
Email notifications should be enabled.

## Rclone Setup for automated uploads (optional)
This program was originally designed to collect data during the day (active mode) and automatically upload it to dropbox 
overnight while deleting the local copies (passive mode). To enable automated uploads, you must complete the following 
steps and provide a value for "cloud_data_dir" in the config.yaml file. Otherwise, data will simply be stored on 
the micro-SD card until it fills up, but this mode of operation has not been fully tested. By default, recording 
starts at 7am (start_hour=7) and ends at 7pm (end_hour=19). These values can be adjusted via the config.yaml, 
but unexpected behavior may occur if the passive mode period is too short to upload the data collected each day.

1) install rclone:
```
sudo -v ; curl https://rclone.org/install.sh | sudo bash
```
2) configure your rclone remote (instructions here: https://rclone.org/dropbox/). The code has only been tested
with Dropbox, but should work with any cloud service supported by rclone
3) To enable automated uploads for a project, first create a new project by running the following command
(but with a unique project id of your choosing)
```
main.py --pid your_project_id
```
4) when prompted, open the config.yaml file, and change the cloud_data_dir variable to your cloud path,
including the rclone remote, where the project will be stored -- e.g., 'my_remote:/my_root/my_project_dir'
5) Save and close the config file. Now rerun main.py (with the same project id ) to initiate data collection.
Automated uploads should now be enabled

## Custom Models
This repository includes two models, ooi.tflite and roi.tflite, trained to detect objects of interest (OOIs, i.e., 
P. demasoni cichlids) and a region of interest (ROI, i.e., a green PVC pipe) in videos like resources/sample_clip.mp4. 
Adapting this repository to new species, environments, or behaviors will require at minimum that you train your own
EfficientDet-Lite0 ROI and OOI models. Models can be trained using 
[this notebook](https://colab.research.google.com/github/google-coral/tutorials/blob/master/retrain_efficientdet_model_maker_tf2.ipynb).
Once you have trained your custom models, replace the provided ooi.tflite and roi.tflite files in the models 
directory with your own ooi.tflite and roi.tflite files. 

If your use case is conceptually equivalent to ours -- i.e., you want to detect when two objects of interest occupy 
the region of interest -- simply replacing the default models with your custom models should be sufficient. If your
use case differs only slightly (e.g., you want to detect a different number of OOIs within the ROI) you may still be
able to achieve this by adjusting the config.yaml values (see "Explanation of config.yaml parameters" below). Otherwise,
you will likely need to modify some elements of the source code to fit your needs. 


## Additional tips for using Screen

To check if you have already created a screen session, open the terminal and run
```
screen -ls
```
If you already have a screen session, you should see a single entry with the session name you chose. It should be in
the "Detached" state. 

If you see multiple entries, you should terminate any you are not using to free up resources. Do
this by attaching to the session with 
```
screen -r <session_name>
```
then terminate it with the command 
```
exit
```
or the by pressing Ctrl-a, entering 
```
quit
```
and pressing enter. Note if you have actively running code in the screen session you want to terminate, you'll may need
to interrupt if first with Ctrl+c to get the prompt back. If, for some reason, you can't get the session to resume, 
or it won't respond once resumed, you can often kill a screen from the outside using the command:
```
screen -X -S <session_name> quit
```

Sometimes, when you run screen -ls, you'll see a screen session in the attached state even though you aren't actually
attached to the session. This can happen if you fail to properly detach the screen before closing the terminal or 
disconnecting via ssh. To detach the session, run
```
screen -d <session_name>
```
This should detach the session, allowing you to reattach via screen -r.

## Troubleshooting

Sometimes, especially after restarting, calls to screen will fail with the following error:
```
Cannot make directory '/var/run/screen': Permission denied
```
To fix this error, run:
```
sudo /etc/init.d/screen-cleanup start
```
If you find you're getting this error alot, you can add the command a crontab job that will run every time you restart.
Open your crontab file with "sudo crontab -e" and add the following line:
```
@reboot sudo /etc/init.d/screen-cleanup start
```
save your changes and close the editor. Restart the pi and confirm that screen now works without running the cleanup
command manually. 

## Explanation of config.yaml parameters
the config.yaml file contains parameters that you can modify to control how the program will run or enable additional
functionality (e.g., email notification and automated uploads). Each time you create a new project, it will be generated
with a default config.yaml file. Any customizations to the config must therefore be repeated each time you create a new
project. An explanation of each config parameter is included below. Note that the order in which they appear in the
actual config.yaml file may be different. 

'project_id': unique project ID. This is auto-populated based on the --pid value provided when you first run main.py.
Manually editing this value can cause unexpected errors.

'cloud_data_dir': cloud path, including the rclone remote, where the project will be uploaded. Required for automated 
uploads to work. See the Rclone Setup section for details.

'user_email': email address that will receive behavioral event notifications and error notifications. Required for email
notification to work. See the Sendgrid Setup section for details

'admin_email': email address that will only receive error notifications. Email notifications to user_email will still work
even if this parameter is left as None. See the sendgrid setup section for details.

'sendgrid_api_key': api key for your sendgrid account. See the sendgrid setup section for details.

'sendgrid_from_email': email account that you used to set up the sendgrid account. required for email notification to work.
see the Sendgrid Setup section for details. 

'min_notification_interval': Minimum interval (in seconds) between successive email notifications. This will also be the 
minimum interval between the creation of the "event_clip.mp4" files. Note that the notification process is resource
intensive, so setting this interval too low may cause problems. Setting it lower than your behavior_check_interval is
also not recommended. 

'max_notifications_per_day': Maximum number of notifications that will be sent per day by this project. This parameter
is useful for preventing a project from flooding your inbox and going over your daily allotment of SendGrid emails if
something goes wrong. 

'roi_model': the file name of the tflite model used for ROI (region of interest) detection. This file should be placed 
in the "models" directory. The default model detects a green pipe.

'ooi_model': the file name of the tflite model used for OOI (object of interest) detection. This file should be placed 
in the "models" directory. The default model detects *P. demasoni*

'roi_confidence_thresh': Minimum confidence score for an ROI detection to be considered valid. Regardless of the value
here, the highest confidence prediction will always be used. However, in the event that the ROI model returns no 
predictions with scores above this value, the program will try again with a new frame until it makes a prediction with
a high enough score.

'ooi_confidence_thresh': Minimum confidence score for an OOI detection to be considered valid. This value is critical
for getting accurate ROI occupancies. If it's too low, you will likely get false positives resulting in occupancy
overestimates. If it's too high, you'll likely get false negatives resulting in occupancy underestimates. The exact
value used depends on your application and model accuracy.

'behavior_check_window': length of the window analyzed (in seconds) at each behavior check. For example, at the default
of 60, the program will use the last minute of occupancy values in its calculations

'behavior_check_interval': seconds between behavior checks. If this value is larger than the behavior check window, 
there will be periods of occupancy data that never reach the behavior detection stage. If it is shorter than the
behavior check window, behavior check windows will overlap. Using the default values creates a 60-second window 
analyzed every 30 seconds, resulting in a rolling window with 50% overlap.  

'behavior_min_individuals_roi': min number of individuals in ROI during behavior event. If the ROI occupancy is below
this value, it will be considered evidence against the behavior of interest.

'behavior_max_individuals_roi': max number of individuals in ROI during behavior event. If the ROI occupancy is above 
this value, it will be considered evidence against the behavior of interest.

'behavior_min_fraction_for_notification': data from each behavior check window is summarized by taking the number of
frames where occupancy is within the range set by 'behavior_min_individuals_roi' and 'behavior_max_individuals_roi'
and dividing it by the total number of frames considered. If this value is above the threshold set by
'behavior_min_fraction_for_notification', the system infers that a behavioral event occurred. 

'framerate': The framerate (frames per second) of the output video. See picamera documentation for supported 
framerate resolution combinations for your camera model.

'h_resolution': the horizontal resolution (in pixels) of the output video. See picamera documentation for supported 
framerate resolution combinations for your camera model. 

'v_resolution': the vertical resolution (in pixels) of the output video. See picamera documentation for supported 
framerate resolution combinations for your camera model. 

'framegrab_interval': The target interval (in seconds) for retrieving a frame, performing object detection, and
generating an occupancy datapoint. Minimum viable value will depend on the exact hardware and parameter configuration 
used.

'roi_update_interval': Interval (in seconds) between ROI updates. If the ROI rarely moves, it is most efficient to set
this to a large number to prevent redundant inference work.

'start_hour': The hour each day at which the system should enter active mode and start collecting/analyzing data.
Should be provided in 24h format, and should be smaller than the 'end_hour'

'end_hour': The hour each day at which the system should exit active mode and enter passive mode to upload data.
Should be provided in 24h format, and should be larger than the 'start_hour' 

'video_split_hours': How frequently (in hours) to split the output video. This is a convenience functionality provided
for to reduce file sizes when recording for long periods. To disable, use a value that exceeds (end_hour - start_hour)

'test': Causes the program to run various self-tests instead of commencing normal operation. Rarely used. 

## Acknowledgements
This repository contains code developed by Tucker Lancaster (McGrath Lab, Georgia Institute of Technology) 
as part of a project designed by Kathryn Leatherbury (Streelman Lab, Georgia Institute of Technology). This material 
is based upon work supported by the National Science Foundation Graduate Research Fellowship awarded to Tucker Lancaster 
under Grant No. DGE-2039655. 
