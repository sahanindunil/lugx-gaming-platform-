from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db, init_db
from models import Order, OrderItem
from datetime import datetime

app = FastAPI(title="Order Service API")

class OrderItemCreate(BaseModel):
    game_id: int
    game_name: str
    price: float
    quantity: int = 1

class OrderCreate(BaseModel):
    user_email: str
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    id: int
    game_id: int
    game_name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_email: str
    status: str
    total_amount: float
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Order Service API"}

@app.post("/orders/", response_model=OrderResponse)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    total = sum(item.price * item.quantity for item in order_data.items)

    new_order = Order(
        user_email=order_data.user_email,
        total_amount=total,
        status="pending"
    )

    db.add(new_order)
    db.flush()  # generates order.id

    # Add items
    for item in order_data.items:
        order_item = OrderItem(
            order_id=new_order.id,
            game_id=item.game_id,
            game_name=item.game_name,
            price=item.price,
            quantity=item.quantity
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)

    return new_order

@app.get("/orders/")
def get_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()

