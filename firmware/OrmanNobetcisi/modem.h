// modem.h - SIMCom A7670E: guc/PWRKEY, AT komut yardimcisi (zaman asimli, akan okuma),
// SMS gonder/oku/sil, RI/DTR uyku yonetimi, CSQ, ag saati, sesli arama.
#pragma once
#include <Arduino.h>

void modemBegin();                       // pinler (modem kapali)

// Modemi acik + uyanik + yapilandirilmis hale getirir.
// Yanit yoksa guc dongusu (Q1); 3 basarisiz denemeden sonra 30 dk bekler.
// force=true (alarm): bekleme suresini yok sayar ve 1 deneme daha yapar.
bool modemEnsure(bool force);
void modemPowerOff();                    // AT+CPOF + VMODEM kesilir
bool modemIsOn();
bool modemInBackoff();
void modemSleep();                       // DTR HIGH (CSCLK=1 ile modem uyur), seri dinleme kapali

bool modemWaitNetwork(uint16_t timeoutS);
bool modemSendSms(const char *number, const char *text);   // <= 160 ASCII karakter

// SIM'deki ilk mesaji okur (AT+CMGL="ALL"). Mesaj yoksa false.
bool modemReadFirstSms(uint16_t *idx, char *sender, uint8_t senderSize, char *text, uint8_t textSize);
bool modemDeleteSms(uint16_t idx);

int8_t modemSignal();                    // CSQ 0..31, 99 bilinmiyor, -1 hata
bool modemNetworkTime(uint32_t *secs2000);
bool modemCall(const char *number, uint8_t seconds);
