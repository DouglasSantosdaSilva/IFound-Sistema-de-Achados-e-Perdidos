/**
 * iFound - Login Page Interactions
 * Handles tab switching and password visibility toggle
 */

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching functionality
    const authTabs = document.querySelectorAll('.auth-tab');
    const authTabContents = document.querySelectorAll('.auth-tab-content');

    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;

            // Remove active class from all tabs and contents
            authTabs.forEach(t => t.classList.remove('active'));
            authTabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked tab
            tab.classList.add('active');

            // Add active class to corresponding content
            const targetContent = document.getElementById(`${tabName}-tab`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // Password visibility toggle
    const passwordToggles = document.querySelectorAll('.password-toggle');

    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            
            const passwordInput = toggle.parentElement.querySelector('.form-input');
            const icon = toggle.querySelector('i');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
                toggle.setAttribute('aria-label', 'Ocultar senha');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
                toggle.setAttribute('aria-label', 'Mostrar senha');
            }
        });
    });

    // Remember me checkbox
    const rememberCheckbox = document.getElementById('remember');
    if (rememberCheckbox) {
        // Load remembered value from localStorage
        const remembered = localStorage.getItem('ifound_remember_me') === 'true';
        if (remembered) {
            rememberCheckbox.checked = true;
            const username = localStorage.getItem('ifound_username');
            const usernameInput = document.getElementById('username');
            if (usernameInput && username) {
                usernameInput.value = username;
            }
        }

        // Save on form submit
        const form = document.querySelector('.auth-form');
        if (form) {
            form.addEventListener('submit', () => {
                const usernameInput = document.getElementById('username');
                if (rememberCheckbox.checked && usernameInput) {
                    localStorage.setItem('ifound_username', usernameInput.value);
                    localStorage.setItem('ifound_remember_me', 'true');
                } else {
                    localStorage.removeItem('ifound_username');
                    localStorage.removeItem('ifound_remember_me');
                }
            });
        }
    }

    // Forgot password link (placeholder)
    const forgotPasswordLink = document.querySelector('.forgot-password');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', (e) => {
            e.preventDefault();
            alert('Por favor, acesse o portal SUAP para recuperar sua senha: https://suap.ifrn.edu.br');
        });
    }

    // Form validation feedback
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    if (usernameInput) {
        usernameInput.addEventListener('blur', () => {
            if (usernameInput.value.trim() === '') {
                usernameInput.classList.add('invalid');
            } else {
                usernameInput.classList.remove('invalid');
            }
        });
    }

    if (passwordInput) {
        passwordInput.addEventListener('blur', () => {
            if (passwordInput.value.trim() === '') {
                passwordInput.classList.add('invalid');
            } else {
                passwordInput.classList.remove('invalid');
            }
        });
    }

    // Smooth scroll to form on error
    const alertMessages = document.querySelectorAll('.alert-error');
    if (alertMessages.length > 0) {
        // Scroll to alerts after short delay to ensure DOM is ready
        setTimeout(() => {
            alertMessages[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }
});
