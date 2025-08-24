from enum import Enum
from fastapi import FastAPI, Query, Path, Body, Cookie, Header
from pydantic import BaseModel, Field, HttpUrl, AfterValidator
from typing import Annotated, Literal, List
from datetime import datetime, time, timedelta
from uuid import UUID

app = FastAPI()

# -------------------- BASIC ROUTES --------------------
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# -------------------- USERS --------------------
@app.get("/users/me")
async def read_current_user():
    return {"user_id": "the current user"}

@app.get("/users/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id}

@app.get("/users")
async def read_users():
    return ["Rick", "Morty"]

@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(
    user_id: int, 
    item_id: str, 
    q: str | None = None, 
    short: bool = False
):
    return {"user_id": user_id, "item_id": item_id, "q": q, "short": short}

# -------------------- MODELS --------------------
class ModelName(str, Enum):
    alexnet = "alexnet"
    resent = "resent"
    lenet = "lenet"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name == ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name == ModelName.lenet:
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some ridiculous"}

# -------------------- FILES --------------------
@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}

# -------------------- ITEMS --------------------
class Item(BaseModel):
    name: str
    description: str | None = None   # optional
    price: float
    tax: float | None = None         # optional

@app.post("/items/")
async def create_item(item: Item):
    # إذا فيه ضريبة، نضيفها على السعر
    item_dict = item.dict()
    if item.tax is not None:
        item_dict["price_with_tax"] = item.price + item.tax
    return item_dict

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.dict()}
    if q:
        result.update({"q": q})
    return result

@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[str | None, Query(alias="item-query")] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results

# -------------------- QUERY PARAMETERS --------------------
@app.get("/usernames/")
async def get_usernames(
    username: Annotated[str, Query(min_length=3, max_length=20, title="Username", description="The username must be between 3 and 20 characters")]
):
    return {"username": username}
    # min_length=3 → لازم طول النص يكون ٣ أحرف أو أكثر
    # max_length=20 → لازم طول النص يكون ٢٠ أو أقل

@app.get("/products/")
async def get_product(
    code: Annotated[str, Query(pattern="^PROD-[0-9]{4}$", title="Product Code", description="Must start with 'PROD-' followed by 4 digits")]
):
    return {"code": code}
    # Regex ^PROD-[0-9]{4}$ → لازم يبدأ بـ PROD- وبعدين ٤ أرقام
    # ✅ صحيح: PROD-1234

@app.get("/search/")
async def search_items(
    keyword: Annotated[str, Query(alias="q", min_length=2, max_length=30, description="Search keyword between 2 and 30 characters")]
):
    return {"search_keyword": keyword}
    # alias="q" → بدل ما تستخدم اسم المتغير keyword في الرابط، تستخدم q

@app.get("/deprecated/")
async def deprecated_param(
    old_param: Annotated[str | None, Query(deprecated=True,description="Deprecated, use 'new_param' instead")] = None, new_param: str | None = None
):
    return {"old_param": old_param, "new_param": new_param}
    # deprecated=True → معناه إن الباراميتر ده قديم ومش هيتستخدم في المستقبل

# -------------------- VALIDATION EXAMPLE --------------------
def no_spaces(v: str) -> str:
    if " " in v:
        raise ValueError("Value must not contain spaces")
    return v

@app.get("/validate/")
async def validate_input(text: Annotated[str, AfterValidator(no_spaces)]):
    return {"text": text}
    # AfterValidator(no_spaces) → يتأكد إن النص مفيهوش مسافات
    # ✅ صحيح: "HelloWorld"

# -------------------- PRODUCT PATH PARAMETERS --------------------
@app.get("/products/{product_id}")
async def get_product_by_id(
    product_id: Annotated[int, Path(title="The ID of the product", ge=1, le=1000)]
):
    return {"product_id": product_id}
    # ge → أكبر من أو يساوي
    # le → أصغر من أو يساوي

@app.get("/sizes/{item_id}")
async def get_size(
    item_id: Annotated[int, Path(ge=1, le=1000)],
    size: Annotated[float, Query(gt=0, lt=10.5)]
):
    return {"item_id": item_id, "size": size}
    # gt → أكبر من
    # lt → أصغر من

# -------------------- QUERY MODELS --------------------
class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)  # limit = كم عنصر نرجع
    offset: int = Field(0, ge=0)           # offset = نبدأ منين (pagination)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []

@app.get("/items-filter/")
async def read_items(filter_query: Annotated[FilterParams, Query()]):
    return filter_query
    # FastAPI هيجمع الباراميترز كلها ويحطها في FilterParams object

# -------------------- EXTRA DATA TYPES --------------------
@app.put("/process/{item_id}")
async def process_item(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }
    # UUID → لازم يكون UUID صحيح
    # datetime, timedelta, time → FastAPI بيحول القيم تلقائياً

# -------------------- COOKIE PARAMETERS --------------------
@app.get("/cookie/")
async def read_cookie(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}
    # ads_id = optional cookie

# -------------------- HEADER PARAMETERS --------------------
@app.get("/header/")
async def read_header(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}
    # user_agent = optional header

@app.get("/multi-header/")
async def read_multi_header(x_token: Annotated[list[str] | None, Header()] = None):
    return {"X-Token values": x_token}
    # لو الهيدر اتكرر، يرجع list
#-------------------------cookie parameters models--------------------
#define a model for cookies 

class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None

#session_id = required cookie
#fatebook_tracker and googall_tracker = optional cookies

#tell fastapi to use it 

@app.get("/items/")
async def read_items(cookies: Annotated[Cookies, Cookie()]):
    return cookies

#Read cookies from the request.
#Match them to your Pydantic model fields.
#Validate them automatically (e.g., type checking).
#Give you a Cookies object instead of raw strings.

class Cookies(BaseModel):
    model_config = {"extra": "forbid"}  # 🚫 reject extra cookies

    session_id: str
    fatebook_tracker: str | None = None
    googall_tracker: str | None = None
