from subprocess import call, check_output
from tempfile import TemporaryDirectory

from fastapi import APIRouter, Form

from .helper import process_images, process_layout_output
from .models import MIResponse, PostprocessRequest, SIResponse
from ..script_identification.models import ModelChoice
from ..script_identification.helper import process_output

router = APIRouter(
    prefix='/layout/postprocess',
    tags=['Postprocess'],
)

@router.post(
    '/language/printed',
    response_model=list[SIResponse],
    response_model_exclude_none=True,
)
def identify_printed_language(si_request: PostprocessRequest) -> list[SIResponse]:
    """
    This is the endpoint for classifying the language of the **printed** images.
    this model works for all the 14 language (13 Indian + english)

    API inputs a list of images in base64 encoded string and outputs a list
    of objects containing **"text"** as key and **language** as value
    """
    tmp = TemporaryDirectory(prefix='language_classify')
    process_images(si_request.images, tmp.name)
    call(f'./lang_iden_printed_v1.sh {tmp.name}', shell=True)
    return process_layout_output(tmp.name)

@router.post(
    '/language/handwritten',
    response_model=list[SIResponse],
    response_model_exclude_none=True,
)
def identify_handwritten_language(si_request: PostprocessRequest) -> list[SIResponse]:
    """
    This is the endpoint for classifying the language of the **handwritten** images.
    this model works for all the 14 language (13 Indian + english)

    API inputs a list of images in base64 encoded string and outputs a list
    of objects containing **"text"** as key and **language** as value
    """
    tmp = TemporaryDirectory(prefix='language_classify')
    process_images(si_request.images, tmp.name)
    call(f'./lang_iden_handwritten_v1.sh {tmp.name}', shell=True)
    return process_layout_output(tmp.name)

@router.post(
    '/language/scenetext',
    response_model=list[SIResponse],
    response_model_exclude_none=True,
)
def identify_scenetext_language(si_request: PostprocessRequest) -> list[SIResponse]:
    """
    This is the endpoint for classifying the language of the **REAL** Scenetext images.
    this model works for all the 14 language (13 Indian + english)

    API inputs a list of images in base64 encoded string and outputs a list
    of objects containing **"text"** as key and **language** as value
    """
    tmp = TemporaryDirectory(prefix='language_classify')
    process_images(si_request.images, tmp.name)
    call(f'./lang_iden_scenetext_v1.sh {tmp.name}', shell=True)
    return process_layout_output(tmp.name)

def run_docker(IMAGE_FOLDER, docker_image_name):
        print(IMAGE_FOLDER)
        try:
            check_output(['docker','run','--rm','--net','host','-v',f'{IMAGE_FOLDER}:/model/data',docker_image_name],shell=True)
        except:
            check_output(['sudo', 'docker','run','--rm','--net','host','-v',f'{IMAGE_FOLDER}:/model/data',docker_image_name],shell=True)
            # check_output(command)
@router.post(
    '/script',
    response_model=list[SIResponse],
    response_model_exclude_none=True
)
def identify_script(si_request: PostprocessRequest, model: ModelChoice, venv_path = "layout-parser-venv", si_venv_path = "server/modules/script_identification/layout-parser-venv-script-identification") -> list[SIResponse]:
    """
    This is an endpoint for identifying the script of the word images.
    this model was contributed by **Punjab university (@Ankur)** on 07-10-2022
    The endpoint takes a list of images in base64 format and outputs the
    identified script for each image in the same order.

    Currently 8 recognized languages are [**hindi, telugu, tamil, gujarati,
    punjabi, urdu, bengali, english**]

    API inputs a list of images in base64 encoded string and outputs a list
    of objects containing **"text"** as key and **language** as value
    """
    tmp = TemporaryDirectory(prefix='st_script')
    process_images(si_request.images, tmp.name)
    if(model==ModelChoice.default):
        call(f'./script_iden_v1.sh {tmp.name}', shell=True)
        ret = process_layout_output(tmp.name)
    elif(model==ModelChoice.alexnet):
        run_docker(tmp.name, "script-identification")	
        ret = process_output(tmp.name)
    return ret
    


@router.post(
    '/modality',
    response_model=list[MIResponse],
    response_model_exclude_none=True,
)
def identify_modality(si_request: PostprocessRequest) -> list[MIResponse]:
    """
    This is the endpoint for classifying the modality of the images.
    this model works for all the 14 language (13 Indian + english) and
    outputs among 3 classes ["**printed**", "**handwritten**", "**scenetext**"]

    API inputs a list of images in base64 encoded string and outputs a list
    of objects containing **"text"** as key and **modality** as value
    """
    tmp = TemporaryDirectory(prefix='modality_classify')
    process_images(si_request.images, tmp.name)
    call(f'./modality_iden_v1.sh {tmp.name}', shell=True)
    return process_layout_output(tmp.name)