/**
 * PWA INSTALLATION HANDLER
 * Gerencia a instalação do Progressive Web App
 */

let deferredPrompt;
let installButton;

// ========================================
// SERVICE WORKER REGISTRATION
// ========================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/service-worker.js', { scope: '/' })
      .then((registration) => {
        console.log('✅ ServiceWorker registered:', registration.scope);

        // Verificar atualizações periodicamente
        setInterval(() => {
          registration.update();
        }, 60000); // A cada 1 minuto

        // Evento de atualização disponível
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;

          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // Nova versão disponível
              showUpdateNotification();
            }
          });
        });
      })
      .catch((error) => {
        console.error('❌ ServiceWorker registration failed:', error);
      });

    // Recarregar quando novo service worker tomar controle
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      if (refreshing) return;
      refreshing = true;
      window.location.reload();
    });
  });
}

// ========================================
// INSTALL PROMPT
// ========================================
window.addEventListener('beforeinstallprompt', (e) => {
  console.log('💡 beforeinstallprompt event fired');

  // Prevenir prompt automático
  e.preventDefault();

  // Salvar evento para usar depois
  deferredPrompt = e;

  // Mostrar botão de instalação
  showInstallButton();
});

// ========================================
// APP INSTALLED
// ========================================
window.addEventListener('appinstalled', () => {
  console.log('✅ PWA installed successfully');

  // Esconder botão de instalação
  hideInstallButton();

  // Limpar prompt
  deferredPrompt = null;

  // Notificar usuário
  showToast('App instalado com sucesso! 🎉', 'success');
});

// ========================================
// MOSTRAR BOTÃO DE INSTALAÇÃO
// ========================================
function showInstallButton() {
  // Criar botão se não existir
  if (!installButton) {
    installButton = document.createElement('button');
    installButton.id = 'pwa-install-button';
    installButton.className = 'btn btn-primary';
    installButton.innerHTML = '<i class="bi bi-download me-2"></i>Instalar App';
    installButton.onclick = installPWA;

    // Adicionar à topbar
    const topbarRight = document.querySelector('.topbar-right');
    if (topbarRight) {
      topbarRight.insertBefore(installButton, topbarRight.firstChild);
    }
  }

  installButton.style.display = 'inline-flex';

  // Adicionar estilos dinâmicos
  addInstallButtonStyles();
}

// ========================================
// ESCONDER BOTÃO DE INSTALAÇÃO
// ========================================
function hideInstallButton() {
  if (installButton) {
    installButton.style.display = 'none';
  }
}

// ========================================
// INSTALAR PWA
// ========================================
async function installPWA() {
  if (!deferredPrompt) {
    console.log('❌ No install prompt available');
    return;
  }

  // Mostrar prompt de instalação
  deferredPrompt.prompt();

  // Aguardar escolha do usuário
  const { outcome } = await deferredPrompt.userChoice;

  console.log(`User response: ${outcome}`);

  if (outcome === 'accepted') {
    console.log('✅ User accepted install');
    showToast('Instalando app...', 'info');
  } else {
    console.log('❌ User dismissed install');
  }

  // Limpar prompt (só pode ser usado uma vez)
  deferredPrompt = null;
  hideInstallButton();
}

// ========================================
// NOTIFICAÇÃO DE ATUALIZAÇÃO
// ========================================
function showUpdateNotification() {
  const updateBanner = document.createElement('div');
  updateBanner.id = 'update-banner';
  updateBanner.className = 'alert alert-info alert-dismissible fade show';
  updateBanner.style.cssText = 'position: fixed; top: 60px; right: 20px; z-index: 9998; max-width: 400px;';
  updateBanner.innerHTML = `
    <i class="bi bi-info-circle me-2"></i>
    <strong>Atualização disponível!</strong>
    <p class="mb-2 mt-1">Uma nova versão do app está disponível.</p>
    <button class="btn btn-sm btn-primary" onclick="updatePWA()">
      <i class="bi bi-arrow-repeat me-1"></i>Atualizar Agora
    </button>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(updateBanner);
}

// ========================================
// ATUALIZAR PWA
// ========================================
window.updatePWA = function() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistration().then((registration) => {
      if (registration && registration.waiting) {
        // Dizer ao service worker para pular a espera
        registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      }
    });
  }
};

// ========================================
// VERIFICAR SE É PWA
// ========================================
function isPWA() {
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true;
}

// ========================================
// ADICIONAR ESTILOS DO BOTÃO
// ========================================
function addInstallButtonStyles() {
  if (document.getElementById('pwa-install-styles')) return;

  const style = document.createElement('style');
  style.id = 'pwa-install-styles';
  style.textContent = `
    #pwa-install-button {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      animation: slideInRight 0.3s ease;
      gap: 0.5rem;
      align-items: center;
    }

    @media (min-width: 769px) {
      #pwa-install-button {
        position: static;
        box-shadow: none;
        animation: none;
      }
    }

    @keyframes slideInRight {
      from {
        transform: translateX(100px);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }

    #pwa-install-button:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
    }

    @media (max-width: 768px) {
      #pwa-install-button {
        bottom: 70px;
        right: 15px;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
      }
    }
  `;

  document.head.appendChild(style);
}

// ========================================
// STATUS PWA
// ========================================
window.addEventListener('DOMContentLoaded', () => {
  const isPwaMode = isPWA();

  console.log('📱 PWA Status:', {
    isPWA: isPwaMode,
    serviceWorkerSupported: 'serviceWorker' in navigator,
    standalone: window.matchMedia('(display-mode: standalone)').matches
  });

  // Se já está instalado, esconder botão
  if (isPwaMode) {
    hideInstallButton();
  }

  // Adicionar classe ao body se for PWA
  if (isPwaMode) {
    document.body.classList.add('pwa-mode');
  }
});

// ========================================
// DETECTAR MODO OFFLINE/ONLINE
// ========================================
window.addEventListener('online', () => {
  console.log('✅ Back online');
  showToast('Conexão restaurada', 'success');

  // Tentar sincronizar dados pendentes
  if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
    navigator.serviceWorker.ready.then((registration) => {
      return registration.sync.register('sync-ativos');
    });
  }
});

window.addEventListener('offline', () => {
  console.log('📴 Offline mode');
  showToast('Você está offline. Algumas funcionalidades podem estar limitadas.', 'warning');
});

// ========================================
// CACHE MANAGEMENT
// ========================================
window.clearPWACache = async function() {
  if ('caches' in window) {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => caches.delete(name))
    );

    console.log('🗑️ Cache cleared');
    showToast('Cache limpo com sucesso!', 'success');

    // Recarregar service worker
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        await registration.unregister();
        window.location.reload();
      }
    }
  }
};

// Log PWA initialization
console.log('🚀 PWA Installation script loaded');
