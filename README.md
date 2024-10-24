# ScoreMOT

## Abstract
Machine vision is one of the major technologies to guarantee intelligent robots’ human-centered embodied intelligence. Especially in the complex dynamic scene involving multi-person, Multi-Object Tracking (MOT), which can accurately identify and track specific targets, significantly influences intelligent robots’ performance regarding behavior perception and monitoring, autonomous decision-making, and providing personalized humanoid services. In order to solve the problem of targets lost and identity switches caused by the scale variations of objects and frequent overlaps during the tracking process, this paper presents a multi-object tracking method using score-driven hierarchical association strategy between predicted tracklets and objects (ScoreMOT). Firstly, a motion prediction of occluded objects based on bounding box variation (MPOBV) is proposed to estimate the position of occluded objects. MPOBV models the motion state of the object using the bounding box and confidence score. Then, a score-driven hierarchical association strategy between predicted tracklets and objects (SHAS) is proposed to correctly associate them in frequently overlapping scenarios. SHAS associates the predicted tracklets and detected objects with different confidence in different stages. 
<p align="center"><img src="assets/Architecture .jpg" width="600"/></p>

## Installation

ScoreMOT code is based on ByteTrack and BoT-SORT. <br>
Visit their installation guides for more setup options.

Step1. Install ScoreMOT.
```shell
git clone https://github.com/tianyiSKY1/ScoreMOT.git
cd ScoreMOT
pip3 install -r requirements.txt
python3 setup.py develop
```

Step2. Others.

```shell
pip3 install cython
pip3 install 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
pip3 install cython_bbox
```


## Data preparation

Download [MOT17](https://motchallenge.net/), [MOT20](https://motchallenge.net/), [DanceTrack](https://github.com/DanceTrack/DanceTrack.git) and put them under <ScoreMOT_HOME>/datasets in the following structure:
```
datasets
   |——————MOT17
   |        └——————train
   |        └——————test
   └——————MOT20
   |        └——————train
   |        └——————test
   └——————DanceTrack
            └——————train
            └——————val
            └——————test
```

Then, you need to turn the datasets to COCO format and mix different training data:

```shell
cd <ScoreMOT_HOME>
python3 tools/convert_mot17_to_coco.py
python3 tools/convert_mot20_to_coco.py
python3 tools/convert_dance_to_coco.py
```

## Tracking performance
The code was tested on Ubuntu 20.04. All experiments were conducted on a single NVIDIA A10 GPU with 24GB RAM.
### Results on MOT challenge test set
| Dataset    |  MOTA | IDF1 | HOTA | FP($10^4$) | FN($10^4$) | IDs | FPS |
|------------|-------|------|------|------|------|------|------|
|MOT17       | 79.8 | 76.7 | 63.0 | 2.57 | 8.43 | 4007 | 25.6 |
|MOT20       | 77.7 | 75.6 | 62.3 | 2.46 | 8.92 | 1440 | 16.2 |

### Results on DanceTrack test set
| Dataset    |  MOTA | IDF1 | HOTA | DetA | AssA |
|------------|-------|------|------|------|------|
|DanceTrack      | 92.7 | 55.2 | 55.5 | 81.0 | 38.2 |

## Case Study on Mobile Robot
To validate the application of the ScoreMOT algorithm in intelligent robotics, we designed and implemented a real-time following system based on ScoreMOT. The core of the system is the ScoreMOT algorithm running on the NVIDIA Jetson Orin platform, which operates with the Ubuntu 20.04 operating system and is developed using the Robot Operating System (ROS) framework.

You can select any person on the screen to follow.

<p align="center">
  <img src="/assets/follow1.gif" alt="Trackbot" width="400"/>
  <img src="/assets/follow2.gif" alt="Trackbot" width="400"/>
</p>

More details can be found at [TrackBot](https://github.com/tianyiSKY1/TrackBot).

## Acknowledgement

A large part of the code is borrowed from [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX), [ByteTrack](https://github.com/ifzhang/ByteTrack), [BoT-SORT](https://github.com/NirAharon/BoT-SORT) and [HybridSORT](https://github.com/ymzis69/HybridSORT). Thanks them for their great works!