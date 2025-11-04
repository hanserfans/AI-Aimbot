
# 在MouseMove.py中添加校正因子
MOVEMENT_CORRECTION_FACTOR = 1.429

def move_mouse_corrected(self, x, y):
    """
    修正后的鼠标移动函数
    """
    # 应用校正因子
    corrected_x = int(x * MOVEMENT_CORRECTION_FACTOR)
    corrected_y = int(y * MOVEMENT_CORRECTION_FACTOR)
    
    # 调用原始移动函数
    return self.move_mouse(corrected_x, corrected_y)

# 全局函数版本
def ghub_move_corrected(x, y):
    """修正后的全局移动函数"""
    corrected_x = int(x * 1.429)
    corrected_y = int(y * 1.429)
    return ghub_move(corrected_x, corrected_y)
