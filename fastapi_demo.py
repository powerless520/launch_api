import json
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi import Request, Response
from pydantic import BaseModel

from SegmentDataQwenChunLianGenerateV6 import pipeline
from file_cloud_def import OssClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
# 静态资源访问
# app.mount("/result", StaticFiles(directory="./result"), name="result")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

oss = OssClient()


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class InputData(BaseModel):
    text: str


class OutPutData(BaseModel):
    code: int
    msg: str
    data: str


@app.post("/chunlian")
@limiter.limit("5/minute")
async def chunlian(request: Request, response: Response):
    requestBody = await request.body()

    jsonBody = json.loads(requestBody)
    custom_text = jsonBody['text']
    if custom_text == '':
        custom_text = '新年快乐'

    print('chunlian custom_text:' + custom_text)
    flag, result = pipeline(custom_text)
    print('custom_text flag:' + str(flag) + '| result:' + result)

    if flag:
        returnUrl = oss.upload_to_oss(result)
        return {"code": "200", "msg": "success", "data": returnUrl}
    else:
        return {"code": "500", "msg": "failure"}


@app.post("/items", response_model=OutPutData)
async def create_item(item: Item) -> OutPutData:
    out = OutPutData(
        code=200,
        msg="success",
        data=item
    )
    return out


@app.post("/img")
@limiter.limit("5/minute")
async def img(request: Request, response: Response):
    body = await request.body()

    print('body:', json.loads(body)['text'])
    return {"code": "200", "msg": "success",
            "data": "https://www.1zhizao.com/generate/cd2df28a-6a97-40a2-9b4c-32a7eeeb64c8-1706442641.png"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8188)
