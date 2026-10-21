// Execute the report's inline interactions against a minimal DOM substitute.
// This is a behavior test, not browser rendering or visual verification.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
for (const path of process.argv.slice(2)) {
  const html = fs.readFileSync(path, 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const buttons = ['13', '52', 'all'].map(range => ({
    dataset: {range}, pressed: range === '52',
    addEventListener(event, handler) {assert.equal(event, 'click'); this.click = handler;},
    setAttribute(name, value) {assert.equal(name, 'aria-pressed'); this.pressed = value === 'true';}
  }));
  const panels = ['13', '52', 'all'].map(rangePanel => ({dataset: {rangePanel}, hidden: rangePanel !== '52'}));
  let width = 960;
  const details = {open: false, addEventListener(event, handler) {
    assert.equal(event, 'toggle'); this.toggle = handler;
  }};
  const hints = [];
  function area(kind, minimumWidth, visible = () => true) {
    return {
      dataset: {scrollKind: kind}, attributes: {}, tabIndex: 0,
      get clientWidth() {return visible() ? width : 0;},
      get scrollWidth() {return Math.max(this.clientWidth, minimumWidth);},
      before(hint) {assert.equal(this.hint, undefined); this.hint = hint;},
      setAttribute(name, value) {this.attributes[name] = value;},
      removeAttribute(name) {delete this.attributes[name];}
    };
  }
  const rangeAreas = panels.map(panel => area('chart', 580, () => !panel.hidden));
  const wideTable = area('table', 640);
  const fittingTable = area('table', 200);
  const detailChart = area('chart', 580, () => details.open);
  const detailTable = area('table', 640, () => details.open);
  // A hidden area's content width can remain nonzero in a DOM measurement.
  const hiddenChart = area('chart', 800, () => false);
  const areas = [...rangeAreas, wideTable, fittingTable, detailChart, detailTable, hiddenChart];
  const document = {
    createElement(tag) {assert.equal(tag, 'p'); const hint = {}; hints.push(hint); return hint;},
    querySelectorAll(selector) {
      if (selector === '[data-range]') return buttons;
      if (selector === '[data-range-panel]') return panels;
      if (selector === '.scroll-area') return areas;
      if (selector === 'details') return [details];
      throw new Error('Unexpected selector: ' + selector);
    }
  };
  const window = {addEventListener(event, handler) {assert.equal(event, 'resize'); this.resize = handler;}};
  function assertCue(target, visible) {
    assert.equal(target.hint.hidden, !visible);
    assert.equal(target.hint.className, 'scroll-hint');
    assert.equal(target.hint.textContent, 'Scroll horizontally to see the full ' + target.dataset.scrollKind + '.');
    assert.equal(target.tabIndex, visible ? 0 : -1);
    assert.equal(target.attributes['aria-describedby'], visible ? target.hint.id : undefined);
  }
  vm.runInNewContext(script, {document, window});
  // Desktop: all content fits, so there are no hints or extra tab stops.
  areas.forEach(target => assertCue(target, false));
  const hintIds = hints.map(hint => hint.id);
  assert.equal(new Set(hintIds).size, areas.length);
  assert.ok(hintIds.every(Boolean));

  // Narrow viewport: only visible, overflowing content gets a described cue.
  width = 320; window.resize();
  assertCue(rangeAreas[0], false);
  assertCue(rangeAreas[1], true);
  assertCue(rangeAreas[2], false);
  assertCue(wideTable, true);
  [fittingTable, detailChart, detailTable, hiddenChart].forEach(target => assertCue(target, false));
  for (const button of buttons) {
    button.click();
    assert.equal(buttons.filter(b => b.pressed).length, 1);
    assert.equal(panels.filter(p => !p.hidden).length, 1);
    assert.equal(panels.find(p => !p.hidden).dataset.rangePanel, button.dataset.range);
    rangeAreas.forEach((target, index) => assertCue(target, panels[index].dataset.rangePanel === button.dataset.range));
  }
  details.open = true; details.toggle();
  assertCue(detailChart, true); assertCue(detailTable, true);
  details.open = false; details.toggle();
  assertCue(detailChart, false); assertCue(detailTable, false);

  // Resize through fitting and rounding boundaries, then back to narrow.
  width = 580; window.resize();
  rangeAreas.forEach(target => assertCue(target, false));
  assertCue(wideTable, true);
  width = 579; window.resize();
  rangeAreas.forEach(target => assertCue(target, false));
  width = 578; window.resize();
  assertCue(rangeAreas[2], true);
  width = 960; window.resize();
  details.open = true; details.toggle();
  areas.forEach(target => assertCue(target, false));
  width = 320; window.resize();
  assertCue(rangeAreas[2], true);
  assertCue(detailChart, true); assertCue(detailTable, true);
  assertCue(fittingTable, false); assertCue(hiddenChart, false);
  assert.equal(hints.length, areas.length);
  assert.deepEqual(hints.map(hint => hint.id), hintIds);
  process.stdout.write(JSON.stringify({path, range_interaction: 'passed', overflow_cues: 'passed', keyboard_and_descriptions: 'passed', resize_and_disclosures: 'passed', environment: 'Node mock DOM; no browser'}) + '\n');
}
