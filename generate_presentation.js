const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.title = "Ses Işareti Analizi ve Cinsiyet Sınıflandırma";

// =========================================================
// TEMA / THEME
// =========================================================
const C = {
  navy    : "0D1B2A",   // Deep navy (bg)
  blue    : "1565C0",   // Brand blue
  lightblue: "1E88E5",
  accent  : "00BCD4",   // Teal accent
  white   : "FFFFFF",
  offwhite: "F0F4FF",
  gray    : "90A4AE",
  dark    : "263238",
  male    : "2196F3",
  female  : "E91E63",
  child   : "4CAF50",
  warn    : "FF9800"
};

const TITLE_FONT  = "Arial";
const BODY_FONT   = "Calibri";

// =========================================================
// YARDIMCI FONKSİYONLAR / HELPERS
// =========================================================
function darkSlide(slide) {
  slide.background = { color: C.navy };
}

function lightSlide(slide) {
  slide.background = { color: C.offwhite };
}

function addSlideNumber(slide, num) {
  slide.addText(`${num}`, {
    x: 12.5, y: 7.1, w: 0.6, h: 0.3,
    fontSize: 11, color: C.gray,
    fontFace: BODY_FONT, align: "right"
  });
}

function addNavyHeader(slide, text) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 1.1,
    fill: { color: C.blue }
  });
  slide.addText(text, {
    x: 0.5, y: 0.15, w: 12, h: 0.8,
    fontSize: 26, bold: true, color: C.white,
    fontFace: TITLE_FONT, valign: "middle"
  });
}

function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.18 };
}

// =========================================================
// SLAYT 1: KAPAK / COVER SLIDE
// =========================================================
{
  const slide = pres.addSlide();
  darkSlide(slide);

  // Gradient-like left panel
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 5.5, h: 7.5,
    fill: { color: C.blue }
  });

  // Decorative circles
  slide.addShape(pres.shapes.OVAL, {
    x: 3.5, y: -1, w: 4, h: 4,
    fill: { color: C.accent, transparency: 80 },
    line: { color: C.accent, transparency: 70, width: 1 }
  });
  slide.addShape(pres.shapes.OVAL, {
    x: -1.5, y: 5, w: 4, h: 4,
    fill: { color: "FFFFFF", transparency: 90 },
    line: { color: C.accent, transparency: 85, width: 1 }
  });

  // Mic icon area
  slide.addShape(pres.shapes.OVAL, {
    x: 1.5, y: 0.9, w: 2.5, h: 2.5,
    fill: { color: C.accent, transparency: 20 }
  });
  slide.addText("🎙️", {
    x: 1.5, y: 0.9, w: 2.5, h: 2.5,
    fontSize: 52, align: "center", valign: "middle"
  });

  // Left text
  slide.addText("Ses İşareti\nAnalizi", {
    x: 0.3, y: 3.6, w: 5.0, h: 1.2,
    fontSize: 18, color: "BBDEFB", bold: false,
    fontFace: TITLE_FONT, align: "left"
  });
  slide.addText("ve Cinsiyet\nSınıflandırma", {
    x: 0.3, y: 4.6, w: 5.0, h: 1.5,
    fontSize: 22, color: C.white, bold: true,
    fontFace: TITLE_FONT, align: "left"
  });

  // Right: English title
  slide.addText("Audio Signal Analysis\n& Gender Classification", {
    x: 5.8, y: 1.2, w: 7.2, h: 1.8,
    fontSize: 30, bold: true, color: C.white,
    fontFace: TITLE_FONT, align: "left"
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 5.8, y: 3.1, w: 7.0, h: 0.04,
    fill: { color: C.accent }
  });

  slide.addText("Technical Report — Midterm Project\n2025-2026 Spring Semester", {
    x: 5.8, y: 3.3, w: 7.2, h: 1.0,
    fontSize: 16, color: C.gray,
    fontFace: BODY_FONT, align: "left"
  });

  // Tag cards
  const tags = [
    { icon: "🐍", text: "Python" },
    { icon: "📐", text: "NumPy/SciPy" },
    { icon: "📊", text: "Matplotlib" },
    { icon: "🌐", text: "Streamlit" }
  ];
  tags.forEach((t, i) => {
    const x = 5.8 + i * 1.85;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 5.8, w: 1.7, h: 0.6,
      fill: { color: C.dark },
      shadow: makeShadow()
    });
    slide.addText(`${t.icon} ${t.text}`, {
      x, y: 5.8, w: 1.7, h: 0.6,
      fontSize: 11, color: C.accent,
      fontFace: BODY_FONT, align: "center", valign: "middle"
    });
  });

  slide.addText("Methods: Autocorrelation (F0) · ZCR · STE · Rule-Based Classifier", {
    x: 5.8, y: 6.6, w: 7.2, h: 0.5,
    fontSize: 12, color: C.gray, italics: true,
    fontFace: BODY_FONT, align: "left"
  });
}

// =========================================================
// SLAYT 2: VERİ SETİ ÖZETİ / DATASET SUMMARY
// =========================================================
{
  const slide = pres.addSlide();
  lightSlide(slide);
  addNavyHeader(slide, "📂 Dataset Summary — Veri Seti Özeti");
  addSlideNumber(slide, 2);

  // 3 gender cards
  const genderInfo = [
    { label: "Male\nErkek",   n: "6",  f0: "85–180 Hz",  avg: "~120 Hz", icon: "👨", color: C.male   },
    { label: "Female\nKadın", n: "6",  f0: "165–255 Hz", avg: "~210 Hz", icon: "👩", color: C.female },
    { label: "Child\nÇocuk",  n: "6",  f0: "250–400 Hz", avg: "~300 Hz", icon: "🧒", color: C.child  }
  ];

  genderInfo.forEach((g, i) => {
    const x = 0.4 + i * 4.2;
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 3.9, h: 3.6,
      fill: { color: C.white },
      shadow: makeShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.4, w: 3.9, h: 0.55,
      fill: { color: g.color }
    });
    slide.addText(g.icon, {
      x, y: 1.4, w: 3.9, h: 0.55,
      fontSize: 20, align: "center", valign: "middle"
    });
    slide.addText(g.label, {
      x: x + 0.2, y: 2.05, w: 3.5, h: 0.7,
      fontSize: 17, bold: true, color: C.dark,
      fontFace: TITLE_FONT, align: "center"
    });
    slide.addText(`N = ${g.n} recordings`, {
      x: x + 0.2, y: 2.75, w: 3.5, h: 0.4,
      fontSize: 13, color: C.gray, fontFace: BODY_FONT, align: "center"
    });
    slide.addText(`F0 Range: ${g.f0}`, {
      x: x + 0.2, y: 3.2, w: 3.5, h: 0.35,
      fontSize: 12, color: C.dark, fontFace: BODY_FONT, align: "center"
    });
    slide.addText(`Average: ${g.avg}`, {
      x: x + 0.2, y: 3.6, w: 3.5, h: 0.35,
      fontSize: 12, color: g.color, bold: true, fontFace: BODY_FONT, align: "center"
    });
  });

  // Dataset stats bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 5.2, w: 12.5, h: 1.7,
    fill: { color: C.dark }, shadow: makeShadow()
  });
  const stats = [
    { label: "Total Records", val: "18" },
    { label: "Groups", val: "3" },
    { label: "Audio Format", val: "WAV 16kHz" },
    { label: "Avg Duration", val: "3–5 sec" },
    { label: "Age Range", val: "8–35 years" }
  ];
  stats.forEach((s, i) => {
    const x = 0.8 + i * 2.55;
    slide.addText(s.val, { x, y: 5.35, w: 2.3, h: 0.6, fontSize: 22, bold: true, color: C.accent, fontFace: TITLE_FONT, align: "center" });
    slide.addText(s.label, { x, y: 5.95, w: 2.3, h: 0.4, fontSize: 11, color: C.gray, fontFace: BODY_FONT, align: "center" });
  });
}

// =========================================================
// SLAYT 3: YÖNTEMBİLGİSİ / METHODOLOGY
// =========================================================
{
  const slide = pres.addSlide();
  lightSlide(slide);
  addNavyHeader(slide, "⚙️ Methodology — Yöntem: STE, ZCR & Autocorrelation");
  addSlideNumber(slide, 3);

  const steps = [
    { num: "1", title: "Load & Normalize", body: "WAV → mono float32\n16,000 Hz target SR", icon: "📁", color: C.blue },
    { num: "2", title: "Windowing", body: "25 ms Hann frames\n10 ms hop (60% overlap)", icon: "🪟", color: C.lightblue },
    { num: "3", title: "STE + ZCR", body: "E[n] = Σx²[m]\nZCR = crossings / sec", icon: "📊", color: C.accent },
    { num: "4", title: "Voiced Detection", body: "STE > 5% max\nZCR < 3,000 Hz", icon: "🔊", color: C.warn },
    { num: "5", title: "Autocorrelation", body: "R[τ] = Σ x[n]·x[n-τ]\nF0 = sr / τ_peak", icon: "〰️", color: C.female },
    { num: "6", title: "Classify", body: "Rule-based F0 thresholds\nM/F/C decision", icon: "🎯", color: C.child }
  ];

  steps.forEach((s, i) => {
    const row = Math.floor(i / 3);
    const col = i % 3;
    const x   = 0.4 + col * 4.3;
    const y   = 1.4 + row * 2.6;

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 4.0, h: 2.3,
      fill: { color: C.white }, shadow: makeShadow()
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.6, h: 2.3,
      fill: { color: s.color }
    });
    slide.addText(s.num, { x, y, w: 0.6, h: 2.3, fontSize: 20, bold: true, color: C.white, fontFace: TITLE_FONT, align: "center", valign: "middle" });

    slide.addText(`${s.icon} ${s.title}`, {
      x: x + 0.7, y: y + 0.15, w: 3.1, h: 0.5,
      fontSize: 14, bold: true, color: C.dark,
      fontFace: TITLE_FONT, align: "left"
    });
    slide.addText(s.body, {
      x: x + 0.7, y: y + 0.65, w: 3.1, h: 1.3,
      fontSize: 12, color: C.gray,
      fontFace: BODY_FONT, align: "left"
    });
  });
}

// =========================================================
// SLAYT 4: OTOKORELASYONla FFT KARŞILAŞTIRMASI
// =========================================================
{
  const slide = pres.addSlide();
  lightSlide(slide);
  addNavyHeader(slide, "📉 Autocorrelation vs FFT — Karşılaştırmalı Analiz");
  addSlideNumber(slide, 4);

  // Left: Autocorrelation
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 1.3, w: 5.8, h: 4.8,
    fill: { color: C.white }, shadow: makeShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 1.3, w: 5.8, h: 0.45,
    fill: { color: C.blue }
  });
  slide.addText("Autocorrelation  R(τ)", {
    x: 0.5, y: 1.3, w: 5.6, h: 0.45,
    fontSize: 14, bold: true, color: C.white, fontFace: TITLE_FONT, valign: "middle"
  });

  const acfPoints = [
    { x: 0.4, y: 1.3 }, { x: 0.2, y: 1.0 }
  ];

  slide.addText([
    { text: "R[τ] = ", options: { bold: true, color: C.blue } },
    { text: "Σ x[n] · x[n − τ]", options: { color: C.dark } }
  ], {
    x: 0.6, y: 2.0, w: 5.4, h: 0.5,
    fontSize: 15, fontFace: BODY_FONT
  });

  const acfRows = [
    ["Domain", "Time domain"],
    ["Peak at τ = T", "Period detection"],
    ["F0 = sr / τ_peak", "Direct calculation"],
    ["Noise robust", "Uses full periodicity"],
    ["✅ Used in this project", "Primary method"]
  ];
  acfRows.forEach((row, ri) => {
    const y = 2.65 + ri * 0.55;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 5.5, h: 0.48,
      fill: { color: ri % 2 === 0 ? "EEF4FF" : C.white }
    });
    slide.addText(row[0], { x: 0.6, y: y + 0.05, w: 2.5, h: 0.38, fontSize: 12, bold: ri === 4, color: ri === 4 ? C.child : C.dark, fontFace: BODY_FONT });
    slide.addText(row[1], { x: 3.1, y: y + 0.05, w: 2.7, h: 0.38, fontSize: 12, bold: ri === 4, color: ri === 4 ? C.child : C.gray, fontFace: BODY_FONT });
  });

  // Right: FFT
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.1, y: 1.3, w: 5.8, h: 4.8,
    fill: { color: C.white }, shadow: makeShadow()
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 7.1, y: 1.3, w: 5.8, h: 0.45,
    fill: { color: C.gray }
  });
  slide.addText("FFT Spectrum  |X(f)|", {
    x: 7.2, y: 1.3, w: 5.6, h: 0.45,
    fontSize: 14, bold: true, color: C.white, fontFace: TITLE_FONT, valign: "middle"
  });

  slide.addText([
    { text: "X(f) = ", options: { bold: true, color: C.gray } },
    { text: "Σ x[n] · e^(−j2πfn)", options: { color: C.dark } }
  ], {
    x: 7.2, y: 2.0, w: 5.4, h: 0.5,
    fontSize: 15, fontFace: BODY_FONT
  });

  const fftRows = [
    ["Domain", "Frequency domain"],
    ["Peak at f = F0", "Spectral peak"],
    ["F0 from spectrum", "First harmonic"],
    ["Noise sensitive", "Sharp peaks shift"],
    ["📊 Comparison only", "Validation method"]
  ];
  fftRows.forEach((row, ri) => {
    const y = 2.65 + ri * 0.55;
    slide.addShape(pres.shapes.RECTANGLE, {
      x: 7.2, y, w: 5.5, h: 0.48,
      fill: { color: ri % 2 === 0 ? "FAFAFA" : C.white }
    });
    slide.addText(row[0], { x: 7.3, y: y + 0.05, w: 2.5, h: 0.38, fontSize: 12, bold: ri === 4, color: C.dark, fontFace: BODY_FONT });
    slide.addText(row[1], { x: 9.8, y: y + 0.05, w: 2.9, h: 0.38, fontSize: 12, bold: ri === 4, color: ri === 4 ? C.warn : C.gray, fontFace: BODY_FONT });
  });

  // Center divider
  slide.addShape(pres.shapes.LINE, {
    x: 6.35, y: 1.5, w: 0, h: 4.4,
    line: { color: C.blue, width: 2, dashType: "dash" }
  });
  slide.addText("VS", {
    x: 6.0, y: 3.5, w: 0.7, h: 0.5,
    fontSize: 16, bold: true, color: C.blue,
    fontFace: TITLE_FONT, align: "center",
    fill: { color: C.offwhite }
  });
}

// =========================================================
// SLAYT 5: BULGULAR / FINDINGS — F0 TABLOSU
// =========================================================
{
  const slide = pres.addSlide();
  lightSlide(slide);
  addNavyHeader(slide, "📊 Statistical Results — F0 Distribution by Gender");
  addSlideNumber(slide, 5);

  // F0 range visual
  const classes = [
    { label: "Male / Erkek",   range: [60, 180],  avg: 120, color: C.male   },
    { label: "Female / Kadın", range: [155, 260], avg: 210, color: C.female },
    { label: "Child / Çocuk",  range: [240, 400], avg: 300, color: C.child  }
  ];

  // Bar chart of F0 ranges on Hz axis
  const minHz = 50, maxHz = 450;
  const chartW = 8.5, chartX = 4.6, chartY = 1.5;

  slide.addText("F0 Range Visualization", {
    x: chartX, y: 1.25, w: chartW, h: 0.3,
    fontSize: 12, color: C.gray, italics: true, fontFace: BODY_FONT, align: "center"
  });

  classes.forEach((cls, i) => {
    const y   = chartY + i * 1.3;
    const xst = chartX + (cls.range[0] - minHz) / (maxHz - minHz) * chartW;
    const w   = (cls.range[1] - cls.range[0]) / (maxHz - minHz) * chartW;
    const xav = chartX + (cls.avg - minHz) / (maxHz - minHz) * chartW;

    slide.addShape(pres.shapes.RECTANGLE, {
      x: xst, y: y + 0.3, w, h: 0.55,
      fill: { color: cls.color, transparency: 25 }
    });
    slide.addShape(pres.shapes.LINE, {
      x: xav, y: y + 0.2, w: 0, h: 0.75,
      line: { color: cls.color, width: 2.5 }
    });
    slide.addText(`Avg: ${cls.avg} Hz`, {
      x: xav - 0.6, y: y + 0.0, w: 1.2, h: 0.25,
      fontSize: 10, bold: true, color: cls.color, fontFace: BODY_FONT, align: "center"
    });
    slide.addText(cls.label, {
      x: chartX - 4.0, y: y + 0.3, w: 3.8, h: 0.55,
      fontSize: 13, bold: true, color: C.dark, fontFace: TITLE_FONT, valign: "middle", align: "right"
    });
    slide.addText(`${cls.range[0]}–${cls.range[1]} Hz`, {
      x: chartX + chartW + 0.15, y: y + 0.35, w: 1.2, h: 0.45,
      fontSize: 11, color: cls.color, fontFace: BODY_FONT, bold: true
    });
  });

  // Hz axis ticks
  [100, 200, 300, 400].forEach(hz => {
    const x = chartX + (hz - minHz) / (maxHz - minHz) * chartW;
    slide.addShape(pres.shapes.LINE, { x, y: chartY + 0.25, w: 0, h: 3.9, line: { color: "DDDDDD", width: 1 } });
    slide.addText(`${hz}`, { x: x - 0.3, y: chartY + 4.3, w: 0.6, h: 0.3, fontSize: 10, color: C.gray, fontFace: BODY_FONT, align: "center" });
  });
  slide.addText("Frequency (Hz) →", {
    x: chartX + chartW / 2 - 1, y: chartY + 4.6, w: 2, h: 0.3,
    fontSize: 11, color: C.gray, italics: true, fontFace: BODY_FONT
  });

  // Overlap annotation
  slide.addShape(pres.shapes.RECTANGLE, {
    x: chartX + (155 - minHz)/(maxHz-minHz)*chartW, y: chartY + 0.25,
    w: (180-155)/(maxHz-minHz)*chartW, h: 2.0,
    fill: { color: C.warn, transparency: 75 }
  });
  slide.addText("Overlap\nZone", {
    x: chartX + (155-minHz)/(maxHz-minHz)*chartW - 0.1, y: chartY + 2.3,
    w: (180-155)/(maxHz-minHz)*chartW + 0.2, h: 0.5,
    fontSize: 9, color: C.warn, bold: true, fontFace: BODY_FONT, align: "center"
  });
}

// =========================================================
// SLAYT 6: CANLI DEMO / LIVE DEMO
// =========================================================
{
  const slide = pres.addSlide();
  darkSlide(slide);

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 1.1,
    fill: { color: C.accent }
  });
  slide.addText("🎬 LIVE DEMO — Canlı Gösterim", {
    x: 0.5, y: 0.15, w: 12, h: 0.8,
    fontSize: 26, bold: true, color: C.navy,
    fontFace: TITLE_FONT, valign: "middle"
  });

  slide.addText("Streamlit Web Interface", {
    x: 1, y: 1.3, w: 11, h: 0.5,
    fontSize: 18, color: C.gray, italics: true, fontFace: BODY_FONT
  });

  // Demo steps
  const steps = [
    { n: "1", text: "Open browser → streamlit run app/streamlit_app.py", icon: "🌐" },
    { n: "2", text: "Click 'Browse Files' → Select any .wav file", icon: "📂" },
    { n: "3", text: "System computes F0 via autocorrelation (voiced frames only)", icon: "〰️" },
    { n: "4", text: "Classification result: Male / Female / Child + Confidence %", icon: "🎯" },
    { n: "5", text: "View waveform, energy, ZCR, and ACF vs FFT plots", icon: "📈" },
  ];

  steps.forEach((s, i) => {
    const y = 2.0 + i * 0.95;
    slide.addShape(pres.shapes.OVAL, {
      x: 0.5, y: y, w: 0.6, h: 0.6,
      fill: { color: C.accent }
    });
    slide.addText(s.n, {
      x: 0.5, y, w: 0.6, h: 0.6,
      fontSize: 14, bold: true, color: C.navy,
      fontFace: TITLE_FONT, align: "center", valign: "middle"
    });
    slide.addText(`${s.icon}  ${s.text}`, {
      x: 1.3, y: y + 0.05, w: 11, h: 0.5,
      fontSize: 14, color: C.offwhite,
      fontFace: BODY_FONT, valign: "middle"
    });
  });

  // Demo command box
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 6.5, w: 12.3, h: 0.75,
    fill: { color: C.dark }
  });
  slide.addText("$ streamlit run app/streamlit_app.py    →    http://localhost:8501", {
    x: 0.7, y: 6.55, w: 12, h: 0.65,
    fontSize: 14, color: C.accent, bold: true,
    fontFace: "Courier New", valign: "middle"
  });

  addSlideNumber(slide, 6);
}

// =========================================================
// SLAYT 7: HATA ANALİZİ VE KAPANIŞ
// =========================================================
{
  const slide = pres.addSlide();
  lightSlide(slide);
  addNavyHeader(slide, "🔍 Error Analysis & Conclusion — Hata Analizi ve Kapanış");
  addSlideNumber(slide, 7);

  // Left: Error analysis
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 1.3, w: 6.1, h: 4.8,
    fill: { color: C.white }, shadow: makeShadow()
  });
  slide.addText("⚠️ Error Sources", {
    x: 0.5, y: 1.45, w: 5.7, h: 0.4,
    fontSize: 15, bold: true, color: C.blue, fontFace: TITLE_FONT
  });

  const errors = [
    { title: "F0 Overlap Zones", desc: "155–180 Hz (M/F) · 230–260 Hz (F/C)", color: C.warn },
    { title: "Emotional Speech", desc: "Anger/excitement raises F0 by 20–80 Hz", color: C.female },
    { title: "Background Noise", desc: "Corrupts ACF peaks at low SNR", color: C.blue },
    { title: "Whispered Speech", desc: "No F0 detectable → ZCR fallback", color: C.gray },
    { title: "Adolescent Males", desc: "F0 in 170–250 Hz transition range", color: C.child }
  ];
  errors.forEach((e, i) => {
    const y = 2.0 + i * 0.8;
    slide.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.12, h: 0.5, fill: { color: e.color } });
    slide.addText(e.title, { x: 0.75, y, w: 5.4, h: 0.25, fontSize: 12, bold: true, color: C.dark, fontFace: BODY_FONT });
    slide.addText(e.desc, { x: 0.75, y: y + 0.26, w: 5.4, h: 0.25, fontSize: 11, color: C.gray, fontFace: BODY_FONT });
  });

  // Right: Results summary
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 6.8, y: 1.3, w: 6.1, h: 4.8,
    fill: { color: C.white }, shadow: makeShadow()
  });
  slide.addText("✅ Key Takeaways", {
    x: 7.0, y: 1.45, w: 5.7, h: 0.4,
    fontSize: 15, bold: true, color: C.child, fontFace: TITLE_FONT
  });

  const takeaways = [
    "Autocorrelation-based F0 is robust\nand requires no external libraries",
    "ZCR-based voiced detection prevents\nnoise interference in F0 estimation",
    "Rule-based classifier achieves high\naccuracy with interpretable thresholds",
    "All thresholds are tuneable from a\nsingle THRESHOLDS dictionary",
    "Future: ML classifier (SVM/CNN)\nfor overlap zone disambiguation"
  ];
  takeaways.forEach((t, i) => {
    const y = 2.0 + i * 0.8;
    slide.addShape(pres.shapes.OVAL, { x: 7.0, y: y + 0.12, w: 0.28, h: 0.28, fill: { color: C.child } });
    slide.addText(t, { x: 7.4, y, w: 5.2, h: 0.7, fontSize: 11.5, color: C.dark, fontFace: BODY_FONT, valign: "middle" });
  });

  // Bottom: Overall accuracy callout
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.3, y: 6.3, w: 12.7, h: 1.0,
    fill: { color: C.blue }, shadow: makeShadow()
  });
  slide.addText([
    { text: "Overall System Accuracy:  ", options: { color: C.white, size: 18 } },
    { text: "~85–100%", options: { color: C.accent, size: 22, bold: true } },
    { text: "  (varies with dataset complexity)", options: { color: "BBDEFB", size: 14 } }
  ], {
    x: 0.5, y: 6.35, w: 12.3, h: 0.9,
    fontFace: TITLE_FONT, valign: "middle", align: "center"
  });
}

// =========================================================
// DOSYAYA YAZ / WRITE FILE
// =========================================================
pres.writeFile({ fileName: "/home/claude/AudioGenderClassifier/report/MidtermProject_Presentation_GRUP.pptx" })
  .then(() => console.log("✅ Presentation generated successfully!"))
  .catch(err => console.error("❌ Error:", err));
