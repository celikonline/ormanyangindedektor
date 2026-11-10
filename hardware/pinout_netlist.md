# ON1-MB Rev A — Pin ve Bağlantı (Netlist) Tablosu

**Orman Nöbetçisi ON-1** — ana kart ON1-MB Rev A + sensör kartı SNS-1 + kart dışı demetler.  
Tarih: 2026-11-10 • Kaynak: `SPEC.md` Rev A • Şema: `schematic/ON1-MB_RevA_schematic_sheet1/2.svg`

> Bu tablo, şema çiziminden **otomatik çıkarılmıştır** (`hardware/tools/gen_schematic.py` → `gen_docs.py`). Şemadaki her tel, pin, güç sembolü ve net etiketi birleştirilerek bağlantılar hesaplanır; ERC kontrolü (tek uçlu net, açık uçlu tel, çakışan isim): **0 sorun**.

Gösterim: `U1:23 (PC0/ADC0 [A0])` = U1’in 23 numaralı pini (pin adı). `(kablo ucu)` = konektörün kablo tarafı.

## 1. SPEC Rev A’ya göre düzeltmeler (şemaya işlendi)

| # | Düzeltme |
|---|---|
| Δ1 | CN3791’de TEMP/NTC pini yok (SSOP-10: VG, GND, CHRG, DONE, COM, MPPT, BAT, CSP, VCC, DRV). NTC → J3 → R11 220k bölücü → A7 (ADC7); şarj kesme: D13 → Q12 BSS138 → MPPT pini GND. |
| Δ2 | J2 batarya konektörü JST-PH (2 A) yerine JST-VH 2p (10 A): LED strob 1,8–2,5 A + modem 2 A darbe. |
| Δ3 | MT3608 VREF = 0,6 V: 200k/18k → 7,27 V verir. 12 V için R50 = 10,5 kΩ %1 (12,03 V). |
| Δ4 | Boost EN=LOW iken çıkış ≈ VBAT−0,4 V kalır, siren zayıf öter/akım çeker → Q11 AO3400A alçak taraf anahtar (D9). |
| Δ5 | NETLIGHT 1,8 V çıkış mavi LED’i (Vf≈2,9 V) süremez → Q13 MMBT3904 + LED3/R29 VMODEM’den (DNP). |
| Δ6 | Kapak reed’i paralel bağlıyken kapak açılınca LOW vermesi için NC (Form-B/C) olmalı; spec’te NO yazıyor. |
| Δ7 | Q4/Q5 baz pull-down 100 kΩ (R23/R21) eklendi: reset/ISP sırasında modem kendiliğinden açılmasın. |

## 2. Güç netleri

| Net | Uç sayısı | Uçlar |
|---|---|---|
| **GND** | 85 | C1:2, C2:2, C5:2, C6:2, C9:2, C10:2, C11:2, C12:2, C13:2, C14:2, C15:2, C16:2, C17:2, C18:2, C19:2, C20:2, C21:2, C22:2, C23:2, C24:2, C26:2, C27:2, C28:2, C29:2, C30:2, C31:2, C32:2, C33:2, C34:2, C35:2, C36:2, C101:2, C103:2, C104:2, C105:2, D2:A, J1:2 (PV−), J3:2 (GND), J4:2 (GND), J4:4 (GND), J6:1 (GND), J6:2 (CTS), J7:6 (GND), J9:2 (GND), J10:2 (GND), J11:C5 (GND), J12:GND, J101:2 (GND), J101:4 (GND), LED1:K, Q3:S, Q4:E, Q5:E, Q11:S, Q12:S, Q13:E, R5:2, R7:2, R10:2, R16:2, R18:2, R21:2, R23:2, R48:2, R50:2, R51:2, R101:2, SW1:2, TVS1:A, TVS2:A, U1:3 (GND), U1:5 (GND), U1:21 (GND), U2:2 (GND), U2:17 (GND), U2:18 (GND), U3:2 (GND), U4:1 (GND), U5:2 (GND), U7:6 (GND), U8:1 (GND), U8:7 (GND), U9:6 (S2), U9:7 (S2), U10:2 (GND) |
| **VBAT** | 16 | C15:1, C16:1, C35:1, F1:1, L2:2, Q1:S, R15:1, R19:1, R41:1, R42:1, R43:1, R44:1, R45:1, R46:1, U4:3 (VIN), U5:5 (IN) |
| **BAT+** | 6 | C6:1, F1:2, J2:1 (B+), R6:1, R9:1, U3:7 (BAT) |
| **SOLAR_IN** | 5 | D1:A, J1:1 (PV+), R4:1, R17:1, TVS1:K |
| **3V3** | 21 | C17:1, C18:1, C19:1, C20:1, C21:1, J6:3 (3V3), J7:2 (VCC), Q2:S, R8:1, R11:1, R12:1, R14:1, R34:1, R35:1, R36:1, R37:1, R38:1, U1:4 (VCC), U1:6 (VCC), U1:18 (AVCC), U4:2 (VOUT) |
| **V_SNS** | 17 | C33:1, C34:1, C101:1, C104:1, C105:1, J4:1 (V_SNS), J101:1 (V_SNS), Q2:D, R39:1, R40:1, U7:5 (AD_SELECT), U7:9 (VDD), U7:13 (VPP), U8:2 (CSB), U8:5 (SDO), U8:6 (VDDIO), U8:8 (VDD) |
| **VMODEM** | 11 | C10:1, C11:1, C12:1, C13:1, C14:1, Q1:D, R29:1, TVS2:K, U2:55 (VBAT), U2:56 (VBAT), U2:57 (VBAT) |
| **VDD_EXT** | 9 | Q6:G, Q7:G, Q8:G, Q9:G, R30:1, R31:1, R32:1, R33:1, U2:15 (VDD_EXT (1V8)) |
| **V12** | 4 | C36:1, D3:K, J5:1 (+12V), R49:1 |

## 3. Sinyal netleri (isimli)

| Net | Uçlar |
|---|---|
| **AMG_INT** | J101:6 (INT), U7:4 (INT) |
| **BAT_NTC** | C9:1, J3:1 (NTC), R11:2, U1:22 (ADC7 [A7]) |
| **BAT−** | C7:2, J2:2 (B−), U6:6 (GND), U9:2 (S1), U9:3 (S1) |
| **CHG_INHIBIT** | J7:3 (SCK), Q12:G, R7:1, U1:17 ([D13] PB5/SCK) |
| **CHG_STAT_N** | LED2:K, U1:26 (PC3/ADC3 [A3]), U3:3 (CHRG) |
| **CSP** | L1:1, R6:2, U3:8 (CSP) |
| **FB** | R49:2, R50:1, U5:3 (FB) |
| **FTDI_DTR** | C25:2, J6:6 (DTR) |
| **FTDI_RX** | J6:4 (RXI), U1:30 ([D0] PD0/RXD) |
| **FTDI_TX** | J6:5 (TXO), U1:31 ([D1] PD1/TXD) |
| **I2C_SCL** | J4:5 (SCL), J101:5 (SCL), R40:2, U1:28 ([A5] PC5/SCL), U7:3 (SCL), U8:4 (SCK) |
| **I2C_SDA** | J4:3 (SDA), J101:3 (SDA), R39:2, U1:27 ([A4] PC4/SDA), U7:2 (SDA), U8:3 (SDI) |
| **LED_K** | J8:7 (K), J8:8 (K), Q3:D |
| **LED_STROBE** | R47:2, U1:10 ([D6] PD6/OC0A) |
| **MCU_RX_MDM** | Q6:D, R34:2, U1:11 ([D7] PD7) |
| **MCU_TX_MDM** | Q7:D, R35:2, U1:12 ([D8] PB0) |
| **MDM_DTR_1V8** | Q8:S, R32:2, U2:3 (DTR) |
| **MDM_NETLIGHT** | R28:1, U2:52 (NETLIGHT) |
| **MDM_RI_1V8** | Q9:S, R33:2, U2:4 (RI) |
| **MDM_RXD_1V8** | Q7:S, R31:2, U2:10 (RXD) |
| **MDM_TXD_1V8** | Q6:S, R30:2, U2:9 (TXD) |
| **MODEM_DTR** | Q8:D, R36:2, U1:9 ([D5] PD5) |
| **MODEM_PWRKEY** | R22:2, U1:2 ([D4] PD4) |
| **MODEM_PWR_EN** | R20:2, U1:14 ([D10] PB2) |
| **MODEM_RI_N** | Q9:D, R37:2, U1:1 ([D3] PD3/INT1) |
| **MPPT** | Q12:D, R4:2, R5:1, U3:6 (MPPT) |
| **Q1_GATE** | Q1:G, Q5:C, R19:2 |
| **RESET_N** | C25:1, J7:5 (RST), R12:2, U1:29 (PC6/RESET) |
| **SENSOR_PWR_N** | J7:4 (MOSI), Q2:G, R38:2, U1:15 ([D11] PB3/MOSI) |
| **SIM_CLK** | J11:C3 (CLK), R25:1, U10:4 (IO3) |
| **SIM_DATA** | J11:C7 (I/O), R24:1, U10:3 (IO2) |
| **SIM_RST** | J11:C2 (RST), R26:1, U10:5 (IO4) |
| **SIM_VDD** | C29:1, C30:1, J11:C1 (VCC), U2:30 (USIM_VDD), U10:1 (IO1) |
| **SIREN_EN** | R51:1, R52:2, U1:13 ([D9] PB1), U5:4 (EN) |
| **SIREN_N** | J5:2 (SİREN−), Q11:D |
| **SOLAR_SENSE** | C28:1, R17:2, R18:1, U1:24 (PC1/ADC1 [A1]) |
| **STATUS_LED** | J7:1 (MISO), R13:1, U1:16 ([D12] PB4/MISO) |
| **SW_BST** | D3:A, L2:1, U5:1 (SW) |
| **SW_CHG** | D2:K, L1:2, Q10:D |
| **TAMPER_N** | C26:1, J9:1 (LID), R14:2, SW1:1, U1:32 ([D2] PD2/INT0) |
| **TEST_REED_N** | J10:1 (TEST), U1:25 (PC2/ADC2 [A2]) |
| **VBAT_SENSE** | C27:1, R15:2, R16:1, U1:23 (PC0/ADC0 [A0]) |
| **VIN_CHG** | C1:1, C2:1, C4:1, D1:K, Q10:S, U3:9 (VCC) |

## 4. Yerel (isimsiz) netler — kart üzeri

İsimsiz netler ilk uca göre adlandırılır (`N_<ref>_<pin>`).

| Net | Uçlar |
|---|---|
| N_C4_2 | C4:2, U3:1 (VG) |
| N_C5_1 | C5:1, R3:2 |
| N_C7_1 | C7:1, R9:2, U6:5 (VCC) |
| N_C22_1 | C22:1, U1:20 (AREF) |
| N_C23_1 | C23:1, U1:7 (PB6/XTAL1), Y1:1 |
| N_C24_1 | C24:1, U1:8 (PB7/XTAL2), Y1:2 |
| N_C31_1 | C31:1, R27:2, U2:60 (RF_ANT) |
| N_C32_1 | C32:1, J12:SIG, R27:1 |
| N_C102_1 | C102:1, U7:10 (AVDD-PC) |
| N_C102_2 | C102:2, R101:1 |
| N_C103_1 | C103:1, U7:12 (DVDD-PC) |
| N_J8_1 | J8:1 (A1), R41:2 |
| N_J8_2 | J8:2 (A2), R42:2 |
| N_J8_3 | J8:3 (A3), R43:2 |
| N_J8_4 | J8:4 (A4), R44:2 |
| N_J8_5 | J8:5 (A5), R45:2 |
| N_J8_6 | J8:6 (A6), R46:2 |
| N_LED1_A | LED1:A, R13:2 |
| N_LED2_A | LED2:A, R8:2 |
| N_LED3_A | LED3:A, R29:2 |
| N_LED3_K | LED3:K, Q13:C |
| N_Q3_G | Q3:G, R47:1, R48:1 |
| N_Q4_B | Q4:B, R22:1, R23:1 |
| N_Q4_C | Q4:C, U2:1 (PWRKEY) |
| N_Q5_B | Q5:B, R20:1, R21:1 |
| N_Q10_G | Q10:G, U3:10 (DRV) |
| N_Q11_G | Q11:G, R52:1 |
| N_Q13_B | Q13:B, R28:2 |
| N_R3_1 | R3:1, U3:5 (COM) |
| N_R10_1 | R10:1, U6:2 (CS) |
| N_R24_2 | R24:2, U2:31 (USIM_DATA) |
| N_R25_2 | R25:2, U2:32 (USIM_CLK) |
| N_R26_2 | R26:2, U2:33 (USIM_RST) |
| N_TP1_1 | TP1:1 (USB_VBUS), U2:24 (USB_VBUS) |
| N_TP2_1 | TP2:1 (USB_DP), U2:27 (USB_DP) |
| N_TP3_1 | TP3:1 (USB_DM), U2:28 (USB_DM) |
| N_TP4_1 | TP4:1 (USB_BOOT), U2:6 (USB_BOOT) |
| N_TP5_1 | TP5:1 (LOG_TX), U2:23 (UART_LOG_TX) |
| N_U6_1 | U6:1 (OD), U9:4 (G1) |
| N_U6_3 | U6:3 (OC), U9:5 (G2) |
| N_U9_1 | U9:1 (D), U9:8 (D) |

## 5. Kablo / kart dışı bağlantılar

| Net | Uçlar |
|---|---|
| N_ANT1_1 | ANT1:1, J12:SIGR |
| N_BT1_+ | BT1:+, BT2:+, J2:1 (kablo ucu) |
| N_BT1_- | BT1:-, BT2:-, J2:2 (kablo ucu) |
| N_J1_1k | J1:1 (kablo ucu), PV1:+ |
| N_J1_2k | J1:2 (kablo ucu), PV1:- |
| N_J3_1k | J3:1 (kablo ucu), NTC1:1 |
| N_J3_2k | J3:2 (kablo ucu), NTC1:2 |
| N_J5_1k | J5:1 (kablo ucu), SR1:1 |
| N_J5_2k | J5:2 (kablo ucu), SR1:2 |
| N_J8_1k | J8:1 (kablo ucu), LD1:A |
| N_J8_2k | J8:2 (kablo ucu), LD2:A |
| N_J8_3k | J8:3 (kablo ucu), LD3:A |
| N_J8_4k | J8:4 (kablo ucu), LD4:A |
| N_J8_5k | J8:5 (kablo ucu), LD5:A |
| N_J8_6k | J8:6 (kablo ucu), LD6:A |
| N_J8_7k | J8:7 (kablo ucu), J8:8 (kablo ucu), LD1:K, LD2:K, LD3:K, LD4:K, LD5:K, LD6:K |
| N_J9_1k | J9:1 (kablo ucu), SW2:1 |
| N_J9_2k | J9:2 (kablo ucu), SW2:2 |
| N_J10_1k | J10:1 (kablo ucu), SW3:1 |
| N_J10_2k | J10:2 (kablo ucu), SW3:2 |
| N_J101_1k | J4:1 (kablo ucu), J101:1 (kablo ucu) |
| N_J101_2k | J4:2 (kablo ucu), J101:2 (kablo ucu) |
| N_J101_3k | J4:3 (kablo ucu), J101:3 (kablo ucu) |
| N_J101_4k | J4:4 (kablo ucu), J101:4 (kablo ucu) |
| N_J101_5k | J4:5 (kablo ucu), J101:5 (kablo ucu) |
| N_J101_6k | J4:6 (kablo ucu), J101:6 (kablo ucu) |

## 6. Konektör pin tabloları

### J1 — Güneş paneli girişi (JST-XH 2p, 2,50 mm)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | PV+ (panel +, kırmızı) | `SOLAR_IN` |
| 2 | PV− (panel −, siyah) | `GND` |

Panel kablosu PG7 rakordan girer. D1 SS34 seri ters polarite, TVS1 SMBJ7.0A paralel.

### J2 — Batarya (JST-VH 2p, 3,96 mm) — Δ2

| Pin | Sinyal | Net |
|---|---|---|
| 1 | B+ (2×18650 paralel +) | `BAT+` |
| 2 | B− (hücre −, FS8205A S1) | `BAT−` |

Hücre tarafı koruma öncesidir; sistem GND’si P− (FS8205A S2).

### J3 — Batarya NTC (JST-PH 2p) — Δ1

| Pin | Sinyal | Net |
|---|---|---|
| 1 | NTC (10k B3950) | `BAT_NTC` |
| 2 | GND | `GND` |

NTC hücreler arasına termal macun/kaptonla yapıştırılır.

### J4 — SNS-1 sensör kablosu, ana kart (JST-SH 6p, 1,00 mm)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | V_SNS (3,3 V anahtarlı) | `V_SNS` |
| 2 | GND | `GND` |
| 3 | I2C_SDA | `I2C_SDA` |
| 4 | GND | `GND` |
| 5 | I2C_SCL | `I2C_SCL` |
| 6 | AMG_INT (ana kartta NC) | `— (NC)` |

Kablo 1:1, ≈25 cm, SDA/SCL arasında GND tel (çapraz konuşma azaltma).

### J101 — SNS-1 kart tarafı (JST-SH 6p)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | V_SNS | `V_SNS` |
| 2 | GND | `GND` |
| 3 | I2C_SDA | `I2C_SDA` |
| 4 | GND | `GND` |
| 5 | I2C_SCL | `I2C_SCL` |
| 6 | AMG_INT (U7 pin 4) | `AMG_INT` |

### J5 — Siren (JST-XH 2p)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | +12V (V12, kırmızı) | `V12` |
| 2 | SİREN− (Q11 drenaj, siyah) | `SIREN_N` |

12 V 105 dB piezo siren ≈30 mA. Siren Q11 ile ayrılır (Δ4).

### J6 — FTDI programlama (1×6, 2,54 mm, Pro Mini sırası)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | GND | `GND` |
| 2 | CTS (GND) | `GND` |
| 3 | 3V3 | `3V3` |
| 4 | RXI ← FTDI TX | `FTDI_RX` |
| 5 | TXO → FTDI RX | `FTDI_TX` |
| 6 | DTR → C25 → RESET | `FTDI_DTR` |

Yalnızca 3,3 V FTDI kullanın; programlamada batarya takılı olmalı.

### J7 — AVR ISP (2×3, 2,54 mm)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | MISO (D12) | `STATUS_LED` |
| 2 | VCC 3V3 | `3V3` |
| 3 | SCK (D13) | `CHG_INHIBIT` |
| 4 | MOSI (D11) | `SENSOR_PWR_N` |
| 5 | RESET | `RESET_N` |
| 6 | GND | `GND` |

ISP sırasında D11 sensör rayını, D13 şarj kesmeyi kısa süre değiştirir — zararsız.

### J8 — LED strob halkası (JST-XH 8p)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | LED1 anot (R41 4,7 Ω → VBAT) | `N_J8_1` |
| 2 | LED2 anot (R42 4,7 Ω → VBAT) | `N_J8_2` |
| 3 | LED3 anot (R43 4,7 Ω → VBAT) | `N_J8_3` |
| 4 | LED4 anot (R44 4,7 Ω → VBAT) | `N_J8_4` |
| 5 | LED5 anot (R45 4,7 Ω → VBAT) | `N_J8_5` |
| 6 | LED6 anot (R46 4,7 Ω → VBAT) | `N_J8_6` |
| 7 | LED_K ortak katot | `LED_K` |
| 8 | LED_K ortak katot | `LED_K` |

Katot dönüşü 2 pine bölünmüştür (≈2,4 A tepe).

### J9 — Kapak reed anahtarı (JST-PH 2p) — Δ6

| Pin | Sinyal | Net |
|---|---|---|
| 1 | TAMPER_N | `TAMPER_N` |
| 2 | GND | `GND` |

Reed NC (Form-B) ya da Form-C’nin NC kontağı; kapak kapalıyken mıknatıs kontağı açık tutar.

### J10 — Test reed anahtarı (JST-PH 2p)

| Pin | Sinyal | Net |
|---|---|---|
| 1 | TEST_REED_N | `TEST_REED_N` |
| 2 | GND | `GND` |

Reed NO; alt PC kubbe kenarına yerleştirilir (teneke manyetik alanı zayıflatır).

### J11 — Nano-SIM (push-push)

| Pin | Sinyal | Net |
|---|---|---|
| C1 | VCC | `SIM_VDD` |
| C2 | RST | `SIM_RST` |
| C3 | CLK | `SIM_CLK` |
| C5 | GND | `GND` |
| C6 | VPP (NC) | `— (NC)` |
| C7 | I/O | `SIM_DATA` |

### J12 — U.FL anten

| Pin | Sinyal | Net |
|---|---|---|
| SIG | RF (π ağı üzerinden U2 pin 60) | `N_C32_1` |
| GND | GND | `GND` |

U.FL → 15 cm pigtail → SMA dişi bulkhead (O-ring) → 3 dBi IP67 LTE anten.

### Sensör kablosu J4 ↔ J101 (JST-SH 6p, 1:1)

| J4 pin | Tel rengi (öneri) | J101 pin | Sinyal |
|---|---|---|---|
| 1 | kırmızı | 1 | V_SNS |
| 2 | siyah | 2 | GND |
| 3 | mavi | 3 | I2C_SDA |
| 4 | siyah | 4 | GND |
| 5 | sarı | 5 | I2C_SCL |
| 6 | beyaz | 6 | AMG_INT |

### LED halkası (Al-MCPCB Ø50 mm, 6 × 1 W kırmızı 625 nm)

| Halka pedi | LED | Bağlantı | J8 pin |
|---|---|---|---|
| A1 | LD1 anot | R41 4,7 Ω 1 W → VBAT | 1 |
| A2 | LD2 anot | R42 4,7 Ω 1 W → VBAT | 2 |
| A3 | LD3 anot | R43 4,7 Ω 1 W → VBAT | 3 |
| A4 | LD4 anot | R44 4,7 Ω 1 W → VBAT | 4 |
| A5 | LD5 anot | R45 4,7 Ω 1 W → VBAT | 5 |
| A6 | LD6 anot | R46 4,7 Ω 1 W → VBAT | 6 |
| K | LD1–LD6 katot (ortak) | Q3 AO3400A drenaj → GND | 7, 8 |

Her LED ≈0,32 A @ 3,7 V (0,40 A @ 4,2 V); desen 60/90/60/790 ms (≈ %12 görev).

### Siren

| Siren teli | J5 pin | Net | Not |
|---|---|---|---|
| + (kırmızı) | 1 | V12 | MT3608 çıkışı 12,03 V (R49 200k / R50 10,5k) |
| − (siyah) | 2 | SIREN_N → Q11 | SIREN_EN (D9) HIGH → U5 EN + Q11 açık |

## 7. ATmega328P pin haritası (Arduino Pro Mini numaralandırması)

| Pin | AVR (TQFP#) | Net | Yön | Açıklama |
|---|---|---|---|---|
| D0 | PD0 (30) | FTDI_RX | G | FTDI başlığı J6.4 |
| D1 | PD1 (31) | FTDI_TX | Ç | FTDI başlığı J6.5 |
| D2 | PD2 (32) | TAMPER_N | G | SW1 ‖ SW2 → GND, 1 MΩ pull-up, INT0 |
| D3 | PD3 (1) | MODEM_RI_N | G | A7670E RI (Q9), INT1 uyandırma |
| D4 | PD4 (2) | MODEM_PWRKEY | Ç | Q4 MMBT3904 → PWRKEY, HIGH = basılı |
| D5 | PD5 (9) | MODEM_DTR | Ç | Q8 → DTR; HIGH = uyku izni |
| D6 | PD6 (10) | LED_STROBE | Ç | Q3 AO3400A (sayfa 1) |
| D7 | PD7 (11) | MCU_RX_MDM | G | SoftwareSerial RX ← A7670E TXD (Q6) |
| D8 | PB0 (12) | MCU_TX_MDM | Ç | SoftwareSerial TX → A7670E RXD (Q7) |
| D9 | PB1 (13) | SIREN_EN | Ç | U5 EN + Q11 kapı, 100 kΩ pull-down |
| D10 | PB2 (14) | MODEM_PWR_EN | Ç | Q5 → Q1 AO3401A, HIGH = modem açık |
| D11 | PB3 (15) | SENSOR_PWR_N | Ç | Q2 AO3401A kapı, LOW = sensör rayı açık |
| D12 | PB4 (16) | STATUS_LED | Ç | LED1 yeşil (R13 1 kΩ), ışık borusu |
| D13 | PB5 (17) | CHG_INHIBIT | Ç | Δ1 YENİ: Q12 → CN3791 MPPT, HIGH = şarj durur |
| A0 | PC0 (23) | VBAT_SENSE | An | 1 MΩ / 330 kΩ, oran 0,2481 |
| A1 | PC1 (24) | SOLAR_SENSE | An | 1 MΩ / 150 kΩ, oran 0,1304 (D1 öncesi) |
| A2 | PC2 (25) | TEST_REED_N | G | SW3 test reed (J10), iç pull-up |
| A3 | PC3 (26) | CHG_STAT_N | G | CN3791 CHRG açık drenaj, iç pull-up |
| A4/A5 | PC4/PC5 (27/28) | I2C_SDA / I2C_SCL | G/Ç | 4,7 kΩ → V_SNS |
| A6 | ADC6 (19) | — |  | boş |
| A7 | ADC7 (22) | BAT_NTC | An | Δ1 YENİ: NTC 10k B3950 / 220 kΩ, 0…45 °C şarj penceresi |

Kullanılmayan: A6 (ADC6). TQFP GND: 3, 5, 21; VCC: 4, 6; AVCC: 18; AREF: 20 (100 nF → GND, iç 1,1 V referans).

## 8. A7670E kullanılan pinler

| Pin | Ad | Bağlantı |
|---|---|---|
| 55, 56, 57 | VBAT | VMODEM (Q1), 2×470 µF + 100 nF + 33 pF + 10 pF + ESD5Z5.0 |
| 1 | PWRKEY | Q4 kollektör (iç 50 kΩ pull-up VBAT’a) |
| 16 | RESET | NC (iç pull-up) |
| 9 | TXD | MDM_TXD_1V8 → Q6 → D7 |
| 10 | RXD | MDM_RXD_1V8 ← Q7 ← D8 |
| 3 | DTR | MDM_DTR_1V8 ← Q8 ← D5 |
| 4 | RI | MDM_RI_1V8 → Q9 → D3 |
| 7, 8, 5 | CTS, RTS, DCD | NC |
| 15 | VDD_EXT (VDD_1V8) | BSS138 kapıları + LV pull-up (50 mA maks.) |
| 30–33 | USIM_VDD/DATA/CLK/RST | J11 (22 Ω seri, ESDA6V1-5SC6, 100 nF + 33 pF) |
| 34 | USIM_DET | NC |
| 60 | RF_ANT | R27 0 Ω π ağı → J12 U.FL |
| 52 | NETLIGHT | R28 → Q13 → LED3 (DNP, Δ5) |
| 66 | STATUS | NC |
| 24, 27, 28, 6, 23 | VBUS, DP, DM, USB_BOOT, LOG_TX | TP1–TP5 (FW güncelleme) |
| 2, 17, 18, … | GND | Tüm GND pinleri katı GND düzlemine |

## 9. DNP (üretimde takılmayan) parçalar

C31, C32, LED2, LED3, Q13, R8, R28, R29 — hata ayıklama / RF ayarı içindir.

## 10. Maliyet özeti (BOM.csv)

Elektronik: **71,22 USD** • Mekanik: **26,58 USD** • Üretim: **16,35 USD** • Genel toplam: **114,15 USD / cihaz** (~100 adet, KDV/nakliye/SIM hariç).
