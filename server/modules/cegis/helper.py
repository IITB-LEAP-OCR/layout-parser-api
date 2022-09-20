import base64
import csv
import os
import shutil
import urllib
import uuid
from os.path import join
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Tuple

import cv2
import numpy as np
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from fastapi import UploadFile

from ..core.config import IMAGE_FOLDER
from .models import *

# TODO: remove this line and try to set the env from the docker-compose file.
os.environ['USE_TORCH'] = '1'


def save_image(url: str, dir_path: str) -> str:
	ret = join(dir_path, 'image.jpg')
	urllib.request.urlretrieve(url, ret)
	return ret



def extractImage(img, coordinate_path, saved_images_path):
	count = 1

	with open(coordinate_path, mode = "r") as file:
		next(file)
		csvFile = csv.reader(file)

		for lines in csvFile:
			x = int(lines[1])
			y = int(lines[2])
			w = int(lines[3])
			h = int(lines[4])

			if w == 0 or h == 0: continue
	
			else:
				images_name = saved_images_path + "/" + str(count)+ ".jpg"
				single_image = img[y: y+h, x: x+w]
				cv2.imwrite(images_name, single_image)

				count += 1
      

def perform_align(imgPath, saved_images_path, template='template1'):
	img_template_path = f'/home/krishna/layout-parser/server/modules/cegis/templates/{template}.png'
	coordinate_path = f'/home/krishna/layout-parser/server/modules/cegis/templates/{template}.csv'
	im1 = cv2.imread(img_template_path)
	im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)

	im2 = cv2.imread(imgPath, cv2.IMREAD_COLOR)
	im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)

	im1_gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
	im2_gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)

	max_num_features = 500
	orb = cv2.ORB_create(max_num_features)
	keypoints1, descriptors1 = orb.detectAndCompute(im1_gray, None)
	keypoints2, descriptors2 = orb.detectAndCompute(im2_gray, None)

	matcher = cv2.DescriptorMatcher_create(
	    cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
	matches = matcher.match(descriptors1, descriptors2, None)

	matches = sorted(matches, key=lambda x: x.distance, reverse=False)

	numGoodMatches = int(len(matches)*0.1)
	matches = matches[:numGoodMatches]

	points1 = np.zeros((len(matches), 2), dtype=np.float32)
	points2 = np.zeros((len(matches), 2), dtype=np.float32)

	for i, match in enumerate(matches):
		points1[i, :] = keypoints1[match.queryIdx].pt
		points2[i, :] = keypoints2[match.trainIdx].pt

	#Find homography
	h, _ = cv2.findHomography(points2, points1, cv2.RANSAC)

	height, width, _ = im1.shape
	im2_reg = cv2.warpPerspective(im2, h, (width, height))
	extractImage(im2_reg, coordinate_path, saved_images_path)

def get_all_images(path):
	a = os.listdir(path)
	a = sorted(a, key=lambda x:int(x.strip().split('.')[0]))
	a = [join(path, i) for i in a]
	a = [base64.b64encode(open(i, 'rb').read()).decode() for i in a]
	return a