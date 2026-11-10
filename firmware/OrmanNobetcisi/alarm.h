// alarm.h - Yerel alarm: engellemesiz cift flas strob (Timer2 ISR) + siren dongusu + susturma.
#pragma once
#include <Arduino.h>

void alarmInit();

// Alarm oturumu: isik 60 dk, siren 3 dk acik / 2 dk kapali, toplam en fazla 30 dk (SPEC §6.1)
void alarmStart(uint32_t now);
void alarmStop();                        // tum cikislar kapali, oturum biter
void alarmMute(uint32_t now, uint16_t minutes);   // 0 = susturmayi iptal et
bool alarmMuted(uint32_t now);
void alarmTest(bool sirenAllowed);       // 5 s isik + siren testi (millis tabanli)

// Ana dongude cagrilir: istenen cikislari hesaplar ve uygular.
void alarmUpdate(uint32_t now, bool sirenEnabled);

bool alarmSessionActive();               // alarm oturumu var mi (isik/siren penceresi)
bool alarmOutputsActive();               // strob veya siren su an calisiyor mu (MCU idle'da kalmali)
