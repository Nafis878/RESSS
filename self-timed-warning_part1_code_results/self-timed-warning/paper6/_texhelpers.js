// LaTeX build of the RESS submission. Same text API as the docx build (_helpers.js), so the manuscript text and every
// consistency check are shared; items are stored raw and rendered to LaTeX at the end (citations need the reference list).
const fs = require('fs');
const N = JSON.parse(fs.readFileSync(__dirname + '/numbers.json'));
const f1 = x => (x === null || x === undefined) ? 'n/a' : Number(x).toFixed(1).replace('-', '−');
const fm = x => String(x).replace('-', '−');
const CHECK = [];
const must = (cond, msg) => { if (!cond) throw new Error('CHECK FAILED: ' + msg); CHECK.push(msg); };
// docx stubs used directly by the text files (title, keywords, supplement banner): ignored, the front matter is built separately
class Paragraph { constructor() { this.k = 'skip'; } }
const runs = () => [];
const AlignmentType = { CENTER: 'c', JUSTIFIED: 'j', LEFT: 'l' };
const P = (t, o = {}) => ({ k: 'p', t, noIndent: !!o.noIndent });
const P0 = t => P(t, { noIndent: true });
const H1 = (t, id) => ({ k: 'h1', t, id });
const H2 = (t, id) => ({ k: 'h2', t, id });
// cross-references: write ⟦T:id⟧, ⟦F:id⟧ or ⟦S:id⟧ in any text; ids are attached with withId (tables, figures) or as the second
// argument of H1/H2; numbers are assigned in order of appearance when the manuscript is rendered (_textail.js)
const withId = (id, arr) => { arr[0].id = id; return arr; };
const EQ = t => ({ k: 'eq', t });
const LI = items => [{ k: 'li', items }];
function table(caption, headers, rows, widths, note, label) { return [{ k: 'table', caption, headers, rows, widths, note, label }]; }
function figure(path, caption, widthIn = 6.5, label) { return [{ k: 'fig', path, caption, widthIn, label }]; }
const S = [];
const tableS = (caption, headers, rows, widths, note) => table(caption, headers, rows, widths, note, 'S');
const figureS = (path, caption, widthIn = 6.5) => figure(path, caption, widthIn, 'S');
