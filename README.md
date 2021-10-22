# Python-Video-Annotator

## Table of contents
* [Introduction](#introduction)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#features)
* [Shortcut-keys](#shortcut-keys)

## Introduction
With the increase of illegal smoking happening around Singapore, our team has come up with a video clip annotator to support and find a way for users to capture it with annotations for future references. The closed-circuit television (CCTV) is used to monitor the public areas and the recording can be analyzed for instances of illegal smoking and annotated accordingly.

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
- Object tracking mode: for the next ten seconds of video frames using object tracking upon annotation drawn
- Manual mode:  where the annotation drawn will be repeatedly drawn at the same location for the next two seconds and paused for the user to interact with the annotation for it to continue drawing the annotation or stop the repetition if no interaction is made.

Annotation tab
- Displays all annotations created in the current frames
- Selecting the annotation, highlights the annotation for further action such as deletion or adjustment

Add other labels
- Default label is 'Smoking'

Save annotations into xml file
- After annotating the video frames, annotations created can be saved into an xml file to be read when opening the video or reviewing the annotations

Delete annotations
- Two different modes of deletion:
  - Delete selected annotation: Remove only the selected annotations
  - Delete associated annotations based on selected annotation:
    - if called on a frame annotated using object tracking mode, all annotations made by the object tracker would be deleted. For manual mode, all annotations which were repeatedly drawn at the same location would be deleted.

Verify annotations
- Saves all annotations created and verifies all annotations including current frame into the xml File
- All annotations verified will have a different color

Unverify annotations
- Save all annotations and unverify all annotations made into the xml file


## Shortcut keys
'ctrl-a' - Annotation mode: To start drawing annotations

'ctrl-s' - Save all annotations created into an xml file in the same file location as the video file

'ctrl-t' - Verify all annotations created till current frame, also saves all annotations made into xml file

'ctrl-d' - Delete all associated annotations created
