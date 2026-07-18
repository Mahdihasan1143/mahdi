/* ===== Ifada Solar — interactions ===== */
(function () {
  'use strict';

  var doc = document;
  var hero = doc.getElementById('hero');
  var navbar = doc.getElementById('navbar');
  var progress = doc.getElementById('scrollProgress');

  /* ---- Navbar scroll state + progress bar ---- */
  function onScroll() {
    var y = window.scrollY || doc.documentElement.scrollTop;
    if (navbar) navbar.classList.toggle('scrolled', y > 40);

    var h = doc.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.width = (h > 0 ? (y / h) * 100 : 0) + '%';

    /* ---- Day -> Night as user scrolls through hero ---- */
    if (hero) {
      var hh = hero.offsetHeight;
      var t = Math.min(Math.max(y / hh, 0), 1); // 0 top .. 1 past hero
      hero.style.setProperty('--night', t.toFixed(3));
      // Sun arcs across the sky and sets
      var sunX = t * 62;                 // vw travelled left->right
      var sunY = Math.sin(t * Math.PI) * -70 + t * 260; // up then down
      hero.style.setProperty('--sun-x', sunX + 'vw');
      hero.style.setProperty('--sun-y', sunY + 'px');
      var sun = doc.getElementById('sun');
      if (sun) sun.style.opacity = (1 - Math.max(0, (t - 0.55) / 0.45)).toFixed(2);
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- Mobile nav toggle ---- */
  var toggle = doc.getElementById('navToggle');
  var links = doc.getElementById('navLinks');
  if (toggle && links) {
    toggle.addEventListener('click', function () { links.classList.toggle('open'); });
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') links.classList.remove('open');
    });
  }

  /* ---- Reveal on scroll ---- */
  var revealEls = doc.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); ro.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el) { ro.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---- Animated counters ---- */
  function animateCount(el) {
    var target = parseFloat(el.getAttribute('data-count')) || 0;
    var suffix = el.getAttribute('data-suffix') || '';
    var dur = 1600, start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = Math.floor(eased * target);
      el.textContent = val.toLocaleString('en-US') + suffix;
      if (p < 1) requestAnimationFrame(step);
      else el.textContent = target.toLocaleString('en-US') + suffix;
    }
    requestAnimationFrame(step);
  }
  var counters = doc.querySelectorAll('.stat-num');
  if ('IntersectionObserver' in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { animateCount(en.target); co.unobserve(en.target); }
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { co.observe(el); });
  } else {
    counters.forEach(animateCount);
  }

  /* ---- Reviews slider ---- */
  var track = doc.getElementById('reviewTrack');
  var dotsWrap = doc.getElementById('reviewDots');
  if (track && dotsWrap) {
    var slides = track.children.length;
    var idx = 0, timer;
    for (var i = 0; i < slides; i++) {
      var b = doc.createElement('button');
      b.setAttribute('aria-label', 'Review ' + (i + 1));
      (function (n) { b.addEventListener('click', function () { go(n); reset(); }); })(i);
      dotsWrap.appendChild(b);
    }
    var dots = dotsWrap.children;
    function go(n) {
      idx = (n + slides) % slides;
      track.style.transform = 'translateX(-' + (idx * 100) + '%)';
      for (var d = 0; d < dots.length; d++) dots[d].classList.toggle('active', d === idx);
    }
    function reset() { clearInterval(timer); timer = setInterval(function () { go(idx + 1); }, 5000); }
    go(0); reset();
  }

  /* ---- FAQ accordion ---- */
  doc.querySelectorAll('.faq-item .faq-q').forEach(function (q) {
    q.addEventListener('click', function () {
      var item = q.parentElement;
      var ans = item.querySelector('.faq-a');
      var isOpen = item.classList.contains('open');
      doc.querySelectorAll('.faq-item.open').forEach(function (o) {
        o.classList.remove('open');
        o.querySelector('.faq-a').style.maxHeight = null;
      });
      if (!isOpen) {
        item.classList.add('open');
        ans.style.maxHeight = ans.scrollHeight + 'px';
      }
    });
  });

  /* ---- Solar savings calculator ---- */
  var bill = doc.getElementById('bill');
  if (bill) {
    var billOut = doc.getElementById('billOut');
    var rSavings = doc.getElementById('rSavings');
    var rSize = doc.getElementById('rSize');
    var rRoi = doc.getElementById('rRoi');
    function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
    function calc() {
      var monthly = parseFloat(bill.value);          // ৳/month
      billOut.textContent = fmt(monthly);
      // ~ average tariff 8 ৳/kWh -> monthly kWh; solar offsets ~80%
      var kwhMonth = monthly / 8;
      var offset = 0.80;
      var savingsMonth = monthly * offset;
      // system size: monthly kWh / (30 days * ~4.2 peak-sun-hours)
      var sizeKw = (kwhMonth * offset) / (30 * 4.2);
      // cost estimate ~ 85,000 ৳ per kW installed
      var cost = sizeKw * 85000;
      var roiYears = cost / (savingsMonth * 12);
      rSavings.textContent = '৳' + fmt(savingsMonth);
      rSize.textContent = (sizeKw < 1 ? sizeKw.toFixed(1) : Math.round(sizeKw)) + ' kW';
      rRoi.textContent = roiYears.toFixed(1) + ' yrs';
    }
    bill.addEventListener('input', calc);
    calc();
  }

  /* ---- Contact form (client-side; no backend) ---- */
  var form = doc.getElementById('contactForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var status = doc.getElementById('formStatus');
      var name = doc.getElementById('name').value.trim();
      var phone = doc.getElementById('phone').value.trim();
      if (!name || !phone) {
        status.textContent = 'Please enter your name and phone number.';
        status.className = 'form-status err';
        return;
      }
      // Open WhatsApp with a pre-filled message as a lightweight lead capture.
      var interest = doc.getElementById('interest').value;
      var msg = doc.getElementById('msg').value.trim();
      var text = 'Hi Ifada Solar! I’m ' + name + ' (' + phone + ').' +
        ' Interested in: ' + interest + '.' + (msg ? ' ' + msg : '');
      status.textContent = 'Thank you, ' + name + '! Opening WhatsApp to complete your request…';
      status.className = 'form-status ok';
      window.open('https://wa.me/8801963920520?text=' + encodeURIComponent(text), '_blank', 'noopener');
      form.reset();
      if (bill) {} // keep calc independent
    });
  }

  /* ---- Morning / Night toggle (Reposit-style preview) ---- */
  var dnToggle = doc.querySelector('.daynight-toggle');
  if (dnToggle && hero) {
    var dnBtns = dnToggle.querySelectorAll('.dn-btn');
    dnBtns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var night = btn.getAttribute('data-mode') === 'night';
        dnToggle.classList.toggle('night', night);
        hero.classList.toggle('is-night', night);
        dnBtns.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        // smoothly drive the hero scene to full day or full night
        var current = parseFloat(hero.style.getPropertyValue('--night')) || 0;
        var target = night ? 1 : 0, startT = null, dur = 900;
        function anim(ts) {
          if (!startT) startT = ts;
          var p = Math.min((ts - startT) / dur, 1);
          var e = 1 - Math.pow(1 - p, 3);
          var v = current + (target - current) * e;
          hero.style.setProperty('--night', v.toFixed(3));
          var sun = doc.getElementById('sun');
          if (sun) sun.style.opacity = (1 - v).toFixed(2);
          if (p < 1) requestAnimationFrame(anim);
        }
        requestAnimationFrame(anim);
      });
    });
  }

  /* ---- Footer year ---- */
  var yr = doc.getElementById('year');
  if (yr) yr.textContent = new Date().getFullYear();
})();
