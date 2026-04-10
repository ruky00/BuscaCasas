/* ========================================
   BuscaCasas Landing — script.js
   ======================================== */

(function () {
    'use strict';

    // --- NAV: scroll shadow ---
    const nav = document.getElementById('nav');
    window.addEventListener('scroll', function () {
        nav.classList.toggle('nav--scrolled', window.scrollY > 10);
    }, { passive: true });

    // --- NAV: mobile menu ---
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');

    hamburger.addEventListener('click', function () {
        mobileMenu.classList.toggle('open');
    });

    // Close mobile menu on link click
    mobileMenu.querySelectorAll('a').forEach(function (link) {
        link.addEventListener('click', function () {
            mobileMenu.classList.remove('open');
        });
    });

    // --- EMAIL VALIDATION ---
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // --- WEB3FORMS CONFIG ---
    // Consigue tu access key gratis en https://web3forms.com
    // Te llegara un email cada vez que alguien se registre
    var WEB3FORMS_KEY = 'c3c4ff9e-dbb3-401d-bde9-a7fc72080ca9';

    // --- FORM HANDLING ---
    function setupForm(formId, emailId, successId) {
        var form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            var emailInput = document.getElementById(emailId);
            var successEl = document.getElementById(successId);
            var submitBtn = form.querySelector('button[type="submit"]');
            var btnText = submitBtn.querySelector('.btn__text');
            var btnLoader = submitBtn.querySelector('.btn__loader');
            var email = emailInput.value.trim();

            // Validate
            if (!isValidEmail(email)) {
                emailInput.style.borderColor = '#ef4444';
                emailInput.focus();
                setTimeout(function () {
                    emailInput.style.borderColor = '';
                }, 2000);
                return;
            }

            // Show loading
            btnText.hidden = true;
            btnLoader.hidden = false;
            submitBtn.disabled = true;
            emailInput.disabled = true;

            // Enviar lead por email via Web3Forms
            sendLead(email).then(function () {
                btnText.hidden = false;
                btnLoader.hidden = true;
                form.querySelector('.form-group').style.display = 'none';
                successEl.hidden = false;
                storeEmail(email);
                console.log('[BuscaCasas] Lead enviado:', email);
            }).catch(function (err) {
                console.warn('[BuscaCasas] Web3Forms no disponible, guardando localmente:', err.message);
                // Fallback: guardar localmente y mostrar exito igualmente
                btnText.hidden = false;
                btnLoader.hidden = true;
                form.querySelector('.form-group').style.display = 'none';
                successEl.hidden = false;
                storeEmail(email);
            });
        });
    }

    function sendLead(email) {
        return fetch('https://api.web3forms.com/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                access_key: WEB3FORMS_KEY,
                subject: 'Nuevo lead en BuscaCasas',
                from_name: 'BuscaCasas Landing',
                email: email,
                message: 'Nuevo interesado solicita acceso: ' + email,
            }),
        }).then(function (res) {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        }).then(function (data) {
            if (!data.success) throw new Error(data.message || 'Error Web3Forms');
            return data;
        });
    }

    function storeEmail(email) {
        try {
            var emails = JSON.parse(localStorage.getItem('buscacasas_leads') || '[]');
            if (emails.indexOf(email) === -1) {
                emails.push(email);
                localStorage.setItem('buscacasas_leads', JSON.stringify(emails));
            }
        } catch (e) {
            // localStorage not available
        }
    }

    // Initialize all forms
    setupForm('heroForm', 'heroEmail', 'heroSuccess');
    setupForm('midForm', 'midEmail', 'midSuccess');
    setupForm('finalForm', 'finalEmail', 'finalSuccess');

    // --- FAQ ACCORDION ---
    var faqItems = document.querySelectorAll('.faq-item');

    faqItems.forEach(function (item) {
        var question = item.querySelector('.faq-item__question');
        var answer = item.querySelector('.faq-item__answer');

        question.addEventListener('click', function () {
            var isOpen = item.classList.contains('open');

            // Close all
            faqItems.forEach(function (other) {
                other.classList.remove('open');
                other.querySelector('.faq-item__question').setAttribute('aria-expanded', 'false');
                other.querySelector('.faq-item__answer').style.maxHeight = '0';
            });

            // Toggle current
            if (!isOpen) {
                item.classList.add('open');
                question.setAttribute('aria-expanded', 'true');
                answer.style.maxHeight = answer.scrollHeight + 'px';
            }
        });
    });

    // --- SCROLL ANIMATIONS ---
    var animateElements = document.querySelectorAll('[data-animate]');

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                // Stagger animation for siblings
                var parent = entry.target.parentElement;
                var siblings = parent.querySelectorAll('[data-animate]');
                var index = Array.prototype.indexOf.call(siblings, entry.target);

                setTimeout(function () {
                    entry.target.classList.add('visible');
                }, index * 100);

                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -40px 0px'
    });

    animateElements.forEach(function (el) {
        observer.observe(el);
    });

    // --- SMOOTH SCROLL for nav links ---
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                var offset = nav.offsetHeight + 16;
                var top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        });
    });

})();
