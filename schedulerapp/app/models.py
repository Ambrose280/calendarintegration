from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from app.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, index=True)
    client_email = Column(String, index=True)
    
    # New Service Fields
    service_name = Column(String)
    price = Column(Float)
    
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    
    # External ID Fields
    google_event_id = Column(String, nullable=True)
    paypal_transaction_id = Column(String, nullable=True)
    
    # Status
    payment_status = Column(String, default="pending")  # 'pending', 'verified'
    reminder_sent = Column(Boolean, default=False)
    
class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    start_time_str = Column(String)  # e.g., "09:00"
    end_time_str = Column(String)    # e.g., "17:00"
