// storage.cpp - Bkz. storage.h
#include "storage.h"
#include "config.h"

#if defined(ARDUINO)
#include <avr/eeprom.h>
#endif

uint8_t crc8(const uint8_t *data, uint16_t len) {
  uint8_t crc = 0x00;
  while (len--) {
    crc ^= *data++;
    for (uint8_t i = 0; i < 8; i++) crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
  }
  return crc;
}

void settingsDefaults(Settings *s) {
  memset(s, 0, sizeof(Settings));
  s->magic = SETTINGS_MAGIC;
  s->version = SETTINGS_VERSION;
  s->deviceId = DEVICE_ID_DEFAULT;
  strncpy(s->pin, DEFAULT_PIN, PIN_LEN - 1);
  s->sens = DEFAULT_SENS;
  s->flags = SFLAG_SIREN_EN;  // siren acik, sesli arama kapali
  s->reportHours = DEFAULT_REPORT_H;
  s->vrefMv = VREF_MV_DEFAULT;
  settingsSeal(s);
}

uint8_t settingsCrc(const Settings *s) {
  return crc8((const uint8_t *)s, (uint16_t)offsetof(Settings, crc));
}

void settingsSeal(Settings *s) { s->crc = settingsCrc(s); }

static bool strFits(const char *p, uint8_t size) { return memchr(p, 0, size) != 0; }

bool settingsValid(const Settings *s) {
  if (s->magic != SETTINGS_MAGIC || s->version != SETTINGS_VERSION) return false;
  if (s->crc != settingsCrc(s)) return false;
  if (s->sens < 1 || s->sens > 3) return false;
  if (s->vrefMv < 1000 || s->vrefMv > 1200) return false;  // datasheet: 1,0..1,2 V
  if (!strFits(s->pin, PIN_LEN) || strlen(s->pin) < 4) return false;
  if (!strFits(s->name, NAME_LEN) || !strFits(s->location, LOC_LEN)) return false;
  for (uint8_t i = 0; i < PHONE_SLOTS; i++)
    if (!strFits(s->phones[i], PHONE_LEN)) return false;
  return true;
}

bool settingsPhoneListEmpty(const Settings *s) {
  for (uint8_t i = 0; i < PHONE_SLOTS; i++)
    if (s->phones[i][0]) return false;
  return true;
}

#if defined(ARDUINO)
bool settingsLoad(Settings *s) {
  eeprom_read_block(s, (const void *)SETTINGS_EE_ADDR, sizeof(Settings));
  if (settingsValid(s)) return true;
  settingsDefaults(s);
  return false;
}

void settingsSave(Settings *s) {
  settingsSeal(s);
  // eeprom_update_block yalniz degisen baytlari yazar (EEPROM omru)
  eeprom_update_block(s, (void *)SETTINGS_EE_ADDR, sizeof(Settings));
}
#endif
