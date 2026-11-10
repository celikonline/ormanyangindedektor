# ON1-DIY Rev A — Netlist ve pin eşleme

Bu dosya `tools/build.py` tarafından `tools/design.py`'den üretilir (elle düzenlemeyin).
Kart: 100 × 75 mm, tek katman (alt bakır), parçalar üstte. Koordinatlar mm, sol-alt köşe (0,0), üstten bakış.

## 1. Arduino pini ↔ modül pini ↔ kart (SPEC.md §3 ile birebir)

| Arduino | Pro Mini pin | SPEC sinyali | Kart üzerinde | SPEC'e uygun |
|---|---|---|---|---|
| D0 | RXI | FTDI_RX | FTDI başlığı (modül üzerinde) | ✔ |
| D1 | TXO | FTDI_TX | FTDI başlığı (modül üzerinde) | ✔ |
| D2 | D2 | TAMPER_N | R24 1 MΩ→3V3, C13 100 nF, SW1 SW-18010P, J8 kapak reed (NC) | ✔ |
| D3 | D3 | MODEM_RI_N | U3 HV1 ↔ LV1 → J2 RI | ✔ |
| D4 | D4 | MODEM_PWRKEY | R4 4,7 kΩ → Q4 2N3904 bazı (R5 100 kΩ), Q4 kollektör → J2 PWRKEY | ✔ |
| D5 | D5 | MODEM_DTR | U3 HV2 ↔ LV2 → J2 DTR | ✔ |
| D6 | D6 | LED_STROBE | R6 100 Ω → Q3 IRLZ44N kapı, R7 100 kΩ pull-down | ✔ |
| D7 | D7 | MODEM_TXD→MCU_RX | U3 HV3 ↔ LV3 → J2 TXD | ✔ |
| D8 | D8 | MCU_TX→MODEM_RXD | U3 HV4 ↔ LV4 → J2 RXD | ✔ |
| D9 | D9 | SIREN_EN | R15 10 kΩ → Q7 2N3904 (R16 100 kΩ) → Q6 AO3401A → MT3608 VIN | ✔ |
| D10 | D10 | MODEM_PWR_EN | R2 10 kΩ → Q5 2N3904 (R3 100 kΩ) → Q1 AO3401A kapı (R1 100 kΩ) | ✔ |
| D11 | D11 | SENSOR_PWR_N | Q2 AO3401A kapı doğrudan, R21 100 kΩ pull-up | ✔ |
| D12 | D12 | STATUS_LED | R25 1 kΩ → LED1 yeşil | ✔ |
| D13 | D13 | CHG_INHIBIT | R27 100 Ω → Q8 2N7000 (R28 100 kΩ) → TP1 MPPT | ✔ |
| A0 | A0 | VBAT_SENSE | R17 1 MΩ / R18 330 kΩ + C3 100 nF | ✔ |
| A1 | A1 | SOLAR_SENSE | R19 1 MΩ / R20 150 kΩ + C4 100 nF | ✔ |
| A2 | A2 | TEST_REED_N | J9 TEST (iç pull-up) | ✔ |
| A3 | A3 | CHG_STAT_N | D2 BAT85 → TP2 CHRG (iç pull-up) | ✔ |
| A4 | A4 | I2C_SDA | J4 SDA, R22 4,7 kΩ → V_SNS | ✔ |
| A5 | A5 | I2C_SCL | J4 SCL, R23 4,7 kΩ → V_SNS | ✔ |
| A6 | A6 | — | boş | ✔ |
| A7 | A7 | BAT_NTC | R26 220 kΩ → 3V3, C14 100 nF, J10 NTC 10k B3950 | ✔ |

Pro Mini besleme: **VCC ← +3V3 (U6 MCP1700)**, GND (iki GND pini modül içinde birleşik), RAW ve RST boş.
Firmware hiçbir değişiklik gerektirmez.

### Seviye çevirici (U3) kanal eşlemesi

SPEC §4.3'teki dört sinyal çifti aynen korunmuştur; yalnızca modül üzerindeki fiziksel kanal numarası,
Pro Mini ile modül arasındaki dört hattın kesişmeden düz gidebilmesi için seçilmiştir (BSS138 kanalları özdeştir):

| SPEC kanalı | Sinyal | Modül HV pini | Modül LV pini | J2 pini |
|---|---|---|---|---|
| (1) | MODEM_TXD → D7 | HV3 | LV3 | J2.6 |
| (2) | D8 → MODEM_RXD | HV4 | LV4 | J2.5 |
| (3) | D5 → DTR | HV2 | LV2 | J2.7 |
| (4) | RI → D3 | HV1 | LV1 | J2.8 |
| — | HV = +3V3, LV = VDD_EXT (1,8 V, modemden) | HV | LV | J2.2 |

## 2. Konnektörler

- **J1 — Güneş paneli 6 V (5,08 mm klemens)**: 1 (-): GND; 2 (SOL+): SOL_IN
- **J2 — A7670E kartı (1×9 pin header, 2,54 mm)**: 1 (VMOD): VMODEM; 2 (VEXT): VDD_EXT; 3 (GND): GND; 4 (GND): GND; 5 (RXD): M_RXD; 6 (TXD): M_TXD; 7 (DTR): M_DTR; 8 (RI): M_RI; 9 (PWRK): M_PWRKEY
- **J3 — Pil 1S2P (5,08 mm klemens)**: 1 (B-): CELL_N; 2 (B+): PACK_P
- **J4 — Sensör kablosu AMG8833 + BME680 (1×4, 2,54 mm)**: 1 (VSNS): V_SNS; 2 (SCL): SCL; 3 (SDA): SDA; 4 (GND): GND
- **J5 — LED halka (5,08 mm klemens)**: 1 (K): LED_K; 2 (K): LED_K; 3 (A1): LED_A1; 4 (A2): LED_A2
- **J6 — LED halka (5,08 mm klemens)**: 1 (A3): LED_A3; 2 (A4): LED_A4; 3 (A5): LED_A5; 4 (A6): LED_A6
- **J7 — Siren 12 V (5,08 mm klemens)**: 1 (+12V): SIREN_P; 2 (GND): GND
- **J8 — Kapak reed anahtarı NC/Form-B (5,08 mm klemens)**: 1 (TMP): TAMPER_N; 2 (GND): GND
- **J9 — Test reed anahtarı (5,08 mm klemens)**: 1 (TEST): A2_TEST; 2 (GND): GND
- **J10 — Pil NTC 10k B3950 (1×2, 2,54 mm)**: 1 (NTC): A7_NTC; 2 (GND): GND
- **U4 — CN3791 MPPT modülü (kablo pedleri)**: IN+: SOL_P; IN-: GND; BAT-: GND; BAT+: PACK_P
- **U5 — 1S koruma modülü (kablo pedleri; P+ = B+)**: B+: PACK_P; P-: GND; B-: CELL_N
- **U7 — MT3608 modülü (kablo pedleri)**: VIN+: SIR_VIN; VIN-: GND; OUT+: SIREN_P; OUT-: GND
- **TP1 — CN3791 MPPT bölücü orta noktası (tel)**: 1 (MPPT): MPPT_INH
- **TP2 — CN3791 CHRG LED katodu (tel)**: 1 (CHRG): CHRG_K

## 3. Net → ped listesi

| Net | Hat genişliği | Pedler |
|---|---|---|
| GND | 1.5 mm | C1.-, C10.-, C11.-, C12.1, C13.1, C14.2, C2.1, C3.1, C4.1, C5.1, C6.2, C8.1, C9.1, J1.1, J10.2, J2.3, J2.4, J4.4, J7.2, J8.2, J9.2, LED1.K, Q3.S, Q4.E, Q5.E, Q7.E, Q8.S, R16.1, R18.2, R20.2, R28.2, R3.2, R5.2, R7.1, SW1.2, TVS1.A, U1.GND, U1.GND2, U3.GNDH, U3.GNDL, U4.BAT-, U4.IN-, U5.P-, U6.GND, U7.OUT-, U7.VIN-, J-W12, J-W13, J-W14, J-W15, J-W16 + bakır döküm (pour) |
| VBAT | 1.5 mm | C5.2, F1.2, Q1.S, Q6.S, R1.1, R10.1, R11.1, R12.1, R13.1, R14.2, R17.2, R8.1, R9.1, U6.VIN, J-W1, J-W2 |
| +3V3 | 0.8 mm | C6.1, Q2.S, R21.1, R24.1, R26.2, U1.VCC, U3.HV, U6.VOUT, J-W3, J-W4 |
| A0_VBAT | 0.8 mm | C3.2, R17.1, R18.1, U1.A0 |
| A1_SOLAR | 0.8 mm | C4.2, R19.1, R20.1, U1.A1, J-W5 |
| A2_TEST | 0.8 mm | J9.1, U1.A2, J-W6, J-W7, J-W8 |
| A3_CHG | 0.8 mm | D2.A, U1.A3 |
| A7_NTC | 0.8 mm | C14.1, J10.1, R26.1, U1.A7 |
| CELL_N | 1.5 mm | J3.1, U5.B- |
| CHRG_K | 0.8 mm | D2.K, TP2.1 |
| D10_MODEM_EN | 0.8 mm | R2.2, U1.D10, J-W9 |
| D11_SNS_N | 0.8 mm | Q2.G, R21.2, U1.D11, J-W10 |
| D12_LED | 0.8 mm | R25.1, U1.D12 |
| D13_CHG_INH | 0.8 mm | R27.2, U1.D13 |
| D3_RI | 0.8 mm | U1.D3, U3.HV1 |
| D4_PWRKEY | 0.8 mm | R4.2, U1.D4, J-W11 |
| D5_DTR | 0.8 mm | U1.D5, U3.HV2 |
| D6_STROBE | 0.8 mm | R6.2, U1.D6 |
| D7_RX | 0.8 mm | U1.D7, U3.HV3 |
| D8_TX | 0.8 mm | U1.D8, U3.HV4 |
| D9_SIREN | 0.8 mm | R15.2, U1.D9 |
| LED_A1 | 1.0 mm | J5.3, R8.2 |
| LED_A2 | 1.0 mm | J5.4, R9.2 |
| LED_A3 | 1.0 mm | J6.1, R10.2 |
| LED_A4 | 1.0 mm | J6.2, R11.2 |
| LED_A5 | 1.0 mm | J6.3, R12.2 |
| LED_A6 | 1.0 mm | J6.4, R13.2 |
| LED_K | 1.5 mm | J5.1, J5.2, Q3.D |
| LED_ST | 0.8 mm | LED1.A, R25.2 |
| MPPT_INH | 0.8 mm | Q8.D, TP1.1 |
| M_DTR | 0.8 mm | J2.7, U3.LV2 |
| M_PWRKEY | 0.8 mm | J2.9, Q4.C |
| M_RI | 0.8 mm | J2.8, U3.LV1 |
| M_RXD | 0.8 mm | J2.5, U3.LV4 |
| M_TXD | 0.8 mm | J2.6, U3.LV3 |
| PACK_P | 1.5 mm | F1.1, J3.2, U4.BAT+, U5.B+ |
| Q1_G | 0.8 mm | Q1.G, Q5.C, R1.2 |
| Q3_G | 0.8 mm | Q3.G, R6.1, R7.2 |
| Q4_B | 0.8 mm | Q4.B, R4.1, R5.1 |
| Q5_B | 0.8 mm | Q5.B, R2.1, R3.1 |
| Q6_G | 0.8 mm | Q6.G, Q7.C, R14.1 |
| Q7_B | 0.8 mm | Q7.B, R15.1, R16.2 |
| Q8_G | 0.8 mm | Q8.G, R27.1, R28.1 |
| SCL | 0.8 mm | J4.2, R23.1, U1.A5 |
| SDA | 0.8 mm | J4.3, R22.1, U1.A4 |
| SIREN_P | 0.8 mm | J7.1, U7.OUT+ |
| SIR_VIN | 1.0 mm | Q6.D, U7.VIN+ |
| SOL_IN | 1.5 mm | D1.A, J1.2 |
| SOL_P | 1.5 mm | C1.+, C2.2, D1.K, R19.2, TVS1.K, U4.IN+ |
| TAMPER_N | 0.8 mm | C13.2, J8.1, R24.2, SW1.1, U1.D2 |
| VDD_EXT | 0.8 mm | J2.2, U3.LV |
| VMODEM | 1.5 mm | C10.+, C11.+, C12.2, J2.1, Q1.D |
| V_SNS | 0.8 mm | C8.2, C9.2, J4.1, Q2.D, R22.2, R23.2 |

Bağlantısız pinler: U1 RXI, TXO (FTDI başlığında), RST×2, RAW, A6.

## 4. Atlama telleri (üst yüz)

| Ref | Net | Uç 1 (x, y) | Uç 2 (x, y) | Boy | Ara lehim noktaları |
|---|---|---|---|---|---|
| J-W1 | VBAT | 50.80, 16.50 | 10.16, 16.50 | 40.64 mm (16 × 2,54) | (45.72, 16.50), (27.94, 16.50), (17.78, 16.50) |
| J-W2 | VBAT | 67.06, 51.56 | 67.06, 31.24 | 20.32 mm (8 × 2,54) | — |
| J-W3 | +3V3 | 37.34, 50.80 | 44.96, 50.80 | 7.62 mm (3 × 2,54) | — |
| J-W4 | +3V3 | 7.87, 62.48 | 28.19, 62.48 | 20.32 mm (8 × 2,54) | — |
| J-W5 | A1_SOLAR | 75.95, 62.23 | 65.79, 62.23 | 10.16 mm (4 × 2,54) | — |
| J-W6 | A2_TEST | 77.98, 68.33 | 65.28, 68.33 | 12.70 mm (5 × 2,54) | — |
| J-W7 | A2_TEST | 49.53, 64.26 | 49.53, 54.10 | 10.16 mm (4 × 2,54) | — |
| J-W8 | A2_TEST | 49.28, 53.85 | 54.36, 53.85 | 5.08 mm (2 × 2,54) | — |
| J-W9 | D10_MODEM_EN | 38.86, 39.12 | 56.64, 39.12 | 17.78 mm (7 × 2,54) | — |
| J-W10 | D11_SNS_N | 60.71, 35.05 | 60.71, 42.67 | 7.62 mm (3 × 2,54) | — |
| J-W11 | D4_PWRKEY | 37.08, 66.29 | 37.08, 56.13 | 10.16 mm (4 × 2,54) | — |
| J-W12 | GND | 78.49, 52.58 | 83.57, 52.58 | 5.08 mm (2 × 2,54) | — |
| J-W13 | GND | 78.49, 34.80 | 91.19, 34.80 | 12.70 mm (5 × 2,54) | — |
| J-W14 | GND | 68.07, 35.31 | 73.15, 35.31 | 5.08 mm (2 × 2,54) | — |
| J-W15 | GND | 62.23, 29.97 | 69.85, 29.97 | 7.62 mm (3 × 2,54) | — |
| J-W16 | GND | 54.61, 25.15 | 44.45, 25.15 | 10.16 mm (4 × 2,54) | — |

Modül içi bağlantılar (bağlantı kontrolünde kullanıldı): U1 GND ↔ GND (Pro Mini üzerinde), U3 GND(LV) ↔ GND(HV) (seviye çevirici üzerinde).

## 5. Seri üretim kartından (ON1-MB Rev A) farklar

- MCU: çıplak ATmega328P-AU yerine **Arduino Pro Mini 3V3/8 MHz** modülü (aynı çip, aynı pin numaraları, Optiboot). FTDI başlığı modülün üzerindedir; ISP başlığı yoktur (gerekirse modülün D11/D12/D13/RST pinlerinden).
- Modem: LGA A7670E yerine **A7670E breakout kartı**, J2 (1×9) ile kablolu. SIM tutucu, anten (U.FL) ve SIM ESD koruması breakout kartın üzerindedir. VMODEM dekuplajı: 2 × 470 µF düşük ESR **elektrolitik** (+100 nF); polimer kondansatör, 33 pF/10 pF ve ESD5Z5.0 yoktur.
- Seviye çevirici: 4 × ayrık BSS138 yerine hazır 4 kanallı BSS138 modülü (10 k pull-up'lar modülde). Fiziksel kanal sırası düz hat için seçildi (§1).
- Şarj: CN3791 devresi (AO3401A, SS34, 22 µH, 0,24 Ω) yerine **hazır CN3791 MPPT modülü**; koruma DW01A+FS8205A yerine hazır **1S koruma modülü**. Pil sıcaklık koruması SPEC güncellemesine uygun olarak MCU'da (A7 NTC + D13 → Q8 → MPPT).
- Ters polarite diyodu SS34 → **1N5822** (THT), TVS SMBJ7.0A → **P6KE8.2A** (THT, Vrwm 7,02 V; P6KE6.8A Vrwm 5,8 V olduğundan panel boşta gerilimini kırpardı — kullanılmadı). PTC 1812 → radyal **RXEF300**.
- Siren: MT3608 entegre devresi + EN pini yerine **MT3608 modülü**; modülde EN pini olmadığı için VIN, Q6 AO3401A ile anahtarlanır (Q7 2N3904 sürücü, D9 HIGH = siren açık — davranış SPEC ile aynı). Modül FB referansı 0,6 V; çıkış trimpotla 12 V.
- LED strob anahtarı AO3400A (SOT-23) → **IRLZ44N** (TO-220, mantık seviyeli). 3,3 V kapı sürüşünde ~1,8 A için yeterli (tipik R_DS(on) < 0,06 Ω @ 3 V). Daha düşük R_DS(on) isterseniz aynı bacak dizilişli **IRLB8721PbF** takılabilir.
- 2N3904 sürücülerin (Q4, Q5, Q7) bazlarına 100 kΩ pull-down eklendi (reset sırasında modem/siren açılmasın).
- MCP1700 SOT-23 → **TO-92** (MCP1700-3302E/TO).
- Sensörler (AMG8833, BME680) ayrı breakout kartlardadır; J4 (1×4) kablosuyla bağlanır. I2C pull-up'lar ve V_SNS anahtarı (Q2) bu karttadır.
- Kart 2 katman 78 × 58 mm yerine **1 katman 100 × 75 mm**; konformal kaplama yerine kalaylama + (isteğe bağlı) şeffaf vernik. Gerekli yerlerde üst yüzde **atlama telleri** (J-Wn).
- Kapak reed anahtarı **NC (Form-B)** olmalıdır (titreşim anahtarına paralel, D2'yi GND'ye çeker).
