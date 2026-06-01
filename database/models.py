# database/models.py
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from decimal import Decimal

@dataclass
class Profile:
    id: str
    agency_name: str
    owner_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Product:
    id: Optional[str]
    user_id: str
    name: str
    category: Optional[str] = None
    base_unit: str = "kg"
    created_at: Optional[datetime] = None
    
@dataclass
class GradingRule:
    id: Optional[str]
    user_id: str
    product_id: str
    std_moisture: float = 15.0
    moisture_ratio: float = 1.2
    std_impurity: float = 1.0
    impurity_ratio: float = 1.0
    description: Optional[str] = None
    is_active: bool = True
    
@dataclass
class Farmer:
    id: Optional[str]
    user_id: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    total_debt: float = 0.0
    note: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Transaction:
    id: Optional[str]
    user_id: str
    farmer_id: str
    product_id: str
    gross_weight: float
    package_weight: float
    measured_moisture: float
    measured_impurity: float
    net_weight: float
    unit_price: float
    total_amount: float
    payment_status: str  # 'paid' or 'debt'
    created_at: Optional[datetime] = None

@dataclass
class Inventory:
    id: Optional[str]
    user_id: str
    product_id: str
    current_stock: float = 0.0
    last_updated: Optional[datetime] = None

@dataclass
class MarketPrice:
    id: Optional[str]
    product_name: str
    price_local: Optional[float] = None
    price_global_london: Optional[float] = None
    price_global_ny: Optional[float] = None
    log_date: Optional[str] = None