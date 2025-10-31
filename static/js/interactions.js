/**
 * SISTEMA DE ATIVOS - INTERAÇÕES E ANIMAÇÕES
 * Gerencia toasts, loading states e micro-interações
 */

// ========================================
// TOAST NOTIFICATIONS
// ========================================

class ToastManager {
    constructor() {
        this.container = this.createContainer();
        this.toasts = [];
    }

    createContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    show(message, type = 'info', options = {}) {
        const {
            title = this.getDefaultTitle(type),
            duration = 5000,
            closeable = true
        } = options;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icon = this.getIcon(type);

        toast.innerHTML = `
            <div class="toast-icon">
                <i class="bi ${icon}"></i>
            </div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
            </div>
            ${closeable ? '<button class="toast-close"><i class="bi bi-x"></i></button>' : ''}
        `;

        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Add close handler
        if (closeable) {
            const closeBtn = toast.querySelector('.toast-close');
            closeBtn.addEventListener('click', () => this.hide(toast));
        }

        // Auto-hide
        if (duration > 0) {
            setTimeout(() => this.hide(toast), duration);
        }

        return toast;
    }

    hide(toast) {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300);
    }

    getIcon(type) {
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };
        return icons[type] || icons.info;
    }

    getDefaultTitle(type) {
        const titles = {
            success: 'Sucesso',
            error: 'Erro',
            warning: 'Atenção',
            info: 'Informação'
        };
        return titles[type] || titles.info;
    }

    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
}

// Instância global
const toast = new ToastManager();

// Substituir função showToast antiga se existir
window.showToast = (message, type = 'info') => {
    toast.show(message, type);
};

// ========================================
// LOADING OVERLAY
// ========================================

class LoadingManager {
    constructor() {
        this.overlay = null;
    }

    show(message = 'Carregando...') {
        this.hide(); // Remove qualquer loading anterior

        this.overlay = document.createElement('div');
        this.overlay.className = 'loading-overlay';
        this.overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner spinner-lg mb-3"></div>
                <p class="mb-0">${message}</p>
            </div>
        `;

        document.body.appendChild(this.overlay);
        document.body.style.overflow = 'hidden';
    }

    hide() {
        if (this.overlay && this.overlay.parentNode) {
            this.overlay.style.opacity = '0';
            setTimeout(() => {
                if (this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
                document.body.style.overflow = '';
            }, 300);
        }
    }
}

const loading = new LoadingManager();

// ========================================
// ANIMAÇÕES DE ENTRADA
// ========================================

const animateOnScroll = () => {
    const elements = document.querySelectorAll('.card, .stats-card, .btn');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 50);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
};

// ========================================
// RIPPLE EFFECT NOS BOTÕES
// ========================================

const addRippleEffect = () => {
    document.addEventListener('click', function(e) {
        const target = e.target.closest('.btn, .clickable-row');
        if (!target) return;

        const ripple = document.createElement('span');
        const rect = target.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');

        // Adiciona estilo inline para o ripple
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            pointer-events: none;
            animation: ripple 0.6s ease-out;
        `;

        const rippleContainer = target.querySelector('.ripple');
        if (rippleContainer) {
            rippleContainer.remove();
        }

        target.style.position = 'relative';
        target.style.overflow = 'hidden';
        target.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
};

// ========================================
// PROGRESS BAR HELPER
// ========================================

class ProgressBar {
    constructor(element) {
        this.element = element;
        this.fill = element.querySelector('.progress-bar-fill');
    }

    set(percentage) {
        const value = Math.max(0, Math.min(100, percentage));
        this.fill.style.width = `${value}%`;
        return this;
    }

    animate(from, to, duration = 1000) {
        const start = Date.now();
        const diff = to - from;

        const step = () => {
            const now = Date.now();
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);

            const value = from + (diff * progress);
            this.set(value);

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
        return this;
    }
}

// ========================================
// SMOOTH SCROLL
// ========================================

const initSmoothScroll = () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
};

// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Ativa animações
    setTimeout(animateOnScroll, 100);

    // Ativa ripple effect
    addRippleEffect();

    // Ativa smooth scroll
    initSmoothScroll();

    // Adiciona classe de carregado ao body
    document.body.classList.add('loaded');

    // Progress bars
    document.querySelectorAll('.progress-bar').forEach(el => {
        el.progressBar = new ProgressBar(el);
    });
});

// ========================================
// EXPORTS GLOBAIS
// ========================================

window.toast = toast;
window.loading = loading;
window.ProgressBar = ProgressBar;
