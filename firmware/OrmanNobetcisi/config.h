// config.h - ON-1 firmware ayarlari. Davranis degerleri SPEC.md §5-§6'dan alinmistir.
#pragma once

#define FW_VERSION "1.0.0"

// ---------------------------------------------------------------------------
// Hata ayiklama: 1 yapilirsa donanim UART'ina (D0/D1, FTDI) 38400 bps log basilir.
// Uretimde 0 olmalidir (Serial tamponlari RAM'e hic baglanmaz).
// ---------------------------------------------------------------------------
#ifndef DEBUG
#define DEBUG 0
#endif
#define DEBUG_BAUD 38400

// ---------------------------------------------------------------------------
// Cihaz kimligi ve varsayilanlar (EEPROM bos/bozuksa kullanilir)
// Her cihaz icin DEVICE_ID_DEFAULT'u degistirip yukleyin -> SMS'lerde "ON1-0007".
// ---------------------------------------------------------------------------
#ifndef DEVICE_ID_DEFAULT
#define DEVICE_ID_DEFAULT 1
#endif
#define DEFAULT_PIN        "1234"
#define DEFAULT_SENS       2       // HASSAS 1/2/3
#define DEFAULT_REPORT_H   24      // RAPOR: gunluk durum SMS'i (saat)
#define VREF_MV_DEFAULT    1100    // ic 1,1 V referans kalibrasyonu (mV) = SPEC vrefCal 1.100

// Gerilim bolucu oranlari (SPEC §3)
#define VBAT_DIV_X10000   2481   // 330k / (1M + 330k) = 0,2481
#define SOLAR_DIV_X10000  1304   // 150k / (1M + 150k) = 0,1304

// ---------------------------------------------------------------------------
// Olcum periyotlari (s) - SPEC §6.1
// ---------------------------------------------------------------------------
#define MEAS_PERIOD_NORMAL_S    60
#define MEAS_PERIOD_HIGHRISK_S  20   // Angstrom I < 2,0
#define MEAS_PERIOD_SUPHE_S      5
#define MEAS_PERIOD_ALARM_S     10
#define MEAS_PERIOD_INSTALL_S    5
#define LOWPOWER_PERIOD_FACTOR   2   // DUSUK_PIL / KRITIK tasarruf modunda periyot carpani

// Durum makinesi
#define SCORE_SUPHE         2
#define SCORE_CONFIRM       3
#define SCORE_ALARM         5
#define SUPHE_SAMPLES       6
#define SUPHE_CONFIRM_HITS  3

// Alarm
#define ALARM_UPDATE_INTERVAL_S  900UL   // 15 dk'da bir guncel SMS
#define ALARM_UPDATE_MAX         4
#define ALARM_CLEAR_S            600UL   // 10 dk skor=0 -> SONA ERDI
#define ALARM_SMS_RETRY_S        60UL    // teslim edilemeyen alarm SMS'i tekrar
#define ALARM_SMS_RETRY_MAX      10
#define SIREN_ON_S               180UL   // 3 dk acik
#define SIREN_OFF_S              120UL   // 2 dk kapali
#define SIREN_TOTAL_S            1800UL  // toplam en fazla 30 dk
#define LIGHT_TOTAL_S            3600UL  // isik 60 dk
#define TEST_DURATION_MS         5000UL  // TEST: 5 s isik + siren
#define CALL_RING_S              30      // ARAMA AC: 1. numarayi 30 s caldir
#define MUTE_MAX_MIN             1440    // SESSIZ ust siniri (24 saat)

// Pil esikleri (SPEC §5)
#define BATT_LOW_MV       3450
#define BATT_CRIT_MV      3300
#define BATT_OK_MV        3600
#define BATT_CONFIRM_CNT  3      // gecis icin art arda olcum sayisi

// Modem
#define MODEM_BAUD               9600
#define MODEM_FACTORY_BAUD       115200UL  // A7670E fabrika hizi (ilk kurulumda 9600'e cekilir)
#define MODEM_MAX_ATTEMPTS       3
#define MODEM_RETRY_BACKOFF_S    1800UL    // 3 basarisiz denemeden sonra 30 dk bekle
#define MODEM_NET_WAIT_S         90        // SMS oncesi sebeke kaydi bekleme ust siniri
#define SMS_POLL_INTERVAL_S      1800UL    // RI kacirilirsa diye 30 dk'da bir SMS kontrolu
#define DAILY_INTERVAL_S         86400UL   // ag saati + sinyal kontrolu
#define SMS_PER_WAKE_MAX         8
#define LINE_TEXT_MAX            121       // gelen SMS metin tamponu (UCS2 hex dahil)

// Kurcalama (TAMPER) - SW-18010P ruzgarda da tetiklenebildigi icin esikli
#define TAMPER_PULSES            5
#define TAMPER_WINDOW_S          120UL
#define TAMPER_HOLD_S            10UL      // hat surekli LOW (kapak acik)
#define TAMPER_SMS_MIN_INTERVAL_S 3600UL

// Test reed / kurulum modu
#define REED_HOLD_MS             2000UL
#define INSTALL_MODE_S           600UL

// Guvenlik: 1 ise EKLE / SIL / PIN komutlarini yalniz 1. numara (yonetici) verebilir.
#define ADMIN_ONLY_CONFIG        1

// WDT 8 s tik suresi (ms). Ag saatiyle gunluk olarak otomatik kalibre edilir.
#define WDT_TICK_MS_DEFAULT      8000

// ---------------------------------------------------------------------------
// Hata ayiklama makrolari
// ---------------------------------------------------------------------------
#if DEBUG
  #define DBG(s)      Serial.print(F(s))
  #define DBGLN(s)    Serial.println(F(s))
  #define DBGV(v)     Serial.print(v)
  #define DBGVLN(v)   Serial.println(v)
#else
  #define DBG(s)      do {} while (0)
  #define DBGLN(s)    do {} while (0)
  #define DBGV(v)     do {} while (0)
  #define DBGVLN(v)   do {} while (0)
#endif
