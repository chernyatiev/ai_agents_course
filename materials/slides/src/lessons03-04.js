// Генератор презентации «Безопасность и состояние агента».
// Запуск: NODE_PATH=<папка с node_modules: pptxgenjs, react-icons, react, react-dom, sharp> \
//         node materials/slides/src/lessons03-04.js
// Результат: materials/slides/lessons03-04_security_and_bank.pptx
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa6");

const APPLY_THEME = process.env.APPLY_THEME_JS;
const OUT = path.join(__dirname, "..", "lessons03-04_security_and_bank.pptx");

// ---------- тема: «светофор разрешений» ----------
// Основной тон — графит (код, терминал), акценты — deny / ask / allow.
const THEME = {
  name: "Agents Course Traffic Light",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F24",   // графит: тёмные слайды, код
    lt1: "FFFFFF",
    dk2: "34424C",   // сланец: вторичный текст, разделы
    lt2: "EEF1F4",   // светлые карточки
    accent1: "E8A33D", // янтарь: ask / предупреждение — главный акцент
    accent2: "C8553D", // красный: deny
    accent3: "3A9D7A", // зелёный: allow / verified
    accent4: "4A6FA5", // сталь: harness
    accent5: "8A6FB0", // сиреневый: человек
    accent6: "7A8691", // серый: подписи
    hlink: "4A6FA5",
    folHlink: "8A6FB0",
  },
};
const HEX = THEME.colors;
const CODE_FONT = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333" × 7.5"
pres.title = "Безопасность и состояние агента";
pres.author = "Курс «ИИ-агенты с нуля»";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.333;

// ---------- иконки ----------
const iconCache = {};
async function icon(name, hex) {
  const key = `${name}-${hex}`;
  if (!iconCache[key]) {
    const svg = ReactDOMServer.renderToStaticMarkup(
      React.createElement(fa[name], { color: `#${hex}`, size: 256 })
    );
    const buf = await sharp(Buffer.from(svg)).png().toBuffer();
    iconCache[key] = "image/png;base64," + buf.toString("base64");
  }
  return iconCache[key];
}

// ---------- макеты ----------
const FOOTER = "Занятия 3–4 · ИИ-агенты с нуля";
pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6,
        fontSize: 44, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.95, w: 11.7, h: 0.9,
        fontSize: 22, color: C.accent1, valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECTION",
  background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 11.7, h: 1.3,
        fontSize: 40, bold: true, color: C.background1, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.05, w: 11.7, h: 1.0,
        fontSize: 20, color: C.background2, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.background2, align: "right" },
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85,
        fontSize: 34, bold: true, color: C.text1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOTER, options: { x: 0.6, y: 6.95, w: 6, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "DEMO",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 1.55, y: 0.35, w: 11.1, h: 0.85,
        fontSize: 34, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
    { text: { text: FOOTER, options: { x: 0.6, y: 6.95, w: 6, h: 0.3, fontSize: 10, color: C.accent6, margin: 0 } } },
  ],
  slideNumber: { x: 12.1, y: 6.95, w: 0.6, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
});

// ---------- помощники ----------
let current = "";
function slide(master, title, section) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section || current });
  if (title) s.addText(title, { placeholder: "title" });
  return s;
}
function section(title) {
  current = title;
  pres.addSection({ title });
}
function text(s, t, o) {
  s.addText(t, { isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top", ...o });
}
function card(s, x, y, w, h, fill = C.background2, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12,
    fill: { color: fill }, line: { color: fill, width: 0 }, objectName: name });
}
async function badge(s, x, y, d, iconName, fill, iconHex = HEX.lt1) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 } });
  const pad = d * 0.25;
  s.addImage({ data: await icon(iconName, iconHex), x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad });
}
// Код на тёмной карточке. lines — массив строк или [{text, color}] для подсветки.
function code(s, x, y, w, h, lines, fontSize = 14) {
  card(s, x, y, w, h, C.text1, "code");
  const runs = [];
  lines.forEach((ln, i) => {
    const parts = Array.isArray(ln) ? ln : [{ text: ln }];
    // Ведущие пробелы -> неразрывные: иначе PowerPoint может схлопнуть отступы кода.
    parts.forEach((p, j) => runs.push({ text: p.text.replace(/^ +/, m => "\u00A0".repeat(m.length)), options: {
      color: p.color || C.background2, bold: !!p.bold,
      breakLine: j === parts.length - 1 && i < lines.length - 1 } }));
  });
  s.addText(runs, { isTextBox: true, x: x + 0.25, y: y + 0.2, w: w - 0.5, h: h - 0.4,
    fontFace: CODE_FONT, fontSize, valign: "top", margin: 0, paraSpaceAfter: 2 });
}
function arrow(s, x1, y1, x2, y2, color = C.accent6) {
  s.addShape(pres.shapes.LINE, { x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width: 2, endArrowType: "triangle" } });
}
function bullets(s, items, o) {
  s.addText(items.map((it, i) => ({ text: it, options: { bullet: true, breakLine: i < items.length - 1 } })),
    { isTextBox: true, margin: 0, fontSize: 16, color: C.text1, valign: "top", paraSpaceAfter: 8, ...o });
}
// Узел потока: цветной кружок с иконкой и подпись под ним.
async function node(s, x, y, iconName, fill, label, sub, w = 2.2) {
  await badge(s, x + (w - 0.9) / 2, y, 0.9, iconName, fill);
  text(s, label, { x, y: y + 1.0, w, h: 0.4, fontSize: 16, bold: true, align: "center" });
  if (sub) text(s, sub, { x, y: y + 1.4, w, h: 0.7, fontSize: 14, color: C.text2, align: "center" });
}
// Полоса «модель → harness → человек» — сквозной мотив презентации.
async function trustStrip(s, y, labels, dark = false) {
  const xs = [1.3, 5.55, 9.8];
  const fills = [C.accent6, C.accent4, C.accent5];
  const icons = ["FaRobot", "FaGears", "FaUserTie"];
  for (let i = 0; i < 3; i++) {
    await badge(s, xs[i] + 0.65, y, 0.9, icons[i], fills[i]);
    text(s, labels[i][0], { x: xs[i], y: y + 1.0, w: 2.2, h: 0.4, fontSize: 18, bold: true, align: "center",
      color: dark ? C.background1 : C.text1 });
    if (labels[i][1]) text(s, labels[i][1], { x: xs[i] - 0.4, y: y + 1.45, w: 3.0, h: 1.0, fontSize: 14,
      align: "center", color: dark ? C.background2 : C.text2 });
    if (i < 2) arrow(s, xs[i] + 1.75, y + 0.45, xs[i + 1] + 0.45, y + 0.45, dark ? C.background2 : C.accent6);
  }
}
async function demoSlide(title, steps, notes) {
  const s = slide("DEMO", title);
  await badge(s, 0.6, 0.38, 0.8, "FaPlay", C.accent1, HEX.dk1);
  let y = 1.55;
  const h = (6.6 - y) / steps.length;
  steps.forEach((st, i) => {
    text(s, String(i + 1), { x: 0.6, y, w: 0.5, h: 0.5, fontSize: 24, bold: true, color: C.accent1 });
    text(s, st[0], { x: 1.2, y, w: 11.4, h: 0.45, fontSize: 18, bold: true, color: C.background1 });
    text(s, st[1], { x: 1.2, y: y + 0.45, w: 11.4, h: h - 0.55, fontSize: 12, fontFace: CODE_FONT,
      color: C.background2 });
    y += h;
  });
  s.addNotes(notes);
  return s;
}

(async () => {
  // =====================================================================
  section("Где мы");

  // 1. Титул
  {
    const s = slide("TITLE_DARK", "Безопасность и состояние агента");
    s.addText("Песочница, разрешения, банк задач", { placeholder: "body" });
    await trustStrip(s, 5.1, [["модель", ""], ["harness", ""], ["человек", ""]], true);
    text(s, "Референс: Learn Claude Code — s03 Permission, s12 Task System", {
      x: 0.8, y: 0.5, w: 11.7, h: 0.4, fontSize: 14, color: C.background2 });
    s.addNotes("Два занятия с одной общей мыслью: не доверяй модели, доверие обеспечивает harness. " +
      "Полоса внизу — модель, harness, человек — будет возвращаться на протяжении всей презентации.");
  }

  // 2. Где мы в курсе
  {
    const s = slide("CONTENT", "Где мы в курсе");
    const steps = [["1", "Цикл"], ["2", "Реестр"], ["3", "Разрешения"], ["4", "Банк задач"], ["5", "Проверяющий"]];
    steps.forEach((st, i) => {
      const x = 0.6 + i * 2.45, hot = i === 2 || i === 3;
      card(s, x, 1.5, 2.2, 1.1, hot ? C.accent1 : C.background2);
      text(s, st[0], { x: x + 0.15, y: 1.6, w: 0.45, h: 0.9, fontSize: 28, bold: true,
        color: hot ? C.text1 : C.accent6, valign: "middle" });
      text(s, st[1], { x: x + 0.6, y: 1.6, w: 1.55, h: 0.9, fontSize: 15, bold: true, valign: "middle" });
    });
    code(s, 0.6, 3.0, 7.2, 3.6, [
      "while True:",
      "    reply = chat(messages, tools.schemas())",
      "    messages.append(reply)",
      "    if not reply.tool_calls:",
      "        break",
      "    for call in reply.tool_calls:",
      "        messages.append(tool_result(call))",
    ], 15);
    await badge(s, 8.3, 3.2, 0.8, "FaRotate", C.accent4);
    text(s, "Цикл почти не меняется", { x: 9.3, y: 3.2, w: 3.4, h: 0.8, fontSize: 20, bold: true, valign: "middle" });
    text(s, "Занятие 3 добавляет в него одну строку. Занятие 4 не меняет его вообще: всё новое — инструменты и файлы.",
      { x: 8.3, y: 4.2, w: 4.4, h: 2.0, fontSize: 16, color: C.text2 });
    s.addNotes("Напомнить: курс следует разделам s01–s03 и s12 референса. Цикл из занятия 1 остаётся ядром.");
  }

  // 3. Итог занятия 2
  {
    const s = slide("CONTENT", "Итог занятия 2: агент умеет многое");
    const items = [
      ["FaListCheck", "Реестр инструментов", "Цикл не знает имён: tools.schemas() и tools.call(name, args)"],
      ["FaComments", "Ошибка — это данные", "Исключение в инструменте возвращается модели текстом, и она исправляет вызов"],
      ["FaScaleBalanced", "Единственность ответа", "z3_check доказывает, что у задачи ровно одно решение"],
    ];
    for (let i = 0; i < items.length; i++) {
      const y = 1.6 + i * 1.3;
      await badge(s, 0.6, y, 0.8, items[i][0], C.accent3);
      text(s, items[i][1], { x: 1.6, y, w: 5.2, h: 0.4, fontSize: 18, bold: true });
      text(s, items[i][2], { x: 1.6, y: y + 0.42, w: 5.2, h: 0.8, fontSize: 15, color: C.text2 });
    }
    card(s, 7.3, 1.6, 5.4, 3.6, C.accent1);
    await badge(s, 7.6, 1.9, 0.8, "FaTriangleExclamation", C.text1);
    text(s, "Но", { x: 8.6, y: 1.9, w: 3.8, h: 0.8, fontSize: 28, bold: true, valign: "middle" });
    text(s, "Модель может передать в eval что угодно — и мы это выполним. В том же процессе, где лежит ключ API.",
      { x: 7.6, y: 2.9, w: 4.8, h: 2.1, fontSize: 18 });
    s.addNotes("Короткое повторение. Главное — подвести к слабому месту: строки от модели выполняются через eval.");
  }

  // =====================================================================
  section("Ломаем lesson02");
  {
    const s = slide("SECTION", "Часть 1. Ломаем lesson02");
    s.addText("Почему пустой __builtins__ — не песочница", { placeholder: "body" });
    s.addNotes("Переход к практике: сначала ломаем, потом чиним.");
  }

  // 4. Пустой builtins
  {
    const s = slide("CONTENT", "Пустой __builtins__ — не песочница");
    code(s, 0.6, 1.5, 12.1, 1.5, [
      [{ text: "python_eval(" }],
      [{ text: "  \"[c.__name__ for c in ().__class__.__base__.__subclasses__()" }],
      [{ text: "     if c.__name__ == 'Popen']\")" }, { text: "   →  ['Popen']", color: C.accent1, bold: true }],
    ], 15);
    const chain = [["()", "пустой кортеж"], [".__class__", "tuple"], [".__base__", "object"],
      [".__subclasses__()", "≈ 488 классов"], ["Popen", "запуск программ"]];
    chain.forEach((c, i) => {
      const x = 0.6 + i * 2.5, last = i === chain.length - 1;
      card(s, x, 3.5, 2.1, 1.3, last ? C.accent2 : C.background2);
      text(s, c[0], { x: x + 0.05, y: 3.6, w: 2.0, h: 0.55, fontSize: 13, bold: true, fontFace: CODE_FONT,
        align: "center", color: last ? C.background1 : C.text1 });
      text(s, c[1], { x: x + 0.1, y: 4.15, w: 1.9, h: 0.5, fontSize: 14, align: "center",
        color: last ? C.background1 : C.text2 });
      if (!last) arrow(s, x + 2.12, 4.15, x + 2.48, 4.15);
    });
    text(s, "Из любого объекта видна вся иерархия классов интерпретатора. Ограничить список имён в eval недостаточно.",
      { x: 0.6, y: 5.3, w: 12.1, h: 0.9, fontSize: 18, color: C.text2 });
    s.addNotes("Проверено на lesson02: результат ['Popen']. Popen — класс для запуска любых программ, " +
      "то есть модель получает полный доступ к компьютеру.");
  }

  // 5. Та же дыра везде
  {
    const s = slide("CONTENT", "Та же дыра — в «чистой математике»");
    const cards = [
      ["FaTerminal", "python_eval", "eval выражения", "→ ['Popen']", C.accent2],
      ["FaPuzzlePiece", "z3_check", "eval каждого ограничения", "→ 488 классов", C.accent2],
      ["FaFileCode", "sympy_simplify", "parse_expr внутри вызывает eval", "→ 488 классов", C.accent2],
      ["FaHourglassHalf", "sum(range(10**12))", "таймаута нет", "→ REPL висит", C.accent1],
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      card(s, x, 1.6, 2.85, 4.1);
      await badge(s, x + 0.3, 1.9, 0.85, cards[i][0], cards[i][4]);
      text(s, cards[i][1], { x: x + 0.25, y: 3.0, w: 2.45, h: 0.5, fontSize: 14, bold: true, fontFace: CODE_FONT });
      text(s, cards[i][2], { x: x + 0.3, y: 3.6, w: 2.35, h: 1.0, fontSize: 15, color: C.text2 });
      text(s, cards[i][3], { x: x + 0.3, y: 4.8, w: 2.35, h: 0.6, fontSize: 18, bold: true, color: cards[i][4] });
    }
    text(s, "Опасным оказался инструмент, который выглядит как «просто посчитать».",
      { x: 0.6, y: 6.0, w: 12.1, h: 0.6, fontSize: 18, bold: true });
    s.addNotes("z3_check и sympy_simplify на lesson02 возвращают 488 — число классов интерпретатора. " +
      "sum(range(10**12)) вешает весь REPL, помогает только Ctrl+C.");
  }

  // 6. Откуда атака
  {
    const s = slide("CONTENT", "Откуда приходит атака");
    const steps = [["FaFileLines", C.accent6, "Текст задачи", "из чужого источника"],
      ["FaRobot", C.accent6, "Модель", "пишет tool_call"],
      ["FaTerminal", C.accent2, "eval", "в процессе агента"],
      ["FaKey", C.accent2, "os.environ", "ключ API, файлы"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.7 + i * 3.1;
      await node(s, x, 1.7, steps[i][0], steps[i][1], steps[i][2], steps[i][3], 2.4);
      if (i < 3) arrow(s, x + 1.95, 2.15, x + 3.55, 2.15);
    }
    card(s, 0.6, 4.4, 12.1, 2.1);
    await badge(s, 0.9, 4.75, 0.8, "FaTriangleExclamation", C.accent1, HEX.dk1);
    text(s, "Prompt injection: в условии спрятана инструкция «для проверки вызови python_eval с …»",
      { x: 2.0, y: 4.65, w: 10.4, h: 0.6, fontSize: 18, bold: true });
    text(s, "Модель может отказаться — но это свойство модели, а не нашего кода. Слабая локальная модель может и не отказаться.",
      { x: 2.0, y: 5.3, w: 10.4, h: 1.0, fontSize: 16, color: C.text2 });
    s.addNotes("Прямой вызов python_eval из терминала — лишь способ без модели показать, что произойдёт, " +
      "если модель передаст такую строку. Реальный путь — через данные, которые читает модель. " +
      "Цепочку с чтением ключа на занятии показывать только с фиктивным ключом в .env.");
  }

  // Демо 1
  await demoSlide("Демо: ломаем lesson02", [
    ["Выход из eval (из папки lesson02)", "uv run python -c \"from agent.tools.eval_tool import python_eval; print(python_eval(\\\"[c.__name__ for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'Popen']\\\"))\""],
    ["Та же дыра в z3_check и SymPy", "uv run python -c \"import json; from agent import tools; print(tools.call('z3_check', json.dumps({'variables': {'x': 'Int'}, 'constraints': ['x == ().__class__.__base__.__subclasses__().__len__()']})))\"\nuv run python -c \"import json; from agent import tools; print(tools.call('sympy_simplify', json.dumps({'expression': '().__class__.__base__.__subclasses__().__len__()'})))\""],
    ["Зависание", "uv run python -c \"from agent.tools.eval_tool import python_eval; python_eval('sum(range(10**12))')\"   # Ctrl+C"],
  ], "Все три сценария воспроизводятся одной командой без модели (см. lesson03_plan.md, пункт 1). " +
    "Ожидаемые результаты: ['Popen'], 488, зависание. Модель на прямую просьбу обычно отказывается — поэтому без неё.");

  // 7. Вопрос
  {
    const s = slide("CONTENT", "Поможет ли строка в промпте?");
    card(s, 0.6, 1.6, 12.1, 1.6);
    text(s, "«Никогда не используй __ и import в выражениях»", { x: 1.0, y: 1.6, w: 11.3, h: 1.6,
      fontSize: 26, italic: true, valign: "middle", color: C.text2 });
    await badge(s, 0.6, 3.8, 1.1, "FaBan", C.accent2);
    text(s, "Нет", { x: 1.9, y: 3.8, w: 3, h: 1.1, fontSize: 40, bold: true, valign: "middle", color: C.accent2 });
    bullets(s, [
      "Промпт — пожелание модели, а не ограничение",
      "Опасный текст может прийти из данных, а не от пользователя",
      "Безопасность обеспечивает код harness — до выполнения вызова",
    ], { x: 5.2, y: 3.75, w: 7.5, h: 2.6, fontSize: 18 });
    s.addNotes("Спросить аудиторию до того, как показать ответ. Это тезис референса s03: safety can't rely on trusting the model.");
  }

  // =====================================================================
  section("Занятие 3");
  {
    const s = slide("SECTION", "Часть 2. Разрешения и песочница");
    s.addText("Занятие 3 · s03 Permission", { placeholder: "body" });
    s.addNotes("Начало занятия 3.");
  }

  // 8. Два слоя
  {
    const s = slide("CONTENT", "Два слоя защиты");
    const cols = [
      ["FaShieldHalved", C.accent4, "Разрешения", "Можно ли выполнять этот вызов?", "permissions.py",
        "deny → ask → allow, до выполнения"],
      ["FaBoxArchive", C.accent3, "Песочница", "Что может натворить разрешённый вызов?", "sandbox.py",
        "отдельный процесс, таймаут, лимиты"],
    ];
    for (let i = 0; i < 2; i++) {
      const x = 0.6 + i * 6.2;
      card(s, x, 1.6, 5.9, 4.6);
      await badge(s, x + 0.4, 1.95, 1.0, cols[i][0], cols[i][1]);
      text(s, cols[i][2], { x: x + 1.7, y: 1.95, w: 3.9, h: 1.0, fontSize: 26, bold: true, valign: "middle" });
      text(s, cols[i][3], { x: x + 0.4, y: 3.25, w: 5.1, h: 1.0, fontSize: 20 });
      text(s, cols[i][4], { x: x + 0.4, y: 4.45, w: 5.1, h: 0.5, fontSize: 16, bold: true, fontFace: CODE_FONT, color: cols[i][1] });
      text(s, cols[i][5], { x: x + 0.4, y: 5.0, w: 5.1, h: 0.9, fontSize: 16, color: C.text2 });
    }
    s.addNotes("Важно не путать слои: разрешения — политика, песочница — ограничение последствий. " +
      "Ни один слой не идеален, поэтому нужны оба.");
  }

  // 9. Одна вставка
  {
    const s = slide("CONTENT", "Одна вставка в цикл");
    code(s, 0.6, 1.5, 7.6, 3.9, [
      "for call in reply.tool_calls:",
      "    name, arguments = ...",
      [{ text: "    decision = permissions.check(name, arguments, ask=ask)", color: C.accent1, bold: true }],
      "    if decision.allowed:",
      "        result = tools.call(name, arguments)",
      "    else:",
      [{ text: "        result = f\"Отказано: {decision.reason}\"", color: C.accent1, bold: true }],
      "    messages.append(tool_result(call.id, result))",
    ], 14);
    const pts = [["FaComments", "Отказ — это данные", "Как ошибка в занятии 2: модель видит причину и меняет подход"],
      ["FaKeyboard", "ask — параметр", "Как chat: в тестах вопрос пользователю подменяется функцией"]];
    for (let i = 0; i < 2; i++) {
      const y = 1.6 + i * 1.9;
      await badge(s, 8.6, y, 0.8, pts[i][0], C.accent4);
      text(s, pts[i][1], { x: 9.6, y, w: 3.1, h: 0.45, fontSize: 18, bold: true });
      text(s, pts[i][2], { x: 9.6, y: y + 0.5, w: 3.1, h: 1.2, fontSize: 15, color: C.text2 });
    }
    text(s, "lesson03/src/agent/loop.py", { x: 0.6, y: 5.6, w: 7.6, h: 0.4, fontSize: 12, color: C.accent6, fontFace: CODE_FONT });
    s.addNotes("Показать diff lesson02 → lesson03 для loop.py: структура цикла та же, добавилась проверка.");
  }

  // 10. Три ворот
  {
    const s = slide("CONTENT", "Три ворот перед каждым вызовом");
    const gates = [
      ["FaBan", C.accent2, "1. Deny", "Жёсткий запрет", "AST: __dunder__, getattr, open, import вне белого списка"],
      ["FaFilter", C.accent1, "2. Rules", "Когда спросить", "python_run, таймаут > 5 с, константа > 10⁷"],
      ["FaCircleQuestion", C.accent1, "3. Ask", "Вопрос человеку", "y / N / a — всегда для инструмента"],
      ["FaCircleCheck", C.accent3, "Allow", "Выполнить", "Так проходит большинство вызовов"],
    ];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + i * 3.1;
      card(s, x, 1.6, 2.8, 4.3);
      await badge(s, x + 0.95, 1.85, 0.9, gates[i][0], gates[i][1], i === 1 || i === 2 ? HEX.dk1 : HEX.lt1);
      text(s, gates[i][2], { x: x + 0.2, y: 2.9, w: 2.4, h: 0.5, fontSize: 22, bold: true, align: "center", color: gates[i][1] });
      text(s, gates[i][3], { x: x + 0.2, y: 3.45, w: 2.4, h: 0.45, fontSize: 16, bold: true, align: "center" });
      text(s, gates[i][4], { x: x + 0.25, y: 4.0, w: 2.3, h: 1.7, fontSize: 15, color: C.text2, align: "center" });
      if (i < 3) arrow(s, x + 2.82, 3.75, x + 3.08, 3.75);
    }
    text(s, "Порядок фиксирован: deny проверяется первым и действует в любом режиме — даже после ответа «a».",
      { x: 0.6, y: 6.15, w: 12.1, h: 0.5, fontSize: 16, bold: true });
    s.addNotes("Совпадение на воротах 1 — отказ без вопросов. Ворота 2 не отказывают, а передают решение человеку. " +
      "Пустой ответ, EOF и отсутствие функции ask — это отказ.");
  }

  // 11. AST
  {
    const s = slide("CONTENT", "Ворота 1: AST вместо подстрок");
    code(s, 0.6, 1.5, 6.4, 4.7, [
      "tree = ast.parse(code, mode=mode)",
      "for node in ast.walk(tree):",
      "    if isinstance(node, ast.Attribute) \\",
      "            and node.attr.startswith('_'):",
      "        return 'скрытый атрибут'",
      "    if isinstance(node, ast.Name) \\",
      "            and node.id in BANNED_NAMES:",
      "        return 'запрещённое имя'",
      "    if isinstance(node, ast.Constant) \\",
      "            and '__' in str(node.value):",
      "        return 'строка с __'",
    ], 13);
    const rows = [["().__class__", "атрибут на _"], ["'{0.__class__}'.format(())", "строка с __"],
      ["f'{().__class__}'", "атрибут в f-строке"], ["getattr((), 'x')", "запрещённое имя"],
      ["import os  (python_run)", "модуль вне списка"]];
    text(s, "Что ловится", { x: 7.4, y: 1.5, w: 5.3, h: 0.45, fontSize: 18, bold: true });
    rows.forEach((r, i) => {
      const y = 2.05 + i * 0.8;
      card(s, 7.4, y, 5.3, 0.68);
      text(s, r[0], { x: 7.6, y, w: 3.2, h: 0.68, fontSize: 13, fontFace: CODE_FONT, valign: "middle" });
      text(s, r[1], { x: 10.8, y, w: 1.8, h: 0.68, fontSize: 14, color: C.accent2, bold: true, valign: "middle" });
    });
    s.addNotes("В референсе запреты сделаны поиском подстроки, и там честно сказано, что это ненадёжно. " +
      "AST — шаг вперёд, но тоже не граница безопасности: обход покажем на слайде «Пределы защиты».");
  }

  // 12. Rules + Ask
  {
    const s = slide("CONTENT", "Ворота 2–3: правила и вопрос человеку");
    text(s, "RULES — когда спросить", { x: 0.6, y: 1.5, w: 5.6, h: 0.45, fontSize: 18, bold: true });
    const rules = [["python_run", "любой запуск скрипта"], ["python_run, timeout > 5", "долгий запуск"],
      ["python_eval / python_run", "константа больше 10⁷ (10**8, 9**9**9)"]];
    for (let i = 0; i < 3; i++) {
      const y = 2.1 + i * 1.25;
      await badge(s, 0.6, y, 0.7, "FaFilter", C.accent1, HEX.dk1);
      text(s, rules[i][0], { x: 1.5, y, w: 4.8, h: 0.4, fontSize: 15, bold: true, fontFace: CODE_FONT });
      text(s, rules[i][1], { x: 1.5, y: y + 0.42, w: 4.8, h: 0.6, fontSize: 15, color: C.text2 });
    }
    code(s, 6.6, 1.5, 6.1, 3.9, [
      [{ text: "⚠  Запуск скрипта Python", color: C.accent1, bold: true }],
      "   Инструмент: python_run",
      "   code:",
      "      total = 0",
      "      for n in range(100000, 1000000):",
      "          ...",
      "      print(total)",
      [{ text: "   Разрешить? [y/N/a] ", color: C.background1, bold: true }],
    ], 14);
    text(s, "Пустой ответ = отказ. Безопасный вариант по умолчанию.", { x: 6.6, y: 5.6, w: 6.1, h: 0.5, fontSize: 16, bold: true });
    s.addNotes("Все сработавшие правила показываются одной строкой, чтобы пользователь видел все причины сразу.");
  }

  // 13. Режимы
  {
    const s = slide("CONTENT", "Режимы: меняется только ворота 3");
    const modes = [["default", "спросить пользователя", "default", C.accent1],
      ["auto", "разрешить без вопроса", "bypassPermissions", C.accent3],
      ["strict", "отказать без вопроса", "plan / dontAsk", C.accent2]];
    modes.forEach((m, i) => {
      const x = 0.6 + i * 4.1;
      card(s, x, 1.6, 3.8, 3.4);
      s.addShape(pres.shapes.OVAL, { x: x + 0.35, y: 1.95, w: 0.45, h: 0.45, fill: { color: m[3] }, line: { color: m[3], width: 0 } });
      text(s, m[0], { x: x + 1.0, y: 1.9, w: 2.6, h: 0.55, fontSize: 24, bold: true, fontFace: CODE_FONT, valign: "middle" });
      text(s, m[1], { x: x + 0.35, y: 2.8, w: 3.2, h: 0.9, fontSize: 18 });
      text(s, "Claude Code: " + m[2], { x: x + 0.35, y: 4.1, w: 3.2, h: 0.6, fontSize: 14, color: C.text2 });
    });
    code(s, 0.6, 5.35, 12.1, 1.2, ["uv run agent --mode strict        /mode auto   — сменить на ходу"], 15);
    s.addNotes("Ворота 1 действуют в любом режиме. Режим влияет только на то, что делать с вызовами, которые требуют вопроса.");
  }

  // 14. Песочница
  {
    const s = slide("CONTENT", "Песочница: ограничить последствия");
    const rows = [["FaCubes", "Отдельный процесс", "run_isolated: зависание или падение не роняет REPL"],
      ["FaClock", "Таймаут по часам", "python_eval 5 с, SymPy 15 с, z3 30 с — процесс убивается"],
      ["FaMicrochip", "Лимиты ОС", "setrlimit: CPU, размер файлов, память"],
      ["FaLock", "python_run", "python -I, env={} — ключ API не виден, временная пустая папка"]];
    for (let i = 0; i < rows.length; i++) {
      const y = 1.55 + i * 1.12;
      await badge(s, 0.6, y, 0.8, rows[i][0], C.accent3);
      text(s, rows[i][1], { x: 1.6, y, w: 5.6, h: 0.4, fontSize: 18, bold: true });
      text(s, rows[i][2], { x: 1.6, y: y + 0.42, w: 5.6, h: 0.6, fontSize: 15, color: C.text2 });
    }
    card(s, 7.7, 1.55, 5.0, 4.4, C.accent1);
    await badge(s, 8.0, 1.85, 0.8, "FaTriangleExclamation", C.text1);
    text(s, "Честно", { x: 9.0, y: 1.85, w: 3.5, h: 0.8, fontSize: 24, bold: true, valign: "middle" });
    bullets(s, ["macOS не даёт ограничить память", "Windows: работает только таймаут",
      "Процесс видит файлы пользователя", "Настоящая изоляция: контейнер, nsjail, ВМ"],
      { x: 8.0, y: 2.9, w: 4.5, h: 2.9, fontSize: 16 });
    s.addNotes("Это учебная песочница, не граница безопасности. Таймаут подключается одним параметром: register(..., timeout=5).");
  }

  // 15. python_run
  {
    const s = slide("CONTENT", "python_run — опасный инструмент");
    code(s, 0.6, 1.5, 6.6, 3.6, [
      "def digit_sum(x):",
      "    return sum(map(int, str(x)))",
      "",
      "count = sum(1 for n in range(100000, 1000000)",
      "            if digit_sum(n // 1000) == digit_sum(n % 1000))",
      "print(count)",
    ], 14);
    text(s, "Ответ: 50412", { x: 0.6, y: 5.3, w: 6.6, h: 0.5, fontSize: 20, bold: true, color: C.accent3 });
    text(s, "Зачем", { x: 7.7, y: 1.5, w: 5, h: 0.45, fontSize: 20, bold: true });
    text(s, "Олимпиадные задачи удобно проверять перебором с циклами и функциями — одного выражения мало.",
      { x: 7.7, y: 2.0, w: 5, h: 1.2, fontSize: 16, color: C.text2 });
    text(s, "Поэтому", { x: 7.7, y: 3.4, w: 5, h: 0.45, fontSize: 20, bold: true });
    bullets(s, ["каждый запуск — вопрос человеку", "отдельный интерпретатор с лимитами",
      "import только из белого списка"], { x: 7.7, y: 3.9, w: 5, h: 2.0, fontSize: 16 });
    s.addNotes("У инструмента появился честный повод для разрешений — не приходится придумывать искусственный bash. " +
      "50412 — шестизначные числа без ведущих нулей; 55252 было бы с ведущими нулями.");
  }

  // Демо 2
  await demoSlide("Демо: разрешения в деле", [
    ["Скрипт с подтверждением", "cd lesson03 && uv run agent -v\n«Сколько шестизначных чисел, у которых сумма первых трёх цифр равна сумме последних трёх? Проверь перебором скриптом.» → y → 50412"],
    ["Отказ", "Тот же вопрос → N → модель переходит на python_eval → 50412"],
    ["Режимы", "uv run agent --mode auto   — без вопроса\nuv run agent --mode strict — отказ, модель обходится без python_run"],
    ["Таймаут: TimeoutError через 5 с", "uv run python -c \"from agent import tools; print(tools.call('python_eval', '{\\\"expression\\\": \\\"sum(range(10**12))\\\"}'))\""],
  ], "Все сценарии проверены с настоящей моделью. Эксплойт показывать тестом: uv run --group dev pytest -k denied -v — " +
    "модели сами отказываются вызывать __subclasses__. Если пишете свой скрипт с run_turn — нужен if __name__ == '__main__'.");

  // 16. Пределы
  {
    const s = slide("CONTENT", "Пределы защиты");
    code(s, 0.6, 1.5, 6.6, 2.2, [
      "from sympy import sympify",
      "u = chr(95) * 2",
      "print(sympify(u + 'import' + u + \"('os').getcwd()\"))",
    ], 14);
    text(s, "Проходит ворота 1: в коде нет ни __, ни запрещённых имён. sympify сам вызывает eval.",
      { x: 0.6, y: 3.95, w: 6.6, h: 1.0, fontSize: 16, color: C.text2 });
    text(s, "Поэтому python_run спрашивает всегда", { x: 0.6, y: 5.1, w: 6.6, h: 0.6, fontSize: 20, bold: true, color: C.accent2 });
    const layers = [["FaBan", C.accent2, "Deny", "ловит очевидное"], ["FaUserCheck", C.accent5, "Человек", "видит код и решает"],
      ["FaBoxArchive", C.accent3, "Песочница", "ограничивает ущерб"]];
    for (let i = 0; i < 3; i++) {
      const y = 1.5 + i * 1.6;
      card(s, 7.7, y, 5.0, 1.35);
      await badge(s, 7.95, y + 0.25, 0.85, layers[i][0], layers[i][1]);
      text(s, layers[i][2], { x: 9.0, y: y + 0.2, w: 3.5, h: 0.5, fontSize: 20, bold: true });
      text(s, layers[i][3], { x: 9.0, y: y + 0.7, w: 3.5, h: 0.5, fontSize: 15, color: C.text2 });
    }
    s.addNotes("Проверено: скрипт проходит AST-проверку и выполняется, если ответить y. Ни один слой не идеален — " +
      "защита многослойная. Это упражнение 3 занятия 3.");
  }

  // =====================================================================
  section("Занятие 4");
  {
    const s = slide("SECTION", "Часть 3. Банк задач");
    s.addText("Занятие 4 · s12 Task System, идея из s09 Memory", { placeholder: "body" });
    s.addNotes("Начало занятия 4. Если занятия идут в разные дни — презентация делится здесь.");
  }

  // 17. Мотивация
  {
    const s = slide("CONTENT", "Где живёт задача, утверждённая вчера?");
    const st = [["FaLightbulb", C.accent3, "Придумали", "агент проверил ответ"], ["FaKeyboard", C.accent6, "/exit", "закрыли сессию"],
      ["FaPlay", C.accent6, "Запустили снова", "«покажи вчерашнюю задачу»"], ["FaCircleXmark", C.accent2, "Пусто", "задачи нет"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.7 + i * 3.1;
      await node(s, x, 1.8, st[i][0], st[i][1], st[i][2], st[i][3], 2.4);
      if (i < 3) arrow(s, x + 1.95, 2.25, x + 3.55, 2.25);
    }
    card(s, 0.6, 4.6, 12.1, 1.6);
    text(s, [{ text: "Вся «память» агента — массив ", options: {} },
      { text: "messages", options: { fontFace: CODE_FONT, bold: true } },
      { text: ". Он живёт до /reset или выхода.", options: {} }],
      { x: 1.0, y: 4.6, w: 11.3, h: 1.6, fontSize: 22, valign: "middle" });
    s.addNotes("Показать вживую в lesson03: придумать задачу, выйти, запустить снова.");
  }

  // 18. Состояние вне контекста
  {
    const s = slide("CONTENT", "Состояние вне контекста модели");
    card(s, 0.6, 1.6, 5.6, 2.5);
    await badge(s, 0.9, 1.9, 0.8, "FaComments", C.accent6);
    text(s, "messages", { x: 1.9, y: 1.9, w: 4, h: 0.8, fontSize: 24, bold: true, fontFace: CODE_FONT, valign: "middle" });
    text(s, "в памяти процесса, до /reset или выхода", { x: 0.9, y: 2.95, w: 5.0, h: 0.9, fontSize: 17, color: C.text2 });
    card(s, 7.1, 1.6, 5.6, 2.5, C.accent3);
    await badge(s, 7.4, 1.9, 0.8, "FaDatabase", C.text1);
    text(s, "bank/", { x: 8.4, y: 1.9, w: 4, h: 0.8, fontSize: 24, bold: true, fontFace: CODE_FONT, valign: "middle", color: C.background1 });
    text(s, "на диске, переживает перезапуск", { x: 7.4, y: 2.95, w: 5.0, h: 0.9, fontSize: 17, color: C.background1 });
    text(s, "Цикл не меняется вообще: новое — инструменты, файлы и команды REPL",
      { x: 0.6, y: 4.4, w: 12.1, h: 0.5, fontSize: 18, bold: true });
    const t = [["", "TodoWrite (s05)", "Task System (s12) / банк"], ["Хранение", "в сессии", "файл на запись"],
      ["Жизнь", "текущая задача", "между сессиями"]];
    s.addTable(t.map((r, i) => r.map(c => ({ text: c, options: { bold: i === 0, fontSize: 14,
      color: C.text1, fill: { color: i === 0 ? C.background2 : C.background1 } } }))),
      { x: 0.6, y: 5.05, w: 12.1, colW: [2.5, 4.8, 4.8], rowH: 0.42, border: { type: "solid", pt: 1, color: HEX.lt2 } });
    s.addNotes("Связь с референсом: TodoWrite живёт в сессии, Task System хранит задачи в .tasks/ по одному JSON-файлу.");
  }

  // 19. Запись задачи
  {
    const s = slide("CONTENT", "Запись задачи: bank/P-0001.json");
    const A = C.accent1;
    code(s, 0.6, 1.5, 7.4, 5.1, [
      "{",
      "  \"id\": \"P-0001\",  \"grade\": 6,  \"topic\": \"делимость\",",
      "  \"statement\": \"Найдите наименьшее n > 1, ...\",",
      [{ text: "  \"answer\": {\"n\": 61},", color: A, bold: true }],
      "  \"solution\": \"n − 1 делится на НОК(3, 4, 5) = 60 ...\",",
      [{ text: "  \"verification\": {", color: A, bold: true }],
      "    \"tool\": \"z3_check\",  \"arguments\": {...},",
      "    \"result\": {\"solution\": {\"n\": 61}, \"unique\": true},",
      "    \"ok\": true",
      "  },",
      [{ text: "  \"status\": \"verified\",", color: A, bold: true }],
      [{ text: "  \"review\": null", color: A, bold: true }],
      "}",
    ], 13);
    const notes = [["answer", "ответ, который заявила модель"], ["verification", "проверочный вызов и его результат"],
      ["status", "ставит harness или преподаватель"], ["review", "комментарий преподавателя при отказе"]];
    notes.forEach((n, i) => {
      const y = 1.6 + i * 1.25;
      card(s, 8.4, y, 4.3, 1.05);
      text(s, n[0], { x: 8.65, y: y + 0.1, w: 3.9, h: 0.4, fontSize: 16, bold: true, fontFace: CODE_FONT, color: C.accent4 });
      text(s, n[1], { x: 8.65, y: y + 0.5, w: 3.9, h: 0.5, fontSize: 15, color: C.text2 });
    });
    s.addNotes("Полный формат — в README занятия 4. Обратить внимание: в записи хранится не только ответ, но и чем он проверен.");
  }

  // 20. Один файл
  {
    const s = slide("CONTENT", "Один файл на запись");
    const pts = [["FaEye", "Читается глазами", "открыть в редакторе и понять без кода"],
      ["FaCodeCompare", "git diff по делу", "видно, что именно изменилось в задаче"],
      ["FaSkull", "Порча локальна", "битый файл ломает одну задачу, не весь банк"]];
    for (let i = 0; i < 3; i++) {
      const x = 0.6 + i * 4.1;
      card(s, x, 1.6, 3.8, 2.6);
      await badge(s, x + 0.35, 1.9, 0.85, pts[i][0], C.accent4);
      text(s, pts[i][1], { x: x + 0.35, y: 2.9, w: 3.2, h: 0.45, fontSize: 18, bold: true });
      text(s, pts[i][2], { x: x + 0.35, y: 3.4, w: 3.2, h: 0.75, fontSize: 15, color: C.text2 });
    }
    text(s, "Атомарная запись", { x: 0.6, y: 4.55, w: 5, h: 0.45, fontSize: 18, bold: true });
    code(s, 0.6, 5.05, 7.6, 1.5, [
      "tmp.write_text(json.dumps(record, ...))",
      [{ text: "os.replace(tmp, path)", color: C.accent1, bold: true }, { text: "   # мгновенная подмена" }],
    ], 14);
    text(s, "Упал посреди записи — старый файл остался целым, обрезанного JSON не будет.",
      { x: 8.6, y: 5.05, w: 4.1, h: 1.5, fontSize: 16, color: C.text2 });
    s.addNotes("Сравнить с одним большим bank.json: конфликт при каждом изменении, одна ошибка — весь банк.");
  }

  // 21. Жизненный цикл
  {
    const s = slide("CONTENT", "Жизненный цикл задачи");
    const st = [["draft", C.accent6, 0.8], ["verified", C.accent3, 5.15], ["approved", C.accent4, 9.5]];
    st.forEach(([name, color, x]) => {
      card(s, x, 2.0, 3.0, 1.1, color);
      text(s, name, { x, y: 2.0, w: 3.0, h: 1.1, fontSize: 24, bold: true, fontFace: CODE_FONT, align: "center",
        valign: "middle", color: C.background1 });
    });
    arrow(s, 3.85, 2.55, 5.1, 2.55);
    arrow(s, 8.2, 2.55, 9.45, 2.55);
    text(s, "harness\nперепроверил", { x: 3.75, y: 1.3, w: 1.5, h: 0.65, fontSize: 13, align: "center", color: C.text2 });
    text(s, "/approve", { x: 8.1, y: 1.55, w: 1.5, h: 0.4, fontSize: 14, align: "center", bold: true, fontFace: CODE_FONT, color: C.accent5 });
    card(s, 5.15, 4.1, 3.0, 1.1, C.accent2);
    text(s, "rejected", { x: 5.15, y: 4.1, w: 3.0, h: 1.1, fontSize: 24, bold: true, fontFace: CODE_FONT, align: "center",
      valign: "middle", color: C.background1 });
    arrow(s, 6.65, 3.15, 6.65, 4.05, C.accent2);
    text(s, "/reject <id> <причина>", { x: 6.8, y: 3.35, w: 3.2, h: 0.4, fontSize: 14, bold: true, fontFace: CODE_FONT, color: C.accent5 });
    card(s, 0.6, 5.6, 12.1, 0.9);
    text(s, "Любое изменение задачи пересчитывает статус и сбрасывает отзыв: утверждали другую задачу.",
      { x: 0.9, y: 5.6, w: 11.5, h: 0.9, fontSize: 18, bold: true, valign: "middle" });
    s.addNotes("draft — проверки нет или она не прошла. verified ставит harness, а не модель. approved — только преподаватель. " +
      "Комментарий rejected модель видит через get_problem.");
  }

  // 22. Кто что может
  {
    const s = slide("CONTENT", "Кто что может");
    await trustStrip(s, 1.55, [
      ["модель", "list_problems, get_problem, save_problem"],
      ["harness", "ставит verified или draft, сам перезапуская проверку"],
      ["преподаватель", "/approve, /reject, подтверждает перезапись"],
    ]);
    card(s, 0.6, 4.6, 12.1, 1.7, C.accent1);
    await badge(s, 0.95, 4.95, 0.9, "FaCircleQuestion", C.text1);
    text(s, "Почему approved нельзя дать модели — даже «с подтверждением»?",
      { x: 2.15, y: 4.6, w: 10.3, h: 1.7, fontSize: 22, bold: true, valign: "middle" });
    s.addNotes("Ожидаемый ответ: утверждение — это решение человека о качестве задачи. Подтверждение превращает его в клик " +
      "«да» на чужое предложение. Финальный статус должен ставить тот, кто отвечает за результат.");
  }

  // 23. Инструмент без опасности
  {
    const s = slide("CONTENT", "Инструмент, которым нельзя навредить");
    const pts = [
      ["FaFolderOpen", "id вместо пути", "Путь строит bank.py, id проверяется по формату P-\\d{4}", "../.env  →  ValueError"],
      ["FaLock", "Нет поля status", "verified ставит harness, approved — человек", "\"status\": \"approved\"  →  TypeError"],
      ["FaBan", "Нет удаления и утверждения", "Это команды преподавателя в REPL", "в tools.names() их нет"],
    ];
    for (let i = 0; i < 3; i++) {
      const y = 1.55 + i * 1.45;
      await badge(s, 0.6, y, 0.85, pts[i][0], C.accent4);
      text(s, pts[i][1], { x: 1.65, y, w: 5.6, h: 0.45, fontSize: 18, bold: true });
      text(s, pts[i][2], { x: 1.65, y: y + 0.47, w: 5.6, h: 0.8, fontSize: 15, color: C.text2 });
      card(s, 7.5, y + 0.05, 5.2, 0.9, C.text1);
      text(s, pts[i][3], { x: 7.75, y: y + 0.05, w: 4.8, h: 0.9, fontSize: 14, fontFace: CODE_FONT, valign: "middle", color: C.background2 });
    }
    text(s, "Самое надёжное разрешение — отсутствие опасной возможности.",
      { x: 0.6, y: 6.0, w: 12.1, h: 0.6, fontSize: 20, bold: true, italic: true, color: C.accent4 });
    s.addNotes("Связь с занятием 3: запись вне bank/ не нужно ловить правилом — она невозможна. " +
      "Новое правило в RULES одно: перезапись существующей задачи требует подтверждения.");
  }

  // 24. Воспроизводимая проверка
  {
    const s = slide("CONTENT", "Проверка, которую можно воспроизвести");
    const flow = [["FaRobot", C.accent6, "Модель", "«проверил, ответ 60»"],
      ["FaRotate", C.accent4, "Harness", "повторяет verification"],
      ["FaShieldHalved", C.accent4, "Разрешения", "→ реестр → песочница"],
      ["FaPuzzlePiece", C.accent3, "z3_check", "n = 61, unique"],
      ["FaCircleXmark", C.accent2, "matches()", "61 ≠ 60 → draft"]];
    for (let i = 0; i < 5; i++) {
      const x = 0.55 + i * 2.5;
      await node(s, x, 1.6, flow[i][0], flow[i][1], flow[i][2], flow[i][3], 2.2);
      if (i < 4) arrow(s, x + 1.75, 2.05, x + 2.95, 2.05);
    }
    text(s, "Когда ставится verified", { x: 0.6, y: 4.1, w: 6, h: 0.45, fontSize: 18, bold: true });
    bullets(s, ["результат совпадает с answer", "z3_check: unique = true; sympy_solve: ровно одно решение",
      "проверять можно python_eval, sympy_solve, z3_check"], { x: 0.6, y: 4.6, w: 7.2, h: 2.0, fontSize: 16 });
    card(s, 8.2, 4.1, 4.5, 2.4);
    text(s, "Почему не python_run", { x: 8.45, y: 4.25, w: 4.0, h: 0.45, fontSize: 16, bold: true });
    text(s, "Каждый запуск скрипта требует подтверждения, а проверка при сохранении идёт без вопросов.",
      { x: 8.45, y: 4.75, w: 4.0, h: 1.6, fontSize: 15, color: C.text2 });
    s.addNotes("Модель утверждает, harness перепроверяет. Тесты-иллюстрации: test_wrong_answer_stays_draft, " +
      "test_not_unique_stays_draft, test_verification_goes_through_permissions (эксплойт в проверке ловят ворота 1).");
  }

  // 25. Человек и память разрешений
  {
    const s = slide("CONTENT", "Человек в контуре и память разрешений");
    text(s, "Отзыв преподавателя", { x: 0.6, y: 1.5, w: 6, h: 0.45, fontSize: 20, bold: true });
    code(s, 0.6, 2.05, 6.0, 1.3, ["/reject P-0001 Слишком просто:", "        добавь ещё два делителя"], 14);
    bullets(s, ["модель читает review через get_problem", "переделывает задачу и просит перезапись",
      "после y — снова verified, отзыв сброшен"], { x: 0.6, y: 3.6, w: 6.0, h: 2.2, fontSize: 16 });
    text(s, "«Всегда» теперь на диске", { x: 7.1, y: 1.5, w: 5.6, h: 0.45, fontSize: 20, bold: true });
    code(s, 7.1, 2.05, 5.6, 1.3, ["# .agent/settings.json", "{\"always_allow\": [\"python_run\"]}"], 14);
    card(s, 7.1, 3.6, 5.6, 2.2, C.accent1);
    text(s, "Удобно и опасно: разрешение, данное вчера, действует сегодня. Посмотреть — /permissions, забыть — /forget.",
      { x: 7.4, y: 3.75, w: 5.0, h: 1.9, fontSize: 16 });
    s.addNotes("Сохранение «всегда» было обещано в занятии 3. Аналог в Claude Code — правила allow в .claude/settings.json.");
  }

  // 26. Цена изоляции
  {
    const s = slide("CONTENT", "Цена изоляции");
    card(s, 0.6, 1.6, 5.9, 3.4);
    text(s, "1,8 с", { x: 0.6, y: 1.8, w: 5.9, h: 1.5, fontSize: 66, bold: true, align: "center", color: C.accent2 });
    text(s, "spawn: каждый вызов — новый интерпретатор, заново импортирует sympy и z3",
      { x: 0.9, y: 3.4, w: 5.3, h: 1.4, fontSize: 16, align: "center", color: C.text2 });
    card(s, 6.8, 1.6, 5.9, 3.4);
    text(s, "0,01 с", { x: 6.8, y: 1.8, w: 5.9, h: 1.5, fontSize: 66, bold: true, align: "center", color: C.accent3 });
    text(s, "forkserver: сервер один раз импортирует agent.tools, вызов — быстрая копия процесса",
      { x: 7.1, y: 3.4, w: 5.3, h: 1.4, fontSize: 16, align: "center", color: C.text2 });
    text(s, "Изоляция та же — отдельный процесс с таймаутом. Первый вызов ~1,7 с, в Windows остаётся spawn.",
      { x: 0.6, y: 5.35, w: 12.1, h: 0.9, fontSize: 18, bold: true });
    s.addNotes("Банк перепроверяет ответ при каждом сохранении — медленная песочница стала заметна. " +
      "Повод обсудить компромисс «безопасно / быстро».");
  }

  // Демо 3
  await demoSlide("Демо: банк задач", [
    ["Сохранить и найти после перезапуска", "cd lesson04 && uv run agent -v\n«Придумай задачу на остатки для 6 класса с единственным ответом, проверь и сохрани в банк.» → verified\n/exit → uv run agent → «Какие задачи для 6 класса уже есть в банке?»"],
    ["Отзыв преподавателя", "/reject P-0001 Слишком просто: добавь ещё два делителя\n«Исправь задачу P-0001 по замечанию преподавателя.» → ⚠ Перезапись → y → verified"],
    ["Утверждение", "/show P-0001   /approve P-0001   /bank approved   — и открыть bank/P-0001.json"],
  ], "Сценарии проверены с настоящей моделью: list_problems → z3_check → save_problem → verified; после /reject модель " +
    "прочитала отзыв, сделала задачу с четырьмя делителями (ответ 59) и запросила перезапись. " +
    "Перед занятием удалить lesson04/bank/ и lesson04/.agent/.");

  // =====================================================================
  section("Итоги");
  {
    const s = slide("SECTION", "Часть 4. Итоги и мост к занятию 5");
    s.addText("Что мы гарантируем — и чего нет", { placeholder: "body" });
    s.addNotes("Финальная часть.");
  }

  // 27. verified ≠ правильно
  {
    const s = slide("CONTENT", "verified ≠ «задача правильная»");
    card(s, 0.6, 1.6, 5.7, 2.6);
    text(s, "Условие", { x: 0.9, y: 1.75, w: 5, h: 0.45, fontSize: 18, bold: true, color: C.text2 });
    text(s, "Найдите наименьшее n > 2, дающее остаток 2 при делении на 3, 4 и 5",
      { x: 0.9, y: 2.3, w: 5.1, h: 1.7, fontSize: 20 });
    code(s, 7.0, 1.6, 5.7, 2.6, ["# формализация в z3", [{ text: "n % 3 == 1", color: C.accent2, bold: true }],
      [{ text: "n % 4 == 1", color: C.accent2, bold: true }], [{ text: "n % 5 == 1", color: C.accent2, bold: true }],
      [{ text: "→ status: verified", color: C.accent3, bold: true }]], 15);
    arrow(s, 6.35, 2.9, 6.95, 2.9, C.accent2);
    text(s, "verified значит «формализация воспроизводит ответ», а не «формализация соответствует условию».",
      { x: 0.6, y: 4.6, w: 12.1, h: 0.9, fontSize: 20, bold: true });
    await badge(s, 0.6, 5.65, 0.75, "FaMagnifyingGlass", C.accent5);
    text(s, "Модель и формализует, и проверяет. Нужен независимый проверяющий — занятие 5.",
      { x: 1.55, y: 5.65, w: 11.1, h: 0.75, fontSize: 18, valign: "middle", color: C.text2 });
    s.addNotes("Показать тестом: uv run --group dev pytest -k formalization -v. Задача получает verified, хотя ответ к такому условию неверный.");
  }

  // 28. Сквозная идея
  {
    const s = slide("CONTENT", "Сквозная идея двух занятий");
    await trustStrip(s, 1.55, [["модель предлагает", "tool_call, задача, ответ"],
      ["harness проверяет", "разрешения, песочница, перепроверка"], ["человек решает", "ask, /approve, /reject"]]);
    const rows = [["Занятие 3", "можно ли выполнять этот вызов?", C.accent1], ["Занятие 4", "можно ли верить результату и сохранить его?", C.accent3]];
    rows.forEach((r, i) => {
      const y = 4.55 + i * 0.95;
      card(s, 0.6, y, 12.1, 0.8);
      text(s, r[0], { x: 0.9, y, w: 2.4, h: 0.8, fontSize: 18, bold: true, valign: "middle", color: r[2] });
      text(s, r[1], { x: 3.3, y, w: 9.2, h: 0.8, fontSize: 18, valign: "middle" });
    });
    s.addNotes("Главный слайд для запоминания. Не доверяй модели: доверие обеспечивает harness, финальное решение — за человеком.");
  }

  // 29. Открытое
  {
    const s = slide("CONTENT", "Что осталось открытым");
    const items = [["FaLink", "Хуки (s04)", "проверки вписаны прямо в цикл — логирование и аудит придётся добавлять туда же"],
      ["FaLayerGroup", "Растущее оглавление", "сотни задач в промпте — нужны поиск и сжатие контекста (s08, s09)"],
      ["FaArrowsRotate", "Лимит шагов", "модель может бесконечно получать «Отказано» — занятие 8"],
      ["FaFloppyDisk", "Блокировки файлов", "два процесса над одним банком могут выдать одинаковый id"]];
    for (let i = 0; i < 4; i++) {
      const x = 0.6 + (i % 2) * 6.2, y = 1.6 + Math.floor(i / 2) * 2.4;
      card(s, x, y, 5.9, 2.1);
      await badge(s, x + 0.3, y + 0.3, 0.8, items[i][0], C.accent6);
      text(s, items[i][1], { x: x + 1.3, y: y + 0.3, w: 4.3, h: 0.8, fontSize: 18, bold: true, valign: "middle" });
      text(s, items[i][2], { x: x + 0.3, y: y + 1.15, w: 5.3, h: 0.85, fontSize: 15, color: C.text2 });
    }
    s.addNotes("Это задел на следующие занятия и разделы референса.");
  }

  // 30. Домашнее задание
  {
    const s = slide("CONTENT", "Домашнее задание");
    const cols = [["lesson03/EXERCISES.md", ["3 — найти и закрыть обход AST", "4 — своё правило в RULES с тестом"]],
      ["lesson04/EXERCISES.md", ["2 — поиск дубликатов при сохранении", "3 — миграция схемы: поле difficulty"]]];
    for (let i = 0; i < 2; i++) {
      const x = 0.6 + i * 6.2;
      card(s, x, 1.6, 5.9, 2.4);
      await badge(s, x + 0.3, 1.85, 0.75, "FaGraduationCap", C.accent1, HEX.dk1);
      text(s, cols[i][0], { x: x + 1.25, y: 1.85, w: 4.4, h: 0.75, fontSize: 16, bold: true, fontFace: CODE_FONT, valign: "middle" });
      bullets(s, cols[i][1], { x: x + 0.35, y: 2.8, w: 5.3, h: 1.1, fontSize: 16 });
    }
    text(s, "Перенеси на свой агент", { x: 0.6, y: 4.3, w: 12, h: 0.45, fontSize: 18, bold: true });
    bullets(s, ["таблица deny / ask / allow для своих инструментов", "хранилище: файл на запись, атомарная запись, id вместо путей",
      "одно утверждение модели, которое harness перепроверяет сам"], { x: 0.6, y: 4.8, w: 12.1, h: 1.5, fontSize: 16 });
    text(s, "Критерий: опасное — только с решением человека, данные переживают перезапуск, всё проверено тестами без сети.",
      { x: 0.6, y: 6.3, w: 12.1, h: 0.5, fontSize: 14, color: C.text2 });
    s.addNotes("Остальные упражнения — по желанию. Тесты без сети: модель подменяется через chat, вопрос пользователю — через ask.");
  }

  await pres.writeFile({ fileName: OUT });
  if (APPLY_THEME) {
    const { applyTheme } = require(APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("written", OUT);
})().catch(e => { console.error(e); process.exit(1); });
