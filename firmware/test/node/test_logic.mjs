// test_logic.mjs - test_logic.cpp ile AYNI test vektorleri (Node.js yedegi). Calistirma: node test_logic.mjs
import * as L from './logic.mjs';

let pass = 0, fail = 0;
const where = () => (new Error().stack.split('\n')[3] || '').trim();
function CHECK(c, msg = '') { if (c) pass++; else { fail++; console.log('FAIL', msg, where()); } }
function EQ(a, b) { if (a === b) pass++; else { fail++; console.log(`FAIL got ${JSON.stringify(a)} want ${JSON.stringify(b)}`, where()); } }

// ---------------- storage ----------------
{
  EQ(L.crc8([...'123456789'].map((c) => c.charCodeAt(0))), 0xf4);
  EQ(L.crc8([]), 0);
  const s = L.settingsDefaults(); L.settingsSeal(s);
  CHECK(L.settingsValid(s)); EQ(s.pin, '1234'); EQ(s.sens, 2); EQ(s.vrefMv, 1100);
  CHECK(s.flags & L.SFLAG_SIREN_EN); CHECK(!(s.flags & L.SFLAG_CALL_EN)); CHECK(L.settingsPhoneListEmpty(s));
  s.name = 'X'; CHECK(!L.settingsValid(s)); L.settingsSeal(s); CHECK(L.settingsValid(s));
  s.magic = 0; L.settingsSeal(s); CHECK(!L.settingsValid(s));
  const s2 = L.settingsDefaults(); s2.sens = 4; L.settingsSeal(s2); CHECK(!L.settingsValid(s2));
}
// ---------------- textbuf ----------------
{
  const tb = new L.TextBuf(160);
  for (let i = 0; i < 300; i++) tb.addChar('A');
  EQ(tb.length, 160);
  tb.clear(); tb.addInt(-1234); tb.addChar(' '); tb.addInt(0); tb.addChar(' '); tb.addUintPad(7, 4); tb.addChar(' ');
  tb.addDec(395, 2); tb.addChar(' '); tb.addDec(-5, 1); tb.addChar(' '); tb.addDec(52, 1);
  EQ(tb.toString(), '-1234 0 0007 3.95 -0.5 5.2');
  const t2 = new L.TextBuf(5); t2.add('ABCDEFGH'); EQ(t2.toString(), 'ABCDE');
}
// ---------------- ascii ----------------
{
  const A = L.asciiFromCodepoint;
  EQ(A(0xe7), 'c'); EQ(A(0x11f), 'g'); EQ(A(0x131), 'i'); EQ(A(0x130), 'I'); EQ(A(0xf6), 'o'); EQ(A(0x15f), 's');
  EQ(A(0xfc), 'u'); EQ(A(0xc7), 'C'); EQ(A(0x11e), 'G'); EQ(A(0x15e), 'S'); EQ(A(0xd6), 'O'); EQ(A(0xdc), 'U');
  EQ(A(0x20ac), '?'); EQ(A(10), ' ');
  EQ(L.utf8ToAscii('\xC3\x87\xC4\xB1\xC4\x9F \xC5\x9E\xC3\x9C\xC3\x96 \xC3\xBCnl\xC3\xBC \xC4\xB0zmir'), 'Cig SUO unlu Izmir');
  EQ(L.utf8ToAscii('\xDD\xFE\xF0\xE7'), 'Isgc');
  EQ(L.utf8ToAscii('\xF0\x9F\x94\xA5 ates'), '? ates');
  EQ(L.ucs2HexDecode('003500360037003800200044005500520055004D'), '5678 DURUM');
  EQ(L.ucs2HexDecode('0035003600370038002000530130004C00200032'), '5678 SIL 2');
  EQ(L.ucs2HexDecode('1234 DURUM'), null);
  EQ(L.ucs2HexDecode('12345678'), null);
  EQ(L.sanitizeAscii('a\x01b\x7F'), 'a?b?');
  EQ(L.toUpperAscii('durum SIL ac'), 'DURUM SIL AC');
  EQ(L.trimInPlace('   x y  '), 'x y');
}
// ---------------- phone / location / time ----------------
{
  EQ(L.phoneNormalize('+90 532 111 22 33', 17)[0], 12); EQ(L.phoneNormalize('+90 532 111 22 33', 17)[1], '+905321112233');
  EQ(L.phoneNormalize('0(532)111-22-33', 17)[1], '05321112233');
  EQ(L.phoneNormalize('12345', 17)[0], 0); EQ(L.phoneNormalize('+90532abc', 17)[0], 0);
  EQ(L.phoneNormalize('90+532111223', 17)[0], 0); EQ(L.phoneNormalize('+1234567890123456', 17)[0], 0);
  CHECK(L.phoneMatch('+905321112233', '05321112233')); CHECK(L.phoneMatch('+905321112233', '5321112233'));
  CHECK(L.phoneMatch('+90 532 111 22 33', '+905321112233')); CHECK(!L.phoneMatch('+905321112233', '+905321112234'));
  CHECK(!L.phoneMatch('+905321112233', '')); CHECK(!L.phoneMatch('TURKCELL', '+905321112233'));
  CHECK(L.phoneMatch('1234567', '1234567')); CHECK(!L.phoneMatch('1234567', '01234567'));
  EQ(L.parseUint16('24'), 24); EQ(L.parseUint16('65535'), 65535); EQ(L.parseUint16('65536'), null);
  EQ(L.parseUint16(''), null); EQ(L.parseUint16('1a'), null); EQ(L.parseUint16('-1'), null);
  EQ(L.locationNormalize('39.70512, 26.85211'), '39.70512,26.85211');
  CHECK(L.locationNormalize('-90,-180') !== null); EQ(L.locationNormalize('90.0001,10'), null);
  EQ(L.locationNormalize('45,180.5'), null); EQ(L.locationNormalize('abc'), null); EQ(L.locationNormalize('39.7'), null);
  EQ(L.locationNormalize('39.,26'), null);
  EQ(L.parseCclk('+CCLK: "26/11/10,13:45:00+12"'), 847633500);
  EQ(L.parseCclk('+CCLK: "24/02/29,23:59:59+12"'), 762566399);
  EQ(L.parseCclk('+CCLK: "25/03/01,00:00:00+00"'), 794102400);
  EQ(L.parseCclk('+CCLK: "70/01/01,00:00:00+00"'), null);
  EQ(L.parseCclk('+CCLK: "26/13/10,13:45:00+12"'), null);
  EQ(L.parseCclk('+CCLK: 26/11/10'), null);
}
// ---------------- angstrom / battery ----------------
{
  EQ(L.angstromIndex100(410, 220), 255); EQ(L.angstromLevel(255), L.RISK_MEDIUM);
  EQ(L.angstromLevel(L.angstromIndex100(200, 350)), L.RISK_VERY_HIGH);
  EQ(L.angstromLevel(199), L.RISK_VERY_HIGH); EQ(L.angstromLevel(200), L.RISK_HIGH); EQ(L.angstromLevel(249), L.RISK_HIGH);
  EQ(L.angstromLevel(250), L.RISK_MEDIUM); EQ(L.angstromLevel(400), L.RISK_MEDIUM); EQ(L.angstromLevel(401), L.RISK_LOW);
  EQ(L.angstromIndex100(800, 100), 570); EQ(L.riskName(0), 'COK YUKSEK'); EQ(L.riskName(3), 'DUSUK');
  EQ(L.batteryPercent(4200), 100); EQ(L.batteryPercent(4300), 100); EQ(L.batteryPercent(3700), 40);
  EQ(L.batteryPercent(3750), 48); EQ(L.batteryPercent(3450), 7); EQ(L.batteryPercent(3000), 0); EQ(L.batteryPercent(2500), 0);
}
// ---------------- thermal ----------------
{
  let px = Array(64).fill(80);
  let t = L.thermalStats(px, L.hotDeltaFor(2)); EQ(t.maxT10, 200); EQ(t.median10, 200); EQ(t.hotCount, 0);
  px = Array(64).fill(80); px[5] = 160; px[17] = 160; px[40] = 121; px[41] = 120;
  t = L.thermalStats(px, L.hotDeltaFor(2)); EQ(t.maxT10, 400); EQ(t.median10, 200); EQ(t.hotCount, 3);
  for (let i = 1; i < 64; i++) CHECK(px[i - 1] <= px[i]);
  px = Array.from({ length: 64 }, (_, i) => -20 + i);
  t = L.thermalStats(px, L.hotDeltaFor(3)); EQ(t.maxT10, 107); EQ(t.median10, 28); EQ(t.hotCount, 2);
}
// ---------------- score ----------------
{
  const base = () => L.scoreInput({ thermalOk: true, maxT10: 250, median10: 240, envOk: true, temp10: 250 });
  const S = (inp, s) => L.detScore(inp, s);
  let inp = base();
  EQ(S(inp, 2).score, 0); EQ(S(inp, 2).reasons, 0);
  inp.maxT10 = 700; EQ(S(inp, 2).score, 3); EQ(S(inp, 2).reasons, L.R.TH_ABS);
  inp.maxT10 = 699; inp.median10 = 200; EQ(S(inp, 2).score, 2); EQ(S(inp, 2).reasons, L.R.TH_DIFF2);
  inp.maxT10 = 449; EQ(S(inp, 2).score, 1); inp.maxT10 = 319; EQ(S(inp, 2).score, 0); inp.maxT10 = 320; EQ(S(inp, 2).score, 1);
  inp = base(); inp.rateValid = true; inp.rate10 = 80; EQ(S(inp, 2).score, 1); EQ(S(inp, 2).reasons, L.R.TH_RATE);
  inp.rate10 = 79; EQ(S(inp, 2).score, 0); inp.rateValid = false; inp.rate10 = 500; EQ(S(inp, 2).score, 0);
  inp = base(); inp.hotCount = 3; EQ(S(inp, 2).score, 1); EQ(S(inp, 1).score, 0);
  inp.hotCount = 2; EQ(S(inp, 3).score, 1); EQ(S(inp, 2).score, 0);
  inp = base(); inp.gasValid = true; inp.gasPm = 399; EQ(S(inp, 2).score, 2); EQ(S(inp, 2).reasons, L.R.GAS2);
  inp.gasPm = 400; EQ(S(inp, 2).score, 1); inp.gasPm = 649; EQ(S(inp, 2).score, 1); inp.gasPm = 650; EQ(S(inp, 2).score, 0);
  inp.gasPm = 300; EQ(S(inp, 1).score, 1); inp.gasPm = 219; EQ(S(inp, 1).score, 2);
  inp.gasPm = 700; EQ(S(inp, 3).score, 1); inp.gasPm = 549; EQ(S(inp, 3).score, 2);
  inp.gasValid = false; inp.gasPm = 10; EQ(S(inp, 2).score, 0);
  inp = base(); inp.temp10 = 550; EQ(S(inp, 2).score, 2); EQ(S(inp, 2).reasons, L.R.AMB_T);
  inp.temp10 = 549; EQ(S(inp, 2).score, 0); EQ(S(inp, 3).score, 2);
  inp.temp10 = 250; inp.riseValid = true; inp.rise10 = 60; inp.dropValid = true; inp.drop10 = 150;
  EQ(S(inp, 2).score, 2); EQ(S(inp, 2).reasons, L.R.AMB_RISE | L.R.RH_DROP); EQ(S(inp, 1).score, 0);
  EQ(L.scaleTh(700, 1), 910); EQ(L.scaleTh(700, 2), 700); EQ(L.scaleTh(700, 3), 525); EQ(L.hotDeltaFor(3), 75);
  inp = base(); Object.assign(inp, { maxT10: 780, median10: 260, hotCount: 6, gasValid: true, gasPm: 380, temp10: 410 });
  CHECK(S(inp, 2).score >= 5); EQ(S(inp, 2).score, 6);
  Object.assign(inp, { rateValid: true, rate10: 200, temp10: 600, riseValid: true, dropValid: true, rise10: 100, drop10: 300 });
  EQ(S(inp, 2).score, 11);
}
// ---------------- evaluate ----------------
{
  const rd = (maxT10, median10, temp10, rh10, gas) => ({ thermalOk: true, envOk: true, gasOk: gas !== 0, hotCount: 0,
    maxT10, median10, temp10, rh10, gasOhm: gas });
  let d = L.detInit(0);
  EQ(L.detEvaluate(d, rd(200, 200, 200, 400, 100000), 0, 2, true), 0);
  CHECK(d.gasBaseValid); EQ(d.gasBase, 100000); EQ(d.gasPm, 1000);
  EQ(L.detEvaluate(d, rd(200, 200, 200, 400, 30000), 60, 2, true), 0); EQ(d.gasPm, 300); EQ(d.gasBase, 93000);
  d = L.detInit(0); L.detEvaluate(d, rd(200, 200, 200, 400, 100000), 0, 2, true);
  EQ(L.detEvaluate(d, rd(200, 200, 200, 400, 35000), 1800, 2, false), 2); EQ(d.reasons, L.R.GAS2); EQ(d.gasBase, 100000);
  EQ(L.detEvaluate(d, rd(200, 200, 200, 400, 70000), 1900, 2, true), 0); EQ(d.gasBase, 100000);
  L.detEvaluate(d, rd(200, 200, 200, 400, 90000), 2000, 2, true); EQ(d.gasBase, 99900);
  L.detEvaluate(d, rd(200, 200, 200, 400, 120000), 2100, 2, true); EQ(d.gasBase, 99900 + 201);
  L.detCalibrateGas(d); EQ(L.detEvaluate(d, rd(200, 200, 200, 400, 50000), 2200, 2, true), 0); EQ(d.gasBase, 50000);
  d = L.detInit(0); L.detEvaluate(d, rd(200, 200, 200, 400, 0), 0, 2, true);
  EQ(L.detEvaluate(d, rd(300, 200, 200, 400, 0), 60, 2, true), 1); EQ(d.reasons, L.R.TH_RATE); EQ(d.rate10, 100);
  d = L.detInit(0); L.detEvaluate(d, rd(200, 200, 200, 400, 0), 0, 2, true);
  EQ(L.detEvaluate(d, rd(300, 200, 200, 400, 0), 40, 2, true), 0); EQ(d.histCount, 1);
  d = L.detInit(0);
  for (let t = 0; t <= 240; t += 60) L.detEvaluate(d, rd(200, 200, 200, 400, 0), t, 2, true);
  EQ(L.detEvaluate(d, rd(200, 200, 270, 200, 0), 300, 2, true), 2); EQ(d.reasons, L.R.AMB_RISE | L.R.RH_DROP);
  EQ(d.rise10, 70); EQ(d.drop10, 200);
  d = L.detInit(0); L.detEvaluate(d, rd(200, 200, 200, 400, 0), 0, 2, true);
  EQ(L.detEvaluate(d, rd(200, 200, 270, 200, 0), 400, 2, true), 0);
  d = L.detInit(0); for (let t = 0; t < 1200; t += 60) L.detEvaluate(d, rd(200, 200, 200, 400, 0), t, 2, true);
  EQ(d.histCount, L.DET_HIST_LEN);
  d = L.detInit(0); const bad = rd(900, 200, 200, 400, 0); bad.thermalOk = false; EQ(L.detEvaluate(d, bad, 0, 2, true), 0);
}
// ---------------- commands ----------------
{
  let lastAct = 0, lastArg = -1, statusCalls = 0;
  const hooks = { status: (tb) => { statusCalls++; tb.add('DURUM ON1-0001 NORMAL'); }, action: (a, g) => { lastAct = a; lastArg = g; } };
  const reply = new L.TextBuf(160);
  const run = (s, snd, msg) => { const r = L.cmdProcess(msg, snd, s, hooks, reply); CHECK(reply.length <= 160); return r; };
  const R = () => reply.toString();
  const ADMIN = '+905321112233', USER2 = '+905321112244', STRANGER = '+905559998877';
  const RS = L.CMDR_REPLY | L.CMDR_SAVE;
  const s = L.settingsDefaults();
  EQ(L.cmdLookup('DURUM'), L.CMD.DURUM); EQ(L.cmdLookup('PIN'), L.CMD.PIN); EQ(L.cmdLookup('SIFIRLA'), L.CMD.SIFIRLA); EQ(L.cmdLookup('XYZ'), 0);
  EQ(run(s, STRANGER, '0000 DURUM'), 0);
  EQ(run(s, STRANGER, '1234 DURUM'), L.CMDR_REPLY); CHECK(R().includes('HATA: once yonetici ekleyin'));
  EQ(run(s, STRANGER, '1234 EKLE 2 +905321112233'), L.CMDR_REPLY); CHECK(L.settingsPhoneListEmpty(s));
  EQ(run(s, STRANGER, '1234'), 0); EQ(run(s, STRANGER, ''), 0);
  EQ(run(s, ADMIN, '1234 ekle 1 +905000000000'), RS); EQ(s.phones[0], ADMIN); EQ(R(), 'ON1-0001 TAMAM: yonetici 1 = +905321112233');
  EQ(run(s, STRANGER, '1234 DURUM'), 0);
  EQ(run(s, ADMIN, '9999 DURUM'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 HATA: PIN yanlis');
  statusCalls = 0; EQ(run(s, '05321112233', '  1234   durum  '), L.CMDR_REPLY); EQ(statusCalls, 1); EQ(R(), 'DURUM ON1-0001 NORMAL');
  EQ(run(s, ADMIN, '1234 EKLE 2 0532 111 22 44'), RS); EQ(s.phones[1], '05321112244'); EQ(R(), 'ON1-0001 TAMAM: 2 = 05321112244');
  EQ(run(s, ADMIN, '1234 EKLE 6 +905321112255'), L.CMDR_REPLY); CHECK(R().includes('HATA: bicim: EKLE'));
  EQ(run(s, ADMIN, '1234 EKLE 3 abc'), L.CMDR_REPLY); CHECK(R().includes('HATA'));
  EQ(run(s, USER2, '1234 EKLE 3 +905321112255'), L.CMDR_REPLY); CHECK(R().includes('yalniz yonetici')); EQ(s.phones[2], '');
  EQ(run(s, USER2, '1234 PIN 0000'), L.CMDR_REPLY); EQ(s.pin, '1234');
  EQ(run(s, USER2, '1234 HASSAS 3'), RS); EQ(s.sens, 3); EQ(R(), 'ON1-0001 TAMAM: HASSAS 3 (yuksek)');
  EQ(run(s, USER2, '1234 HASSAS 4'), L.CMDR_REPLY); EQ(s.sens, 3);
  EQ(run(s, ADMIN, '1234 LISTE'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 LISTE 1:+905321112233 2:05321112244 3:- 4:- 5:-');
  EQ(run(s, ADMIN, '1234 SIL 2'), RS); EQ(s.phones[1], '');
  EQ(run(s, ADMIN, '1234 SIL 0'), L.CMDR_REPLY); CHECK(R().includes('HATA'));
  EQ(run(s, ADMIN, '1234 KONUM'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 KONUM ayarlanmamis');
  EQ(run(s, ADMIN, '1234 KONUM 39.70512, 26.85211'), RS); EQ(s.location, '39.70512,26.85211');
  EQ(run(s, ADMIN, '1234 KONUM 99.1,26'), L.CMDR_REPLY); EQ(s.location, '39.70512,26.85211');
  EQ(run(s, ADMIN, '1234 KONUM'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 KONUM maps.google.com/?q=39.70512,26.85211');
  EQ(run(s, ADMIN, '1234 AD KazDagi-K3'), RS); EQ(s.name, 'KazDagi-K3');
  EQ(run(s, ADMIN, '1234 AD Kaz Da\xC4\x9F\xC4\xB1 K3'), RS); EQ(s.name, 'Kaz-Dagi-K3');
  EQ(run(s, ADMIN, '1234 AD 123456789012345678901'), L.CMDR_REPLY); CHECK(R().includes('HATA')); EQ(s.name, 'Kaz-Dagi-K3');
  EQ(run(s, ADMIN, '1234 AD 12345678901234567890'), RS); EQ(s.name.length, 20);
  lastAct = 0; EQ(run(s, ADMIN, '1234 SESSIZ 30'), L.CMDR_REPLY); EQ(lastAct, L.ACT_MUTE); EQ(lastArg, 30);
  EQ(R(), 'ON1-0001 TAMAM: yerel alarm 30 dk sessiz (SMS devam eder)');
  EQ(run(s, ADMIN, '1234 SESS\xC4\xB0Z 0'), L.CMDR_REPLY); EQ(lastArg, 0); EQ(R(), 'ON1-0001 TAMAM: sessiz iptal');
  EQ(run(s, ADMIN, '1234 SESSIZ 5000'), L.CMDR_REPLY); CHECK(R().includes('HATA'));
  EQ(run(s, ADMIN, '1234 SIREN KAPA'), RS); CHECK(!(s.flags & L.SFLAG_SIREN_EN)); EQ(R(), 'ON1-0001 TAMAM: SIREN KAPALI');
  EQ(run(s, ADMIN, '1234 S\xC4\xB0REN A\xC3\x87'), RS); CHECK(s.flags & L.SFLAG_SIREN_EN);
  EQ(run(s, ADMIN, '1234 ARAMA ac'), RS); CHECK(s.flags & L.SFLAG_CALL_EN);
  EQ(run(s, ADMIN, '1234 ARAMA'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 ARAMA ACIK');
  EQ(run(s, ADMIN, '1234 ARAMA belki'), L.CMDR_REPLY); CHECK(R().includes('HATA'));
  EQ(run(s, ADMIN, '1234 RAPOR 12'), RS); EQ(s.reportHours, 12);
  EQ(run(s, ADMIN, '1234 RAPOR 0'), RS); EQ(R(), 'ON1-0001 TAMAM: RAPOR kapali');
  EQ(run(s, ADMIN, '1234 RAPOR 200'), L.CMDR_REPLY); EQ(s.reportHours, 0);
  EQ(run(s, ADMIN, '1234 KALIBRE'), L.CMDR_REPLY); EQ(lastAct, L.ACT_CALIBRATE);
  EQ(run(s, ADMIN, '1234 SIFIRLA'), L.CMDR_REPLY); EQ(lastAct, L.ACT_RESET);
  EQ(run(s, ADMIN, '1234 TEST'), 0); EQ(lastAct, L.ACT_TEST);
  EQ(run(s, ADMIN, '1234 YARDIM'), L.CMDR_REPLY); CHECK(R().includes('bilinmeyen komut'));
  EQ(run(s, ADMIN, '1234 PIN 12a4'), L.CMDR_REPLY); EQ(s.pin, '1234');
  EQ(run(s, ADMIN, '1234 PIN 5678'), RS); EQ(s.pin, '5678');
  EQ(run(s, ADMIN, '1234 DURUM'), L.CMDR_REPLY); EQ(R(), 'ON1-0001 HATA: PIN yanlis');
  statusCalls = 0; EQ(run(s, ADMIN, '003500360037003800200044005500520055004D'), L.CMDR_REPLY); EQ(statusCalls, 1);
  EQ(run(s, ADMIN, '5678 SIL 1'), RS); CHECK(L.settingsPhoneListEmpty(s));
  EQ(run(s, USER2, '5678 EKLE 1'), RS); EQ(s.phones[0], USER2);
}

console.log(`\n${pass} gecti, ${fail} basarisiz`);
process.exit(fail ? 1 : 0);
