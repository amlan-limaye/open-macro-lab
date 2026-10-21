// Execute only the inline range-selector code against a minimal DOM substitute.
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
  const document = {querySelectorAll(selector) {
    if (selector === '[data-range]') return buttons;
    if (selector === '[data-range-panel]') return panels;
    throw new Error('Unexpected selector: ' + selector);
  }};
  vm.runInNewContext(script, {document});
  for (const button of buttons) {
    button.click();
    assert.equal(buttons.filter(b => b.pressed).length, 1);
    assert.equal(panels.filter(p => !p.hidden).length, 1);
    assert.equal(panels.find(p => !p.hidden).dataset.rangePanel, button.dataset.range);
  }
  process.stdout.write(JSON.stringify({path, range_interaction: 'passed', environment: 'Node mock DOM; no browser'}) + '\n');
}
