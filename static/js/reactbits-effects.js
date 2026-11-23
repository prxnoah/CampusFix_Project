/* ReactBits-inspired interaction layer for the Flask/Jinja build.
   These effects intentionally use framework-free JS so the existing Flask app stays lightweight. */
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const root = document.documentElement;

  // Spotlight cursor / background glow.
  if (!reduce) {
    const spotlight = document.createElement('div');
    spotlight.className = 'cursor-spotlight';
    document.body.appendChild(spotlight);
    window.addEventListener('pointermove', e => {
      root.style.setProperty('--mx', `${e.clientX}px`);
      root.style.setProperty('--my', `${e.clientY}px`);
      spotlight.style.transform = `translate3d(${e.clientX}px,${e.clientY}px,0)`;
    }, {passive:true});
  }

  // Magnetic buttons.
  document.querySelectorAll('.magnetic').forEach(el => {
    if (reduce) return;
    el.addEventListener('pointermove', e => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left - r.width/2) * .10;
      const y = (e.clientY - r.top - r.height/2) * .10;
      el.style.transform = `translate(${x}px,${y}px)`;
    });
    el.addEventListener('pointerleave', () => el.style.transform = '');
  });

  // 3D tilt cards.
  document.querySelectorAll('[data-tilt]').forEach(card => {
    if (reduce) return;
    card.addEventListener('pointermove', e => {
      const r = card.getBoundingClientRect();
      const rx = ((e.clientY-r.top)/r.height-.5)*-7;
      const ry = ((e.clientX-r.left)/r.width-.5)*7;
      card.style.setProperty('--rx', `${rx}deg`);
      card.style.setProperty('--ry', `${ry}deg`);
    });
    card.addEventListener('pointerleave', () => { card.style.setProperty('--rx','0deg'); card.style.setProperty('--ry','0deg'); });
  });

  // Scroll-linked reveal progress.
  const reveal = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add('rb-visible'); reveal.unobserve(entry.target); }
  }), {threshold:.08});
  document.querySelectorAll('.reveal, .program-card, .lpu-news-card, .split-image').forEach(el => reveal.observe(el));

  // FAQ-style auto focus for search fields and animated nav header.
  const header = document.getElementById('siteHeader');
  window.addEventListener('scroll', () => header?.classList.toggle('scrolled', window.scrollY > 18), {passive:true});

  // Scroll progress.
  const bar = document.getElementById('scrollProgress');
  window.addEventListener('scroll', () => {
    const h = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.width = `${h ? (window.scrollY/h)*100 : 0}%`;
  }, {passive:true});
})();
