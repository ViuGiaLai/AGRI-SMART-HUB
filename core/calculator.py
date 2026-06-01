"""
Module tính toán trừ lùi cho nông sản (Cà phê và Hồ tiêu)
Version: 2.0
Author: GASH System
"""

from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== ENUMS AND CONSTANTS ====================

class ProductType(Enum):
    """Loại nông sản"""
    COFFEE = "cà phê"
    PEPPER = "hồ tiêu"
    
class QualityGrade(Enum):
    """Xếp loại chất lượng"""
    PREMIUM = "Loại Đặc biệt"
    GRADE_1 = "Loại 1"
    GRADE_2 = "Loại 2"
    STANDARD = "Loại Thường"
    LOW = "Loại Kém"
    
@dataclass
class QualityStandard:
    """Tiêu chuẩn chất lượng cho sản phẩm"""
    std_moisture: float  # Độ ẩm tiêu chuẩn (%)
    std_impurity: float  # Tạp chất tiêu chuẩn (%)
    moisture_ratio: float  # Hệ số trừ ẩm
    impurity_ratio: float  # Hệ số trừ tạp chất
    liter_weight_std: Optional[float] = None  # Dung trọng tiêu chuẩn (g/l) - chỉ cho hồ tiêu
    
# Tiêu chuẩn cho từng loại sản phẩm
PRODUCT_STANDARDS = {
    ProductType.COFFEE: QualityStandard(
        std_moisture=12.5,
        std_impurity=0.5,
        moisture_ratio=1.2,
        impurity_ratio=1.0
    ),
    ProductType.PEPPER: QualityStandard(
        std_moisture=13.0,
        std_impurity=0.2,
        moisture_ratio=1.2,
        impurity_ratio=1.0,
        liter_weight_std=500.0
    )
}

# ==================== DATA CLASSES ====================

@dataclass
class CalculationResult:
    """Kết quả tính toán"""
    product_type: str
    gross_weight: float
    package_weight: float
    weight_after_package: float
    measured_moisture: float
    measured_impurity: float
    moisture_subtraction: float
    impurity_subtraction: float
    net_weight: float
    quality_grade: Optional[str] = None
    liter_weight: Optional[float] = None
    warnings: list = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict:
        """Chuyển đổi kết quả thành dictionary"""
        return {
            "product_type": self.product_type,
            "gross_weight": round(self.gross_weight, 2),
            "package_weight": round(self.package_weight, 2),
            "weight_after_package": round(self.weight_after_package, 2),
            "measured_moisture": round(self.measured_moisture, 1),
            "measured_impurity": round(self.measured_impurity, 1),
            "moisture_subtraction": round(self.moisture_subtraction, 2),
            "impurity_subtraction": round(self.impurity_subtraction, 2),
            "net_weight": round(self.net_weight, 2),
            "quality_grade": self.quality_grade,
            "liter_weight": self.liter_weight,
            "warnings": self.warnings
        }
    
    def format_for_display(self) -> str:
        """Định dạng kết quả để hiển thị"""
        lines = [
            f"📊 KẾT QUẢ TÍNH TOÁN - {self.product_type.upper()}",
            "=" * 40,
            f"⚖️ Tổng cân:              {self.gross_weight:>10,.2f} kg",
            f"📦 Bao bì:                {self.package_weight:>10,.2f} kg",
            f"✅ Cân sau bao bì:        {self.weight_after_package:>10,.2f} kg",
            f"💧 Độ ẩm đo được:        {self.measured_moisture:>10,.1f} %",
            f"🧹 Tạp chất đo được:      {self.measured_impurity:>10,.1f} %",
            "-" * 40,
            f"🔻 Trừ ẩm:                {self.moisture_subtraction:>10,.2f} kg",
            f"🔻 Trừ tạp chất:          {self.impurity_subtraction:>10,.2f} kg",
            "-" * 40,
            f"🏆 CÂN TỊNH THỰC TẾ:      {self.net_weight:>10,.2f} kg",
        ]
        
        if self.quality_grade:
            lines.append(f"⭐ Xếp loại:              {self.quality_grade}")
        
        if self.liter_weight:
            lines.append(f"📏 Dung trọng:            {self.liter_weight:>10,.0f} g/l")
        
        if self.warnings:
            lines.append("\n⚠️ CẢNH BÁO:")
            for warning in self.warnings:
                lines.append(f"   • {warning}")
        
        return "\n".join(lines)

# ==================== VALIDATION FUNCTIONS ====================

def validate_inputs(
    gross_weight: float,
    package_weight: float,
    measured_moisture: float,
    measured_impurity: float,
    liter_weight: Optional[float] = None
) -> Tuple[bool, list]:
    """
    Kiểm tra tính hợp lệ của dữ liệu đầu vào
    
    Returns:
        Tuple[bool, list]: (hợp_lệ, danh_sách_cảnh_báo)
    """
    warnings = []
    
    # Kiểm tra giá trị âm
    if gross_weight <= 0:
        warnings.append("Tổng cân phải lớn hơn 0")
    elif gross_weight < package_weight:
        warnings.append("Tổng cân nhỏ hơn khối lượng bao bì")
    
    if package_weight < 0:
        warnings.append("Khối lượng bao bì không thể âm")
    
    if measured_moisture < 0 or measured_moisture > 100:
        warnings.append("Độ ẩm phải trong khoảng 0-100%")
    
    if measured_impurity < 0 or measured_impurity > 100:
        warnings.append("Tạp chất phải trong khoảng 0-100%")
    
    if liter_weight is not None and (liter_weight < 0 or liter_weight > 1000):
        warnings.append("Dung trọng phải trong khoảng 0-1000 g/l")
    
    # Cảnh báo về giá trị bất thường
    if measured_moisture > 25:
        warnings.append(f"Độ ẩm {measured_moisture}% rất cao - sản phẩm có thể bị ẩm mốc")
    
    if measured_impurity > 10:
        warnings.append(f"Tạp chất {measured_impurity}% rất cao - chất lượng kém")
    
    if package_weight > gross_weight * 0.1:  # Bao bì > 10% tổng cân
        warnings.append("Khối lượng bao bì chiếm tỷ lệ lớn (>10%)")
    
    return len([w for w in warnings if "phải" in w]) == 0, warnings

def round_decimal(value: float, decimals: int = 2) -> float:
    """Làm tròn số theo quy tắc ngân hàng"""
    return float(Decimal(str(value)).quantize(
        Decimal('0.' + '0' * decimals), 
        rounding=ROUND_HALF_UP
    ))

# ==================== MAIN CALCULATION FUNCTIONS ====================

def calculate_coffee_subtraction(
    gross_weight: float,
    package_weight: float,
    measured_moisture: float,
    measured_impurity: float,
    std_moisture: Optional[float] = None,
    moisture_ratio: Optional[float] = None,
    std_impurity: Optional[float] = None,
    impurity_ratio: Optional[float] = None,
    auto_validate: bool = True
) -> Dict[str, Any]:
    """
    Tính toán khối lượng và trừ lùi cho Cà phê (Coffee)
    
    Args:
        gross_weight: Tổng cân (kg)
        package_weight: Khối lượng bao bì (kg)
        measured_moisture: Độ ẩm đo được (%)
        measured_impurity: Tạp chất đo được (%)
        std_moisture: Độ ẩm tiêu chuẩn (mặc định: 12.5%)
        moisture_ratio: Hệ số trừ ẩm (mặc định: 1.2)
        std_impurity: Tạp chất tiêu chuẩn (mặc định: 0.5%)
        impurity_ratio: Hệ số trừ tạp chất (mặc định: 1.0)
        auto_validate: Tự động kiểm tra dữ liệu đầu vào
    
    Returns:
        Dict chứa kết quả tính toán
    """
    # Sử dụng tiêu chuẩn mặc định nếu không có
    standards = PRODUCT_STANDARDS[ProductType.COFFEE]
    std_moisture = std_moisture or standards.std_moisture
    moisture_ratio = moisture_ratio or standards.moisture_ratio
    std_impurity = std_impurity or standards.std_impurity
    impurity_ratio = impurity_ratio or standards.impurity_ratio
    
    # Validation
    warnings = []
    if auto_validate:
        is_valid, validation_warnings = validate_inputs(
            gross_weight, package_weight, measured_moisture, measured_impurity
        )
        warnings.extend(validation_warnings)
        if not is_valid:
            logger.warning(f"Validation failed: {warnings}")
    
    # Khối lượng sau khi trừ bao bì
    weight_after_package = max(0, gross_weight - package_weight)
    
    # Tính trừ độ ẩm
    w_moisture_sub = 0.0
    moisture_excess = max(0, measured_moisture - std_moisture)
    if moisture_excess > 0:
        w_moisture_sub = weight_after_package * moisture_excess * moisture_ratio / 100.0
    
    # Tính trừ tạp chất
    w_impurity_sub = 0.0
    impurity_excess = max(0, measured_impurity - std_impurity)
    if impurity_excess > 0:
        w_impurity_sub = weight_after_package * impurity_excess * impurity_ratio / 100.0
    
    # Tính cân tịnh
    net_weight = max(0, weight_after_package - w_moisture_sub - w_impurity_sub)
    
    # Làm tròn kết quả
    result = CalculationResult(
        product_type="cà phê",
        gross_weight=round_decimal(gross_weight),
        package_weight=round_decimal(package_weight),
        weight_after_package=round_decimal(weight_after_package),
        measured_moisture=round_decimal(measured_moisture, 1),
        measured_impurity=round_decimal(measured_impurity, 1),
        moisture_subtraction=round_decimal(w_moisture_sub),
        impurity_subtraction=round_decimal(w_impurity_sub),
        net_weight=round_decimal(net_weight),
        warnings=warnings
    )
    
    return result.to_dict()

def calculate_pepper_subtraction(
    gross_weight: float,
    package_weight: float,
    measured_moisture: float,
    measured_impurity: float,
    liter_weight: Optional[float] = None,
    std_moisture: Optional[float] = None,
    moisture_ratio: Optional[float] = None,
    std_impurity: Optional[float] = None,
    impurity_ratio: Optional[float] = None,
    liter_weight_std: Optional[float] = None,
    auto_validate: bool = True
) -> Dict[str, Any]:
    """
    Tính toán khối lượng và trừ lùi cho Hồ tiêu (Pepper)
    
    Args:
        gross_weight: Tổng cân (kg)
        package_weight: Khối lượng bao bì (kg)
        measured_moisture: Độ ẩm đo được (%)
        measured_impurity: Tạp chất đo được (%)
        liter_weight: Dung trọng (g/l) - optional
        std_moisture: Độ ẩm tiêu chuẩn (mặc định: 13.0%)
        moisture_ratio: Hệ số trừ ẩm (mặc định: 1.2)
        std_impurity: Tạp chất tiêu chuẩn (mặc định: 0.2%)
        impurity_ratio: Hệ số trừ tạp chất (mặc định: 1.0)
        liter_weight_std: Dung trọng tiêu chuẩn (mặc định: 500 g/l)
        auto_validate: Tự động kiểm tra dữ liệu đầu vào
    
    Returns:
        Dict chứa kết quả tính toán
    """
    # Sử dụng tiêu chuẩn mặc định nếu không có
    standards = PRODUCT_STANDARDS[ProductType.PEPPER]
    std_moisture = std_moisture or standards.std_moisture
    moisture_ratio = moisture_ratio or standards.moisture_ratio
    std_impurity = std_impurity or standards.std_impurity
    impurity_ratio = impurity_ratio or standards.impurity_ratio
    liter_weight_std = liter_weight_std or standards.liter_weight_std
    
    # Validation
    warnings = []
    if auto_validate:
        is_valid, validation_warnings = validate_inputs(
            gross_weight, package_weight, measured_moisture, measured_impurity, liter_weight
        )
        warnings.extend(validation_warnings)
    
    # Khối lượng sau khi trừ bao bì
    weight_after_package = max(0, gross_weight - package_weight)
    
    # Tính trừ độ ẩm
    w_moisture_sub = 0.0
    moisture_excess = max(0, measured_moisture - std_moisture)
    if moisture_excess > 0:
        w_moisture_sub = weight_after_package * moisture_excess * moisture_ratio / 100.0
    
    # Tính trừ tạp chất
    w_impurity_sub = 0.0
    impurity_excess = max(0, measured_impurity - std_impurity)
    if impurity_excess > 0:
        w_impurity_sub = weight_after_package * impurity_excess * impurity_ratio / 100.0
    
    # Tính cân tịnh
    net_weight = max(0, weight_after_package - w_moisture_sub - w_impurity_sub)
    
    # Đánh giá chất lượng dựa trên dung trọng
    quality_grade = None
    if liter_weight is not None:
        if liter_weight >= 600:
            quality_grade = QualityGrade.PREMIUM.value
        elif liter_weight >= 550:
            quality_grade = QualityGrade.GRADE_1.value
        elif liter_weight >= 500:
            quality_grade = QualityGrade.GRADE_2.value
        elif liter_weight >= 450:
            quality_grade = QualityGrade.STANDARD.value
        else:
            quality_grade = QualityGrade.LOW.value
            warnings.append(f"Dung trọng thấp ({liter_weight} g/l) - chất lượng kém")
    else:
        quality_grade = QualityGrade.STANDARD.value
    
    # Làm tròn kết quả
    result = CalculationResult(
        product_type="hồ tiêu",
        gross_weight=round_decimal(gross_weight),
        package_weight=round_decimal(package_weight),
        weight_after_package=round_decimal(weight_after_package),
        measured_moisture=round_decimal(measured_moisture, 1),
        measured_impurity=round_decimal(measured_impurity, 1),
        moisture_subtraction=round_decimal(w_moisture_sub),
        impurity_subtraction=round_decimal(w_impurity_sub),
        net_weight=round_decimal(net_weight),
        quality_grade=quality_grade,
        liter_weight=round_decimal(liter_weight, 0) if liter_weight else None,
        warnings=warnings
    )
    
    return result.to_dict()

# ==================== UTILITY FUNCTIONS ====================

def batch_calculate(
    products_data: list,
    product_type: ProductType
) -> list:
    """
    Tính toán hàng loạt cho nhiều lô hàng
    
    Args:
        products_data: Danh sách các dict chứa thông tin sản phẩm
        product_type: Loại sản phẩm (COFFEE hoặc PEPPER)
    
    Returns:
        List kết quả tính toán
    """
    results = []
    calc_func = calculate_coffee_subtraction if product_type == ProductType.COFFEE else calculate_pepper_subtraction
    
    for idx, data in enumerate(products_data):
        try:
            result = calc_func(**data)
            result['batch_index'] = idx
            results.append(result)
        except Exception as e:
            logger.error(f"Lỗi tính toán batch {idx}: {e}")
            results.append({
                'batch_index': idx,
                'error': str(e),
                'net_weight': 0
            })
    
    return results

def calculate_total_stats(results: list) -> Dict:
    """
    Tính toán thống kê tổng hợp từ kết quả
    
    Args:
        results: Danh sách kết quả từ batch_calculate
    
    Returns:
        Dict thống kê
    """
    valid_results = [r for r in results if 'error' not in r]
    
    if not valid_results:
        return {
            'total_batches': len(results),
            'valid_batches': 0,
            'total_net_weight': 0,
            'avg_moisture': 0,
            'avg_impurity': 0
        }
    
    total_net = sum(r['net_weight'] for r in valid_results)
    avg_moisture = sum(r['measured_moisture'] for r in valid_results) / len(valid_results)
    avg_impurity = sum(r['measured_impurity'] for r in valid_results) / len(valid_results)
    
    return {
        'total_batches': len(results),
        'valid_batches': len(valid_results),
        'failed_batches': len(results) - len(valid_results),
        'total_net_weight': round(total_net, 2),
        'avg_moisture': round(avg_moisture, 1),
        'avg_impurity': round(avg_impurity, 1),
        'max_net_weight': max(r['net_weight'] for r in valid_results),
        'min_net_weight': min(r['net_weight'] for r in valid_results)
    }

# ==================== EXPORTS ====================

__all__ = [
    'calculate_coffee_subtraction',
    'calculate_pepper_subtraction',
    'ProductType',
    'QualityGrade',
    'batch_calculate',
    'calculate_total_stats',
    'validate_inputs'
]

# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Ví dụ tính toán cho cà phê
    coffee_result = calculate_coffee_subtraction(
        gross_weight=1000,
        package_weight=15,
        measured_moisture=17.5,
        measured_impurity=2.0
    )
    print("Coffee Calculation:")
    for key, value in coffee_result.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")
    
    # Ví dụ tính toán cho hồ tiêu
    pepper_result = calculate_pepper_subtraction(
        gross_weight=500,
        package_weight=10,
        measured_moisture=15.0,
        measured_impurity=1.0,
        liter_weight=520
    )
    print("Pepper Calculation:")
    for key, value in pepper_result.items():
        print(f"  {key}: {value}")
    
    # Hiển thị định dạng đẹp
    print("\n" + "="*50 + "\n")
    print("Formatted Result:")
    # Tạo CalculationResult object để hiển thị
    result_obj = CalculationResult(**pepper_result)
    print(result_obj.format_for_display())