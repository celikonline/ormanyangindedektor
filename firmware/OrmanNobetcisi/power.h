// power.h - Uyku (WDT), saat, kesmeler, ADC (pil/gunes, ic 1,1 V), raylar.
#pragma once
#include <Arduino.h>

// Uyanma bayraklari
#define WAKE_WDT     0x01
#define WAKE_TAMPER  0x02   // INT0
#define WAKE_RI      0x04   // INT1 (modem RI)

extern uint8_t g_resetCause;   // MCUSR (PORF/EXTRF/BORF/WDRF)

void powerInit();

// Saniye saati: uykuda WDT tikleri, uyanikken millis() ile ilerler (monoton, acilistan beri).
void clockUpdate();
uint32_t clockNow();
void clockCalibrate(uint32_t realElapsedS, uint32_t clockElapsedS);  // ag saatiyle WDT duzeltmesi
uint16_t clockTickMs();

// Arka plan servisi: WDT besleme + saat. Uzun beklemelerde surekli cagrilir.
void svcPoll();
void svcDelay(uint16_t ms);

// Uyku
uint8_t powerTakeWakeFlags();
void powerSleep(uint32_t maxSeconds);   // power-down; WDT (8/4/2/1 s), INT0, INT1, A2 PCINT ile uyanir
void powerIdle();                       // idle (Timer0/Timer2 calisir) - alarm/test sirasinda

// Olcumler
uint16_t readVbatMv(uint16_t vrefMv);
uint16_t readVsolarMv(uint16_t vrefMv);
bool isCharging();
// Batarya sicaklik korumasi (CN3791'de TEMP pini yok -> MCU yapar, SPEC Δ1)
enum ChgTemp : uint8_t { CHG_TEMP_OK = 0, CHG_TEMP_COLD, CHG_TEMP_HOT, CHG_TEMP_FAULT };
uint8_t chargeTempControl(uint16_t vrefMv);   // NTC'yi okur, D13 ile sarji keser/acar; durumu dondurur
bool chargeInhibited();

// Raylar
void sensorRail(bool on);
