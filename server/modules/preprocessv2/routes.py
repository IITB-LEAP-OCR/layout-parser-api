import json
import os
import pickle
import cv2
from fastapi import UploadFile, Form
from fastapi.responses import Response
from subprocess import call
from tempfile import TemporaryDirectory

from .models import *

from .helper import save_uploaded_images, delete_files_in_directory

from ..core.config import IMAGE_FOLDER
from ..preprocess.routes import router


@router.post('/font_v2',response_model=None)
async def get_font_properties_from_image(
	images: List[UploadFile],
	model: ModelChoice = Form(ModelChoice.doctr),
	task: TaskChoice = Form(TaskChoice.attributes),
	k_size: int = Form(default=4),
	bold_threshold: float = Form(default=0.3)
	):
	"""
	This endpoint returns the font attributes of text from images.
	"""
	temp = TemporaryDirectory()
	image_path = save_uploaded_images(images,temp.name)
	
	config = {
		"model": "doctr" if model == ModelChoice.doctr else "tesseract",
		"k_size": k_size,
		"bold_threshold": bold_threshold
	}

	with open(os.path.join(image_path,"config"),"wb") as f:
		pickle.dump(config,f)

	print("Calling docker")
	# model_dir = os.path.join(os.getcwd(),"models")
	# call(f"docker run --rm -v {temp.name}:/model/data -v{model_dir}:/root/.cache/doctr/models textattrib")
	call(f"docker run --rm -v {temp.name}:/model/data textattrib", shell = True)
	print("Done docker")
	

	if task == TaskChoice.attributes:
		with open(os.path.join(temp.name,"out.json")) as f:
			out = json.load(f)	
		response = FontAttributesResponse.model_validate(out)
	
	else:
		result_images = [os.path.join(temp.name,"result",i) for i in os.listdir(os.path.join(temp.name,"result"))]
		img = cv2.imread(result_images[0])
		res, im_png = cv2.imencode(".png", img)
		response = Response(content=im_png.tobytes(),media_type="image/png")
	
	# temp.cleanup()
	return response
