(() => {
  'use strict';
  const won = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 });
  document.querySelectorAll('[data-tour-cost]').forEach(form => {
    const result = form.querySelector('output');
    const changed = () => {
      result.textContent = 'Values changed. Select Compare whole-party totals to update the result.';
    };
    form.addEventListener('input', changed);
    form.addEventListener('change', changed);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const value = name => form.elements.namedItem(name).value;
      const travelers = Number(value('travelers'));
      const total = key => Number(value(`${key}Price`)) * (value(`${key}Basis`) === 'person' ? travelers : 1) + Number(value(`${key}Extras`));
      const a = total('a');
      const b = total('b');
      if (!Number.isSafeInteger(a) || !Number.isSafeInteger(b)) {
        result.textContent = 'Enter whole-won amounts within the limits shown.';
        return;
      }
      const difference = Math.abs(a - b);
      const conclusion = difference === 0
        ? 'Both quotes have the same total.'
        : `Quote ${a < b ? 'A' : 'B'} costs ${won.format(difference)} less for the whole party.`;
      result.textContent = `For ${travelers} ${travelers === 1 ? 'traveler' : 'travelers'}: Quote A ${won.format(a)}; Quote B ${won.format(b)}. ${conclusion} Check the itinerary and inclusions before choosing.`;
    });
    form.querySelector('button').disabled = false;
  });
})();
