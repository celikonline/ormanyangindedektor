// detector.h - SAF MANTIK (AVR + host). Coklu sensor fuzyonu ile yangin skoru,
// Angstrom yangin risk indeksi, gaz tabani EMA'si ve artis hizi gecmisi (SPEC §6.2).
//
// 8 bit MCU'da kod boyutu icin SABIT NOKTALI aritmetik kullanilir:
//   sicaklik  : 0,1 C   (int16, "x10")      ornek: 70,0 C -> 700
//   nem       : 0,1 %   (int16, "x10")
//   gaz orani : binde   (uint16, "pm")      ornek: 0,40 -> 400
//   Angstrom I: yuzde   (int16, "x100")     ornek: 2,50 -> 250
//   pil       : mV      (uint16)
#pragma once
#include "compat.h"

// --- Esikler (HASSAS 2 / normal degerleri; seviye 1 x1,3, seviye 3 x0,75) ---
#define TH_MAXT_ABS_X10     700   // maxT >= 70 C            -> +3
#define TH_DIFF_HIGH_X10    250   // maxT - medyan >= 25 C   -> +2
#define TH_DIFF_LOW_X10     120   // maxT - medyan >= 12 C   -> +1
#define TH_RATE_X10          80   // maxT artis >= 8 C/dk    -> +1
#define TH_HOT_DELTA_X10    100   // sicak piksel: > medyan + 10 C
#define TH_HOT_COUNT          3   // sicak piksel sayisi >= 3 -> +1
#define TH_GAS_HIGH_PM      400   // gazR/taban < 0,40       -> +2
#define TH_GAS_LOW_PM       650   // gazR/taban < 0,65       -> +1
#define TH_AMB_TEMP_X10     550   // ortam >= 55 C           -> +2
#define TH_AMB_RISE_X10      60   // 5 dk'da >= 6 C artis    -> +1
#define TH_RH_DROP_X10      150   // 5 dk'da nem >= 15 puan dusus -> +1

// Hassasiyet carpani (binde): seviye 1 -> 1300, 2 -> 1000, 3 -> 750
#define SENS_K_LOW   1300
#define SENS_K_NORM  1000
#define SENS_K_HIGH   750

// --- Gaz tabani ---
#define DET_GAS_ALPHA_DIV        100   // alfa = 0,01
#define DET_GAS_ALPHA_WARM_DIV    10   // isinmada alfa = 0,1 (hizli takip, puan verilmez)
#define DET_GAS_UPDATE_MIN_PM    800   // yalniz oran > 0,8 iken guncelle
#define DET_GAS_WARMUP_S       1800UL  // ilk 30 dk isinma

// --- Gecmis (artis hizi / 5 dk pencereleri) ---
#define DET_HIST_LEN       8
#define DET_HIST_SPACING_S 50     // gecmise en sik 50 s'de bir kayit
#define DET_WINDOW_S       330    // "5 dk" penceresi (+30 s olcum payi)
#define DET_RATE_MIN_AGE_S 45     // C/dk hesabi icin en az 45 s once alinmis ornek

// Puan nedenleri (bit maskesi)
#define R_TH_ABS   0x0001
#define R_TH_DIFF2 0x0002
#define R_TH_DIFF1 0x0004
#define R_TH_RATE  0x0008
#define R_TH_HOT   0x0010
#define R_GAS2     0x0020
#define R_GAS1     0x0040
#define R_AMB_T    0x0080
#define R_AMB_RISE 0x0100
#define R_RH_DROP  0x0200

enum RiskLevel : uint8_t { RISK_VERY_HIGH = 0, RISK_HIGH = 1, RISK_MEDIUM = 2, RISK_LOW = 3 };

// Bir olcum dongusunun sonuclari
struct Reading {
  bool thermalOk;
  bool envOk;
  bool gasOk;
  uint8_t hotCount;   // > medyan + esik
  int16_t maxT10;     // 0,1 C
  int16_t median10;   // 0,1 C
  int16_t temp10;     // 0,1 C
  int16_t rh10;       // 0,1 %
  uint32_t gasOhm;
};

// Puanlama girdisi (saf fonksiyon)
struct ScoreInput {
  bool thermalOk;
  bool rateValid;
  bool gasValid;
  bool envOk;
  bool riseValid;
  bool dropValid;
  uint8_t hotCount;
  int16_t maxT10, median10;
  int16_t rate10;     // 0,1 C/dk
  uint16_t gasPm;     // binde
  int16_t temp10;
  int16_t rise10;     // 0,1 C (5 dk)
  int16_t drop10;     // 0,1 puan (5 dk)
};

struct HistEntry {
  uint32_t t;
  int16_t maxT10;
  int16_t temp10;
  int16_t rh10;
  uint8_t flags;      // bit0 termal gecerli, bit1 ortam gecerli
};

struct Detector {
  uint32_t gasBase;   // Ohm
  bool gasBaseValid;
  uint32_t gasWarmStart;
  HistEntry hist[DET_HIST_LEN];
  uint8_t histHead;   // bir sonraki yazma konumu
  uint8_t histCount;
  // son degerlendirme
  uint8_t score;
  uint16_t reasons;
  int16_t gasPm;      // < 0 ise gecersiz
  int16_t rate10;
  int16_t rise10;
  int16_t drop10;
};

uint16_t sensK(uint8_t sens);                       // 1300 / 1000 / 750
int16_t scaleTh(int16_t th, uint8_t sens);          // th * k / 1000
int16_t hotDeltaFor(uint8_t sens);                  // 0,1 C

// 8x8 piksel (0,25 C birimi) dizisini YERINDE siralar ve istatistik cikarir.
void thermalStats(int16_t *px, uint8_t n, int16_t hotDelta10, int16_t *maxT10, int16_t *median10,
                  uint8_t *hotCount);

int16_t angstromIndex100(int16_t rh10, int16_t temp10);   // I x100 = RH/20 + (27 - T)/10
uint8_t angstromLevel(int16_t idx100);                    // RiskLevel
const char *riskNameP(uint8_t level);                     // PROGMEM: "COK YUKSEK" ...

uint8_t batteryPercent(uint16_t mv);                      // Li-ion 1S yaklasik dolum yuzdesi

void detInit(Detector *d, uint32_t now);
void detCalibrateGas(Detector *d);   // KALIBRE: taban bir sonraki okumadan yeniden alinir

uint8_t detScore(const ScoreInput *in, uint8_t sens, uint16_t *reasons);

// Okumayi degerlendirir: gecmisten hiz/artis hesaplar, puanlar, tabani ve gecmisi gunceller.
// allowBaseline: yalniz NORMAL durumda true verilmelidir.
uint8_t detEvaluate(Detector *d, const Reading *r, uint32_t now, uint8_t sens, bool allowBaseline);

// 0,1 birimli degeri en yakin tam sayiya yuvarlar (-0,5 -> -1)
int16_t roundX10(int16_t v10);
