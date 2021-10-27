# Python-Video-Annotator

## Table of contents
* [Introduction](#introduction)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Interannotator Agreement](#interannotator-agreement)
* [Shortcut-keys](#shortcut-keys)


## Introduction
With the increase of illegal smoking happening around Singapore, our team has come up with a video clip annotator to support and find a way for users to capture it with annotations for future references. The closed-circuit television (CCTV) is used to monitor the public areas and the recording can be analyzed for instances of illegal smoking and annotated accordingly.

Click the image below to watch our video demonstration for this project.

<a href="https://www.youtube.com/watch?v=FloDsSYSAqo"
target="_blank"><img src="http://img.youtube.com/vi/FloDsSYSAqo/0.jpg" 
alt="Python Video Annotator" width="480" border="10" /></a>


## Technologies
Project is created with:
* kivy version: 2.0.0
* kivymd version: 0.104.2
* opencv-contrib-python
* pascal-voc-writer
* nanoid version: 2.0.0


## Setup
To run this project, install it locally using pip:

```
$ cd ../Python-Video-Annotator
$ pip install -r requirements.txt
$ python main.py
```

## Features
File Manager
- Choose video file to be read for annotating or reviewing annotations

Video playback
- Enable a video read to be played in a sequence of frames for annotations or reviewing annotations

Modes to create annotation
- Object tracking mode:  Annotations will be drawn automatically for the next five seconds of video frames using object tracking.
- Manual mode: Annotations will be drawn for two seconds. When the video is resumed, it will automatically pause at the last frame drawn and you can choose to click or edit your annotation for it to continue drawing the same area for another two seconds, or press play to stop drawing and proceed with the video.

Annotation tab
- Displays all annotations created in the current frames
- Selecting the annotation, highlights the annotation for further action such as deletion or adjustment

Label tab
- Displays all the labels
- Selecting the label, changes the label for the annotation created

Create new labels
- Default label is 'Smoking'

Save annotations into xml file
- After annotating the video frames, annotations created can be saved into an xml file to be read when opening the video or reviewing the annotations

Delete annotations
- Two different modes of deletion:
  - Delete selected annotation: Remove only the selected annotations
  - Delete associated annotations based on selected annotation:
    - For object tracking mode, all annotations made by the object tracker would be deleted.
    - For manual mode, all annotations which were repeatedly drawn at the same location would be deleted.

Verify annotations
- Saves all annotations created and verifies all annotations including current frame into the xml File
- All annotations verified will have a different color bounding box

Unverify annotations
- Save all annotations and unverify all annotations made into the xml file


## Interannotator Agreement
- Add or remove the xml files created by the application to folders 'person1' and 'person2' to compute their interannotator agreement
- Run the following commands

```
$ ./compute.ps1
```

Sample output

![image](https://user-images.githubusercontent.com/24503925/139047179-cdb066a1-29ae-4c43-9bd5-dedeb156b5bb.png)


## Shortcut keys
'ctrl-a' - Annotation mode: To start drawing annotations

'ctrl-m' - Switch Annotation modes: Object Tracking or manual

'ctrl-l' - Triggers popup dialog for creating new label

'ctrl-s' - Save all annotations created into an xml file in the same file location as the video file

'ctrl-t' - Verify all annotations created till current frame, also saves all annotations made into xml file

'ctrl-d' - Delete all associated annotations created

'del' - Delete selected annotation

'space-bar' - Play/Pause Video

'q or left-arrow' - Go back 5 frames

'e or right-arrow' - Go forward 5 frames
