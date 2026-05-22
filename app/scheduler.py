import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from app.database import AsyncSessionLocal
from app.models import Booking
from app.email_service import send_reminder_email

scheduler = AsyncIOScheduler()

async def check_and_send_reminders():
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.datetime.utcnow()
            one_hour_later = now + datetime.timedelta(hours=1)
            
            result = await db.execute(
                select(Booking).filter(
                    Booking.start_time > now,
                    Booking.start_time <= one_hour_later,
                    Booking.reminder_sent == False
                )
            )
            upcoming_bookings = result.scalars().all()
            
            for booking in upcoming_bookings:
                success = await send_reminder_email(
                    to_email=booking.client_email,
                    to_name=booking.client_name,
                    meeting_time=booking.start_time.strftime("%B %d, %Y at %I:%M %p UTC")
                )
                if success:
                    booking.reminder_sent = True
                    await db.commit()
        except Exception as e:
            print(f"Error checking reminders: {e}")

def start_scheduler():
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=1)
    scheduler.start()

