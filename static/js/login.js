/**
 * iFound - Login e Cadastro
 * Interações da página de autenticação
 */

document.addEventListener('DOMContentLoaded', () => {

    // ==========================================
    // TROCA DE ABAS
    // ==========================================

    const authTabs = document.querySelectorAll('.auth-tab');
    const authTabContents = document.querySelectorAll('.auth-tab-content');

    authTabs.forEach(tab => {
        tab.addEventListener('click', () => {

            const tabName = tab.dataset.tab;

            authTabs.forEach(t => {
                t.classList.remove('active');
            });

            authTabContents.forEach(content => {
                content.classList.remove('active');
            });

            tab.classList.add('active');

            const targetContent = document.getElementById(`${tabName}-tab`);

            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });


    // ==========================================
    // MOSTRAR / OCULTAR SENHA
    // ==========================================

    const passwordToggles = document.querySelectorAll('.password-toggle');

    passwordToggles.forEach(toggle => {

        toggle.addEventListener('click', (event) => {

            event.preventDefault();

            const passwordInput =
                toggle.parentElement.querySelector('.form-input');

            const icon = toggle.querySelector('i');

            if (!passwordInput) {
                return;
            }

            if (passwordInput.type === 'password') {

                passwordInput.type = 'text';

                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');

                toggle.setAttribute(
                    'aria-label',
                    'Ocultar senha'
                );

            } else {

                passwordInput.type = 'password';

                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');

                toggle.setAttribute(
                    'aria-label',
                    'Mostrar senha'
                );
            }
        });
    });


    // ==========================================
    // LEMBRAR MATRÍCULA
    // ==========================================

    const rememberCheckbox =
        document.getElementById('remember');

    const usernameInput =
        document.getElementById('username');

    if (rememberCheckbox && usernameInput) {

        const remembered =
            localStorage.getItem('ifound_remember_me') === 'true';

        if (remembered) {

            rememberCheckbox.checked = true;

            const savedUsername =
                localStorage.getItem('ifound_username');

            if (savedUsername) {
                usernameInput.value = savedUsername;
            }
        }

        const loginForm =
            usernameInput.closest('form');

        if (loginForm) {

            loginForm.addEventListener('submit', () => {

                if (rememberCheckbox.checked) {

                    localStorage.setItem(
                        'ifound_username',
                        usernameInput.value
                    );

                    localStorage.setItem(
                        'ifound_remember_me',
                        'true'
                    );

                } else {

                    localStorage.removeItem(
                        'ifound_username'
                    );

                    localStorage.removeItem(
                        'ifound_remember_me'
                    );
                }
            });
        }
    }


    // ==========================================
    // RECUPERAÇÃO DE SENHA
    // ==========================================

    const forgotPasswordLink =
        document.querySelector('.forgot-password');

    if (forgotPasswordLink) {

        forgotPasswordLink.addEventListener('click', (event) => {

            event.preventDefault();

            alert(
                'A recuperação de senha ainda não está disponível. ' +
                'Entre em contato com a administração do iFound.'
            );
        });
    }


    // ==========================================
    // VALIDAÇÃO DOS CAMPOS
    // ==========================================

    const formInputs =
        document.querySelectorAll('.form-input');

    formInputs.forEach(input => {

        input.addEventListener('blur', () => {

            if (
                input.hasAttribute('required') &&
                input.value.trim() === ''
            ) {

                input.classList.add('invalid');

            } else {

                input.classList.remove('invalid');
            }
        });

        input.addEventListener('input', () => {

            if (input.value.trim() !== '') {
                input.classList.remove('invalid');
            }
        });
    });


    // ==========================================
    // VALIDAÇÃO DAS SENHAS NO CADASTRO
    // ==========================================

    const signupForm =
        document.querySelector('#signup-tab form');

    const signupPassword =
        document.getElementById('signup_password');

    const passwordConfirm =
        document.getElementById('password_confirm');

    if (
        signupForm &&
        signupPassword &&
        passwordConfirm
    ) {

        signupForm.addEventListener('submit', (event) => {

            if (
                signupPassword.value !==
                passwordConfirm.value
            ) {

                event.preventDefault();

                passwordConfirm.classList.add('invalid');

                alert('As senhas não coincidem.');

                passwordConfirm.focus();

            } else {

                passwordConfirm.classList.remove('invalid');
            }
        });
    }


    // ==========================================
    // EXIBIR MENSAGENS DE ERRO
    // ==========================================

    const alertMessages =
        document.querySelectorAll('.alert-error');

    if (alertMessages.length > 0) {

        setTimeout(() => {

            const firstMessage =
                alertMessages[0];

            firstMessage.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });

        }, 100);
    }

});