(()=>{const body=document.body,menu=document.querySelector('.menu-toggle'),nav=document.querySelector('.navlinks');const closeMenu=()=>{nav?.classList.remove('open');menu?.setAttribute('aria-expanded','false')};menu?.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open))});document.addEventListener('click',e=>{if(nav?.classList.contains('open')&&!nav.contains(e.target)&&!menu.contains(e.target))closeMenu()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});nav?.querySelectorAll('a').forEach(a=>a.addEventListener('click',closeMenu));const theme=document.querySelector('.theme-toggle');if(localStorage.getItem('buildspot-theme')==='dark')body.classList.add('dark');theme?.addEventListener('click',()=>{body.classList.toggle('dark');localStorage.setItem('buildspot-theme',body.classList.contains('dark')?'dark':'light')});document.querySelectorAll('.enquire-product').forEach(btn=>btn.addEventListener('click',()=>{const id=document.getElementById('product-id');if(id)id.value=btn.dataset.product;const msg=document.querySelector('[name="message"]');if(msg&&!msg.value)msg.value=`Hello, I am interested in ${btn.dataset.name}. Please share availability and current pricing.`;document.getElementById('enquiry')?.scrollIntoView({behavior:'smooth',block:'start'});msg?.focus({preventScroll:true})}));
let installPrompt;
const installBtn = document.querySelector('.install-btn');
const installed = () =>
    window.matchMedia('(display-mode: standalone)').matches ||
    window.navigator.standalone === true;
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);

if (installBtn) {
    installBtn.hidden = installed();
}

window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    if (installBtn && !installed()) {
        installBtn.hidden = false;
        installBtn.textContent = 'Install BuildSpot App';
    }
});

installBtn?.addEventListener('click', async () => {
    if (installed()) {
        installBtn.hidden = true;
        return;
    }

    if (installPrompt) {
        installPrompt.prompt();
        const choice = await installPrompt.userChoice;
        if (choice?.outcome === 'accepted') {
            installBtn.hidden = true;
        }
        installPrompt = null;
        return;
    }

    if (isIOS) {
        alert('To install BuildSpot on iPhone or iPad, open this page in Safari, tap Share, then choose Add to Home Screen.');
    } else {
        alert('To install BuildSpot, open your browser menu and look for Install app or Add to Home Screen. If that option is unavailable, check that the site is using HTTPS and your browser supports installation.');
    }
});

window.addEventListener('appinstalled', () => {
    if (installBtn) installBtn.hidden = true;
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/pwa/sw.js').catch(() => {});
    });
}

})();;


/* BuildSpot: accessible password show/hide controls */
(() => {
  function addPasswordToggles() {
    document.querySelectorAll('input[type="password"]').forEach((input) => {
      if (input.dataset.visibilityToggleAdded === 'true') return;

      const wrapper = input.closest('.form-field') || input.parentElement;
      if (!wrapper) return;

      wrapper.classList.add('password-field-enhanced');
      input.dataset.visibilityToggleAdded = 'true';

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'password-visibility-toggle';
      button.textContent = 'Show';
      button.setAttribute('aria-label', 'Show password');
      button.setAttribute('aria-pressed', 'false');

      button.addEventListener('click', () => {
        const reveal = input.type === 'password';
        input.type = reveal ? 'text' : 'password';
        button.textContent = reveal ? 'Hide' : 'Show';
        button.setAttribute('aria-label', reveal ? 'Hide password' : 'Show password');
        button.setAttribute('aria-pressed', String(reveal));
        input.focus();
      });

      input.insertAdjacentElement('afterend', button);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', addPasswordToggles);
  } else {
    addPasswordToggles();
  }
})();
