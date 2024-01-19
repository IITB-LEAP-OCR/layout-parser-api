import os
import json
from subprocess import call 
import time
from typing import List

from ..core.config import *
from .models import *


def logtime(t: float, msg:  str) -> None:
	print(f'[{int(time.time() - t)}s]\t {msg}')

t = time.time()
models_folder_name='models'
models_dir_path=os.path.join(os.path.dirname(IMAGE_FOLDER),models_folder_name)
docker_image_name= "shouryatyagi222/textron:1"

def run_docker():
    call(f'docker run --rm --net host -v {IMAGE_FOLDER}:/data {docker_image_name}', shell = True)

def process_textron_output(folder_path: str) -> List[LayoutImageResponse]:
    try:
        # call(f'./textron.sh', shell=True)
        run_docker()
        a = open(IMAGE_FOLDER+'/out.json', 'r').read().strip()
        a = json.loads(a)
        ret=[]
        for page in a.keys():
            regions=[]
            for bbox in a[page]:
                regions.append(
                    Region.from_bounding_box(
                        BoundingBox(x=int(bbox['x']),y=int(bbox['y']),w=int(bbox['w']),h=int(bbox['h']),
                            label=bbox['label'],
                        )
					)
                )
            ret.append(
                LayoutImageResponse(
                  image_name=page,
                  regions=regions.copy()
                )
            )
        return ret     
                     
    except Exception as e:
        print(e)

def textron_visualize(image_path: str) -> List[Region]:
    # try:
    #     check_output(['docker','run','--rm','--net','host','-v',f'{IMAGE_FOLDER}:/data','textron:1'])
    # except:
    #     check_output(['sudo','docker','run','--rm','--net','host','-v',f'{IMAGE_FOLDER}:/data','textron:1'])
    run_docker()
    a = open(IMAGE_FOLDER+'/out.json', 'r').read().strip()
    a = json.loads(a)
    for page in a.keys():
        regions=[]
        for bbox in a[page]:
            regions.append(
                Region.from_bounding_box(
                    BoundingBox(x=int(bbox['x']),y=int(bbox['y']),w=int(bbox['w']),h=int(bbox['h']),
                        label=bbox['label'],
                    )
                )
            )
        return regions