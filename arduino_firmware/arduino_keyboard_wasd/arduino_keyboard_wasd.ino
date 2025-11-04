/*
 * Arduino Leonardo 键盘驱动 - WASD 控制
 * 功能：通过串口指令控制 WASD 四个键的按下和弹起
 * 作者：AI-Aimbot 项目
 * 版本：1.0
 * 
 * 指令格式：
 * - 按下键：'w', 'a', 's', 'd' (小写)
 * - 弹起键：'W', 'A', 'S', 'D' (大写)
 * - 释放所有键：'R' 或 'r'
 * - 查询状态：'?' 
 */

#include <Keyboard.h>

// 键盘状态跟踪
bool keyPressed[4] = {false, false, false, false}; // W, A, S, D
char keyChars[4] = {'w', 'a', 's', 'd'};
String keyNames[4] = {"W", "A", "S", "D"};

// 静默期控制
bool silenceMode = false;
unsigned long silenceStartTime = 0;
unsigned long silenceDuration = 150; // 默认150ms静默期

// 状态指示灯（如果板子有内置LED）
const int ledPin = LED_BUILTIN;
bool ledState = false;

void setup() {
  // 初始化串口通信
  Serial.begin(115200);
  
  // 初始化键盘功能
  Keyboard.begin();
  
  // 初始化LED
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
  
  // 等待串口连接
  while (!Serial) {
    delay(10);
  }
  
  // 发送启动信息
  Serial.println("=== Arduino WASD 键盘驱动已启动 ===");
  Serial.println("版本: 1.0");
  Serial.println("支持指令:");
  Serial.println("  按下: w, a, s, d (小写)");
  Serial.println("  弹起: W, A, S, D (大写)");
  Serial.println("  释放所有: R 或 r");
  Serial.println("  查询状态: ?");
  Serial.println("  开始静默期: X");
  Serial.println("  停止静默期: x");
  Serial.println("  设置静默时长: T<毫秒> (如 T200)");
  Serial.println("================================");
  
  // LED闪烁表示就绪
  for (int i = 0; i < 3; i++) {
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
    delay(200);
  }
}

void loop() {
  // 检查静默期状态
  checkSilenceMode();
  
  // 检查串口数据
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    // 清除串口缓冲区中的其他字符
    while (Serial.available() > 0) {
      Serial.read();
      delay(1);
    }
    
    processCommand(command);
  }
  
  // 心跳LED（每秒闪烁一次）
  static unsigned long lastHeartbeat = 0;
  if (millis() - lastHeartbeat > 1000) {
    ledState = !ledState;
    digitalWrite(ledPin, ledState);
    lastHeartbeat = millis();
  }
  
  delay(1); // 小延迟避免过度占用CPU
}

void processCommand(char command) {
  switch (command) {
    // 按下键
    case 'w':
      pressKey(0);
      break;
    case 'a':
      pressKey(1);
      break;
    case 's':
      pressKey(2);
      break;
    case 'd':
      pressKey(3);
      break;
    
    // 弹起键
    case 'W':
      releaseKey(0);
      break;
    case 'A':
      releaseKey(1);
      break;
    case 'S':
      releaseKey(2);
      break;
    case 'D':
      releaseKey(3);
      break;
    
    // 释放所有键
    case 'R':
    case 'r':
      releaseAllKeys();
      break;
    
    // 查询状态
    case '?':
      printStatus();
      break;
    
    // 开始静默期
    case 'X':
      startSilenceMode();
      break;
    
    // 停止静默期
    case 'x':
      stopSilenceMode();
      break;
    
    // 设置静默时长 (T后跟数字)
    case 'T':
      setSilenceDuration();
      break;
    
    // 未知指令
    default:
      Serial.print("错误: 未知指令 '");
      Serial.print(command);
      Serial.println("'");
      break;
  }
}

void pressKey(int keyIndex) {
  if (keyIndex < 0 || keyIndex > 3) return;
  
  if (!keyPressed[keyIndex]) {
    Keyboard.press(keyChars[keyIndex]);
    keyPressed[keyIndex] = true;
    Serial.print("按下: ");
    Serial.println(keyNames[keyIndex]);
  } else {
    Serial.print("警告: ");
    Serial.print(keyNames[keyIndex]);
    Serial.println(" 键已经处于按下状态");
  }
}

void releaseKey(int keyIndex) {
  if (keyIndex < 0 || keyIndex > 3) return;
  
  if (keyPressed[keyIndex]) {
    Keyboard.release(keyChars[keyIndex]);
    keyPressed[keyIndex] = false;
    Serial.print("弹起: ");
    Serial.println(keyNames[keyIndex]);
  } else {
    Serial.print("警告: ");
    Serial.print(keyNames[keyIndex]);
    Serial.println(" 键已经处于弹起状态");
  }
}

void releaseAllKeys() {
  bool anyKeyPressed = false;
  
  for (int i = 0; i < 4; i++) {
    if (keyPressed[i]) {
      Keyboard.release(keyChars[i]);
      keyPressed[i] = false;
      anyKeyPressed = true;
    }
  }
  
  if (anyKeyPressed) {
    Serial.println("释放所有按键");
  } else {
    Serial.println("所有按键已处于弹起状态");
  }
}

void printStatus() {
  Serial.println("=== 当前键盘状态 ===");
  for (int i = 0; i < 4; i++) {
    Serial.print(keyNames[i]);
    Serial.print(": ");
    Serial.println(keyPressed[i] ? "按下" : "弹起");
  }
  Serial.print("静默模式: ");
  Serial.println(silenceMode ? "开启" : "关闭");
  Serial.print("静默时长: ");
  Serial.print(silenceDuration);
  Serial.println("ms");
  Serial.println("==================");
}

void checkSilenceMode() {
  if (silenceMode) {
    // 检查静默期是否结束
    if (millis() - silenceStartTime >= silenceDuration) {
      stopSilenceMode();
      return;
    }
    
    // 在静默期内持续释放WASD键
    static unsigned long lastReleaseTime = 0;
    if (millis() - lastReleaseTime >= 10) { // 每10ms释放一次
      for (int i = 0; i < 4; i++) {
        if (keyPressed[i]) {
          Keyboard.release(keyChars[i]);
          keyPressed[i] = false;
        }
      }
      lastReleaseTime = millis();
    }
  }
}

void startSilenceMode() {
  if (!silenceMode) {
    silenceMode = true;
    silenceStartTime = millis();
    
    // 立即释放所有WASD键
    releaseAllKeys();
    
    Serial.print("开始静默期: ");
    Serial.print(silenceDuration);
    Serial.println("ms");
  } else {
    Serial.println("静默期已在进行中");
  }
}

void stopSilenceMode() {
  if (silenceMode) {
    silenceMode = false;
    Serial.println("静默期结束");
  }
}

void setSilenceDuration() {
  // 读取T后面的数字
  String durationStr = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      durationStr += c;
    }
    delay(1);
  }
  
  if (durationStr.length() > 0) {
    unsigned long newDuration = durationStr.toInt();
    if (newDuration > 0 && newDuration <= 5000) { // 限制在5秒内
      silenceDuration = newDuration;
      Serial.print("设置静默时长: ");
      Serial.print(silenceDuration);
      Serial.println("ms");
    } else {
      Serial.println("错误: 静默时长必须在1-5000ms之间");
    }
  } else {
    Serial.println("错误: 请提供有效的时长数字");
  }
}