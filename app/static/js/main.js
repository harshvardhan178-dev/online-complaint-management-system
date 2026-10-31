// Main UI interactions & SaaS animations
document.addEventListener('DOMContentLoaded', () => {
    // Mobile sidebar toggle with backdrop
    const toggleBtn = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');

    function openSidebar() {
        if (sidebar) sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('active');
    }

    function closeSidebar() {
        if (sidebar) sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('active');
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', closeSidebar);
    }

    // Modal open/close triggers
    document.querySelectorAll('[data-modal-target]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = trigger.getAttribute('data-modal-target');
            const modal = document.getElementById(targetId);
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    document.querySelectorAll('.modal-close, [data-modal-close]').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            const modal = closeBtn.closest('.modal-overlay');
            if (modal) {
                modal.classList.remove('active');
            }
        });
    });

    // Close modal on background click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-overlay')) {
            e.target.classList.remove('active');
        }
    });

    // Auto dismiss alerts after 5 seconds with smooth fade
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Demo credential pills on login page
    document.querySelectorAll('.demo-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            const email = pill.getAttribute('data-email');
            const password = pill.getAttribute('data-password');
            const emailInput = document.getElementById('email');
            const passwordInput = document.getElementById('password');
            if (emailInput && passwordInput) {
                emailInput.value = email;
                passwordInput.value = password;
                // Highlight input momentarily
                emailInput.style.borderColor = '#0F766E';
                passwordInput.style.borderColor = '#0F766E';
            }
        });
    });

    // Dark / Light Theme Toggle
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const savedTheme = localStorage.getItem('smartcomplaint-theme') || 'light';
    if (savedTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeToggleBtn) themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            if (isDark) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('smartcomplaint-theme', 'light');
                themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            } else {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('smartcomplaint-theme', 'dark');
                themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            }
        });
    }
});
