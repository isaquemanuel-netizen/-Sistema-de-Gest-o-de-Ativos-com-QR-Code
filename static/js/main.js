/**
 * SISTEMA DE ATIVOS - MAIN JAVASCRIPT
 */

// ========================================
// SIDEBAR TOGGLE
// ========================================

function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const body = document.body;

  // Mobile: toggle show class
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('show');
    body.classList.toggle('sidebar-open');
  } else {
    // Desktop: toggle collapsed class
    sidebar.classList.toggle('collapsed');

    // Save state to localStorage
    const isCollapsed = sidebar.classList.contains('collapsed');
    localStorage.setItem('sidebarCollapsed', isCollapsed);
  }
}

// Close sidebar when clicking on overlay (mobile)
document.addEventListener('click', function(event) {
  if (window.innerWidth <= 768) {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    const body = document.body;

    // Check if click was outside sidebar and not on toggle button
    if (sidebar && body.classList.contains('sidebar-open')) {
      if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
        sidebar.classList.remove('show');
        body.classList.remove('sidebar-open');
      }
    }
  }
});

// Handle window resize - reset states
let resizeTimer;
window.addEventListener('resize', function() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(function() {
    const sidebar = document.querySelector('.sidebar');
    const body = document.body;

    if (window.innerWidth > 768) {
      // Desktop: remove mobile classes
      sidebar.classList.remove('show');
      body.classList.remove('sidebar-open');

      // Restore collapsed state from localStorage
      const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
      if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
      } else {
        sidebar.classList.remove('collapsed');
      }
    } else {
      // Mobile: remove collapsed class
      sidebar.classList.remove('collapsed');
    }
  }, 250);
});

// Restore sidebar state on page load (desktop only)
document.addEventListener('DOMContentLoaded', function() {
  if (window.innerWidth > 768) {
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
      document.querySelector('.sidebar')?.classList.add('collapsed');
    }
  }
});

// ========================================
// DARK MODE TOGGLE
// ========================================

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');

  // Save preference to localStorage
  const isDarkMode = document.body.classList.contains('dark-mode');
  localStorage.setItem('darkMode', isDarkMode);

  // Update icon
  const icon = document.querySelector('.theme-toggle i');
  if (icon) {
    icon.className = isDarkMode ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
  }
}

// Restore dark mode preference on page load
document.addEventListener('DOMContentLoaded', function() {
  const darkMode = localStorage.getItem('darkMode') === 'true';
  if (darkMode) {
    document.body.classList.add('dark-mode');
    const icon = document.querySelector('.theme-toggle i');
    if (icon) {
      icon.className = 'bi bi-sun-fill';
    }
  }
});

// ========================================
// TOAST NOTIFICATIONS
// ========================================

function showToast(message, type = 'info') {
  // Remove any existing toasts
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    existingToast.remove();
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast-notification toast-${type}`;

  // Icon based on type
  let icon = 'bi-info-circle';
  switch(type) {
    case 'success':
      icon = 'bi-check-circle-fill';
      break;
    case 'error':
      icon = 'bi-x-circle-fill';
      break;
    case 'warning':
      icon = 'bi-exclamation-triangle-fill';
      break;
  }

  toast.innerHTML = `
    <div class="toast-content">
      <i class="bi ${icon}"></i>
      <span>${message}</span>
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">
      <i class="bi bi-x"></i>
    </button>
  `;

  // Add to body
  document.body.appendChild(toast);

  // Animate in
  setTimeout(() => toast.classList.add('show'), 10);

  // Auto remove after 5 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

// Add toast styles dynamically
const toastStyles = `
  .toast-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    display: flex;
    align-items: center;
    gap: 1rem;
    transform: translateX(400px);
    transition: transform 0.3s ease;
    z-index: 9999;
    max-width: 400px;
  }

  .toast-notification.show {
    transform: translateX(0);
  }

  .toast-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex: 1;
  }

  .toast-content i {
    font-size: 1.25rem;
  }

  .toast-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem;
    opacity: 0.6;
    transition: opacity 0.2s;
  }

  .toast-close:hover {
    opacity: 1;
  }

  .toast-success {
    border-left: 4px solid #059669;
    color: #065f46;
  }

  .toast-success i {
    color: #059669;
  }

  .toast-error {
    border-left: 4px solid #dc2626;
    color: #991b1b;
  }

  .toast-error i {
    color: #dc2626;
  }

  .toast-warning {
    border-left: 4px solid #d97706;
    color: #92400e;
  }

  .toast-warning i {
    color: #d97706;
  }

  .toast-info {
    border-left: 4px solid #0284c7;
    color: #075985;
  }

  .toast-info i {
    color: #0284c7;
  }

  body.dark-mode .toast-notification {
    background: #1e293b;
    color: #f1f5f9;
  }
`;

// Inject toast styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// ========================================
// FORM VALIDATION
// ========================================

function validateForm(formId) {
  const form = document.getElementById(formId);
  if (!form) return false;

  let isValid = true;
  const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

  inputs.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add('is-invalid');
      input.classList.remove('is-valid');
      isValid = false;
    } else {
      input.classList.add('is-valid');
      input.classList.remove('is-invalid');
    }
  });

  return isValid;
}

// Real-time validation
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input[required], select[required], textarea[required]');

  inputs.forEach(input => {
    input.addEventListener('blur', function() {
      if (!this.value.trim()) {
        this.classList.add('is-invalid');
        this.classList.remove('is-valid');
      } else {
        this.classList.add('is-valid');
        this.classList.remove('is-invalid');
      }
    });

    input.addEventListener('input', function() {
      if (this.classList.contains('is-invalid') || this.classList.contains('is-valid')) {
        if (!this.value.trim()) {
          this.classList.add('is-invalid');
          this.classList.remove('is-valid');
        } else {
          this.classList.add('is-valid');
          this.classList.remove('is-invalid');
        }
      }
    });
  });
});

// ========================================
// CONFIRM DELETE
// ========================================

function confirmDelete(message = 'Tem certeza que deseja excluir este item?') {
  return confirm(message);
}

// ========================================
// ACTIVE NAV LINK
// ========================================

document.addEventListener('DOMContentLoaded', function() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.sidebar-nav-link');

  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
});

// ========================================
// SEARCH DEBOUNCE
// ========================================

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ========================================
// PRINT QR CODE
// ========================================

function printQRCode(qrImageUrl) {
  const printWindow = window.open('', '_blank');
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Imprimir QR Code</title>
      <style>
        body {
          display: flex;
          justify-content: center;
          align-items: center;
          height: 100vh;
          margin: 0;
        }
        img {
          max-width: 300px;
        }
      </style>
    </head>
    <body>
      <img src="${qrImageUrl}" onload="window.print(); window.close();" />
    </body>
    </html>
  `);
  printWindow.document.close();
}

// ========================================
// COPY TO CLIPBOARD
// ========================================

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    showToast('Copiado para a área de transferência!', 'success');
  } catch (err) {
    showToast('Erro ao copiar', 'error');
  }
}

// ========================================
// FORMAT DATE
// ========================================

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
}

function formatDateTime(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('pt-BR');
}

// ========================================
// LOADING SPINNER
// ========================================

function showLoading() {
  const spinner = document.createElement('div');
  spinner.id = 'loading-spinner';
  spinner.innerHTML = `
    <div class="spinner-backdrop">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Carregando...</span>
      </div>
    </div>
  `;
  document.body.appendChild(spinner);
}

function hideLoading() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) {
    spinner.remove();
  }
}

// Add spinner styles
const spinnerStyles = `
  #loading-spinner {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10000;
  }

  .spinner-backdrop {
    background: rgba(0, 0, 0, 0.5);
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .spinner-border {
    width: 3rem;
    height: 3rem;
    border: 0.25em solid rgba(255, 255, 255, 0.3);
    border-right-color: white;
    border-radius: 50%;
    animation: spinner-border 0.75s linear infinite;
  }

  @keyframes spinner-border {
    to { transform: rotate(360deg); }
  }
`;

const spinnerStyleSheet = document.createElement('style');
spinnerStyleSheet.textContent = spinnerStyles;
document.head.appendChild(spinnerStyleSheet);

// ========================================
// INITIALIZE
// ========================================

console.log('Sistema de Ativos - Frontend carregado com sucesso! ✓');
