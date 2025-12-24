/**
 * Affiliate Click Tracking for GA4
 * 
 * Sends 'affiliate_click' event with detailed parameters:
 * - slot: Offer slot key (e.g., KOREA_TOUR_DEALS)
 * - pos: Position in page (top/mid/bottom)
 * - provider: Affiliate provider (klook/amazon/viator/etc)
 * - page_type: Type of page (post/hub/deals/home)
 * - page_path: URL path of the page
 * - link_url: Destination URL
 * 
 * GA4 Custom Dimensions Setup (recommended):
 * - slot → event-scoped dimension
 * - pos → event-scoped dimension
 * - provider → event-scoped dimension
 * - page_type → event-scoped dimension
 */
(function() {
  'use strict';

  // Check if gtag is available
  function getGtag() {
    return (typeof window.gtag === 'function') ? window.gtag : null;
  }

  // Extract category from page path (e.g., /posts/k-travel/... → k-travel)
  function extractCategory(path) {
    if (!path) return 'unknown';
    var match = path.match(/\/posts\/([^\/]+)\//);
    if (match) return match[1];
    if (path.indexOf('/deals/') === 0) return 'deals';
    return 'other';
  }

  // Main click handler
  function handleAffiliateClick(e) {
    var a = e.target.closest ? e.target.closest('a[data-affiliate="1"]') : null;
    if (!a) return;

    var gtag = getGtag();
    if (!gtag) {
      console.warn('[Affiliate Tracking] gtag not available');
      return;
    }

    // Extract all tracking data
    var slot = a.getAttribute('data-slot') || 'unknown';
    var pos = a.getAttribute('data-pos') || 'unknown';
    var provider = a.getAttribute('data-provider') || 'unknown';
    var pageType = a.getAttribute('data-page-type') || 'unknown';
    var pagePath = a.getAttribute('data-page-path') || window.location.pathname;
    var slug = a.getAttribute('data-slug') || 'unknown';
    var linkUrl = a.getAttribute('href') || '';
    var category = extractCategory(pagePath);

    // Send GA4 event
    gtag('event', 'affiliate_click', {
      // Core parameters
      slot: slot,
      pos: pos,
      provider: provider,
      page_type: pageType,
      slug: slug,  // Links back to keywords CSV
      
      // Additional context
      page_path: pagePath,
      page_category: category,
      link_url: linkUrl,
      
      // For easier BigQuery/Looker analysis
      slot_pos: slot + '_' + pos,
      provider_slot: provider + '_' + slot,
      
      // Timestamp for debugging
      click_time: new Date().toISOString()
    });

    // Debug log in development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      console.log('[Affiliate Tracking] Event sent:', {
        slot: slot,
        pos: pos,
        provider: provider,
        page_type: pageType,
        page_path: pagePath
      });
    }
  }

  // Attach event listener (capture phase for reliability)
  document.addEventListener('click', handleAffiliateClick, true);

  // Expose for debugging
  window.__affiliateTracking = {
    version: '2.0.0',
    test: function() {
      console.log('[Affiliate Tracking] Test mode - gtag available:', !!getGtag());
    }
  };
})();