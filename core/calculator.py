def calculate_coffee_subtraction(gross_weight, package_weight, measured_moisture, measured_impurity, std_moisture=15.0, moisture_ratio=1.2, std_impurity=1.0, impurity_ratio=1.0):
    """
    Tính toán khối lượng và trừ lùi cho Cà phê (Coffee)
    """
    # Khối lượng sau khi trừ bao bì
    weight_after_package = gross_weight - package_weight
    
    # Tính trừ độ ẩm
    w_moisture_sub = 0.0
    if measured_moisture > std_moisture:
        w_moisture_sub = weight_after_package * (measured_moisture - std_moisture) * moisture_ratio / 100.0
        
    # Tính trừ tạp chất
    w_impurity_sub = 0.0
    if measured_impurity > std_impurity:
        w_impurity_sub = weight_after_package * (measured_impurity - std_impurity) * impurity_ratio / 100.0
        
    # Tính cân tịnh (Net Weight)
    net_weight = weight_after_package - w_moisture_sub - w_impurity_sub
    net_weight = max(0.0, net_weight)
    
    return {
        "weight_after_package": weight_after_package,
        "moisture_subtraction": w_moisture_sub,
        "impurity_subtraction": w_impurity_sub,
        "net_weight": net_weight
    }

def calculate_pepper_subtraction(gross_weight, package_weight, measured_moisture, measured_impurity, liter_weight=500.0, std_moisture=13.0, moisture_ratio=1.2, std_impurity=0.2, impurity_ratio=1.0):
    """
    Tính toán khối lượng và trừ lùi cho Hồ tiêu (Pepper)
    """
    # Khối lượng sau khi trừ bao bì
    weight_after_package = gross_weight - package_weight
    
    # Tính trừ độ ẩm
    w_moisture_sub = 0.0
    if measured_moisture > std_moisture:
        w_moisture_sub = weight_after_package * (measured_moisture - std_moisture) * moisture_ratio / 100.0
        
    # Tính trừ tạp chất
    w_impurity_sub = 0.0
    if measured_impurity > std_impurity:
        w_impurity_sub = weight_after_package * (measured_impurity - std_impurity) * impurity_ratio / 100.0
        
    # Tính cân tịnh (Net Weight)
    net_weight = weight_after_package - w_moisture_sub - w_impurity_sub
    net_weight = max(0.0, net_weight)
    
    # Đánh giá theo Dung trọng (g/l)
    quality_grade = "Standard"
    if liter_weight < 500.0:
        quality_grade = "Low Quality"
    elif liter_weight >= 550.0:
        quality_grade = "High Quality"
        
    return {
        "weight_after_package": weight_after_package,
        "moisture_subtraction": w_moisture_sub,
        "impurity_subtraction": w_impurity_sub,
        "net_weight": net_weight,
        "quality_grade": quality_grade
    }
