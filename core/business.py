# core/business.py
from typing import Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BusinessLogic:
    """Xử lý logic nghiệp vụ"""
    
    @staticmethod
    def calculate_net_weight(
        gross_weight: float,
        package_weight: float,
        measured_moisture: float,
        measured_impurity: float,
        grading_rule: Dict
    ) -> Dict:
        """
        Tính toán cân tịnh dựa trên quy tắc trừ lùi
        
        Returns:
            Dict với các thông số đã tính
        """
        # Khối lượng sau trừ bao bì
        weight_after_package = max(0, gross_weight - package_weight)
        
        # Trừ ẩm
        moisture_excess = max(0, measured_moisture - grading_rule['std_moisture'])
        moisture_subtraction = weight_after_package * moisture_excess * grading_rule['moisture_ratio'] / 100
        
        # Trừ tạp chất
        impurity_excess = max(0, measured_impurity - grading_rule['std_impurity'])
        impurity_subtraction = weight_after_package * impurity_excess * grading_rule['impurity_ratio'] / 100
        
        # Cân tịnh
        net_weight = max(0, weight_after_package - moisture_subtraction - impurity_subtraction)
        
        return {
            'weight_after_package': round(weight_after_package, 2),
            'moisture_subtraction': round(moisture_subtraction, 2),
            'impurity_subtraction': round(impurity_subtraction, 2),
            'net_weight': round(net_weight, 2)
        }
    
    @staticmethod
    def suggest_unit_price(
        product_name: str,
        market_prices: list,
        quality_grade: str = "standard"
    ) -> float:
        """Gợi ý đơn giá dựa trên giá thị trường"""
        if not market_prices:
            return 0
        
        # Lấy giá trung bình
        avg_price = sum(p.get('price_local', 0) for p in market_prices) / len(market_prices)
        
        # Điều chỉnh theo chất lượng
        quality_multiplier = {
            "premium": 1.15,
            "grade_1": 1.05,
            "standard": 1.0,
            "low": 0.9
        }.get(quality_grade, 1.0)
        
        return round(avg_price * quality_multiplier, 2)
    
    @staticmethod
    def calculate_payment(
        net_weight: float,
        unit_price: float,
        payment_status: str
    ) -> Dict:
        """Tính toán thanh toán"""
        total_amount = net_weight * unit_price
        
        return {
            'total_amount': round(total_amount, 2),
            'payment_status': payment_status,
            'payment_due': total_amount if payment_status == 'debt' else 0
        }
    
    @staticmethod
    def validate_transaction(data: Dict) -> Tuple[bool, Optional[str]]:
        """Kiểm tra tính hợp lệ của giao dịch"""
        # Kiểm tra các trường bắt buộc
        required_fields = ['gross_weight', 'unit_price']
        for field in required_fields:
            if field not in data or data[field] <= 0:
                return False, f"{field} không hợp lệ"
        
        # Kiểm tra cân nặng
        if data['gross_weight'] <= 0:
            return False, "Tổng cân phải lớn hơn 0"
        
        if data.get('package_weight', 0) >= data['gross_weight']:
            return False, "Khối lượng bao bì không được lớn hơn tổng cân"
        
        # Kiểm tra độ ẩm, tạp chất
        if data.get('measured_moisture', 0) < 0 or data.get('measured_moisture', 0) > 100:
            return False, "Độ ẩm phải từ 0-100%"
        
        if data.get('measured_impurity', 0) < 0 or data.get('measured_impurity', 0) > 100:
            return False, "Tạp chất phải từ 0-100%"
        
        return True, None

class FarmerDebtManager:
    """Quản lý công nợ của nông dân"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def record_payment(self, farmer_id: str, amount: float, note: str = "") -> bool:
        """Ghi nhận thanh toán từ nông dân"""
        if amount <= 0:
            return False
        
        # Cập nhật công nợ (giảm nợ)
        return self.db.update_farmer_debt(farmer_id, amount, is_increase=False)
    
    def get_debt_summary(self, user_id: str) -> Dict:
        """Lấy tổng kết công nợ"""
        farmers = self.db.get_farmers(user_id)
        
        total_debt = sum(f['total_debt'] for f in farmers)
        farmers_in_debt = [f for f in farmers if f['total_debt'] > 0]
        
        return {
            'total_debt': total_debt,
            'farmers_in_debt': len(farmers_in_debt),
            'max_debt': max([f['total_debt'] for f in farmers_in_debt]) if farmers_in_debt else 0,
            'avg_debt': total_debt / len(farmers_in_debt) if farmers_in_debt else 0
        }