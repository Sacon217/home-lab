from fastapi import FastAPI
from email_parser import parse_bac, parse_proamerica
from pydantic import BaseModel, field_validator
from typing import List
from fastapi.responses import JSONResponse
import logging
import sys

logger = logging.getLogger("fastapi")

class EmailItem(BaseModel):
    html: str
    from_address: str

    @field_validator("html")
    def html_must_not_be_empty(cls, html_content):

        if not html_content.strip():
            raise ValueError("html cannot be empty")

        return html_content

    @field_validator("from_address")
    def address_must_not_be_empty(cls, email):

        if not email.strip():
            raise ValueError("from_address cannot be empty")
            
        return email

from_addreses = {
    "notificacion@notificacionesbaccr.com": parse_bac,
    "info@promerica.fi.cr": parse_proamerica,
} 

app = FastAPI()

@app.get("/",  status_code=200)
def health():
    return {"message": "Server is up"}

@app.post("/parser",  status_code=201)
def parse_html(items: List[EmailItem]):

    if not items:
        return JSONResponse(status_code=400, content={"message": "No items provided"})

    logger.info(f"Received {len(items)} items")
    
    transactions = []
    try:
        for item in items:
            html = item.html
            parser_fn = from_addreses.get(item.from_address)

            if not parser_fn:
                raise ValueError(f"No mapped parser for sender: {item}")
            transactions.append(parser_fn(html))

    except Exception as e:
        logger.error(f"Error encountered: {e}")
        return JSONResponse(status_code=422, content={"message": str(e)})

    if len(transactions) == 0:
        return JSONResponse(status_code=400, content={"message": "No items parsed"})

    return {"message": transactions}
