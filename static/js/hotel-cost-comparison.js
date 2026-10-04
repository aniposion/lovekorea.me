(() => {
  'use strict';
  const won = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 });
  document.querySelectorAll('[data-hotel-cost]').forEach(form => {
    const result = form.querySelector('output');
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const value = name => Number(form.elements.namedItem(name).value);
      const nights = value('nights');
      const a = value('aRate') * nights + value('aExtras');
      const b = value('bRate') * nights + value('bExtras');
      if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b)) {
        result.textContent = 'Enter whole-won amounts within the limits shown.';
        return;
      }
      const difference = Math.abs(a - b);
      const conclusion = difference === 0
        ? 'Both options have the same total.'
        : `Hotel ${a < b ? 'A' : 'B'} costs ${won.format(difference)} less for the whole stay.`;
      result.textContent = `Hotel A: ${won.format(a)}. Hotel B: ${won.format(b)}. ${conclusion} Compare travel time and refund terms before choosing.`;
    });
    form.addEventListener('input', () => {
      result.textContent = 'Values changed. Select Compare trip totals to update the result.';
    });
    form.querySelector('button').disabled = false;
  });
})();
