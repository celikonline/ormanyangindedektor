// pins.h - ON-1 pin haritasi. KAYNAK: SPEC.md §3. Burada DEGISIKLIK YAPMAYIN;
// pin degisikligi once SPEC.md'de yapilir.
#pragma once

// D0/D1: FTDI (programlama / DEBUG seri port)
#define PIN_TAMPER_N      2   // PD2 INT0  - titresim + kapak reed, 1M pull-up, aktif LOW
#define PIN_MODEM_RI_N    3   // PD3 INT1  - A7670E RI, aktif LOW darbe
#define PIN_MODEM_PWRKEY  4   // PD4       - HIGH = PWRKEY GND'ye cekilir (Q4)
#define PIN_MODEM_DTR     5   // PD5       - HIGH = modem uyuyabilir, LOW = uyandir
#define PIN_LED_STROBE    6   // PD6       - HIGH = 6x1W kirmizi LED (Q3)
#define PIN_MODEM_RX      7   // PD7       - SoftwareSerial RX  (A7670E TXD)
#define PIN_MODEM_TX      8   // PB0       - SoftwareSerial TX  (A7670E RXD)
#define PIN_SIREN_EN      9   // PB1       - HIGH = MT3608 12 V siren
#define PIN_MODEM_PWR_EN 10   // PB2       - HIGH = VMODEM acik (Q5->Q1)
#define PIN_SENSOR_PWR_N 11   // PB3       - LOW  = sensor rayi acik (Q2)
#define PIN_STATUS_LED   12   // PB4       - yesil durum LED'i
#define PIN_CHG_INHIBIT  13   // PB5 (ISP SCK) - HIGH = sarj durur (Q12 -> CN3791 MPPT GND)  [SPEC Δ1]

#define PIN_VBAT_SENSE   A0   // 1M/330k bolucu, ic 1,1 V referans
#define PIN_SOLAR_SENSE  A1   // 1M/150k bolucu, ic 1,1 V referans
#define PIN_TEST_REED_N  A2   // PC2 PCINT10 - manyetik test reed, ic pull-up, aktif LOW
#define PIN_CHG_STAT_N   A3   // PC3       - CN3791 CHRG, ic pull-up, LOW = sarj oluyor
#define PIN_BAT_NTC      A7   // ADC7      - 220k (3V3) / NTC 10k B3950 (GND) bolucu  [SPEC Δ1]
// A4/A5: I2C SDA/SCL (4,7k pull-up sensor rayina)

// Dogrudan port erisimi (ISR icinde hizli yazma icin)
#define STROBE_PORT  PORTD
#define STROBE_BIT   6
#define SLED_PORT    PORTB
#define SLED_BIT     4
