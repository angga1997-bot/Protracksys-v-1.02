// login.js - Eel Login Page Script

function doLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorMsg = document.getElementById('error-msg');
    const btn = document.getElementById('loginBtn');
    const btnText = document.getElementById('btn-text');

    // Basic validation
    if (!username || !password) {
        errorMsg.textContent = '⚠️ Please enter username and password';
        errorMsg.classList.remove('hidden');
        return;
    }

    // Show loading state
    errorMsg.classList.add('hidden');
    btn.disabled = true;
    btnText.textContent = 'Signing in...';

    // Call Python login function via Eel
    eel.login(username, password)(function (result) {
        if (result.success) {
            btnText.textContent = '✅ Success!';
            btn.style.background = 'linear-gradient(135deg, #00c896, #00a876)';
        } else {
            btn.disabled = false;
            btnText.textContent = 'Login';
            errorMsg.textContent = '❌ ' + result.message;
            errorMsg.classList.remove('hidden');

            // Shake animation
            btn.style.animation = 'none';
            document.querySelector('.login-card').style.animation = 'shake 0.4s ease';
            setTimeout(() => {
                document.querySelector('.login-card').style.animation = '';
            }, 400);
        }
    });
}

// Allow pressing Enter to login
document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') doLogin();
});

// Add shake keyframe dynamically
const style = document.createElement('style');
style.textContent = `
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-8px); }
    40% { transform: translateX(8px); }
    60% { transform: translateX(-5px); }
    80% { transform: translateX(5px); }
}`;
document.head.appendChild(style);
