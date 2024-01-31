import os

from typing import List
import json
import io
from fastapi import APIRouter, Form, UploadFile
from fastapi.responses import StreamingResponse
from tempfile import TemporaryDirectory
from subprocess import call
from .helper import save_uploaded_images
from .models import LayoutImageResponse, ModelChoice



router = APIRouter(
	prefix='/layout',
	tags=['table'],
)

@router.post('/table', response_model=None)
async def table_layout_parser(
	images: List[UploadFile],
	model: ModelChoice = Form(ModelChoice.fasterrcnn),
	dilate: bool = Form(False),
	):
	"""
	API endpoint for calling the layout parser
	"""
	temp = TemporaryDirectory()

	image_path = save_uploaded_images(images,temp.name)
	
	print("Calling docker")
	command = ["docker", "run", "--rm", "-v", f"{temp.name}:/model/data", "tabledockerize"]
	call(command, shell=True)
	# call(f"docker run --rm -v {temp.name}:/model/data tabledockerize")
	print("Done docker")

	files_in_temp = os.listdir(temp.name)

	# Print the list of files
	print("Files in temporary directory:")
	for file_name in files_in_temp:
		print(file_name)
	
	with open(os.path.join(temp.name, "out.json")) as f:
			out = json.load(f)	
	response = LayoutImageResponse.model_validate(out)
	print("response:", response)
	
	temp.cleanup()
	return response


@router.post('/visualize/table')
async def layout_parser_swagger_only_demo_table(
	images: List[UploadFile],
	model: ModelChoice = Form(ModelChoice.fasterrcnn),
	dilate: bool = Form(False),
):
	"""
	This endpoint is only used to demonstration purposes.
	this endpoint returns/displays the input image with the
	bounding boxes clearly marked in blue rectangles.

	PS: This endpoint is not to be called from outside of swagger
	"""
	temp = TemporaryDirectory()

	image_path = save_uploaded_images(images,temp.name)

	print("Calling docker")
	command = ["docker", "run", "--rm", "-v", f"{temp.name}:/model/data", "tabledockerize"]
	call(command, shell=True)
	print("Done docker")

	files_in_temp = os.listdir(temp.name)

	# Print the list of files
	print("Files in temporary directory:")
	for file_name in files_in_temp:
		print(file_name)
	image_path_with_boxes = os.path.join(temp.name, "boxes.jpg")

	with open(image_path_with_boxes, mode="rb") as img_file:
		return StreamingResponse(io.BytesIO(img_file.read()), media_type="image/jpeg")