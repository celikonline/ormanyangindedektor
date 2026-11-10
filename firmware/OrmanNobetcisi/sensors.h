// sensors.h - AMG8833 (8x8 termal, 0x69) + BME680 (gaz/T/RH/P, 0x77) dogrudan yazmac surucusu.
// I2C kilitlenmesinde SENSOR_PWR_N (Q2) rayi kapatilip acilir ve sensorler yeniden baslatilir.
#pragma once
#include <Arduino.h>
#include "detector.h"

bool sensorsBegin();             // ray acik, I2C, her iki sensoru baslat
// Tek olcum dongusu (~0,3 s). keepAwake: AMG8833'u uyutma (SUPHE/ALARM/kurulum modunda).
// Basarisizlikta bir kez ray dongusu + yeniden deneme yapar.
void sensorsMeasure(Reading *r, uint8_t sens, bool keepAwake);
void sensorsRecover();           // ray kapat/ac + yeniden baslat
uint8_t sensorsFaultMask();      // bit0 AMG8833, bit1 BME680 (son olcumde hata)
