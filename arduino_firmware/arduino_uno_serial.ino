/*
 * Arduino Uno/Nano 串口通信固件
 * 用于 AI-Aimbot 外部硬件控制
 * 注意：Uno/Nano 不支持 HID，需要配合其他软件使用
 */

void setup() {
  // 初始化串口通信
  Serial.begin(9600);
  
  // 等待串口连接
  while (!Serial) {
    ; // 等待串口端口连接
  }
  
  Serial.println("Arduino Serial Controller Ready!");
  Serial.println("Commands: M<x>,<y> - Mouse move data");
  Serial.println("Example: M10,-5");
}

void loop() {
  // 检查是否有串口数据
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // 移除空白字符
    
    // 解析移动命令 M<x>,<y>
    if (command.startsWith("M")) {
      parseMouseCommand(command);
    }
    // 状态查询
    else if (command == "STATUS") {
      Serial.println("OK");
    }
    // 测试命令
    else if (command == "TEST") {
      Serial.println("Arduino Uno Serial Test OK");
    }
  }
}

void parseMouseCommand(String command) {
  // 移除 'M' 前缀
  command = command.substring(1);
  
  // 查找逗号分隔符
  int commaIndex = command.indexOf(',');
  
  if (commaIndex > 0) {
    // 解析 X 和 Y 坐标
    int x = command.substring(0, commaIndex).toInt();
    int y = command.substring(commaIndex + 1).toInt();
    
    // 限制移动范围
    x = constrain(x, -127, 127);
    y = constrain(y, -127, 127);
    
    // 输出移动数据（供 Python 脚本处理）
    if (x != 0 || y != 0) {
      Serial.print("MOVE:");
      Serial.print(x);
      Serial.print(",");
      Serial.println(y);
    }
  } else {
    Serial.println("ERROR: Invalid move command format");
  }
}