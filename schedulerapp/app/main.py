import os
import datetime
import requests
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()

# Allow HTTP traffic for local development with OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from app.database import engine, Base, get_db
from app.models import Booking, Availability
from app.scheduler import start_scheduler
from app.google_auth import get_google_auth_flow, create_google_calendar_event

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "super-secret-key-fallback"))

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Availability))
    availability = result.scalars().all()
    user_name = request.session.get("user_name")
    user_email = request.session.get("user_email")
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID", "test")
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "request": request, 
            "availability": availability,
            "user_name": user_name,
            "user_email": user_email,
            "paypal_client_id": paypal_client_id
        }
    )

@app.get("/login")
async def login():
    flow = get_google_auth_flow()
    if not flow:
        return HTMLResponse("Google Auth not configured properly (missing .env variables).", status_code=500)
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return RedirectResponse(url=auth_url, status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/auth/callback")
async def auth_callback(request: Request, state: str, code: str):
    flow = get_google_auth_flow()
    if not flow:
        return HTMLResponse("Google Auth not configured.", status_code=500)
    
    flow.fetch_token(authorization_response=str(request.url))
    credentials = flow.credentials
    
    # Fetch user profile information
    userinfo_response = requests.get(f'https://www.googleapis.com/oauth2/v1/userinfo?access_token={credentials.token}')
    if userinfo_response.status_code == 200:
        userinfo = userinfo_response.json()
        request.session['user_name'] = userinfo.get('name')
        request.session['user_email'] = userinfo.get('email')
    
    request.session['google_credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return RedirectResponse(url="/", status_code=303)

@app.get("/calendar", response_class=HTMLResponse)
async def calendar_admin(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Availability))
    availability = result.scalars().all()
    return templates.TemplateResponse(
        request=request, 
        name="calendar.html", 
        context={
            "request": request,
            "availability": availability
        }
    )

@app.post("/availability")
async def save_availability(
    day_of_week: int = Form(...),
    start_time_str: str = Form(...),
    end_time_str: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    new_avail = Availability(
        day_of_week=day_of_week,
        start_time_str=start_time_str,
        end_time_str=end_time_str
    )
    db.add(new_avail)
    await db.commit()
    return RedirectResponse(url="/calendar", status_code=303)

@app.post("/book")
async def book_appointment(
    request: Request,
    client_name: str = Form(...),
    client_email: str = Form(...),
    service_name: str = Form(...),
    price: float = Form(...),
    paypal_transaction_id: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    
    new_booking = Booking(
        client_name=client_name,
        client_email=client_email,
        service_name=service_name,
        price=price,
        start_time=start_dt,
        end_time=end_dt,
        paypal_transaction_id=paypal_transaction_id,
        payment_status="verified"
    )
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    
    google_creds = request.session.get('google_credentials')
    if google_creds:
        try:
            event_id = create_google_calendar_event(google_creds, new_booking)
            new_booking.google_event_id = event_id
            await db.commit()
        except Exception as e:
            print(f"Error creating google calendar event: {e}")
            
    return RedirectResponse(url="/success", status_code=303)

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse(request=request, name="success.html", context={"request": request})
