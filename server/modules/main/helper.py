import os
import shutil
import uuid
from os.path import join
from subprocess import run
from tempfile import TemporaryDirectory
from typing import List, Tuple

from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from fastapi import UploadFile

from ..core.config import IMAGE_FOLDER
from .models import *

# TODO: remove this line and try to set the env from the docker-compose file.
os.environ['USE_TORCH'] = '1'


def save_uploaded_images(files: List[UploadFile]) -> str:
	print('removing all the previous uploaded files from the image folder')
	os.system(f'rm -rf {IMAGE_FOLDER}/*')
	print(f'Saving {len(files)} to location: {IMAGE_FOLDER}')
	for image in files:
		location = join(IMAGE_FOLDER, f'{image.filename}')
		with open(location, 'wb') as f:
			shutil.copyfileobj(image.file, f)
	return IMAGE_FOLDER


def save_uploaded_image(image: UploadFile) -> str:
	"""
	function to save the uploaded image to the disk

	@returns the absolute location of the saved image
	"""
	location = join(IMAGE_FOLDER, '{}.{}'.format(
		str(uuid.uuid4()),
		image.filename.strip().split('.')[-1]
	))
	with open(location, 'wb+') as f:
		shutil.copyfileobj(image.file, f)
	return location

def convert_geometry_to_bbox(
	geometry: Tuple[Tuple[float, float], Tuple[float, float]],
	dim: Tuple[int, int]
) -> BoundingBox:
	"""
	converts the geometry that is fetched from the doctr models
	to the standard bounding box model
	format of the geometry is ((Xmin, Ymin), (Xmax, Ymax))
	format of the dim is (height, width)
	"""
	x1 = int(geometry[0][0] * dim[1])
	y1 = int(geometry[0][1] * dim[0])
	x2 = int(geometry[1][0] * dim[1])
	y2 = int(geometry[1][1] * dim[0])
	return BoundingBox(
		x=x1,
		y=y1,
		w=x2-x1,
		h=y2-y1,
	)

def process_multiple_image_craft(folder_path: str) -> List[Region]:
	"""
	Given a path to the folder if images, this function returns a list
	of word level bounding boxes of all the images
	"""
	run([
		'docker',
		'run',
		'--rm',
		'--gpus', 'all',
		'-v', f'{folder_path}:/data',
		'parser:craft',
		'python', 'test.py'
	])
	files = [join(folder_path, i) for i in os.listdir(folder_path) if i.endswith('txt')]
	ret = []
	for file in files:
		# TODO: add the proper error detection if the txt file is not found
		image_name = os.path.basename(file).strip()[4:].replace('txt', 'jpg')
		a = open(file, 'r').read().strip()
		a = a.split('\n\n')
		a = [i.strip().split('\n') for i in a]
		regions = []
		for i, line in enumerate(a):
			for j in line:
				word = j.strip().split(',')
				word = list(map(int, word))
				regions.append(
					Region.from_bounding_box(
						BoundingBox(
							x=word[0],
							y=word[1],
							w=word[2],
							h=word[3],
						),
						line=i+1
					)
				)
		ret.append(
			LayoutImageResponse(
				image_name=image_name,
				regions=regions.copy()
			)
		)
	return ret

def process_image_craft(image_path: str) -> List[Region]:
	"""
	given the path of the image, this function returns a list
	of bounding boxes of all the word detected regions.

	@returns: list of BoundingBox class
	"""
	print('running craft model for image...', end='')
	tmp = TemporaryDirectory(prefix='craft')
	os.system(f'cp {image_path} {tmp.name}')
	print(tmp.name)
	run([
		'docker',
		'run',
		'--rm',
		'--gpus', 'all',
		'-v', f'{tmp.name}:/data',
		'parser:craft',
		'python', 'test.py'
	])
	a = [join(tmp.name, i) for i in os.listdir(tmp.name) if i.endswith('txt')]
	# TODO: add the proper error detection if the txt file is not found
	a = a[0]
	a = open(a, 'r').read().strip()
	a = a.split('\n\n')
	a = [i.strip().split('\n') for i in a]
	ret = []
	for i, line in enumerate(a):
		for j in line:
			word = j.strip().split(',')
			word = list(map(int, word))
			ret.append(
				Region.from_bounding_box(
					BoundingBox(
						x=word[0],
						y=word[1],
						w=word[2],
						h=word[3],
					),
					line=i+1
				)
			)
	return ret


def process_image(image_path: str) -> List[Region]:
	"""
	given the path of the image, this function returns a list
	of bounding boxes of all the word detected regions.

	@returns list of BoundingBox class
	"""
	print('running the doctr model for image...', end='')
	predictor = ocr_predictor(pretrained=True)
	doc = DocumentFile.from_images(image_path)
	a = predictor(doc)
	print('done')
	a = a.pages[0]
	# in the format (height, width)
	dim = a.dimensions
	lines = []
	for i in a.blocks:
		lines += i.lines
	ret = []
	for i, line in enumerate(lines):
		for word in line.words:
			ret.append(
				Region.from_bounding_box(
					convert_geometry_to_bbox(word.geometry, dim),
					line=i+1,
				)
			)
	return ret