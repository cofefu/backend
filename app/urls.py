from fastapi import APIRouter, Depends, BackgroundTasks, Body
from starlette.responses import FileResponse

from db.models import Customer
from auth.dependencies import get_current_user

from bot.services import send_feedback_to_telegram, send_bugreport_to_telegram

router = APIRouter(prefix='/api')


# TEST return svg or ico depending on the user's browser
@router.get('/favicon.svg',
            description='Возвращает логотип в формате .svg',
            response_class=FileResponse)
async def get_favicon_svg():
    return FileResponse('assets/beans.svg')


@router.get('/favicon.ico',
            description='Возвращает логотип в формате .ico',
            response_class=FileResponse)
async def get_favicon_svg():
    return FileResponse('assets/beans.ico')


@router.post('/feedback', description='Для советов, пожеланий и т.д.')
async def send_feedback(background_tasks: BackgroundTasks, msg: str = Body(...)):
    background_tasks.add_task(send_feedback_to_telegram, msg)


@router.post('/bugreport',
             tags=['jwt require'],
             description='Для информации о различных ошибках')
async def send_bugreport(background_tasks: BackgroundTasks,
                         msg: str = Body(...),
                         customer: Customer = Depends(get_current_user)):
    background_tasks.add_task(send_bugreport_to_telegram, msg, customer)
