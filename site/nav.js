// Marks the section you are currently reading, in the sidebar and the navbar.
// A link with no visible current state leaves you lost once the scroll lands.
(function () {
  var links = document.querySelectorAll('.doc-side a[href^="#"], .nav-links a[href^="#"]');
  if (!links.length) return;

  var linkFor = {};
  var targets = [];
  links.forEach(function (link) {
    var el = document.getElementById(link.getAttribute('href').slice(1));
    if (!el) return;
    linkFor[el.id] = link;
    targets.push(el);
  });
  if (!targets.length) return;

  var visible = {};

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });

    // the band is the strip just under the navbar, so the section that wins
    // is the last one to have crossed it, never the one scrolling out
    var current = targets.filter(function (el) { return visible[el.id]; }).pop();
    links.forEach(function (link) { link.removeAttribute('aria-current'); });
    if (current) linkFor[current.id].setAttribute('aria-current', 'true');
  }, { rootMargin: '-70px 0px -78% 0px' });

  targets.forEach(function (el) { observer.observe(el); });
})();
