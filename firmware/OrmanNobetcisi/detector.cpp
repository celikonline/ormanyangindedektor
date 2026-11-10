// detector.cpp - SAF MANTIK (AVR + host). Bkz. detector.h ve SPEC §6.2
#include "detector.h"

uint16_t sensK(uint8_t sens) {
  if (sens == 1) return SENS_K_LOW;    // dusuk hassasiyet: esikler buyur
  if (sens == 3) return SENS_K_HIGH;   // yuksek hassasiyet: esikler kuculur
  return SENS_K_NORM;
}

int16_t scaleTh(int16_t th, uint8_t sens) { return (int16_t)(((int32_t)th * sensK(sens)) / 1000); }

int16_t hotDeltaFor(uint8_t sens) { return scaleTh(TH_HOT_DELTA_X10, sens); }

int16_t roundX10(int16_t v10) { return (int16_t)((v10 >= 0 ? v10 + 5 : v10 - 5) / 10); }

void thermalStats(int16_t *px, uint8_t n, int16_t hotDelta10, int16_t *maxT10, int16_t *median10,
                  uint8_t *hotCount) {
  // Eklemeli siralama (64 eleman, ek RAM kullanmaz)
  for (uint8_t i = 1; i < n; i++) {
    int16_t v = px[i];
    int8_t j = (int8_t)(i - 1);
    while (j >= 0 && px[j] > v) {
      px[j + 1] = px[j];
      j--;
    }
    px[j + 1] = v;
  }
  // medQ2 = 2 x medyan (0,25 C birimi)
  int16_t medQ2 = (n & 1u) ? (int16_t)(2 * px[n / 2]) : (int16_t)(px[n / 2 - 1] + px[n / 2]);
  *maxT10 = (int16_t)((int32_t)px[n - 1] * 5 / 2);   // 0,25 C -> 0,1 C
  *median10 = (int16_t)((int32_t)medQ2 * 5 / 4);
  // piksel > medyan + delta  <=>  10*q > 5*medQ2 + 4*delta10
  int32_t thr = (int32_t)medQ2 * 5 + (int32_t)hotDelta10 * 4;
  uint8_t cnt = 0;
  for (int8_t i = (int8_t)(n - 1); i >= 0 && (int32_t)px[i] * 10 > thr; i--) cnt++;
  *hotCount = cnt;
}

int16_t angstromIndex100(int16_t rh10, int16_t temp10) {
  // I = RH/20 + (27 - T)/10  ->  I*100 = RH10/2 + 270 - T10
  return (int16_t)(rh10 / 2 + 270 - temp10);
}

uint8_t angstromLevel(int16_t idx100) {
  if (idx100 < 200) return RISK_VERY_HIGH;
  if (idx100 < 250) return RISK_HIGH;
  if (idx100 <= 400) return RISK_MEDIUM;
  return RISK_LOW;
}

static const char rk0[] PROGMEM = "COK YUKSEK";
static const char rk1[] PROGMEM = "YUKSEK";
static const char rk2[] PROGMEM = "ORTA";
static const char rk3[] PROGMEM = "DUSUK";

const char *riskNameP(uint8_t level) {
  switch (level) {
    case RISK_VERY_HIGH: return rk0;
    case RISK_HIGH: return rk1;
    case RISK_MEDIUM: return rk2;
    default: return rk3;
  }
}

uint8_t batteryPercent(uint16_t mv) {
  // Li-ion 1S, hafif yukte yaklasik egri (mV -> %), dogrusal ara degerleme
  static const uint16_t tv[] PROGMEM = {4200, 4100, 4000, 3900, 3800, 3700, 3600, 3500, 3400, 3300, 3000};
  static const uint8_t tp[] PROGMEM = {100, 90, 79, 68, 55, 40, 22, 10, 4, 1, 0};
  if (mv >= 4200) return 100;
  for (uint8_t i = 1; i < sizeof(tp); i++) {
    uint16_t lo = pgm_read_word(&tv[i]);
    if (mv >= lo) {
      uint16_t hi = pgm_read_word(&tv[i - 1]);
      uint8_t pl = pgm_read_byte(&tp[i]), ph = pgm_read_byte(&tp[i - 1]);
      return (uint8_t)(pl + ((uint32_t)(ph - pl) * (mv - lo) + (hi - lo) / 2) / (hi - lo));
    }
  }
  return 0;
}

void detInit(Detector *d, uint32_t now) {
  memset(d, 0, sizeof(Detector));
  d->gasWarmStart = now;
  d->gasPm = -1;
}

void detCalibrateGas(Detector *d) { d->gasBaseValid = false; }

uint8_t detScore(const ScoreInput *in, uint8_t sens, uint16_t *reasons) {
  uint8_t s = 0;
  uint16_t r = 0;

  if (in->thermalOk) {
    int16_t diff = (int16_t)(in->maxT10 - in->median10);
    if (in->maxT10 >= scaleTh(TH_MAXT_ABS_X10, sens)) {
      s += 3;
      r |= R_TH_ABS;
    } else if (diff >= scaleTh(TH_DIFF_HIGH_X10, sens)) {
      s += 2;
      r |= R_TH_DIFF2;
    } else if (diff >= scaleTh(TH_DIFF_LOW_X10, sens)) {
      s += 1;
      r |= R_TH_DIFF1;
    }
    if (in->rateValid && in->rate10 >= scaleTh(TH_RATE_X10, sens)) {
      s += 1;
      r |= R_TH_RATE;
    }
    uint8_t hotMin = (uint8_t)(((uint32_t)TH_HOT_COUNT * sensK(sens) + 500) / 1000);  // 4 / 3 / 2
    if (in->hotCount >= hotMin) {
      s += 1;
      r |= R_TH_HOT;
    }
  }

  if (in->gasValid) {
    // Oran esikleri "dusus miktari" (1 - oran) uzerinden olceklenir:
    // seviye 1: <0,22 / <0,545   seviye 2: <0,40 / <0,65   seviye 3: <0,55 / <0,7375
    int16_t rHigh = (int16_t)(1000 - scaleTh(1000 - TH_GAS_HIGH_PM, sens));
    int16_t rLow = (int16_t)(1000 - scaleTh(1000 - TH_GAS_LOW_PM, sens));
    if (rHigh < 50) rHigh = 50;
    if ((int16_t)in->gasPm < rHigh) {
      s += 2;
      r |= R_GAS2;
    } else if ((int16_t)in->gasPm < rLow) {
      s += 1;
      r |= R_GAS1;
    }
  }

  if (in->envOk) {
    if (in->temp10 >= scaleTh(TH_AMB_TEMP_X10, sens)) {
      s += 2;
      r |= R_AMB_T;
    }
    if (in->riseValid && in->rise10 >= scaleTh(TH_AMB_RISE_X10, sens)) {
      s += 1;
      r |= R_AMB_RISE;
    }
    if (in->dropValid && in->drop10 >= scaleTh(TH_RH_DROP_X10, sens)) {
      s += 1;
      r |= R_RH_DROP;
    }
  }
  if (reasons) *reasons = r;
  return s;
}

uint8_t detEvaluate(Detector *d, const Reading *r, uint32_t now, uint8_t sens, bool allowBaseline) {
  ScoreInput in;
  memset(&in, 0, sizeof(in));
  in.thermalOk = r->thermalOk;
  in.maxT10 = r->maxT10;
  in.median10 = r->median10;
  in.hotCount = r->hotCount;
  in.envOk = r->envOk;
  in.temp10 = r->temp10;

  // --- Gecmisten hiz ve 5 dk degisimleri (penceredeki en buyuk artis/dusus) ---
  for (uint8_t i = 0; i < d->histCount; i++) {
    const HistEntry *e = &d->hist[i];
    uint32_t age = now - e->t;
    if (age == 0 || age > DET_WINDOW_S) continue;
    if (r->thermalOk && (e->flags & 1u) && age >= DET_RATE_MIN_AGE_S) {
      int16_t rate = (int16_t)(((int32_t)r->maxT10 - e->maxT10) * 60 / (int32_t)age);
      if (!in.rateValid || rate > in.rate10) in.rate10 = rate;
      in.rateValid = true;
    }
    if (r->envOk && (e->flags & 2u)) {
      int16_t rise = (int16_t)(r->temp10 - e->temp10);
      int16_t drop = (int16_t)(e->rh10 - r->rh10);
      if (!in.riseValid || rise > in.rise10) in.rise10 = rise;
      if (!in.dropValid || drop > in.drop10) in.drop10 = drop;
      in.riseValid = in.dropValid = true;
    }
  }

  // --- Gaz orani ---
  bool warm = (now - d->gasWarmStart) >= DET_GAS_WARMUP_S;
  int16_t ratio = -1;
  if (r->gasOk && r->gasOhm >= 100) {
    if (!d->gasBaseValid || d->gasBase < 100) {
      d->gasBase = r->gasOhm;  // ilk okuma / KALIBRE sonrasi tohum
      d->gasBaseValid = true;
      ratio = 1000;
    } else {
      uint32_t pm = (r->gasOhm * 10UL) / (d->gasBase / 100UL);  // binde, %1 hassasiyet
      ratio = (int16_t)(pm > 9999UL ? 9999UL : pm);
      in.gasValid = warm;
      in.gasPm = (uint16_t)ratio;
    }
  }

  d->score = detScore(&in, sens, &d->reasons);
  d->gasPm = ratio;
  d->rate10 = in.rateValid ? in.rate10 : 0;
  d->rise10 = in.riseValid ? in.rise10 : 0;
  d->drop10 = in.dropValid ? in.drop10 : 0;

  // --- Taban guncelleme (EMA), yalniz NORMAL durumda ---
  if (ratio > 0 && allowBaseline) {
    int32_t delta = (int32_t)r->gasOhm - (int32_t)d->gasBase;
    if (!warm) d->gasBase = (uint32_t)((int32_t)d->gasBase + delta / DET_GAS_ALPHA_WARM_DIV);
    else if (ratio > DET_GAS_UPDATE_MIN_PM)
      d->gasBase = (uint32_t)((int32_t)d->gasBase + delta / DET_GAS_ALPHA_DIV);
  }

  // --- Gecmise ekle ---
  bool push = d->histCount == 0;
  if (!push) {
    uint8_t last = (uint8_t)((d->histHead + DET_HIST_LEN - 1) % DET_HIST_LEN);
    push = (now - d->hist[last].t) >= DET_HIST_SPACING_S;
  }
  if (push && (r->thermalOk || r->envOk)) {
    HistEntry *e = &d->hist[d->histHead];
    e->t = now;
    e->maxT10 = r->thermalOk ? r->maxT10 : 0;
    e->temp10 = r->envOk ? r->temp10 : 0;
    e->rh10 = r->envOk ? r->rh10 : 0;
    e->flags = (uint8_t)((r->thermalOk ? 1u : 0u) | (r->envOk ? 2u : 0u));
    d->histHead = (uint8_t)((d->histHead + 1) % DET_HIST_LEN);
    if (d->histCount < DET_HIST_LEN) d->histCount++;
  }
  return d->score;
}
