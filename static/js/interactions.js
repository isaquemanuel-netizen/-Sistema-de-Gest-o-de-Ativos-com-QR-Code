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

    // Inicializa tooltips modernos
    new ModernTooltip();

    // Inicializa contadores animados
    AnimatedCounter.observeAndAnimate();

    // Inicializa atalhos de teclado
    new KeyboardShortcuts();

    // Inicializa validação de formulários
    document.querySelectorAll('form[data-validate]').forEach(form => {
        FormValidator.initForm(form);
    });

    // Adiciona estilos de validação ao CSS
    const style = document.createElement('style');
    style.textContent = `
        .is-valid {
            border-color: #10b981 !important;
            box-shadow: 0 0 0 0.2rem rgba(16, 185, 129, 0.25) !important;
        }
        .is-invalid {
            border-color: #ef4444 !important;
            box-shadow: 0 0 0 0.2rem rgba(239, 68, 68, 0.25) !important;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 0.2rem rgba(10, 92, 60, 0.25);
        }
    `;
    document.head.appendChild(style);
});

// ========================================
// CONFIRMAÇÕES MODERNAS
// ========================================

class ConfirmDialog {
    constructor() {
        this.dialog = null;
    }

    show(options = {}) {
        const {
            title = 'Confirmar ação',
            message = 'Tem certeza que deseja continuar?',
            confirmText = 'Confirmar',
            cancelText = 'Cancelar',
            type = 'warning', // warning, danger, info
            onConfirm = () => {},
            onCancel = () => {}
        } = options;

        return new Promise((resolve) => {
            // Remove diálogos anteriores
            this.hide();

            // Cria overlay
            const overlay = document.createElement('div');
            overlay.className = 'confirm-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(4px);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.2s ease;
            `;

            // Cria diálogo
            this.dialog = document.createElement('div');
            this.dialog.className = `confirm-dialog confirm-${type}`;
            this.dialog.style.cssText = `
                background: white;
                border-radius: 12px;
                padding: 2rem;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                animation: scaleIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
            `;

            const icon = this.getIcon(type);
            const color = this.getColor(type);

            this.dialog.innerHTML = `
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <div style="
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        background: ${color}15;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        margin-bottom: 1rem;
                    ">
                        <i class="bi ${icon}" style="font-size: 2rem; color: ${color};"></i>
                    </div>
                    <h3 style="margin: 0 0 0.5rem 0; color: #111827;">${title}</h3>
                    <p style="color: #6b7280; margin: 0;">${message}</p>
                </div>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button class="confirm-cancel-btn" style="
                        padding: 0.75rem 1.5rem;
                        border: 2px solid #e5e7eb;
                        background: white;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        color: #6b7280;
                        transition: all 0.2s;
                    ">${cancelText}</button>
                    <button class="confirm-ok-btn" style="
                        padding: 0.75rem 1.5rem;
                        border: none;
                        background: ${color};
                        color: white;
                        border-radius: 8px;
                        cursor: pointer;
                        font-weight: 600;
                        transition: all 0.2s;
                        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    ">${confirmText}</button>
                </div>
            `;

            overlay.appendChild(this.dialog);
            document.body.appendChild(overlay);
            this.currentOverlay = overlay;

            // Handlers
            const confirmBtn = this.dialog.querySelector('.confirm-ok-btn');
            const cancelBtn = this.dialog.querySelector('.confirm-cancel-btn');

            confirmBtn.addEventListener('click', () => {
                onConfirm();
                resolve(true);
                this.hide();
            });

            cancelBtn.addEventListener('click', () => {
                onCancel();
                resolve(false);
                this.hide();
            });

            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    onCancel();
                    resolve(false);
                    this.hide();
                }
            });

            // Hover effects
            confirmBtn.addEventListener('mouseenter', () => {
                confirmBtn.style.transform = 'translateY(-2px)';
                confirmBtn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.1)';
            });
            confirmBtn.addEventListener('mouseleave', () => {
                confirmBtn.style.transform = '';
                confirmBtn.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            });

            cancelBtn.addEventListener('mouseenter', () => {
                cancelBtn.style.background = '#f3f4f6';
            });
            cancelBtn.addEventListener('mouseleave', () => {
                cancelBtn.style.background = 'white';
            });
        });
    }

    hide() {
        if (this.currentOverlay && this.currentOverlay.parentNode) {
            this.currentOverlay.style.opacity = '0';
            setTimeout(() => {
                if (this.currentOverlay.parentNode) {
                    this.currentOverlay.parentNode.removeChild(this.currentOverlay);
                }
            }, 200);
        }
    }

    getIcon(type) {
        const icons = {
            warning: 'bi-exclamation-triangle-fill',
            danger: 'bi-x-circle-fill',
            info: 'bi-info-circle-fill',
            success: 'bi-check-circle-fill'
        };
        return icons[type] || icons.warning;
    }

    getColor(type) {
        const colors = {
            warning: '#f59e0b',
            danger: '#ef4444',
            info: '#3b82f6',
            success: '#10b981'
        };
        return colors[type] || colors.warning;
    }
}

const confirm = new ConfirmDialog();

// Sobrescrever window.confirm
window.confirmModern = (message, title) => {
    return confirm.show({
        title: title || 'Confirmar',
        message: message
    });
};

// ========================================
// CONTADORES ANIMADOS
// ========================================

class AnimatedCounter {
    static animate(element, target, duration = 2000) {
        const start = parseInt(element.textContent) || 0;
        const range = target - start;
        const startTime = Date.now();

        const step = () => {
            const now = Date.now();
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Easing function (easeOutExpo)
            const eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const current = Math.floor(start + (range * eased));

            element.textContent = current.toLocaleString('pt-BR');

            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                element.textContent = target.toLocaleString('pt-BR');
            }
        };

        requestAnimationFrame(step);
    }

    static observeAndAnimate() {
        const counters = document.querySelectorAll('[data-counter]');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    const target = parseInt(entry.target.dataset.counter);
                    AnimatedCounter.animate(entry.target, target);
                    entry.target.dataset.animated = 'true';
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => observer.observe(counter));
    }
}

// ========================================
// TOOLTIPS MODERNOS
// ========================================

class ModernTooltip {
    constructor() {
        this.tooltip = null;
        this.init();
    }

    init() {
        // Cria tooltip element
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'modern-tooltip';
        this.tooltip.style.cssText = `
            position: absolute;
            background: #1f2937;
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.875rem;
            z-index: 10001;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            white-space: nowrap;
            max-width: 300px;
        `;
        document.body.appendChild(this.tooltip);

        // Add arrow
        const arrow = document.createElement('div');
        arrow.style.cssText = `
            position: absolute;
            width: 8px;
            height: 8px;
            background: #1f2937;
            transform: rotate(45deg);
            bottom: -4px;
            left: 50%;
            margin-left: -4px;
        `;
        this.tooltip.appendChild(arrow);
        this.arrow = arrow;

        // Attach listeners
        this.attachListeners();
    }

    attachListeners() {
        document.addEventListener('mouseenter', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.show(target);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.hide();
            }
        }, true);
    }

    show(element) {
        const text = element.dataset.tooltip;
        if (!text) return;

        this.tooltip.childNodes[0].textContent = text;

        const rect = element.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();

        // Position above element
        this.tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltipRect.width / 2)}px`;
        this.tooltip.style.top = `${rect.top - tooltipRect.height - 10}px`;
        this.tooltip.style.opacity = '1';
    }

    hide() {
        this.tooltip.style.opacity = '0';
    }
}

// ========================================
// VALIDAÇÃO DE FORMULÁRIOS
// ========================================

class FormValidator {
    static validateField(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');
        let isValid = true;
        let message = '';

        // Remove previous validation
        FormValidator.clearValidation(input);

        if (required && !value) {
            isValid = false;
            message = 'Este campo é obrigatório';
        } else if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Email inválido';
            }
        } else if (input.hasAttribute('minlength')) {
            const minLength = parseInt(input.getAttribute('minlength'));
            if (value.length < minLength) {
                isValid = false;
                message = `Mínimo de ${minLength} caracteres`;
            }
        }

        FormValidator.showValidation(input, isValid, message);
        return isValid;
    }

    static showValidation(input, isValid, message) {
        const parent = input.parentElement;

        if (isValid) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');

            // Add error message
            const error = document.createElement('div');
            error.className = 'invalid-feedback';
            error.textContent = message;
            error.style.cssText = 'display: block; color: #ef4444; font-size: 0.875rem; margin-top: 0.25rem;';
            parent.appendChild(error);
        }
    }

    static clearValidation(input) {
        input.classList.remove('is-valid', 'is-invalid');
        const feedback = input.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    static initForm(form) {
        const inputs = form.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value) {
                    FormValidator.validateField(input);
                }
            });

            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    FormValidator.validateField(input);
                }
            });
        });

        form.addEventListener('submit', (e) => {
            let isValid = true;
            inputs.forEach(input => {
                if (!FormValidator.validateField(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                toast.error('Por favor, corrija os erros no formulário');
            }
        });
    }
}

// ========================================
// ATALHOS DE TECLADO
// ========================================

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            const key = this.getKeyCombo(e);
            const handler = this.shortcuts.get(key);

            if (handler && !this.isInputFocused()) {
                e.preventDefault();
                handler(e);
            }
        });

        // Register default shortcuts
        this.register('ctrl+k', () => {
            const search = document.querySelector('#globalSearch');
            if (search) search.focus();
        });

        this.register('ctrl+n', () => {
            const newBtn = document.querySelector('[href*="novo"]');
            if (newBtn) newBtn.click();
        });

        this.register('?', () => {
            this.showHelp();
        });
    }

    register(combo, handler) {
        this.shortcuts.set(combo.toLowerCase(), handler);
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        return parts.join('+');
    }

    isInputFocused() {
        const active = document.activeElement;
        return ['INPUT', 'TEXTAREA', 'SELECT'].includes(active.tagName);
    }

    showHelp() {
        confirm.show({
            title: '⌨️ Atalhos de Teclado',
            message: `
                Ctrl + K: Buscar<br>
                Ctrl + N: Novo item<br>
                ?: Mostrar ajuda
            `,
            confirmText: 'Entendi',
            type: 'info',
            cancelText: ''
        });
    }
}

// ========================================
// EXPORTS GLOBAIS
// ========================================

window.toast = toast;
window.loading = loading;
window.ProgressBar = ProgressBar;
window.confirm = confirm;
window.confirmModern = (msg, title) => confirm.show({ message: msg, title: title || 'Confirmar' });
window.AnimatedCounter = AnimatedCounter;
window.FormValidator = FormValidator;
