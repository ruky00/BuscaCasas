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

    // --- CONFIG ---
    var WEB3FORMS_KEY = 'c3c4ff9e-dbb3-401d-bde9-a7fc72080ca9';

    // Cloudflare Turnstile: consigue tu sitekey gratis en https://dash.cloudflare.com -> Turnstile
    // Usa '1x00000000000000000000AA' para testing (siempre pasa)
    var TURNSTILE_SITEKEY = '0x4AAAAAAC6N6HjEctFAOxlC';

    // --- CAPTCHA: Render Turnstile widgets cuando el SDK cargue ---
    var captchaTokens = {};

    function renderTurnstile() {
        if (typeof turnstile === 'undefined') return;

        var widgets = [
            { container: '#heroCaptcha', formId: 'heroForm' },
            { container: '#midCaptcha', formId: 'midForm' },
            { container: '#finalCaptcha', formId: 'finalForm' },
        ];

        widgets.forEach(function (w) {
            var el = document.querySelector(w.container);
            if (!el || el.dataset.rendered) return;
            el.dataset.rendered = 'true';

            turnstile.render(w.container, {
                sitekey: TURNSTILE_SITEKEY,
                theme: 'light',
                size: 'flexible',
                callback: function (token) {
                    captchaTokens[w.formId] = token;
                },
                'expired-callback': function () {
                    captchaTokens[w.formId] = null;
                },
                'error-callback': function () {
                    captchaTokens[w.formId] = null;
                },
            });
        });
    }

    // Intentar renderizar; reintentar si el SDK aun no cargo
    if (typeof turnstile !== 'undefined') {
        renderTurnstile();
    } else {
        var _tsInterval = setInterval(function () {
            if (typeof turnstile !== 'undefined') {
                clearInterval(_tsInterval);
                renderTurnstile();
            }
        }, 300);
        setTimeout(function () { clearInterval(_tsInterval); }, 10000);
    }

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

            // Limpiar error previo de captcha
            var prevErr = form.querySelector('.captcha-error');
            if (prevErr) prevErr.remove();

            // Validar email
            if (!isValidEmail(email)) {
                emailInput.style.borderColor = '#ef4444';
                emailInput.focus();
                setTimeout(function () {
                    emailInput.style.borderColor = '';
                }, 2000);
                return;
            }

            // Validar CAPTCHA — bloquear si no hay token
            var token = captchaTokens[formId];
            if (!token) {
                var errMsg = document.createElement('p');
                errMsg.className = 'captcha-error';
                errMsg.textContent = 'Por favor, completa la verificacion de seguridad.';
                errMsg.style.cssText = 'color:#ef4444;font-size:0.85rem;margin:8px 0 0;';
                var wrapper = form.querySelector('.cf-turnstile-wrapper');
                if (wrapper) wrapper.insertAdjacentElement('afterend', errMsg);
                return;
            }

            // Show loading
            btnText.hidden = true;
            btnLoader.hidden = false;
            submitBtn.disabled = true;
            emailInput.disabled = true;

            // Enviar lead por email via Web3Forms + token Turnstile
            sendLead(email, token).then(function () {
                btnText.hidden = false;
                btnLoader.hidden = true;
                form.querySelector('.form-group').style.display = 'none';
                var captchaEl = form.querySelector('.cf-turnstile-wrapper');
                if (captchaEl) captchaEl.style.display = 'none';
                successEl.hidden = false;
                storeEmail(email);
                console.log('[BuscaCasas] Lead enviado:', email);
            }).catch(function (err) {
                console.warn('[BuscaCasas] Web3Forms error, guardando localmente:', err.message);
                btnText.hidden = false;
                btnLoader.hidden = true;
                form.querySelector('.form-group').style.display = 'none';
                var captchaEl = form.querySelector('.cf-turnstile-wrapper');
                if (captchaEl) captchaEl.style.display = 'none';
                successEl.hidden = false;
                storeEmail(email);
            });
        });
    }

    function sendLead(email, captchaToken) {
        var payload = {
            access_key: WEB3FORMS_KEY,
            subject: 'Nuevo lead en BuscaCasas',
            from_name: 'BuscaCasas Landing',
            email: email,
            message: 'Nuevo interesado solicita acceso: ' + email,
        };
        if (captchaToken) {
            payload['cf-turnstile-response'] = captchaToken;
        }

        return fetch('https://api.web3forms.com/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
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
