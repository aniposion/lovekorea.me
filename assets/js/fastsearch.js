import * as params from '@params';

let fuse; // holds our search engine
let resList = document.getElementById('searchResults');
let sInput = document.getElementById('searchInput');
let first, last;
let resultsAvailable = false;

const searchStatus = document.getElementById('searchStatus');
const searchRetry = document.getElementById('searchRetry');

function searchUnavailable() {
    resultsAvailable = false;
    resList.replaceChildren();
    resList.setAttribute('aria-busy', 'false');
    searchStatus.textContent = 'Search is unavailable right now. Reload search or browse the categories below.';
    searchRetry.hidden = false;
}

// Keep typing available while the index loads, then search the latest input.
searchStatus.textContent = 'Loading search…';
resList.setAttribute('aria-busy', 'true');
window.addEventListener('load', function () {
    const xhr = new XMLHttpRequest();
    xhr.onload = function () {
        if (xhr.status !== 200) {
            searchUnavailable();
            return;
        }
        try {
            const data = JSON.parse(xhr.responseText);
            if (!Array.isArray(data)) throw new Error('Invalid search index');
            const configured = params.fuseOpts || {};
            fuse = new Fuse(data, {
                isCaseSensitive: configured.iscasesensitive ?? false,
                includeScore: configured.includescore ?? false,
                includeMatches: configured.includematches ?? false,
                minMatchCharLength: configured.minmatchcharlength ?? 1,
                shouldSort: configured.shouldsort ?? true,
                findAllMatches: configured.findallmatches ?? false,
                keys: configured.keys ?? ['title', 'permalink', 'summary', 'content'],
                location: configured.location ?? 0,
                threshold: configured.threshold ?? 0.4,
                distance: configured.distance ?? 100,
                ignoreLocation: configured.ignorelocation ?? true
            });
            resList.setAttribute('aria-busy', 'false');
            searchGuides();
        } catch (error) {
            searchUnavailable();
        }
    };
    xhr.onerror = searchUnavailable;
    xhr.ontimeout = searchUnavailable;
    xhr.open('GET', '../index.json');
    xhr.timeout = 15000;
    xhr.send();
});

function activeToggle(ae) {
    document.querySelectorAll('.focus').forEach(function (element) {
        // rm focus class
        element.classList.remove("focus")
    });
    if (ae) {
        ae.focus()
        ae.parentElement.classList.add("focus")
    } else {
        document.activeElement.parentElement.classList.add("focus")
    }
}

function reset() {
    sInput.value = '';
    searchGuides();
    sInput.focus();
}

function searchGuides() {
    if (!fuse) return;
    const query = sInput.value.trim();
    const results = query ? fuse.search(query, {limit: params.fuseOpts?.limit}) : [];
    const fragment = document.createDocumentFragment();

    for (const {item} of results) {
        const row = document.createElement('li');
        row.className = 'post-entry';
        const heading = document.createElement('header');
        heading.className = 'entry-header';
        heading.textContent = item.title + ' »';
        const link = document.createElement('a');
        link.href = item.permalink;
        link.setAttribute('aria-label', item.title);
        row.append(heading, link);
        fragment.append(row);
    }

    resList.replaceChildren(fragment);
    resultsAvailable = results.length > 0;
    first = resList.firstElementChild;
    last = resList.lastElementChild;
    if (!query) {
        searchStatus.textContent = 'Type a destination or topic to find a guide.';
    } else if (!resultsAvailable) {
        searchStatus.textContent = `No guides found for “${query}”. Try a shorter term, such as Jeju or AREX.`;
    } else {
        searchStatus.textContent = `${results.length} ${results.length === 1 ? 'result' : 'results'} for “${query}”.`;
    }
}

// Input covers typing, paste, speech input and the browser's clear button.
sInput.addEventListener('input', searchGuides);
sInput.addEventListener('search', searchGuides);

// kb bindings
document.onkeydown = function (e) {
    let key = e.key;
    let ae = document.activeElement;

    let inbox = document.getElementById("searchbox").contains(ae)

    if (ae === sInput) {
        let elements = document.getElementsByClassName('focus');
        while (elements.length > 0) {
            elements[0].classList.remove('focus');
        }
    }

    if (!inbox) return;

    if (key === "Escape") {
        reset()
    } else if (!resultsAvailable || (ae !== sInput && !resList.contains(ae))) {
        return
    } else if (key === "ArrowDown") {
        e.preventDefault();
        if (ae == sInput) {
            // if the currently focused element is the search input, focus the <a> of first <li>
            activeToggle(resList.firstChild.lastChild);
        } else if (ae.parentElement != last) {
            // if the currently focused element's parent is last, do nothing
            // otherwise select the next search result
            activeToggle(ae.parentElement.nextSibling.lastChild);
        }
    } else if (key === "ArrowUp") {
        e.preventDefault();
        if (ae.parentElement == first) {
            // if the currently focused element is first item, go to input box
            activeToggle(sInput);
        } else if (ae != sInput) {
            // if the currently focused element is input box, do nothing
            // otherwise select the previous search result
            activeToggle(ae.parentElement.previousSibling.lastChild);
        }
    } else if (key === "ArrowRight") {
        ae.click(); // click on active link
    }
}
