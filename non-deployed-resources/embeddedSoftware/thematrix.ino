#include <Base64.h>
#include <LRAS1130.h>

using namespace lr;
AS1130 ledDriver;

int togglePixel(String coordinate);

typedef AS1130Picture24x5 Picture;
Picture picture;

void setup() {
  Wire.begin();
  Serial.begin(115200);
    
  // Wait until the chip is ready.
  delay(100); 
  Serial.println(F("Initialize chip"));
  
  // Check if the chip is addressable.
  if (!ledDriver.isChipConnected()) {
    Serial.println(F("Communication problem with chip."));
    Serial.flush();
    return;
  }

  // Set-up everything.
  ledDriver.setRamConfiguration(AS1130::RamConfiguration1);
  ledDriver.setOnOffFrameAllOff(0);
  ledDriver.setBlinkAndPwmSetAll(0);
  ledDriver.setCurrentSource(AS1130::Current30mA);
  ledDriver.setScanLimit(AS1130::ScanLimitFull);
  ledDriver.setMovieEndFrame(AS1130::MovieEndWithFirstFrame);
  ledDriver.setMovieFrameCount(4);
  ledDriver.setFrameDelayMs(100);
  ledDriver.setMovieLoopCount(AS1130::MovieLoop6);
  ledDriver.setScrollingEnabled(true);
  ledDriver.startPicture(0);

  // Enable the chip
  ledDriver.startChip();
  
  Particle.function("toggle", togglePixel);
  Particle.function("write", loadB64Image);
  Particle.function("ledtest", ledtest);
 }

int togglePixel(String coordinate) {
    uint8_t  posX = coordinate.substring(0,2).toInt();
    uint8_t  posY = coordinate.substring(2).toInt();
    bool state = picture.getPixel(posX, posY);
    picture.setPixel(posX, posY, !state);
    ledDriver.setOnOffFrame(0, picture);
    return 0;
}

int ledtest(String unused) {
    int colsPerRow = 24;
    int rows = 5;
    for (int i = 0; i < (colsPerRow * rows); i++) {
        uint8_t  y = i / colsPerRow;
        uint8_t  x = i % colsPerRow;
        picture.setPixel(x, y, 0X01);
    }
    ledDriver.setOnOffFrame(0, picture);
    return 0;
}

int loadB64Image(String encodedImage) {
    int encodedBufLen = min(encodedImage.length() + 1, 30);
    char encodedBuf[30];
    encodedImage.toCharArray(encodedBuf, encodedBufLen);
    int decodedBufLen = base64_dec_len(encodedBuf, encodedBufLen);
    char decodedBuf[30];
    int decodeResult = base64_decode(decodedBuf, encodedBuf, encodedBufLen);
    int colsPerRow = 24;
    int index = 0;
    for (int i = 0; i < decodedBufLen; i++) {
                char char_to_print = decodedBuf[i];
                for (uint8_t  bit = 0; bit < 8; bit++) {
                    uint8_t  y = index / colsPerRow;
                    uint8_t  x = index % colsPerRow;
                    picture.setPixel(x, y, (char_to_print >> bit) & 0X01);
                    index++;
                }
        }
    
    ledDriver.setOnOffFrame(0, picture);
    return 0;
}

void loop() {
    if (Particle.connected()) {
        if (!RGB.controlled()) {
            RGB.control(true);
            RGB.color(0, 0, 0);
        }
    } else {
        if (RGB.controlled()) {
            RGB.control(false);
        }
    }
}

