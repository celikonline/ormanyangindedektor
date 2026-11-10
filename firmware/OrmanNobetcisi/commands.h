// commands.h - SAF MANTIK (AVR + host). SMS komut ayristirici ve yurutucu (SPEC §6.3).
// Bicim: "<PIN> KOMUT [parametre]", buyuk/kucuk harf duyarsiz.
#pragma once
#include "compat.h"
#include "storage.h"
#include "textutil.h"

// Cihaz tarafinda yapilacak eylemler (hook.action ile bildirilir)
enum CmdAction : uint8_t {
  ACT_TEST = 1,      // 5 s isik+siren testi + tum numaralara test SMS'i
  ACT_MUTE,          // arg = dakika (0 = iptal)
  ACT_RESET,         // alarmi onayla, NORMAL'e don
  ACT_CALIBRATE      // gaz tabanini sifirla
};

// cmdProcess donus bitleri
#define CMDR_REPLY  0x01   // reply tamponundaki metin gonderene SMS olarak gonderilmeli
#define CMDR_SAVE   0x02   // ayarlar degisti, EEPROM'a yazilmali

// Komut kimlikleri (test ve hata ayiklama icin disari acik)
enum CmdId : uint8_t {
  CMD_NONE = 0, CMD_DURUM, CMD_TEST, CMD_EKLE, CMD_SIL, CMD_LISTE, CMD_KONUM, CMD_AD,
  CMD_HASSAS, CMD_SESSIZ, CMD_SIREN, CMD_ARAMA, CMD_RAPOR, CMD_KALIBRE, CMD_SIFIRLA, CMD_PIN
};

struct CmdHooks {
  void (*status)(TextBuf &tb);              // DURUM raporunu tb'ye yazar
  void (*action)(uint8_t act, uint16_t arg);
};

// Anahtar kelimeyi (BUYUK harf) komut kimligine cevirir.
uint8_t cmdLookup(const char *kwUpper);

// "ON1-0007 " onekini ekler.
void cmdAddDeviceId(TextBuf &tb, uint16_t id);

// Gelen SMS metnini isler. 'text' yerinde degistirilir (UCS2/UTF-8 cozme, bolme).
// sender: gonderen numara (modemden). Donus: CMDR_* bitleri (0 = yanit yok / yok say).
uint8_t cmdProcess(char *text, const char *sender, Settings *s, const CmdHooks *h, TextBuf &reply);
