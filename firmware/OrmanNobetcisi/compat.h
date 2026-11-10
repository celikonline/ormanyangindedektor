// compat.h - AVR (PROGMEM) ve masaustu (host test) derlemesi icin ortak katman.
// Saf mantik dosyalari (detector, commands, textutil, storage) bu baslik sayesinde
// hem ATmega328P'de hem de PC'de (g++/clang/cl) degisiklik yapmadan derlenir.
#pragma once

#include <stdint.h>
#include <stddef.h>
#include <string.h>

#if defined(__AVR__)
  #include <avr/pgmspace.h>
#else
  // Host: PROGMEM yok, tum veriler RAM'de.
  #ifndef PROGMEM
    #define PROGMEM
  #endif
  #ifndef PSTR
    #define PSTR(s) (s)
  #endif
  #define pgm_read_byte(p) (*(const uint8_t *)(p))
  #define pgm_read_word(p) (*(const uint16_t *)(p))
  #define strcmp_P(a, b) strcmp((a), (b))
  #define strlen_P(s) strlen(s)
  #define strncmp_P(a, b, n) strncmp((a), (b), (n))
  #define memcpy_P(d, s, n) memcpy((d), (s), (n))
#endif
