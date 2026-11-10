// storage.h - EEPROM ayar yapisi: sihirli sayi + surum + CRC8 (SPEC §6.5).
// Yapi/CRC/varsayilan kismi SAF MANTIKtir (host testinde derlenir);
// EEPROM okuma/yazma yalniz Arduino derlemesinde vardir.
#pragma once
#include "compat.h"

#define SETTINGS_MAGIC    0x4F4Eu   // "ON"
#define SETTINGS_VERSION  1
#define SETTINGS_EE_ADDR  0

#define PHONE_SLOTS  5
#define PHONE_LEN    17   // '+' + 15 hane + NUL
#define NAME_LEN     21   // <= 20 karakter + NUL
#define LOC_LEN      24   // "-39.7051234,-126.8521123" + NUL
#define PIN_LEN      7    // 4..6 hane + NUL

#define SFLAG_SIREN_EN  0x01   // SIREN AC/KAPA
#define SFLAG_CALL_EN   0x02   // ARAMA AC/KAPA

struct Settings {
  uint16_t magic;
  uint8_t  version;
  uint16_t deviceId;                    // ON1-XXXX
  char     pin[PIN_LEN];
  char     phones[PHONE_SLOTS][PHONE_LEN];  // [0] = yonetici
  char     name[NAME_LEN];
  char     location[LOC_LEN];
  uint8_t  sens;                        // 1..3
  uint8_t  flags;                       // SFLAG_*
  uint8_t  reportHours;                 // 0 = kapali
  uint16_t vrefMv;                      // ic 1,1 V referans kalibrasyonu (mV, SPEC "vrefCal")
  uint8_t  crc;                         // her zaman son alan
};

// CRC-8 (polinom 0x07, baslangic 0x00; "123456789" -> 0xF4)
uint8_t crc8(const uint8_t *data, uint16_t len);

void    settingsDefaults(Settings *s);
uint8_t settingsCrc(const Settings *s);      // crc alani haric tum baytlar
bool    settingsValid(const Settings *s);    // sihirli sayi + surum + CRC + aralik
void    settingsSeal(Settings *s);           // crc alanini gunceller
bool    settingsPhoneListEmpty(const Settings *s);

#if defined(ARDUINO)
bool settingsLoad(Settings *s);              // gecersizse varsayilanlari yukler, false doner
void settingsSave(Settings *s);
#endif
