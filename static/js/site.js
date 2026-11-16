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

    if (!installPrompt) {
        return;
    }

    try {
        await installPrompt.prompt();
        const choice = await installPrompt.userChoice;
        if (choice?.outcome === 'accepted' && installBtn) {
            installBtn.hidden = true;
        }
    } catch (error) {
        console.error('BuildSpot installation prompt failed:', error);
    } finally {
        installPrompt = null;
    }
});

window.addEventListener('appinstalled', () => {
    if (installBtn) installBtn.hidden = true;
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
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

/* BuildSpot: user-controlled web push opt-in and quiet subscription refresh. */
(() => {
  if (window.BUILDSPOT_PUSH_ENABLED !== true) return;

  const button = document.getElementById('buildspot-enable-push');
  const status = document.getElementById('buildspot-push-status');
  if (!button || !status) return;

  const say = message => {
    status.textContent = message;
    status.style.display = message ? 'block' : 'none';
  };

  function finishPushSetup(showToast = true) {
    button.hidden = true;
    button.disabled = true;
    say('');
    const banner = document.getElementById('buildspot-push-optin');
    if (banner) banner.hidden = true;

    if (!showToast) return;
    const toast = document.createElement('div');
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = '✓ Notifications enabled';
    Object.assign(toast.style, {
      position: 'fixed',
      right: '20px',
      bottom: '20px',
      zIndex: '100000',
      maxWidth: 'calc(100vw - 40px)',
      padding: '14px 20px',
      borderRadius: '12px',
      background: '#176b3a',
      color: '#fff',
      fontSize: '14px',
      fontWeight: '700',
      boxShadow: '0 8px 28px rgba(0,0,0,.18)',
      opacity: '0',
      transform: 'translateY(8px)',
      transition: 'opacity .3s ease, transform .3s ease'
    });
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });
    window.setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(8px)';
      window.setTimeout(() => toast.remove(), 350);
    }, 2600);
  }
  const csrfCookie = () => {
    const item = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return item ? decodeURIComponent(item.split('=').slice(1).join('=')) : '';
  };

  const decodeKey = value => {
    const padding = '='.repeat((4 - value.length % 4) % 4);
    const decoded = atob((value + padding).replace(/-/g, '+').replace(/_/g, '/'));
    return Uint8Array.from(decoded, char => char.charCodeAt(0));
  };

  const supported = () =>
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window;

  async function saveSubscription(subscription) {
    const csrf = csrfCookie();
    if (!csrf) throw new Error('Security token missing. Refresh the page and try again.');

    const response = await fetch('/push/subscribe/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify(subscription.toJSON())
    });

    if (!response.ok) {
      throw new Error('BuildSpot could not save your subscription. Please try again.');
    }

    const data = await response.json();
    if (!data.ok) throw new Error('BuildSpot could not save your subscription.');
  }

  async function createOrRefreshSubscription() {
    if (!supported()) {
      throw new Error('This browser does not support web push notifications. Try an updated browser.');
    }
    if (Notification.permission !== 'granted') {
      throw new Error('Notification permission has not been granted.');
    }

    let registration;
    try {
      const timeout = (message) => new Promise((_, reject) =>
        setTimeout(() => reject(new Error(message)), 15000)
      );

      registration = await Promise.race([
        navigator.serviceWorker.register('/sw.js', { scope: '/' }),
        timeout('BuildSpot could not register its service worker. Reload the page and try again.')
      ]);

      if (!registration.active) {
        const worker = registration.installing || registration.waiting;

        if (!worker) {
          throw new Error('BuildSpot service worker has no active worker. Reload the page and try again.');
        }

        await Promise.race([
          new Promise((resolve, reject) => {
            const checkState = () => {
              if (worker.state === 'activated') {
                worker.removeEventListener('statechange', checkState);
                resolve();
              } else if (worker.state === 'redundant') {
                worker.removeEventListener('statechange', checkState);
                reject(new Error('BuildSpot service worker installation failed. Reload the page and try again.'));
              }
            };

            worker.addEventListener('statechange', checkState);
            checkState();
          }),
          timeout('BuildSpot service worker is taking too long to activate. Reload the page and try again.')
        ]);
      }
    } catch (error) {
      throw new Error(
        error && error.message
          ? error.message
          : 'BuildSpot service worker could not start. Reload the page and try again.'
      );
    }
    const keyResponse = await fetch('/push/vapid-public-key/', {
      credentials: 'same-origin',
      cache: 'no-store'
    });
    if (!keyResponse.ok) throw new Error('Notification setup is temporarily unavailable.');

    const keyData = await keyResponse.json();
    if (!keyData.publicKey) throw new Error('The notification public key is unavailable.');

    let subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: decodeKey(keyData.publicKey)
      });
    }

    await saveSubscription(subscription);
  }

  function updatePermissionDisplay() {
    if (!supported()) {
      button.disabled = true;
      button.style.display = 'none';
      say('Web push is not supported by this browser. In-app alerts remain available.');
      return;
    }

    if (Notification.permission === 'denied') {
      button.disabled = true;
      button.textContent = 'Notifications blocked';
      say('Notifications are blocked by your browser. Change BuildSpot notification permission in browser site settings, then reload.');
    } else if (Notification.permission === 'granted') {
      button.disabled = false;
      button.textContent = 'Refresh notifications';
      say('Browser permission is granted. Checking your subscription…');
    } else {
      button.disabled = false;
      button.textContent = 'Enable notifications';
      say('');
    }
  }

  button.addEventListener('click', async () => {
    if (!supported()) {
      // Hide the opt-in banner immediately when browser permission is already granted.
  // Do not make banner visibility depend on a successful subscription refresh.
  if (supported() && Notification.permission === 'granted') {
    const existingBanner = document.getElementById('buildspot-push-optin');
    if (existingBanner) existingBanner.hidden = true;
  }

  updatePermissionDisplay();
      return;
    }

    button.disabled = true;
    try {
      if (Notification.permission === 'default') {
        // This permission request is made directly in response to the click.
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
          updatePermissionDisplay();
          if (permission === 'default') {
            say('Permission was not granted. Click Enable notifications to try again.');
          }
          return;
        }
      }

      say('Setting up your notifications…');
      await createOrRefreshSubscription();
      finishPushSetup();
    } catch (error) {
      console.error('BuildSpot notification setup failed:', error);
      say('We couldn’t enable notifications just now. Please try again.');
    } finally {
      button.disabled = Notification.permission === 'denied';
    }
  });

  updatePermissionDisplay();

  // Refresh an existing permission-granted subscription without prompting.
  if (supported() && Notification.permission === 'granted') {
    const refresh = async () => {
      try {
        await createOrRefreshSubscription();
        finishPushSetup(false);
      } catch (error) {
        console.error('BuildSpot subscription refresh failed:', error);
        say('Notifications couldn’t be refreshed. Please try again.');
      }
    };

    if (document.readyState === 'complete') {
      refresh();
    } else {
      window.addEventListener('load', refresh, { once: true });
    }
  }
})();
