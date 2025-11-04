
# DPI 1600专用校正因子
MOVEMENT_CORRECTION_FACTOR_1600DPI = 0.62

def ghub_move_1600dpi(x, y):
    """为1600 DPI优化的G-Hub鼠标移动函数"""
    corrected_x = int(x * MOVEMENT_CORRECTION_FACTOR_1600DPI)
    corrected_y = int(y * MOVEMENT_CORRECTION_FACTOR_1600DPI)
    return mouse_instance.move_mouse(corrected_x, corrected_y)
