// Arduino Leonardo 键盘驱动代码
// 控制 WASD 四个按键的按下与弹起

#include <Keyboard.h>

void setup() {
  // 初始化串行通信，用于调试和接收指令
  Serial.begin(9600);
  // 启动键盘模拟功能
  Keyboard.begin();
  Serial.println("Arduino Keyboard Driver Ready!");
  Serial.println("Send 'w', 'a', 's', 'd' to press the key.");
  Serial.println("Send 'W', 'A', 'S', 'D' to release the key.");
}

void loop() {
  // 检查是否有串行数据可用
  if (Serial.available() > 0) {
    // 读取接收到的字符
    char command = Serial.read();

    switch (command) {
      case 'w':
        Serial.println("Pressing W");
        Keyboard.press('w');
        break;
      case 'a':
        Serial.println("Pressing A");
        Keyboard.press('a');
        break;
      case 's':
        Serial.println("Pressing S");
        Keyboard.press('s');
        break;
      case 'd':
        Serial.println("Pressing D");
        Keyboard.press('d');
        break;
      case 'W':
        Serial.println("Releasing W");
        Keyboard.release('w');
        break;
      case 'A':
        Serial.println("Releasing A");
        Keyboard.release('a');
        break;
      case 'S':
        Serial.println("Releasing S");
        Keyboard.release('s');
        break;
      case 'D':
        Serial.println("Releasing D");
        Keyboard.release('d');
        break;
      default:
        Serial.print("Unknown command: ");
        Serial.println(command);
        break;
    }
  }
}