// logic.mjs - ON-1 saf mantik modullerinin Node.js'e SATIR SATIR cevirisi.
// YALNIZCA yerel C++ derleyici bulunmayan ortamlar icin yedektir; asil test test_logic.cpp'dir.
// C tamsayi semantigi korunur: bolme sifira dogru kesilir (Math.trunc), int16/uint32 tasmalari.
// Kaynaklar: ../../OrmanNobetcisi/{storage,textutil,detector,commands}.cpp  - degisiklikte esitleyin.

const trunc = Math.trunc;
const i16 = (x) => (x << 16) >> 16;
const u32 = (x) => x >>> 0;

// ------------------------------- storage -----------------------------------
export function crc8(bytes) {
  let crc = 0;
  for (const b of bytes) {
    crc ^= b;
    for (let i = 0; i < 8; i++) crc = crc & 0x80 ? ((crc << 1) ^ 0x07) & 0xff : (crc << 1) & 0xff;
  }
  return crc;
}
export const SFLAG_SIREN_EN = 1, SFLAG_CALL_EN = 2, PHONE_SLOTS = 5, PHONE_LEN = 17, NAME_LEN = 21,
  LOC_LEN = 24, PIN_LEN = 7;
export function settingsDefaults() {
  return { magic: 0x4f4e, version: 1, deviceId: 1, pin: '1234', phones: ['', '', '', '', ''], name: '',
    location: '', sens: 2, flags: SFLAG_SIREN_EN, reportHours: 24, vrefMv: 1100 };
}
// AVR bellek duzeni (paketli) ile seri hale getir -> CRC
function serialize(s) {
  const out = [s.magic & 0xff, s.magic >> 8, s.version, s.deviceId & 0xff, s.deviceId >> 8];
  const fix = (str, n) => { for (let i = 0; i < n; i++) out.push(i < str.length ? str.charCodeAt(i) : 0); };
  fix(s.pin, PIN_LEN);
  for (const p of s.phones) fix(p, PHONE_LEN);
  fix(s.name, NAME_LEN);
  fix(s.location, LOC_LEN);
  out.push(s.sens, s.flags, s.reportHours, s.vrefMv & 0xff, s.vrefMv >> 8);
  return out;
}
export function settingsSeal(s) { s.crc = crc8(serialize(s)); }
export function settingsValid(s) {
  if (s.magic !== 0x4f4e || s.version !== 1) return false;
  if (s.crc !== crc8(serialize(s))) return false;
  if (s.sens < 1 || s.sens > 3) return false;
  if (s.vrefMv < 1000 || s.vrefMv > 1200) return false;
  if (s.pin.length < 4 || s.pin.length >= PIN_LEN) return false;
  return true;
}
export const settingsPhoneListEmpty = (s) => s.phones.every((p) => !p);

// ------------------------------- textutil ----------------------------------
export class TextBuf {
  constructor(cap) { this.c = cap; this.b = ''; }
  clear() { this.b = ''; }
  addChar(ch) { if (this.b.length < this.c) this.b += ch; }
  add(s) { for (const ch of s) { if (this.b.length >= this.c) break; this.b += ch; } }
  addP(s) { this.add(s); }
  addInt(v) { this.add(String(trunc(v))); }
  addUintPad(v, w) { let s = String(v & 0xffff); while (s.length < w) s = '0' + s; this.add(s); }
  addDec(v, d) {
    let mult = 1;
    for (let i = 0; i < d; i++) mult *= 10;
    if (v < 0) { this.addChar('-'); v = -v; }
    this.addInt(trunc(v / mult));
    if (d) { this.addChar('.'); this.addUintPad(v % mult, d); }
  }
  get length() { return this.b.length; }
  toString() { return this.b; }
}

export function asciiFromCodepoint(cp) {
  if (cp === 9 || cp === 13 || cp === 10) return ' ';
  if (cp >= 0x20 && cp < 0x7f) return String.fromCharCode(cp);
  const m = { 0xc7: 'C', 0xe7: 'c', 0x11e: 'G', 0x11f: 'g', 0x130: 'I', 0x131: 'i', 0xd6: 'O', 0xf6: 'o',
    0x15e: 'S', 0x15f: 's', 0xdc: 'U', 0xfc: 'u', 0xc2: 'A', 0xe2: 'a', 0xce: 'I', 0xee: 'i', 0xdb: 'U', 0xfb: 'u' };
  return m[cp] ?? '?';
}
function latin5ToCodepoint(ch) {
  return { 0xd0: 0x11e, 0xf0: 0x11f, 0xdd: 0x130, 0xfd: 0x131, 0xde: 0x15e, 0xfe: 0x15f }[ch] ?? ch;
}
// Girdi/cikti: her karakteri bir bayt olan "bayt dizgisi"
export function utf8ToAscii(s) {
  const r = [...s].map((c) => c.charCodeAt(0));
  r.push(0);
  let out = '', i = 0;
  while (r[i]) {
    const ch = r[i];
    if (ch < 0x80) { out += asciiFromCodepoint(ch); i++; }
    else if ((ch & 0xe0) === 0xc0 && (r[i + 1] & 0xc0) === 0x80) { out += asciiFromCodepoint(((ch & 0x1f) << 6) | (r[i + 1] & 0x3f)); i += 2; }
    else if ((ch & 0xf0) === 0xe0 && (r[i + 1] & 0xc0) === 0x80 && (r[i + 2] & 0xc0) === 0x80) {
      out += asciiFromCodepoint(((ch & 0x0f) << 12) | ((r[i + 1] & 0x3f) << 6) | (r[i + 2] & 0x3f)); i += 3;
    } else if ((ch & 0xf8) === 0xf0 && (r[i + 1] & 0xc0) === 0x80 && (r[i + 2] & 0xc0) === 0x80 && (r[i + 3] & 0xc0) === 0x80) {
      out += '?'; i += 4;
    } else { out += asciiFromCodepoint(latin5ToCodepoint(ch)); i++; }
  }
  return out;
}
const isHex = (c) => /[0-9A-Fa-f]/.test(c);
// Basarili ise cozulmus dizgi, degilse null
export function ucs2HexDecode(s) {
  if (s.length < 8 || (s.length & 3) !== 0 || s[0] !== '0' || s[1] !== '0') return null;
  if (![...s].every(isHex)) return null;
  let out = '';
  for (let i = 0; i < s.length; i += 4) out += asciiFromCodepoint(parseInt(s.substr(i, 4), 16));
  return out;
}
export const sanitizeAscii = (s) => [...s].map((c) => { const ch = c.charCodeAt(0);
  return ch === 13 || ch === 10 || ch === 9 ? ' ' : ch < 0x20 || ch >= 0x7f ? '?' : c; }).join('');
export const toUpperAscii = (s) => s.replace(/[a-z]/g, (c) => c.toUpperCase());
export const trimInPlace = (s) => s.replace(/^ +/, '').replace(/ +$/, '');

// Donus: [rakamSayisi, normalize]
export function phoneNormalize(inp, outSize) {
  let o = '', digits = 0, first = true;
  for (const ch of inp) {
    if (' -().'.includes(ch)) continue;
    if (ch === '+' && first) { if (o.length + 1 >= outSize) return [0, '']; o += '+'; }
    else if (ch >= '0' && ch <= '9') { if (o.length + 1 >= outSize) return [0, '']; o += ch; digits++; }
    else return [0, ''];
    first = false;
  }
  if (digits < 7 || digits > 15) return [0, ''];
  return [digits, o];
}
export function phoneMatch(a, b) {
  if (!a || !b) return false;
  const da = a.replace(/[^0-9]/g, ''), db = b.replace(/[^0-9]/g, '');
  if (da.length < 7 || db.length < 7) return false;
  if (da.length >= 10 && db.length >= 10) return da.slice(-10) === db.slice(-10);
  return da.length === db.length && da === db;
}
export function parseUint16(s) {
  if (!s) return null;
  let v = 0;
  for (const c of s) { if (c < '0' || c > '9') return null; v = v * 10 + (c.charCodeAt(0) - 48); if (v > 65535) return null; }
  return v;
}
function parseCoord(s, p, maxInt) {
  if (s[p] === '-' || s[p] === '+') p++;
  let ip = 0, nd = 0;
  while (s[p] >= '0' && s[p] <= '9') { ip = ip * 10 + (s.charCodeAt(p) - 48); if (++nd > 3) return -1; p++; }
  if (nd === 0) return -1;
  let fracNonZero = false;
  if (s[p] === '.') {
    p++;
    let nf = 0;
    while (s[p] >= '0' && s[p] <= '9') { if (s[p] !== '0') fracNonZero = true; if (++nf > 8) return -1; p++; }
    if (nf === 0) return -1;
  }
  if (ip > maxInt || (ip === maxInt && fracNonZero)) return -1;
  return p;
}
// Donus: normalize dizgi veya null
export function locationNormalize(s) {
  s = s.replace(/ /g, '');
  let p = parseCoord(s, 0, 90);
  if (p < 0 || s[p] !== ',') return null;
  p = parseCoord(s, p + 1, 180);
  return p >= 0 && p === s.length ? s : null;
}
export function parseCclk(line) {
  let p = line.indexOf('"');
  if (p < 0) return null;
  const q = line.slice(p + 1);
  if (q.length < 17 || q[2] !== '/' || q[5] !== '/' || q[8] !== ',' || q[11] !== ':' || q[14] !== ':') return null;
  const two = (i) => (/[0-9]{2}/.test(q.substr(i, 2)) ? parseInt(q.substr(i, 2), 10) : 255);
  const yy = two(0), mo = two(3), dd = two(6), hh = two(9), mi = two(12), ss = two(15);
  if (yy < 24 || yy > 69 || mo < 1 || mo > 12 || dd < 1 || dd > 31 || hh > 23 || mi > 59 || ss > 59) return null;
  const md = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let days = 0;
  for (let y = 0; y < yy; y++) days += (y & 3) === 0 ? 366 : 365;
  for (let m = 1; m < mo; m++) { days += md[m - 1]; if (m === 2 && (yy & 3) === 0) days++; }
  days += dd - 1;
  return days * 86400 + hh * 3600 + mi * 60 + ss;
}

// ------------------------------- detector ----------------------------------
export const TH = { MAXT: 700, DIFF_HIGH: 250, DIFF_LOW: 120, RATE: 80, HOT_DELTA: 100, HOT_COUNT: 3,
  GAS_HIGH: 400, GAS_LOW: 650, AMB_T: 550, AMB_RISE: 60, RH_DROP: 150 };
export const R = { TH_ABS: 1, TH_DIFF2: 2, TH_DIFF1: 4, TH_RATE: 8, TH_HOT: 16, GAS2: 32, GAS1: 64, AMB_T: 128,
  AMB_RISE: 256, RH_DROP: 512 };
export const RISK_VERY_HIGH = 0, RISK_HIGH = 1, RISK_MEDIUM = 2, RISK_LOW = 3;
const HIST_LEN = 8, HIST_SPACING = 50, WINDOW = 330, RATE_MIN_AGE = 45, WARMUP = 1800;
export const DET_HIST_LEN = HIST_LEN;

export const sensK = (s) => (s === 1 ? 1300 : s === 3 ? 750 : 1000);
export const scaleTh = (th, s) => i16(trunc((th * sensK(s)) / 1000));
export const hotDeltaFor = (s) => scaleTh(TH.HOT_DELTA, s);
export const roundX10 = (v) => i16(trunc((v >= 0 ? v + 5 : v - 5) / 10));

export function thermalStats(px, hotDelta10) {
  const n = px.length;
  for (let i = 1; i < n; i++) {
    const v = px[i];
    let j = i - 1;
    while (j >= 0 && px[j] > v) { px[j + 1] = px[j]; j--; }
    px[j + 1] = v;
  }
  const medQ2 = n & 1 ? 2 * px[n >> 1] : px[(n >> 1) - 1] + px[n >> 1];
  const maxT10 = trunc((px[n - 1] * 5) / 2);
  const median10 = trunc((medQ2 * 5) / 4);
  const thr = medQ2 * 5 + hotDelta10 * 4;
  let cnt = 0;
  for (let i = n - 1; i >= 0 && px[i] * 10 > thr; i--) cnt++;
  return { maxT10, median10, hotCount: cnt };
}
export const angstromIndex100 = (rh10, t10) => i16(trunc(rh10 / 2) + 270 - t10);
export const angstromLevel = (i) => (i < 200 ? RISK_VERY_HIGH : i < 250 ? RISK_HIGH : i <= 400 ? RISK_MEDIUM : RISK_LOW);
export const riskName = (l) => ['COK YUKSEK', 'YUKSEK', 'ORTA', 'DUSUK'][l] ?? 'DUSUK';
export function batteryPercent(mv) {
  const tv = [4200, 4100, 4000, 3900, 3800, 3700, 3600, 3500, 3400, 3300, 3000];
  const tp = [100, 90, 79, 68, 55, 40, 22, 10, 4, 1, 0];
  if (mv >= 4200) return 100;
  for (let i = 1; i < tp.length; i++) {
    const lo = tv[i];
    if (mv >= lo) { const hi = tv[i - 1]; return tp[i] + trunc(((tp[i - 1] - tp[i]) * (mv - lo) + trunc((hi - lo) / 2)) / (hi - lo)); }
  }
  return 0;
}
export function detInit(now) {
  return { gasBase: 0, gasBaseValid: false, gasWarmStart: now, hist: Array.from({ length: HIST_LEN }, () => ({ t: 0, maxT10: 0, temp10: 0, rh10: 0, flags: 0 })),
    histHead: 0, histCount: 0, score: 0, reasons: 0, gasPm: -1, rate10: 0, rise10: 0, drop10: 0 };
}
export const detCalibrateGas = (d) => { d.gasBaseValid = false; };
export function scoreInput(o) {
  return { thermalOk: false, rateValid: false, gasValid: false, envOk: false, riseValid: false, dropValid: false,
    hotCount: 0, maxT10: 0, median10: 0, rate10: 0, gasPm: 0, temp10: 0, rise10: 0, drop10: 0, ...o };
}
export function detScore(inp, sens) {
  let s = 0, r = 0;
  if (inp.thermalOk) {
    const diff = i16(inp.maxT10 - inp.median10);
    if (inp.maxT10 >= scaleTh(TH.MAXT, sens)) { s += 3; r |= R.TH_ABS; }
    else if (diff >= scaleTh(TH.DIFF_HIGH, sens)) { s += 2; r |= R.TH_DIFF2; }
    else if (diff >= scaleTh(TH.DIFF_LOW, sens)) { s += 1; r |= R.TH_DIFF1; }
    if (inp.rateValid && inp.rate10 >= scaleTh(TH.RATE, sens)) { s += 1; r |= R.TH_RATE; }
    const hotMin = trunc((TH.HOT_COUNT * sensK(sens) + 500) / 1000);
    if (inp.hotCount >= hotMin) { s += 1; r |= R.TH_HOT; }
  }
  if (inp.gasValid) {
    let rHigh = 1000 - scaleTh(1000 - TH.GAS_HIGH, sens);
    const rLow = 1000 - scaleTh(1000 - TH.GAS_LOW, sens);
    if (rHigh < 50) rHigh = 50;
    if (inp.gasPm < rHigh) { s += 2; r |= R.GAS2; } else if (inp.gasPm < rLow) { s += 1; r |= R.GAS1; }
  }
  if (inp.envOk) {
    if (inp.temp10 >= scaleTh(TH.AMB_T, sens)) { s += 2; r |= R.AMB_T; }
    if (inp.riseValid && inp.rise10 >= scaleTh(TH.AMB_RISE, sens)) { s += 1; r |= R.AMB_RISE; }
    if (inp.dropValid && inp.drop10 >= scaleTh(TH.RH_DROP, sens)) { s += 1; r |= R.RH_DROP; }
  }
  return { score: s, reasons: r };
}
export function detEvaluate(d, rd, now, sens, allowBaseline) {
  const inp = scoreInput({ thermalOk: rd.thermalOk, maxT10: rd.maxT10, median10: rd.median10, hotCount: rd.hotCount,
    envOk: rd.envOk, temp10: rd.temp10 });
  for (let i = 0; i < d.histCount; i++) {
    const e = d.hist[i];
    const age = u32(now - e.t);
    if (age === 0 || age > WINDOW) continue;
    if (rd.thermalOk && e.flags & 1 && age >= RATE_MIN_AGE) {
      const rate = i16(trunc(((rd.maxT10 - e.maxT10) * 60) / age));
      if (!inp.rateValid || rate > inp.rate10) inp.rate10 = rate;
      inp.rateValid = true;
    }
    if (rd.envOk && e.flags & 2) {
      const rise = i16(rd.temp10 - e.temp10), drop = i16(e.rh10 - rd.rh10);
      if (!inp.riseValid || rise > inp.rise10) inp.rise10 = rise;
      if (!inp.dropValid || drop > inp.drop10) inp.drop10 = drop;
      inp.riseValid = inp.dropValid = true;
    }
  }
  const warm = u32(now - d.gasWarmStart) >= WARMUP;
  let ratio = -1;
  if (rd.gasOk && rd.gasOhm >= 100) {
    if (!d.gasBaseValid || d.gasBase < 100) { d.gasBase = rd.gasOhm; d.gasBaseValid = true; ratio = 1000; }
    else {
      const pm = Math.floor((rd.gasOhm * 10) / Math.floor(d.gasBase / 100));
      ratio = pm > 9999 ? 9999 : pm;
      inp.gasValid = warm;
      inp.gasPm = ratio;
    }
  }
  const sc = detScore(inp, sens);
  d.score = sc.score; d.reasons = sc.reasons; d.gasPm = ratio;
  d.rate10 = inp.rateValid ? inp.rate10 : 0; d.rise10 = inp.riseValid ? inp.rise10 : 0; d.drop10 = inp.dropValid ? inp.drop10 : 0;
  if (ratio > 0 && allowBaseline) {
    const delta = rd.gasOhm - d.gasBase;
    if (!warm) d.gasBase = u32(d.gasBase + trunc(delta / 10));
    else if (ratio > 800) d.gasBase = u32(d.gasBase + trunc(delta / 100));
  }
  let push = d.histCount === 0;
  if (!push) push = u32(now - d.hist[(d.histHead + HIST_LEN - 1) % HIST_LEN].t) >= HIST_SPACING;
  if (push && (rd.thermalOk || rd.envOk)) {
    d.hist[d.histHead] = { t: now, maxT10: rd.thermalOk ? rd.maxT10 : 0, temp10: rd.envOk ? rd.temp10 : 0,
      rh10: rd.envOk ? rd.rh10 : 0, flags: (rd.thermalOk ? 1 : 0) | (rd.envOk ? 2 : 0) };
    d.histHead = (d.histHead + 1) % HIST_LEN;
    if (d.histCount < HIST_LEN) d.histCount++;
  }
  return d.score;
}

// ------------------------------- commands ----------------------------------
export const ACT_TEST = 1, ACT_MUTE = 2, ACT_RESET = 3, ACT_CALIBRATE = 4;
export const CMDR_REPLY = 1, CMDR_SAVE = 2;
const KEYWORDS = ['DURUM', 'TEST', 'EKLE', 'SIL', 'LISTE', 'KONUM', 'AD', 'HASSAS', 'SESSIZ', 'SIREN', 'ARAMA', 'RAPOR', 'KALIBRE', 'SIFIRLA', 'PIN'];
export const CMD = Object.fromEntries(KEYWORDS.map((k, i) => [k, i + 1]));
export const cmdLookup = (kw) => KEYWORDS.indexOf(kw) + 1;
export function cmdAddDeviceId(tb, id) { tb.add('ON1-'); tb.addUintPad(id, 4); tb.addChar(' '); }

// nextToken: [token|null, kalan]
function nextToken(s) {
  let i = 0;
  while (s[i] === ' ') i++;
  if (i >= s.length) return [null, ''];
  const st = i;
  while (i < s.length && s[i] !== ' ') i++;
  const tok = s.slice(st, i);
  if (i < s.length) i++;
  while (s[i] === ' ') i++;
  return [tok, s.slice(i)];
}
function parseOnOff(a) {
  a = toUpperAscii(a);
  if (['AC', 'ACIK', 'ON'].includes(a)) return 1;
  if (['KAPA', 'KAPAT', 'KAPALI', 'OFF'].includes(a)) return 0;
  return -1;
}
function sanitizeName(inp) {
  let o = '';
  for (let ch of inp) {
    if (ch === ' ') ch = '-';
    if (!/[A-Za-z0-9_.\-]/.test(ch)) continue;
    if (o.length >= NAME_LEN - 1) return null;
    o += ch;
  }
  return o.length ? o : null;
}
const isAdmin = (s, snd) => !!s.phones[0] && phoneMatch(s.phones[0], snd);
const senderListed = (s, snd) => s.phones.some((p) => p && phoneMatch(p, snd));
const isDigits = (p, mn, mx) => /^[0-9]*$/.test(p) && p.length >= mn && p.length <= mx;

export function cmdProcess(text, sender, s, hooks, r) {
  r.clear();
  if (text == null || !sender) return 0;
  const dec = ucs2HexDecode(text);
  text = dec !== null ? dec : utf8ToAscii(text);
  text = trimInPlace(text);
  let pinTok, kwTok, args;
  [pinTok, args] = nextToken(text);
  [kwTok, args] = nextToken(args);
  if (!pinTok || !kwTok) return 0;
  args = trimInPlace(args);
  kwTok = toUpperAscii(kwTok);
  const cmd = cmdLookup(kwTok);
  const listEmpty = settingsPhoneListEmpty(s);
  if (!listEmpty && !senderListed(s, sender)) return 0;
  if (pinTok !== s.pin) {
    if (listEmpty) return 0;
    cmdAddDeviceId(r, s.deviceId); r.add('HATA: '); r.add('PIN yanlis');
    return CMDR_REPLY;
  }
  cmdAddDeviceId(r, s.deviceId);
  const err = (m) => { r.add('HATA: '); r.add(m); return CMDR_REPLY; };
  const ok = () => r.add('TAMAM: ');
  if (listEmpty) {
    const [slotTok] = nextToken(args);
    if (cmd !== CMD.EKLE || slotTok !== '1') return err('once yonetici ekleyin: EKLE 1 <numara>');
    const [n, norm] = phoneNormalize(sender, PHONE_LEN);
    if (!n) return 0;
    s.phones[0] = norm; ok(); r.add('yonetici 1 = '); r.add(norm);
    return CMDR_REPLY | CMDR_SAVE;
  }
  if ((cmd === CMD.EKLE || cmd === CMD.SIL || cmd === CMD.PIN) && !isAdmin(s, sender)) return err('bu komut yalniz yonetici (1) icindir');
  let num;
  switch (cmd) {
    case CMD.DURUM: r.clear(); hooks.status(r); return CMDR_REPLY;
    case CMD.TEST: hooks.action(ACT_TEST, 0); r.clear(); return 0;
    case CMD.EKLE: {
      const [slotTok, rest] = nextToken(args);
      num = slotTok ? parseUint16(slotTok) : null;
      const [n, norm] = phoneNormalize(rest, PHONE_LEN);
      if (!slotTok || num === null || num < 1 || num > 5 || !n) return err('bicim: EKLE <1-5> <numara>');
      s.phones[num - 1] = norm; ok(); r.addInt(num); r.add(' = '); r.add(norm);
      return CMDR_REPLY | CMDR_SAVE;
    }
    case CMD.SIL:
      num = parseUint16(args);
      if (num === null || num < 1 || num > 5) return err('bicim: SIL <1-5>');
      s.phones[num - 1] = ''; ok(); r.addInt(num); r.add(' silindi');
      return CMDR_REPLY | CMDR_SAVE;
    case CMD.LISTE:
      r.add('LISTE');
      for (let i = 0; i < 5; i++) { r.addChar(' '); r.addInt(i + 1); r.addChar(':'); r.add(s.phones[i] || '-'); }
      return CMDR_REPLY;
    case CMD.KONUM: {
      if (!args) { r.add('KONUM '); if (s.location) { r.add('maps.google.com/?q='); r.add(s.location); } else r.add('ayarlanmamis'); return CMDR_REPLY; }
      const loc = locationNormalize(args);
      if (!loc || loc.length >= LOC_LEN) return err('bicim: KONUM 39.70512,26.85211');
      s.location = loc; ok(); r.add('KONUM '); r.add(loc);
      return CMDR_REPLY | CMDR_SAVE;
    }
    case CMD.AD: {
      const nm = sanitizeName(args);
      if (!nm) return err('AD 1-20 karakter (harf, rakam, - _ .)');
      s.name = nm; ok(); r.add('AD '); r.add(nm);
      return CMDR_REPLY | CMDR_SAVE;
    }
    case CMD.HASSAS:
      num = parseUint16(args);
      if (num === null || num < 1 || num > 3) return err('bicim: HASSAS 1/2/3');
      s.sens = num; ok(); r.add('HASSAS '); r.addInt(num); r.add([' (dusuk)', ' (normal)', ' (yuksek)'][num - 1]);
      return CMDR_REPLY | CMDR_SAVE;
    case CMD.SESSIZ:
      num = parseUint16(args);
      if (num === null || num > 1440) return err('bicim: SESSIZ <0-1440 dk>');
      hooks.action(ACT_MUTE, num); ok();
      if (num === 0) r.add('sessiz iptal'); else { r.add('yerel alarm '); r.addInt(num); r.add(' dk sessiz (SMS devam eder)'); }
      return CMDR_REPLY;
    case CMD.SIREN: case CMD.ARAMA: {
      const bit = cmd === CMD.SIREN ? SFLAG_SIREN_EN : SFLAG_CALL_EN;
      let fl = 0;
      if (args) {
        const v = parseOnOff(args);
        if (v < 0) return err(cmd === CMD.SIREN ? 'bicim: SIREN AC/KAPA' : 'bicim: ARAMA AC/KAPA');
        if (v) s.flags |= bit; else s.flags &= ~bit;
        ok(); fl = CMDR_SAVE;
      }
      r.add(cmd === CMD.SIREN ? 'SIREN ' : 'ARAMA '); r.add(s.flags & bit ? 'ACIK' : 'KAPALI');
      return CMDR_REPLY | fl;
    }
    case CMD.RAPOR:
      num = parseUint16(args);
      if (num === null || num > 168) return err('bicim: RAPOR <0-168 saat>');
      s.reportHours = num; ok(); r.add('RAPOR ');
      if (num) { r.addInt(num); r.add(' saat'); } else r.add('kapali');
      return CMDR_REPLY | CMDR_SAVE;
    case CMD.KALIBRE: hooks.action(ACT_CALIBRATE, 0); ok(); r.add('gaz tabani sifirlandi'); return CMDR_REPLY;
    case CMD.SIFIRLA: hooks.action(ACT_RESET, 0); ok(); r.add('alarm onaylandi, durum NORMAL'); return CMDR_REPLY;
    case CMD.PIN:
      if (!isDigits(args, 4, PIN_LEN - 1)) return err('PIN 4-6 rakam olmali');
      s.pin = args; ok(); r.add('PIN degistirildi');
      return CMDR_REPLY | CMDR_SAVE;
    default:
      return err('bilinmeyen komut. DURUM TEST EKLE SIL LISTE KONUM AD HASSAS SESSIZ SIREN ARAMA RAPOR KALIBRE SIFIRLA PIN');
  }
}
