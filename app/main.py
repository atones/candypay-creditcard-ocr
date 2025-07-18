from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from PIL import Image
import pytesseract
from io import BytesIO
from pydantic import BaseModel, Field
import re
import os

app = FastAPI()

security = HTTPBearer()
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("환경변수 API_TOKEN 이 설정되지 않았습니다.")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Authorization: Bearer <credentials.credentials> 헤더를 검사
    """
    if credentials.scheme.lower() != "bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# 1) 정상 응답 모델
class CardInfo(BaseModel):
    cardNumber: str | None = Field(..., description="16자리 카드 번호")
    expireYY: str | None = Field(..., description="만료년")
    expireMM: str | None = Field(..., description="만료월")
    cvc: str | None = Field(..., description="3자리 CVC 코드")


class ErrorResponse(BaseModel):
    detail: str


WHITELIST = "0123456789.,-+*/"
PSM = 4
CONFIG = f"--psm {PSM} " f"-c tessedit_char_whitelist={WHITELIST}"

CARD_RE = re.compile(
    r"""
    \b                             # 단어 경계
    (?:                            # 아래 세 경우를 모두 포괄
        \d{16}                     # 1) 연속된 16자리
      | \d{8}\s*\d{8}              # 2) 8자리 + (공백?) + 8자리
      | \d{4}(?:\s*\d{4}){3}       # 3) 4자리 + (공백?+4자리)×3
    )
    \b
""",
    re.VERBOSE,
)

CVC_RE = re.compile(
    r"""
    \b       # 단어 경계
    (\d{3})  # 정확히 3자리 숫자
    \b
    """,
    re.VERBOSE,
)

EXP_RE = re.compile(
    r"""
    \b        # 단어 경계
    (\d{2}/\d{2})  # 정확히 2자리 숫자 + 슬래시 + 2자리 숫자
    \b
    """,
    re.VERBOSE,
)


@app.post("/ocr/", response_model=CardInfo)
async def ocr_image(
    file: UploadFile = File(...),
    token: str = Depends(verify_token),
):
    if not file.content_type.startswith("image/"):
        await file.close()
        raise HTTPException(status_code=400, detail="이미지 파일을 업로드해주세요.")
    try:
        contents = await file.read()
    finally:
        await file.close()

    try:
        with Image.open(BytesIO(contents)) as image:
            text: str = await run_in_threadpool(
                pytesseract.image_to_string, image, lang="eng", config=CONFIG
            )
    except OSError:
        raise HTTPException(status_code=500, detail="이미지 파싱 실패")
    except pytesseract.TesseractError:
        raise HTTPException(status_code=500, detail="OCR 처리 중 오류 발생")

    text = text.strip()

    card_number = re.sub(r"\s+", "", m.group()) if (m := CARD_RE.search(text)) else None
    cvc = cvc_match.group(1) if (cvc_match := CVC_RE.search(text)) else None

    if exp := EXP_RE.search(text):
        mm, yy = exp.group(1).split("/")
    else:
        mm = yy = None

    return CardInfo(cardNumber=card_number, cvc=cvc, expireMM=mm, expireYY=yy)
