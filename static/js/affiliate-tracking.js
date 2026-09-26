/**
 * Owned-Shop and Affiliate Click Tracking for GA4
 *
 * Sends 'owned_shop_click' for HTTPS Obang House links tagged with
 * utm_source=lovekorea. Parameters: placement (utm_content), campaign
 * (utm_campaign), shop_name, page_path, and link_url.
 * Owned-shop clicks are kept separate from affiliate clicks.
 * 
 * Sends 'affiliate_click' only for approved tracked partner links.
 * Direct booking links use the separate 'offer_outbound_click' event.
 * Both offer events include:
 * - slot: Offer slot key (e.g., KOREA_TOUR_DEALS)
 * - pos: Position in page (top/mid/bottom)
 * - provider: Destination provider (klook/booking/amazon/etc)
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

  function getOwnedShopUrl(anchor) {
    if (!anchor) return null;

    var url;
    try {
      url = new URL(anchor.getAttribute('href') || '', window.location.href);
    } catch (e) {
      return null;
    }

    if (url.protocol !== 'https:' ||
        (url.hostname !== 'obanghouse.com' && url.hostname !== 'www.obanghouse.com') ||
        url.searchParams.get('utm_source') !== 'lovekorea') {
      return null;
    }

    return url;
  }

  function handleClick(e) {
    var anchor = e.target.closest ? e.target.closest('a[href]') : null;
    var ownedShopUrl = getOwnedShopUrl(anchor);

    if (!ownedShopUrl) {
      handleOfferClick(e);
      return;
    }

    var gtag = getGtag();
    if (!gtag) return;

    gtag('event', 'owned_shop_click', {
      placement: ownedShopUrl.searchParams.get('utm_content') || '',
      campaign: ownedShopUrl.searchParams.get('utm_campaign') || '',
      shop_name: 'obang_house',
      page_path: window.location.pathname,
      link_url: ownedShopUrl.href
    });
  }

  // Tracked partner links and direct booking links have separate event names.
  function handleOfferClick(e) {
    var a = e.target.closest ? e.target.closest('a[data-affiliate="1"], a[data-outbound-offer="1"]') : null;
    if (!a) return;

    var gtag = getGtag();
    if (!gtag) return;

    // Extract all tracking data
    var slot = a.getAttribute('data-slot') || 'unknown';
    var pos = a.getAttribute('data-pos') || 'unknown';
    var provider = a.getAttribute('data-provider') || 'unknown';
    var pageType = a.getAttribute('data-page-type') || 'unknown';
    var pagePath = a.getAttribute('data-page-path') || window.location.pathname;
    var slug = a.getAttribute('data-slug') || 'unknown';
    var linkUrl = a.getAttribute('href') || '';
    var category = a.getAttribute('data-page-category') ||
      (pageType === 'deals' ? 'deals' : 'other');
    var eventName = a.getAttribute('data-affiliate') === '1'
      ? 'affiliate_click'
      : 'offer_outbound_click';

    // Send GA4 event
    gtag('event', eventName, {
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
      console.log('[Offer Tracking] ' + eventName + ' sent:', {
        slot: slot,
        pos: pos,
        provider: provider,
        page_type: pageType,
        page_path: pagePath
      });
    }
  }

  // Attach event listener (capture phase for reliability)
  document.addEventListener('click', handleClick, true);

  // Expose for debugging
  window.__affiliateTracking = {
    version: '2.2.1',
    test: function() {
      console.log('[Affiliate Tracking] Test mode - gtag available:', !!getGtag());
    }
  };
})();
