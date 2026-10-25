/* Keep operator QA and local previews out of reader analytics. */
(function () {
  'use strict';

  var tagId = 'G-2RHGK56598';
  var qaKey = 'lovekorea_qa';
  var isQa = new URLSearchParams(window.location.search).get('lk_qa') === '1';
  try {
    if (isQa) window.sessionStorage.setItem(qaKey, '1');
    isQa = isQa || window.sessionStorage.getItem(qaKey) === '1';
  } catch (error) {
    // A marked URL still disables this page when browser storage is unavailable.
  }

  if (isQa || window.location.hostname !== 'lovekorea.me') {
    // Set Google's opt-out before any tag/config call, and do not load its library.
    window['ga-disable-' + tagId] = true;
    return;
  }

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', tagId);

  var tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + tagId;
  document.head.appendChild(tag);
})();
