from typing import Annotated

from fastapi import Depends, Request

from app.bmkg.client import BmkgClient


def get_bmkg(request: Request) -> BmkgClient:
    return request.app.state.bmkg


Bmkg = Annotated[BmkgClient, Depends(get_bmkg)]
