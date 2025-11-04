/*
 * Arduino Leonardo 鼠标驱动
 * 功能：通过串口指令控制鼠标移动和点击
 * 作者：AI-Aimbot 项目
 * 版本：1.0
 * 
 * 指令格式：
 * - 鼠标移动：M<x>,<y> (例如: M10,-5)
 * - 鼠标点击：CL (左键), CR (右键), CM (中键)
 * - 状态查询：STATUS (返回 "OK")
 */

#include "Mouse.h"

void setup() {
  // 初始化串口通信
  Serial.begin(9600);
  
  // 初始化鼠标功能
  Mouse.begin();
  
  // 等待串口连接
  while (!Serial) {
    ; // 等待串口连接
  }
  
  // 发送启动信息
  Serial.println("Arduino Mouse Controller Ready!");
  Serial.println("Commands: M<x>,<y> - Move mouse");
  Serial.println("Commands: CL/CR/CM - Click mouse");
  Serial.println("Commands: STATUS - Check status");
  Serial.println("Example: M10,-5");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // 移除前后空白字符
    
    if (command.startsWith("M")) {
      parseMouseCommand(command);
    }
    else if (command.startsWith("C")) {
      parseClickCommand(command);
    }
    else if (command == "STATUS") {
      Serial.println("OK");
    }
    else {
      Serial.println("ERROR: Unknown command");
    }
  }
}

/**
 * 解析鼠标移动命令
 * 格式: M<x>,<y>
 * 例如: M10,-5 表示向右移动10像素，向上移动5像素
 */
void parseMouseCommand(String command) {
  command = command.substring(1); // 移除 'M' 前缀
  
  int commaIndex = command.indexOf(',');
  
  if (commaIndex > 0) {
    int x = command.substring(0, commaIndex).toInt();
    int y = command.substring(commaIndex + 1).toInt();
    
    // 限制移动范围在 -127 到 127 之间
    x = constrain(x, -127, 127);
    y = constrain(y, -127, 127);
    
    if (x != 0 || y != 0) {
      Mouse.move(x, y);
      Serial.print("Moved: ");
      Serial.print(x);
      Serial.print(",");
      Serial.println(y);
    }
  } else {
    Serial.println("ERROR: Invalid move command format");
  }
}

/**
 * 解析鼠标点击命令
 * 格式: CL (左键), CR (右键), CM (中键)
 */
void parseClickCommand(String command) {
  command = command.substring(1); // 移除 'C' 前缀
  
  if (command == "L") {
    Mouse.click(MOUSE_LEFT);
    Serial.println("Left Click");
  } else if (command == "R") {
    Mouse.click(MOUSE_RIGHT);
    Serial.println("Right Click");
  } else if (command == "M") {
    Mouse.click(MOUSE_MIDDLE);
    Serial.println("Middle Click");
  } else {
    Serial.println("ERROR: Invalid click command");
  }
}